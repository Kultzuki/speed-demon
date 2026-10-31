"""Measure BFS locality with bounded reusable full-width distance pages."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/prototypes'
source=(OUT/'continuation5-start-d.cpp').read_text()
REORDER=r'''
    std::vector<uint32_t> reorder() {
        std::vector<uint32_t> order,perm(n,UINT32_MAX);
        order.reserve(n);
        for(uint32_t root=0;root<n;++root) if(perm[root]==UINT32_MAX) {
            size_t first=order.size();perm[root]=first;order.push_back(root);
            for(size_t h=first;h<order.size();++h) {
                uint32_t u=order[h];
                for(uint32_t e=offset[0][u];e<offset[0][u+1];++e) {
                    uint32_t v=edges[0][e].node;
                    if(perm[v]==UINT32_MAX) {perm[v]=order.size();order.push_back(v);}
                }
            }
        }
        std::vector<uint32_t> head[2];EdgeStore packed[2];
        for(unsigned d=0;d<2;++d) {
            head[d].resize(size_t(n)+1);
            for(uint32_t v=0;v<n;++v) head[d][v+1]=head[d][v]+offset[d][order[v]+1]-offset[d][order[v]];
            packed[d].configure(n);packed[d].resize(edges[d].size());
        }
        std::vector<std::thread> pool;
        for(unsigned t=0;t<6;++t) pool.emplace_back([&,t] {
            uint32_t lo=uint64_t(n)*t/6,hi=uint64_t(n)*(t+1)/6;
            for(unsigned d=0;d<2;++d) for(uint32_t v=lo;v<hi;++v) {
                uint32_t u=order[v],at=head[d][v];
                for(uint32_t e=offset[d][u];e<offset[d][u+1];++e) {
                    auto old=edges[d][e];packed[d].set(at++,{perm[old.node],old.weight});
                }
            }
        });
        for(auto& t:pool)t.join();
        for(unsigned d=0;d<2;++d) {packed[d].finish();offset[d].swap(head[d]);edges[d].swap(packed[d]);}
        return perm;
    }
'''
at=source.index('\n};\n\n// Non-negative')
source=source[:at]+REORDER+source[at:]
supplied=(ROOT/'research/supplied-fifth/track-d.cpp').read_text()
start=supplied.index('class PagedDist {')
stop=supplied.index('\ntemplate <class F>',start)
paged=supplied[start:stop]
paged=paged.replace('u32','uint32_t').replace('u64','uint64_t').replace('INF','(UINT64_MAX/2)')
paged=paged.replace('static constexpr uint32_t PAGE = 512;', 'static constexpr uint32_t PAGE = 128;')
paged=paged.replace('void reset()', 'void clear()')
source=source.replace('struct Search {',paged+'\nstruct Search {')
source=source.replace('    SparseState state[2];','    PagedDist state[2];')
source=source.replace('    explicit Search(uint32_t) {}','    explicit Search(uint32_t n):state{PagedDist(n),PagedDist(n)} {}')
source=source.replace('        MappedFile file(paths.data + "/queries.txt");', '        auto perm=graph.reorder();\n        MappedFile file(paths.data + "/queries.txt");')
source=source.replace('            queries.emplace_back(s,t);','            queries.emplace_back(perm[s],perm[t]);')
source=source.replace('        std::vector<int64_t> answers(queries.size());','        std::vector<uint32_t>{}.swap(perm);\n        std::vector<int64_t> answers(queries.size());')
(OUT/'d-locality5.cpp').write_text(source,encoding='utf-8',newline='\n')
