#include "common.hpp"
#include <atomic>
#include <array>
#include <bit>
#include <numeric>
#include <thread>
#include <mutex>

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
    std::vector<uint8_t> has_in;

    explicit Graph(const std::string& path) {
        MappedFile file(path);
        const char* p=file.data;
        n=integer(p);++p;
        uint32_t m=integer(p);++p;
        unsigned workers=std::min(6u,std::max(1u,std::thread::hardware_concurrency()));
        if (file.size<2*1024*1024) workers=1;
        std::vector<const char*> cuts(workers+1);
        cuts[0]=p;cuts[workers]=file.end();
        for (unsigned i=1;i<workers;++i) {
            auto at=p+(file.end()-p)*i/workers;
            while (at<file.end() && at[-1]!='\n') ++at;
            cuts[i]=at;
        }
        offset[0].resize(size_t(n)+1);has_in.resize(n);
        std::vector<std::thread> threads;
        // Atomic references avoid allocating a second degree table.
        for (unsigned i=0;i<workers;++i) threads.emplace_back([&,i] {
            const char* at=cuts[i];
            while (at<cuts[i+1]) {
                uint32_t u=integer(at);++at;
                uint32_t v=integer(at);++at;
                integer(at);++at;
                std::atomic_ref<uint32_t>(offset[0][u+1]).fetch_add(1,std::memory_order_relaxed);
                std::atomic_ref<uint8_t>(has_in[v]).store(1,std::memory_order_relaxed);
            }
        });
        for (auto& t:threads)t.join();
        for (unsigned d=0;d<1;++d) {
            std::partial_sum(offset[d].begin(),offset[d].end(),offset[d].begin());
            edges[d].configure(n);edges[d].resize(m);
        }
        auto forward=offset[0];
        threads.clear();
        for (unsigned i=0;i<workers;++i) threads.emplace_back([&,i] {
            const char* at=cuts[i];
            while (at<cuts[i+1]) {
                uint32_t u=integer(at);++at;
                uint32_t v=integer(at);++at;
                uint32_t w=integer(at);++at;
                uint32_t a=std::atomic_ref<uint32_t>(forward[u]).fetch_add(1,std::memory_order_relaxed);
                
                edges[0].set(a,{v,w});
            }
        });
        for (auto& t:threads)t.join();
        for (auto& side:edges) side.finish();
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



// Most edge relaxations stay within a short monotone window. The radix heap
// retains every farther uint64 key exactly, without narrowing or restarting.
struct WindowHeap {
    static constexpr uint64_t WIDTH=4096;
    std::array<std::vector<uint32_t>,WIDTH> ring;
    RadixHeap far;
    uint64_t last=0;
    size_t size=0,near=0;
    using Item=RadixHeap::Item;
    bool use_far=false;
    void clear() {for(auto& b:ring)b.clear();far.clear();last=0;size=near=0;}
    bool empty() const {return !size;}
    void push(uint64_t d,uint32_t v) {
        if(d-last<WIDTH) {ring[d&(WIDTH-1)].push_back(v);++near;}
        else far.push(d,v);
        ++size;
    }
    Item top() {
        uint64_t candidate=last;
        if(near) while(ring[candidate&(WIDTH-1)].empty()) ++candidate;
        else candidate=UINT64_MAX;
        if(!far.empty() && far.top().first<candidate) {use_far=true;return far.top();}
        use_far=false;
        last=candidate;
        return {last,ring[last&(WIDTH-1)].back()};
    }
    Item pop() {
        auto item=top();
        if(use_far) {
            item=far.pop();last=item.first;
        } else {ring[last&(WIDTH-1)].pop_back();--near;}
        --size;return item;
    }
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
    WindowHeap heap[2];
    static constexpr uint64_t INF=UINT64_MAX/2;
    explicit Search(uint32_t) {}
    void push(int dir, uint64_t d, uint32_t v) {
        heap[dir].push(d, v);
    }

    int64_t run(const Graph& graph,uint32_t s,uint32_t t) {
        if(s==t)return 0;
        if(graph.offset[0][s]==graph.offset[0][s+1] || !graph.has_in[t])return -1;
        state[0].clear();heap[0].clear();state[0].set(s,0);heap[0].push(0,s);
        while(!heap[0].empty()) {
            auto [du,u]=heap[0].pop();
            if(du!=state[0].get(u))continue;
            if(u==t)return du;
            for(uint32_t e=graph.offset[0][u];e<graph.offset[0][u+1];++e) {
                auto [v,w]=graph.edges[0][e];uint64_t nd=du+w;
                if(nd<state[0].get(v)) {state[0].set(v,nd);heap[0].push(nd,v);}
            }
        }
        return -1;
    }

};

int main(int argc, char** argv) {
    try {
        Paths paths(argc, argv);
        Graph graph(paths.data + "/graph.txt");
        MappedFile file(paths.data + "/queries.txt");
        std::vector<std::pair<uint32_t, uint32_t>> queries;
        const char* p = file.data;
        while (p < file.end()) {
            uint32_t s = integer(p); ++p;
            uint32_t t = integer(p); ++p;
            queries.emplace_back(s,t);
        }
        std::vector<int64_t> answers(queries.size());
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
        std::string output;
        for (auto answer : answers) { number(output, answer); output += '\n'; }
        write_output(paths.out + "/distances.txt", output);
    } catch (const std::exception& e) { fprintf(stderr, "%s\n", e.what()); return 1; }
}
