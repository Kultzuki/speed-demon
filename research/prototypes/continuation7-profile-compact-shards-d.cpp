#include "common.hpp"

#include <chrono>
static auto phase_start=std::chrono::steady_clock::now();
static void phase(const char* label) {
 auto now=std::chrono::steady_clock::now();
 fprintf(stderr,"PHASE %s %.9f\n",label,std::chrono::duration<double>(now-phase_start).count());
 phase_start=now;
}

#include <atomic>
#include <array>
#include <bit>
#include <numeric>
#include <thread>
#include <mutex>
#include <memory>

struct Edge { uint32_t node, weight; };

// Destination width is derived from n. The remaining bits store small weights;
// a sentinel uses an exact, indexed overflow entry for every wider weight.
struct EdgeStore {
    std::vector<uint32_t> words;
    std::vector<std::pair<uint32_t,uint32_t>> overflow;
    std::mutex mutex;
    unsigned shift=0;
    uint32_t mask=0;
    void configure(uint32_t n) {
        unsigned bits=std::max(1u,unsigned(std::bit_width(n-1)));
        if (bits>=32) throw std::runtime_error("Graph exceeds compact node budget");
        shift=32-bits;mask=(uint32_t(1)<<shift)-1;
    }
    void resize(size_t count) {words.resize(count);}
    size_t size() const {return words.size();}
    void set(uint32_t i,Edge e) {
        words[i]=(e.node<<shift)|std::min(e.weight,mask);
        if (e.weight>=mask) {
            std::lock_guard<std::mutex> lock(mutex);
            overflow.emplace_back(i,e.weight);
        }
    }
    void finish() {std::sort(overflow.begin(),overflow.end());}
    Edge operator[](uint32_t i) const {
        uint32_t word=words[i],weight=word&mask;
        if (weight==mask) {
            auto at=std::lower_bound(overflow.begin(),overflow.end(),std::pair<uint32_t,uint32_t>{i,0});
            weight=at->second;
        }
        return {word>>shift,weight};
    }
    void swap(EdgeStore& other) {words.swap(other.words);overflow.swap(other.overflow);}
};

struct Graph {
    std::vector<uint32_t> offset[2];
    EdgeStore edges[2];
    uint32_t n;


