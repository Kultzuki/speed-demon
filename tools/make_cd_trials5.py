"""Independent bounded CSV structural scanning and forward-search experiments."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/prototypes'

STRUCTURE=r'''
// Quote parity masks exclude commas and LFs in quoted fields. Loads stay
// inside this worker's complete-record range, including the final short tail.
struct Structure {
    struct Separator {const char* at;uint64_t quotes;};
    const char* next_block;
    const char* block=nullptr;
    const char* end;
    uint32_t quotes=0,bits=0;
    uint64_t before=0;
    bool carry=false;
    Structure(const char* begin,const char* limit):next_block(begin),end(limit) {}
    Separator next() {
        while(!bits) {
            before+=std::popcount(quotes);quotes=0;
            if(next_block==end) return {end,before};
            block=next_block;
            size_t n=std::min<size_t>(32,end-block);
            alignas(32) char tail[32]{};
            const char* input=block;
            if(n<32) {memcpy(tail,block,n);input=tail;}
            auto bytes=_mm256_loadu_si256(reinterpret_cast<const __m256i*>(input));
            quotes=uint32_t(_mm256_movemask_epi8(_mm256_cmpeq_epi8(bytes,_mm256_set1_epi8('"'))));
            auto parity=_mm_clmulepi64_si128(_mm_cvtsi64_si128(quotes),_mm_set1_epi8(-1),0);
            uint32_t inside=uint32_t(_mm_cvtsi128_si64(parity))^(carry?UINT32_MAX:0);
            carry=inside>>31;
            bits=uint32_t(_mm256_movemask_epi8(_mm256_or_si256(_mm256_cmpeq_epi8(bytes,_mm256_set1_epi8(',')),_mm256_cmpeq_epi8(bytes,_mm256_set1_epi8('\n')))))&~inside;
            next_block+=n;
        }
        unsigned i=std::countr_zero(bits);bits&=bits-1;
        return {block+i,before+std::popcount(quotes&((uint32_t(1)<<i)-1))};
    }
};
'''

def structural(source, pipeline):
    source='#pragma GCC target("avx2,pclmul,popcnt")\n'+source
    source=source.replace('// Nodes never move.',STRUCTURE+'\n// Nodes never move.')
    source=source.replace('        while (p < end) {\n            if (static_cast', '        Structure separators(begin,end);\n        while (p < end) {\n            auto [f1,q1]=separators.next();auto [f2,q2]=separators.next();\n            auto [f3,q3]=separators.next();separators.next();separators.next();\n            if (static_cast')
    scratch='next.scratch' if pipeline else 'scratch'
    old=f'''            Field name = text_field(p, end, &{scratch});
            ++p;
            Field note = text_field(p, end, nullptr);
            ++p;'''
    new=f'''            uint64_t nq=q2-q1,tq=q3-q2;
            Field name{{{{p+(nq!=0),size_t(f2-p)-2*(nq!=0)}},size_t(f2-p)-(nq?nq/2+1:0)}};
            if(nq>2) name=text_field(p,f2,&{scratch});
            Field note{{{{}},size_t(f3-f2-1)-(tq?tq/2+1:0)}};
            p=f3+1;'''
    assert old in source
    return source.replace(old,new)

def forward(source):
    source=source.replace('    uint32_t n;','    uint32_t n;\n    std::vector<uint8_t> has_in;')
    source=source.replace('for (auto& side:offset) side.resize(size_t(n)+1);','offset[0].resize(size_t(n)+1);has_in.resize(n);')
    source=source.replace('std::atomic_ref<uint32_t>(offset[1][v+1]).fetch_add(1,std::memory_order_relaxed);','std::atomic_ref<uint8_t>(has_in[v]).store(1,std::memory_order_relaxed);')
    source=source.replace('for (unsigned d=0;d<2;++d)', 'for (unsigned d=0;d<1;++d)')
    source=source.replace('auto forward=offset[0],reverse=offset[1];', 'auto forward=offset[0];')
    source=source.replace('uint32_t b=std::atomic_ref<uint32_t>(reverse[v]).fetch_add(1,std::memory_order_relaxed);','')
    source=source.replace('edges[0].set(a,{v,w});edges[1].set(b,{u,w});', 'edges[0].set(a,{v,w});')
    start=source.index('    int64_t run(const Graph& graph,')
    stop=source.index('\n};\n\nint main',start)
    source=source[:start]+r'''
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
'''+source[stop:]
    return source

for piped in [False,True]:
    source=(OUT/('c-prefetch5.cpp' if piped else 'continuation5-start-c.cpp')).read_text()
    (OUT/('c-structure-prefetch5.cpp' if piped else 'c-structure5.cpp')).write_text(structural(source,piped),encoding='utf-8',newline='\n')
for window in [False,True]:
    source=(OUT/('d-window5.cpp' if window else 'continuation5-start-d.cpp')).read_text()
    (OUT/('d-forward-window5.cpp' if window else 'd-forward5.cpp')).write_text(forward(source),encoding='utf-8',newline='\n')
