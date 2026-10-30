"""Generate exact sparse-state and parallel-construction graph experiments."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=(root/"track-d/main.cpp").read_text()
source=source.replace('std::vector<uint64_t> state[2];\n    uint64_t mask, epoch = 0;', r'''
    struct Label {uint64_t distance;uint32_t node;};
    std::vector<uint32_t> indices[2];
    std::vector<Label> labels[2];
    bool has(int dir,uint32_t v) const {
        uint32_t at=indices[dir][v];
        return at<labels[dir].size() && labels[dir][at].node==v;
    }
    uint64_t get(int dir,uint32_t v) const {return labels[dir][indices[dir][v]].distance;}
    void set(int dir,uint32_t v,uint64_t distance) {
        if (has(dir,v)) labels[dir][indices[dir][v]].distance=distance;
        else {indices[dir][v]=labels[dir].size();labels[dir].push_back({distance,v});}
    }''')
start=source.index('        // Every accepted shortest label')
stop=source.index('    void push(',start)
source=source[:start]+'''        for (auto& side:indices) side.resize(n);
    }
'''+source[stop:]
start=source.index('        epoch += mask + 1;')
stop=source.index('        push(0, 0, s);',start)
source=source[:start]+'''        for (auto& side:labels) side.clear();
        set(0,s,0);set(1,t,0);
'''+source[stop:]
source=source.replace('(state[d][heap[d].top().second] & mask)', 'get(d,heap[d].top().second)')
source=source.replace('(state[1 - dir][u] & ~mask) == epoch', 'has(1-dir,u)')
source=source.replace('(state[1 - dir][u] & mask)', 'get(1-dir,u)')
source=source.replace('(state[dir][v] & ~mask) != epoch || nd < (state[dir][v] & mask)', '!has(dir,v) || nd<get(dir,v)')
source=source.replace('state[dir][v] = epoch | nd;', 'set(dir,v,nd);')
source=source.replace('(state[1 - dir][v] & ~mask) == epoch', 'has(1-dir,v)')
source=source.replace('(state[1 - dir][v] & mask)', 'get(1-dir,v)')
(root/"research/prototypes/d-sparse.cpp").write_text(source)
start=source.index('    explicit Graph(')
stop=source.index('    void reorder()',start)
constructor=r'''
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
        for (auto& side:offset) side.resize(size_t(n)+1);
        std::vector<std::thread> threads;
        // Atomic references avoid allocating a second degree table.
        for (unsigned i=0;i<workers;++i) threads.emplace_back([&,i] {
            const char* at=cuts[i];
            while (at<cuts[i+1]) {
                uint32_t u=integer(at);++at;
                uint32_t v=integer(at);++at;
                integer(at);++at;
                std::atomic_ref<uint32_t>(offset[0][u+1]).fetch_add(1,std::memory_order_relaxed);
                std::atomic_ref<uint32_t>(offset[1][v+1]).fetch_add(1,std::memory_order_relaxed);
            }
        });
        for (auto& t:threads)t.join();
        for (unsigned d=0;d<2;++d) {
            std::partial_sum(offset[d].begin(),offset[d].end(),offset[d].begin());
            edges[d].resize(m);
        }
        auto forward=offset[0],reverse=offset[1];
        threads.clear();
        for (unsigned i=0;i<workers;++i) threads.emplace_back([&,i] {
            const char* at=cuts[i];
            while (at<cuts[i+1]) {
                uint32_t u=integer(at);++at;
                uint32_t v=integer(at);++at;
                uint32_t w=integer(at);++at;
                uint32_t a=std::atomic_ref<uint32_t>(forward[u]).fetch_add(1,std::memory_order_relaxed);
                uint32_t b=std::atomic_ref<uint32_t>(reverse[v]).fetch_add(1,std::memory_order_relaxed);
                edges[0][a]={v,w};edges[1][b]={u,w};
            }
        });
        for (auto& t:threads)t.join();
    }
'''
source=source[:start]+constructor+source[stop:]
(root/"research/prototypes/d-sparse-parallel.cpp").write_text(source)
old='int dir = heap[0].top().first <= heap[1].top().first ? 0 : 1;'
new='int dir = heap[0].size <= heap[1].size ? 0 : 1;'
assert old in source
(root/"research/prototypes/d-balanced-sparse-parallel.cpp").write_text(source.replace(old,new))
packed=(root/"track-d/main.cpp").read_text().replace(old,new)
(root/"research/prototypes/d-balanced.cpp").write_text(packed)
packed=packed[:packed.index('    explicit Graph(')]+constructor+packed[packed.index('    void reorder()'):]
(root/"research/prototypes/d-balanced-parallel.cpp").write_text(packed)
source=(root/"research/prototypes/d-balanced-sparse-parallel.cpp").read_text()
source=source.replace('#include <thread>','#include <thread>\n#include <mutex>')
store=r'''
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
    uint32_t node(uint32_t i) const {return words[i]>>shift;}
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
'''
source=source.replace('struct Graph {',store+'\nstruct Graph {')
source=source.replace('std::vector<Edge> edges[2];','EdgeStore edges[2];')
source=source.replace('edges[d].resize(m);','edges[d].configure(n);edges[d].resize(m);')
source=source.replace('edges[0][a]={v,w};edges[1][b]={u,w};','edges[0].set(a,{v,w});edges[1].set(b,{u,w});')
source=source.replace('for (auto& t:threads)t.join();\n    }\n    void reorder()',
                      'for (auto& t:threads)t.join();\n        for (auto& side:edges) side.finish();\n    }\n    void reorder()')
source=source.replace('uint32_t v = edges[0][i].node;', 'uint32_t v = edges[0].node(i);')
source=source.replace('std::vector<Edge> reordered_edges(edges[dir].size());', 'EdgeStore reordered_edges;reordered_edges.configure(n);reordered_edges.resize(edges[dir].size());')
source=source.replace('reordered_edges[position++] = {remap[edge.node], edge.weight};','reordered_edges.set(position++,{remap[edge.node],edge.weight});')
source=source.replace('offset[dir].swap(reordered_offsets); edges[dir].swap(reordered_edges);',
                      'reordered_edges.finish();offset[dir].swap(reordered_offsets); edges[dir].swap(reordered_edges);')
(root/"research/prototypes/d-compact.cpp").write_text(source)
for label in ['d-balanced-sparse-parallel','d-compact']:
    trial=(root/f'research/prototypes/{label}.cpp').read_text()
    trial=trial.replace('graph.reorder();','graph.remap.resize(graph.n);std::iota(graph.remap.begin(),graph.remap.end(),0);')
    (root/f'research/prototypes/{label}-identity.cpp').write_text(trial)
source=(root/'research/prototypes/d-balanced-sparse-parallel-identity.cpp').read_text()
source=source.replace('std::vector<std::thread> threads;\n        // Atomic references avoid allocating a second degree table.',r'''
        std::vector<std::thread> threads;
        std::vector<std::array<std::vector<uint32_t>,2>> counts(workers);
        for (auto& part:counts) for (auto& side:part) side.resize(n);
        // Each chunk owns its counters and later receives disjoint CSR ranges.''')
source=source.replace('std::atomic_ref<uint32_t>(offset[0][u+1]).fetch_add(1,std::memory_order_relaxed);\n                std::atomic_ref<uint32_t>(offset[1][v+1]).fetch_add(1,std::memory_order_relaxed);',
                      '++counts[i][0][u];++counts[i][1][v];')
old='''        for (unsigned d=0;d<2;++d) {
            std::partial_sum(offset[d].begin(),offset[d].end(),offset[d].begin());
            edges[d].resize(m);
        }
        auto forward=offset[0],reverse=offset[1];'''
new='''        for (unsigned d=0;d<2;++d) {
            uint32_t position=0;
            for (uint32_t u=0;u<n;++u) {
                offset[d][u]=position;
                for (unsigned i=0;i<workers;++i) {
                    uint32_t count=counts[i][d][u];
                    counts[i][d][u]=position;position+=count;
                }
            }
            offset[d][n]=position;edges[d].resize(m);
        }'''
assert old in source
source=source.replace(old,new)
source=source.replace('std::atomic_ref<uint32_t>(forward[u]).fetch_add(1,std::memory_order_relaxed)','counts[i][0][u]++')
source=source.replace('std::atomic_ref<uint32_t>(reverse[v]).fetch_add(1,std::memory_order_relaxed)','counts[i][1][v]++')
(root/'research/prototypes/d-private-build.cpp').write_text(source)