    explicit Graph(const std::string& path) {
        MappedFile file(path);
        const char* p=file.data;
        n=integer(p);++p;
        uint32_t m=integer(p);++p;
        constexpr unsigned SHARDS=64;
        unsigned shift=unsigned(std::max(0,int(std::bit_width(n-1))-6));
        unsigned workers=std::min(6u,std::max(1u,std::thread::hardware_concurrency()));
        if(file.size<2*1024*1024) workers=1;
        std::vector<const char*> cuts(workers+1);
        cuts[0]=p;cuts[workers]=file.end();
        for(unsigned i=1;i<workers;++i) {
            auto at=p+(file.end()-p)*i/workers;
            while(at<file.end() && at[-1]!='\n') ++at;
            cuts[i]=at;
        }
        struct Triple {uint32_t u,v,w;};
        std::vector<std::vector<uint64_t>> parsed(workers);
        std::vector<std::vector<Triple>> wide(workers);
        for(auto& side:edges) side.configure(n);
        unsigned weight_bits=edges[0].shift;
        uint64_t sentinel=edges[0].mask;
        // A sentinel record indexes a growing per-worker stream, preserving
        // all endpoints and uint32 weights. Normal records need eight bytes.
        auto decode=[&](uint64_t word) -> Triple {
            if((word&sentinel)==sentinel) {
                uint64_t index=word>>weight_bits;
                return wide[index%workers][index/workers];
            }
            return {uint32_t(word>>32),uint32_t(word)>>weight_bits,uint32_t(word&sentinel)};
        };
        std::vector<std::array<uint32_t,SHARDS>> counts[2];
        for(auto& side:counts) side.resize(workers);
        std::vector<std::thread> threads;
        for(unsigned t=0;t<workers;++t) threads.emplace_back([&,t] {
            auto& part=parsed[t];
            part.reserve(size_t(m)/workers+4096);
            const char* at=cuts[t];
            while(at<cuts[t+1]) {
                uint32_t u=integer(at);++at;
                uint32_t v=integer(at);++at;
                uint32_t w=integer(at);++at;
                if(w>=sentinel) {
                    uint64_t index=uint64_t(wide[t].size())*workers+t;
                    if(index>(UINT64_MAX>>weight_bits)) std::terminate();
                    part.push_back((index<<weight_bits)|sentinel);
                    wide[t].push_back({u,v,w});
                } else part.push_back((uint64_t(u)<<32)|(uint64_t(v)<<weight_bits)|w);
                ++counts[0][t][u>>shift];++counts[1][t][v>>shift];
            }
        });
        for(auto& thread:threads) thread.join();
        threads.clear();
        std::unique_ptr<uint64_t[]> bucket(new uint64_t[m]);
        std::vector<uint32_t> cursor(n);
        for(auto& side:offset) side.resize(size_t(n)+1);
        for(unsigned d=0;d<2;++d) {
            std::array<uint32_t,SHARDS+1> first{};
            auto positions=counts[d];
            uint32_t total=0;
            for(unsigned b=0;b<SHARDS;++b) {
                first[b]=total;
                for(unsigned t=0;t<workers;++t) {
                    uint32_t count=counts[d][t][b];
                    positions[t][b]=total;total+=count;
                }
            }
            first[SHARDS]=total;
            if(total!=m) throw std::runtime_error("Edge count mismatch");
            for(unsigned t=0;t<workers;++t) threads.emplace_back([&,t] {
                auto at=positions[t];
                for(uint64_t word:parsed[t]) {
                    auto edge=decode(word);
                    bucket[at[(d?edge.v:edge.u)>>shift]++]=word;
                }
            });
            for(auto& thread:threads) thread.join();
            threads.clear();
            if(d) std::vector<std::vector<uint64_t>>{}.swap(parsed);
            edges[d].configure(n);edges[d].resize(m);
            std::atomic<unsigned> next{0};
            for(unsigned t=0;t<workers;++t) threads.emplace_back([&] {
                for(unsigned b;(b=next.fetch_add(1,std::memory_order_relaxed))<SHARDS;) {
                    uint32_t lo=std::min<uint64_t>(n,uint64_t(b)<<shift);
                    uint32_t hi=std::min<uint64_t>(n,uint64_t(b+1)<<shift);
                    for(uint32_t i=first[b];i<first[b+1];++i) {
                        auto edge=decode(bucket[i]);
                        ++offset[d][(d?edge.v:edge.u)+1];
                    }
                    uint32_t sum=first[b];
                    for(uint32_t u=lo;u<hi;++u) {
                        cursor[u]=sum;sum+=offset[d][u+1];offset[d][u+1]=sum;
                    }
                    for(uint32_t i=first[b];i<first[b+1];++i) {
                        auto edge=decode(bucket[i]);
                        uint32_t u=d?edge.v:edge.u,v=d?edge.u:edge.v;
                        edges[d].set(cursor[u]++,{v,edge.w});
                    }
                }
            });
            for(auto& thread:threads) thread.join();
            threads.clear();
            edges[d].finish();
        }
    }

};

// Non-negative edges make extracted distances monotone. A radix heap groups
// keys by the highest bit differing from the last extracted distance.
struct RadixHeap {
    using Item = std::pair<uint64_t, uint32_t>;
    std::array<std::vector<Item>, 65> buckets;
    uint64_t last = 0;
    size_t size = 0;
    void clear() { for (auto& b : buckets) b.clear(); last = 0; size = 0; }
    bool empty() const { return size == 0; }
    void push(uint64_t key, uint32_t node) {
        buckets[std::bit_width(key ^ last)].emplace_back(key, node); ++size;
    }
    const Item& top() {
        if (buckets[0].empty()) {
            unsigned i = 1;
            while (buckets[i].empty()) ++i;
            last = UINT64_MAX;
            for (auto [key, node] : buckets[i]) last = std::min(last, key);
            for (auto item : buckets[i]) buckets[std::bit_width(item.first ^ last)].push_back(item);
            buckets[i].clear();
        }
        return buckets[0].back();
    }
    Item pop() { Item item = top(); buckets[0].pop_back(); --size; return item; }
};


