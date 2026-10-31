"""Isolated, exact graph-construction and bitmap ownership experiments."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'

GRAPH = r'''
struct Graph {
    static constexpr uint32_t INLINE=3;
    std::vector<uint32_t> offset[2],degree[2];
    EdgeStore edges[2],local[2];
    uint32_t n;

    template<class F> void visit(unsigned d,uint32_t u,F&& emit) const {
        uint32_t count=degree[d][u];
        for(uint32_t i=0;i<std::min(count,INLINE);++i) emit(local[d][u*INLINE+i]);
        if(count>INLINE)
            for(uint32_t i=offset[d][u];i<offset[d][u+1];++i) emit(edges[d][i]);
    }

    explicit Graph(const std::string& path) {
        MappedFile file(path);
        const char* p=file.data;
        n=integer(p);++p;
        uint32_t m=integer(p);++p;
        if(uint64_t(n)*INLINE>UINT32_MAX) throw std::runtime_error("Graph exceeds inline index budget");
        unsigned workers=std::min(6u,std::max(1u,std::thread::hardware_concurrency()));
        if(file.size<2*1024*1024) workers=1;
        std::vector<const char*> cuts(workers+1);
        cuts[0]=p;cuts[workers]=file.end();
        for(unsigned i=1;i<workers;++i) {
            auto at=p+(file.end()-p)*i/workers;
            while(at<file.end() && at[-1]!='\n') ++at;
            cuts[i]=at;
        }
        for(unsigned d=0;d<2;++d) {
            degree[d].resize(n);
            local[d].configure(n);local[d].resize(size_t(n)*INLINE);
            edges[d].configure(n);
        }
        struct Extra {uint32_t tail,head,weight;};
        std::vector<std::array<std::vector<Extra>,2>> spill(workers);
        std::vector<std::thread> threads;
        for(unsigned t=0;t<workers;++t) threads.emplace_back([&,t] {
            for(auto& side:spill[t]) side.reserve(m/workers/4+64);
            auto put=[&](unsigned d,uint32_t u,uint32_t v,uint32_t w) {
                uint32_t slot=std::atomic_ref<uint32_t>(degree[d][u]).fetch_add(1,std::memory_order_relaxed);
                if(slot<INLINE) local[d].set(u*INLINE+slot,{v,w});
                else spill[t][d].push_back({u,v,w});
            };
            const char* at=cuts[t];
            while(at<cuts[t+1]) {
                uint32_t u=integer(at);++at;
                uint32_t v=integer(at);++at;
                uint32_t w=integer(at);++at;
                put(0,u,v,w);put(1,v,u,w);
            }
        });
        for(auto& thread:threads) thread.join();
        threads.clear();
        for(unsigned d=0;d<2;++d) threads.emplace_back([&,d] {
            offset[d].resize(size_t(n)+1);
            for(uint32_t u=0;u<n;++u)
                offset[d][u+1]=offset[d][u]+(degree[d][u]>INLINE?degree[d][u]-INLINE:0);
            edges[d].resize(offset[d].back());
            auto cursor=offset[d];
            for(auto& part:spill) for(auto edge:part[d])
                edges[d].set(cursor[edge.tail]++,{edge.head,edge.weight});
            local[d].finish();edges[d].finish();
        });
        for(auto& thread:threads) thread.join();
    }
};
'''


def save(name, source):
    path = PROTO / (name + '.cpp')
    if path.exists():
        raise FileExistsError(path)
    path.write_text(source)


def main():
    d = (PROTO / 'continuation7-base-d.cpp').read_text()
    start = d.index('struct Graph {')
    stop = d.index('// Non-negative edges')
    d = d[:start] + GRAPH + '\n' + d[stop:]
    d = d.replace('graph.offset[0][s] == graph.offset[0][s + 1] || graph.offset[1][t] == graph.offset[1][t + 1]',
                  'graph.degree[0][s] == 0 || graph.degree[1][t] == 0')
    d = d.replace('for (uint32_t i = graph.offset[dir][u]; i < graph.offset[dir][u + 1]; ++i) {\n                auto [v, w] = graph.edges[dir][i];',
                  'graph.visit(dir,u,[&](Edge edge) {\n                auto [v, w] = edge;')
    d = d.replace('best=std::min(best,nd+state[1-dir].get(v));\n                }\n            }',
                  'best=std::min(best,nd+state[1-dir].get(v));\n                }\n            });')
    save('continuation7-inline3-d', d)
    save('continuation7-inline4-d', d.replace('INLINE=3', 'INLINE=4'))
    save('continuation7-inline3-build12-d', d.replace('std::min(6u,', 'std::min(12u,', 1))
    b = (PROTO / 'continuation7-base-b.cpp').read_text()
    b = b.replace('const u32 first = ix.first[t] = begin < end ? parse_id(begin) : 0;',
                  'const u32 first = ix.first[t] = begin < end ? parse_id(begin) : 0;\n            const u32 stop_doc=end<base+size?parse_id(end):ix.docs;')
    old = '''std::atomic_ref<u64>(ix.bits[d * ix.words + doc / 64])
                        .fetch_or(1ull << (doc % 64), std::memory_order_relaxed);'''
    new = '''u64& word=ix.bits[d * ix.words + doc / 64];
                    u64 bit=1ull<<(doc%64);
                    if(doc/64>first/64 && doc/64<stop_doc/64) word|=bit;
                    else std::atomic_ref<u64>(word).fetch_or(bit,std::memory_order_relaxed);'''
    assert old in b
    save('continuation7-ownedbits-b', b.replace(old, new))
    print('Created inline/spill D variants and exclusive-interior-word B variant.')


if __name__ == '__main__':
    main()