struct SparseState {
    struct Slot {uint64_t distance=0;uint32_t node=0,epoch=0;};
    std::vector<Slot> slots=std::vector<Slot>(1024);
    uint32_t epoch=0;
    size_t used=0;
    void clear() {
        used=0;
        if (!++epoch) {for (auto& slot:slots) slot.epoch=0;epoch=1;}
    }
    uint64_t get(uint32_t node) const {
        size_t at=(node*2654435761u)&(slots.size()-1);
        while (slots[at].epoch==epoch) {
            if (slots[at].node==node) return slots[at].distance;
            at=(at+1)&(slots.size()-1);
        }
        return UINT64_MAX/2;
    }
    void set(uint32_t node,uint64_t distance) {
        if ((used+1)*2>=slots.size()) {
            std::vector<Slot> grown(slots.size()*2);
            for (auto slot:slots) if (slot.epoch==epoch) {
                size_t at=(slot.node*2654435761u)&(grown.size()-1);
                while (grown[at].epoch==epoch) at=(at+1)&(grown.size()-1);
                grown[at]=slot;
            }
            slots.swap(grown);
        }
        size_t at=(node*2654435761u)&(slots.size()-1);
        while (slots[at].epoch==epoch && slots[at].node!=node) at=(at+1)&(slots.size()-1);
        if (slots[at].epoch!=epoch) ++used;
        slots[at]={distance,node,epoch};
    }
};

struct Search {
    SparseState state[2];
    RadixHeap heap[2];
    static constexpr uint64_t INF=UINT64_MAX/2;
    explicit Search(uint32_t) {}
    void push(int dir, uint64_t d, uint32_t v) {
        heap[dir].push(d, v);
    }
    int64_t run(const Graph& graph, uint32_t s, uint32_t t) {
        if (s == t) return 0;
        if (graph.offset[0][s] == graph.offset[0][s + 1] || graph.offset[1][t] == graph.offset[1][t + 1]) return -1;
        for (auto& h : heap) h.clear();
        for (auto& side:state) side.clear();
        state[0].set(s,0);state[1].set(t,0);
        push(0, 0, s); push(1, 0, t);
        uint64_t best = INF;
        for (;;) {
            for (int d = 0; d < 2; ++d)
                while (!heap[d].empty() && heap[d].top().first != state[d].get(heap[d].top().second)) heap[d].pop();
            if (heap[0].empty() || heap[1].empty()) break;
            // Every unfinished s-t path costs at least the two frontier minima.
            if (heap[0].top().first + heap[1].top().first >= best) break;
            int dir = heap[0].size <= heap[1].size ? 0 : 1;
            auto [du, u] = heap[dir].pop();
            best=std::min(best,du+state[1-dir].get(u));
            for (uint32_t i = graph.offset[dir][u]; i < graph.offset[dir][u + 1]; ++i) {
                auto [v, w] = graph.edges[dir][i];
                uint64_t nd = du + w;
                if (nd<state[dir].get(v)) {
                    state[dir].set(v,nd);
                    push(dir, nd, v);
                    best=std::min(best,nd+state[1-dir].get(v));
                }
            }
        }
        return best == INF ? -1 : static_cast<int64_t>(best);
    }
};

int main(int argc, char** argv) {
    try {
        Paths paths(argc, argv);
        Graph graph(paths.data + "/graph.txt"); phase("build-cleanup");
        MappedFile file(paths.data + "/queries.txt");
        std::vector<std::pair<uint32_t, uint32_t>> queries;
        const char* p = file.data;
        while (p < file.end()) {
            uint32_t s = integer(p); ++p;
            uint32_t t = integer(p); ++p;
            queries.emplace_back(s,t);
        }
        phase("parse-queries"); std::vector<int64_t> answers(queries.size());
        std::atomic<size_t> next{0};
        unsigned workers = std::min(6u, std::max(1u, std::thread::hardware_concurrency()));
        workers=std::min(12u,std::max(1u,std::thread::hardware_concurrency()));
        if (queries.size() < 100) workers = 1;
        std::vector<std::thread> threads;
        for (unsigned i = 0; i < workers; ++i) threads.emplace_back([&] {
            Search search(graph.n);
            for (;;) {
                size_t q = next.fetch_add(1, std::memory_order_relaxed);
                if (q >= queries.size()) break;
                answers[q] = search.run(graph, queries[q].first, queries[q].second);
            }
        });
        for (auto& thread : threads) thread.join();
        phase("search"); std::string output;
        for (auto answer : answers) { number(output, answer); output += '\n'; }
        phase("format"); write_output(paths.out + "/distances.txt", output);
    phase("output"); } catch (const std::exception& e) { fprintf(stderr, "%s\n", e.what()); return 1; }
}
