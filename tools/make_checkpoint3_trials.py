"""Small, independently benchmarkable changes to the d069bfd kernels."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/prototypes'

def baseline(track):
    return (OUT/f'checkpoint3-{track}.cpp').read_text()

def save(label,source):
    (OUT/(label+'.cpp')).write_text(source)

def replace(source,old,new):
    assert source.count(old)==1,old
    return source.replace(old,new)

def main():
    source=baseline('b')
    start=source.index('// A vector load is permitted')
    stop=source.index('template<class Doc,class Offset> struct Occurrences',start)
    original=source[start:stop]
    scanner=r'''
// SIMD finds token boundaries in whole blocks; every load stays in the range.
template<class Emit> void scan_tokens(const char* p,const char* end,const Lookup& lookup,Emit emit) {
    const char* start=nullptr;
    auto finish=[&](const char* stop) {
        size_t length=stop-start;
        if (length>32) {emit(start,NONE);return;}
        alignas(32) char word[32]{};
        if (end-start>=32) {
            auto bytes=_mm256_loadu_si256(reinterpret_cast<const __m256i*>(start));
            _mm256_store_si256(reinterpret_cast<__m256i*>(word),_mm256_or_si256(bytes,_mm256_set1_epi8(32)));
        } else {
            for (size_t i=0;i<length;++i) word[i]=normalized(start[i]);
        }
        emit(start,lookup.find({word,length}));
    };
    while (end-p>=32) {
        auto bytes=_mm256_loadu_si256(reinterpret_cast<const __m256i*>(p));
        auto lower=_mm256_or_si256(bytes,_mm256_set1_epi8(32));
        auto letters=_mm256_and_si256(_mm256_cmpgt_epi8(lower,_mm256_set1_epi8('a'-1)),_mm256_cmpgt_epi8(_mm256_set1_epi8('z'+1),lower));
        auto digits=_mm256_and_si256(_mm256_cmpgt_epi8(bytes,_mm256_set1_epi8('0'-1)),_mm256_cmpgt_epi8(_mm256_set1_epi8('9'+1),bytes));
        uint32_t mask=_mm256_movemask_epi8(_mm256_or_si256(letters,digits));
        uint32_t events=mask^((mask<<1)|uint32_t(start!=nullptr));
        while (events) {
            unsigned i=std::countr_zero(events);
            if ((mask>>i)&1) start=p+i;
            else {finish(p+i);start=nullptr;}
            events&=events-1;
        }
        p+=32;
    }
    while (p<end) {
        if (raw_token(*p)) {if (!start) start=p;}
        else if (start) {finish(p);start=nullptr;}
        ++p;
    }
    if (start) finish(end);
}

'''
    # Keep the scalar-token reader for the small anchor sampling pass.
    source=source[:stop]+scanner+source[stop:]
    old='''                while (*current != '\\n') {
                    if (!raw_token(*current)) { ++current; continue; }
                    const char* start = current;
                    uint32_t id = read_token(current, cuts[worker + 1], lookup);
                    if (id == NONE) continue;'''
    new='''                const char* line_end=static_cast<const char*>(memchr(current,'\\n',cuts[worker+1]-current));
                scan_tokens(current,line_end,lookup,[&](const char* start,uint32_t id) {
                    if (id == NONE) return;'''
    source=replace(source,old,new)
    source=replace(source,'''                    }
                }
                ++current;
            }
        });''','''                    }
                });
                current=line_end+1;
            }
        });''')
    save('b-blockscan3',source)
    save('b-blockscan3-twelve',source.replace('std::min(6u,','std::min(12u,'))
    save('b-twelve3',baseline('b').replace('std::min(6u,','std::min(12u,'))
    b=(OUT/'b-twelve3.cpp').read_text()
    b=replace(b,'if (dense()) {storage.bits[(doc-base)/64]|=uint64_t(1)<<((doc-base)%64);return;}',
        'if (dense()) {if (count!=doc) {storage.bits[(doc-base)/64]|=uint64_t(1)<<((doc-base)%64);count=doc;}return;}')
    b=replace(b,'storage.bits=bits; capacity=UINT32_MAX; return;','storage.bits=bits; capacity=UINT32_MAX;count=doc; return;')
    save('b-dedup3',b)
    b=replace(b,'    size_t mask;','    size_t mask;\n    std::array<uint64_t,8192> filter{};\n    static uint64_t filter_bits(uint32_t h) {return (uint64_t(1)<<((h>>13)&63))|(uint64_t(1)<<((h>>19)&63));}')
    b=replace(b,'uint32_t hash = std::hash<std::string_view>()(word); size_t at = hash & mask;\n            while',
        'uint32_t hash = std::hash<std::string_view>()(word); size_t at = hash & mask;\n            filter[hash&8191]|=filter_bits(hash);\n            while')
    b=replace(b,'uint32_t hash = std::hash<std::string_view>()(word); size_t at = hash & mask;\n        for',
        'uint32_t hash = std::hash<std::string_view>()(word); size_t at = hash & mask;\n        uint64_t wanted=filter_bits(hash);\n        if ((filter[hash&8191]&wanted)!=wanted) return NONE;\n        for')
    save('b-bloom3',b)
    fast_lookup=r'''struct Lookup {
    struct Slot {uint64_t first=0;uint32_t length=0,id=NONE;};
    const std::vector<Term>& terms;
    std::vector<Slot> slots;
    size_t mask;
    static uint64_t first(std::string_view word) {
        uint64_t value=0;memcpy(&value,word.data(),std::min<size_t>(8,word.size()));return value;
    }
    static uint32_t hash(std::string_view word,uint64_t w0) {
        uint64_t h=(word.size()*UINT64_C(0x9E3779B97F4A7C15)^w0)*UINT64_C(0xFF51AFD7ED558CCD);
        for (size_t i=8;i<word.size();i+=8) {
            uint64_t w=0;memcpy(&w,word.data()+i,std::min<size_t>(8,word.size()-i));
            h=(h^w)*UINT64_C(0xFF51AFD7ED558CCD);
        }
        return h>>32;
    }
    explicit Lookup(const std::unordered_map<std::string_view,uint32_t>& dictionary,const std::vector<Term>& words):terms(words) {
        size_t capacity=1;while (capacity<dictionary.size()*2) capacity*=2;
        slots.resize(capacity);mask=capacity-1;
        for (auto [word,id]:dictionary) {
            uint64_t w0=first(word);size_t at=hash(word,w0)&mask;
            while (slots[at].id!=NONE) at=(at+1)&mask;
            slots[at]={w0,uint32_t(word.size()),id};
        }
    }
    uint32_t find(std::string_view word) const {
        uint64_t w0=first(word);size_t at=hash(word,w0)&mask;
        for (;;) {
            const auto& s=slots[at];
            if (s.id==NONE) return NONE;
            if (s.first==w0 && s.length==word.size() && (word.size()<=8 || terms[s.id].word==word)) return s.id;
            at=(at+1)&mask;
        }
    }
};

'''
    for label,trial in [('b-wordlookup3',baseline('b')),('b-blockwords3',source)]:
        begin=trial.index('struct Lookup {');end=trial.index('// A vector load is permitted',begin)
        save(label,trial[:begin]+fast_lookup+trial[end:])
    source=baseline('c')
    source=replace(source,'Node* insert(std::string_view name,size_t hash,Node* next) {','Node* insert(std::string_view name,size_t hash,Node* next,bool copy) {')
    source=replace(source,'size_t bytes=sizeof(Node)+name.size();','size_t bytes=sizeof(Node)+(copy?name.size():0);')
    source=replace(source,'std::string_view(data+sizeof(Node),name.size())','copy?std::string_view(data+sizeof(Node),name.size()):name')
    source=replace(source,'memcpy(data+sizeof(Node),name.data(),name.size());','if (copy) memcpy(data+sizeof(Node),name.data(),name.size());')
    source=replace(source,'bool add(std::string_view name,uint16_t country) {','bool add(std::string_view name,uint16_t country,bool copy=true) {')
    source=replace(source,'node=shard.insert(name,hash,first);','node=shard.insert(name,hash,first,copy);')
    source=replace(source,'names.add(name.value, country)','names.add(name.value, country, name.value.data()==scratch.data())')
    save('c-views3',source)
    source=replace(source,'    void parse(const char* begin, const char* end, const std::vector<uint16_t>& lookup, size_t count, SharedNames& names) {','    template<class Id> void parse(const char* begin, const char* end, const std::vector<Id>& lookup, size_t count, SharedNames& names) {')
    source=replace(source,'std::vector<uint16_t> lookup(1000000);','std::vector<uint8_t> lookup(1000000);')
    save('c-byteviews3',source)
    source=baseline('c')
    source=replace(source,'        size_t hash;\n        std::string_view name;','        size_t length;\n        std::string_view name() const {return {reinterpret_cast<const char*>(this)+sizeof(Node),length};}')
    source=replace(source,'Node* insert(std::string_view name,size_t hash,Node* next) {','Node* insert(std::string_view name,Node* next) {')
    source=replace(source,'Node{next,hash,std::string_view(data+sizeof(Node),name.size())}','Node{next,name.size()}')
    source=replace(source,'(node->hash!=hash || node->name!=name)','(node->name()!=name)')
    source=replace(source,'node=shard.insert(name,hash,first);','node=shard.insert(name,first);')
    save('c-compactnames3',source)
    source=replace(source,'    void parse(const char* begin, const char* end, const std::vector<uint16_t>& lookup, size_t count, SharedNames& names) {','    template<class Id> void parse(const char* begin, const char* end, const std::vector<Id>& lookup, size_t count, SharedNames& names) {')
    source=replace(source,'std::vector<uint16_t> lookup(1000000);','std::vector<uint8_t> lookup(1000000);')
    save('c-compactbyte3',source)
    source=baseline('c')
    start=source.index('// Nodes never move.')
    stop=source.index('struct Country {',start)
    source=source[:start]+(OUT/'c-flatnames3.inc').read_text()+source[stop:]
    save('c-flatnames3',source)
    source=baseline('d')
    insert=r'''
    bool relax(uint32_t node,uint64_t distance) {
        size_t at=(node*2654435761u)&(slots.size()-1);
        while (slots[at].epoch==epoch) {
            if (slots[at].node==node) {
                if (distance>=slots[at].distance) return false;
                slots[at].distance=distance;return true;
            }
            at=(at+1)&(slots.size()-1);
        }
        set(node,distance);return true;
    }
'''
    source=replace(source,'    void set(uint32_t node,uint64_t distance) {',insert+'\n    void set(uint32_t node,uint64_t distance) {')
    source=replace(source,'if (nd<state[dir].get(v)) {\n                    state[dir].set(v,nd);','if (state[dir].relax(v,nd)) {')
    save('d-relax3',source)
    # Checked narrow search labels halve hot hash-slot size. Any relaxation
    # that cannot be represented redoes the query with exact uint64 labels.
    source=replace(source,'struct SparseState {\n    struct Slot {uint64_t distance=0;uint32_t node=0,epoch=0;};',
        'template<class Distance=uint64_t,class Epoch=uint32_t> struct State {\n    struct Slot {Distance distance=0;Epoch epoch=0;uint32_t node=0;};\n    static constexpr uint64_t LIMIT=std::numeric_limits<Distance>::max();')
    source=replace(source,'uint32_t epoch=0;','Epoch epoch=0;')
    source=replace(source,'struct Search {\n    SparseState state[2];','using SparseState=State<>;\n\ntemplate<class Labels=SparseState> struct SearchT {\n    Labels state[2];')
    source=replace(source,'explicit Search(uint32_t) {}','explicit SearchT(uint32_t) {}')
    source=source.replace('slots[at]={distance,node,epoch};','slots[at]={static_cast<Distance>(distance),epoch,node};')
    source=replace(source,'uint64_t nd = du + w;','uint64_t nd = du + w;\n                if (nd>=best) continue;\n                if constexpr (Labels::LIMIT<UINT64_MAX) if (nd>Labels::LIMIT) return INT64_MIN;')
    source=replace(source,'int main(int argc, char** argv) {','using Search=SearchT<>;\n\nint main(int argc, char** argv) {')
    source=replace(source,'Search search(graph.n);','SearchT<State<uint16_t,uint16_t>> search(graph.n);\n            Search wide(graph.n);')
    source=replace(source,'answers[q] = search.run(graph, queries[q].first, queries[q].second);','answers[q] = search.run(graph, queries[q].first, queries[q].second);\n                if (answers[q]==INT64_MIN) answers[q]=wide.run(graph,queries[q].first,queries[q].second);')
    source=source.replace('#include <mutex>','#include <mutex>\n#include <limits>')
    save('d-narrow3',source)
    # Only the query pool grows; graph construction keeps the measured six workers.
    save('d-narrow3-twelve',source.replace('if (queries.size() < 100) workers = 1;','workers=std::min(12u,std::max(1u,std::thread::hardware_concurrency()));\n        if (queries.size() < 100) workers = 1;'))
    source=baseline('d').replace('if (queries.size() < 100) workers = 1;','workers=std::min(12u,std::max(1u,std::thread::hardware_concurrency()));\n        if (queries.size() < 100) workers = 1;')
    save('d-wide3-twelve',source)
    start=source.index('        unsigned workers=std::min',source.index('explicit Graph'))
    stop=source.index('        for (auto& side:edges) side.finish();',start)
    serial=r'''        for (auto& side:offset) side.resize(size_t(n)+1);
        const char* body=p;
        while (p<file.end()) {
            uint32_t u=integer(p);++p;
            uint32_t v=integer(p);++p;
            integer(p);++p;
            ++offset[0][u+1];++offset[1][v+1];
        }
        for (unsigned d=0;d<2;++d) {
            std::partial_sum(offset[d].begin(),offset[d].end(),offset[d].begin());
            edges[d].configure(n);edges[d].resize(m);
        }
        auto forward=offset[0],reverse=offset[1];
        p=body;
        while (p<file.end()) {
            uint32_t u=integer(p);++p;
            uint32_t v=integer(p);++p;
            uint32_t w=integer(p);++p;
            edges[0].set(forward[u]++,{v,w});edges[1].set(reverse[v]++,{u,w});
        }
'''
    save('d-serial3',source[:start]+serial+source[stop:])
    source=(OUT/'d-wide3-twelve.cpp').read_text()
    start=source.index('        for (auto& side:offset) side.resize',source.index('explicit Graph'))
    stop=source.index('        for (auto& side:edges) side.finish();',start)+len('        for (auto& side:edges) side.finish();')
    source=source[:start]+'''        if (!build<uint8_t>(cuts,m) && !build<uint16_t>(cuts,m) && !build<uint32_t>(cuts,m))
            throw std::runtime_error("CSR degree overflow");'''+source[stop:]
    source=source.replace('    explicit Graph(const std::string& path) {',(OUT/'d-private3.inc').read_text()+'    explicit Graph(const std::string& path) {')
    source=source.replace('#include <mutex>','#include <mutex>\n#include <limits>')
    save('d-private3',source)
    a=(OUT/'a-bucket3.cpp').read_text()
    save('a-bucket3-six',a.replace('std::min(12u,','std::min(6u,'))
    a='#pragma GCC target("avx2")\n'+a
    a=replace(a,'''            while (*p!=' ') ++p;
            uint16_t tag''','''            while (end-p>=32) {
                auto bytes=_mm256_loadu_si256(reinterpret_cast<const __m256i*>(p));
                uint32_t mask=_mm256_movemask_epi8(_mm256_cmpeq_epi8(bytes,_mm256_set1_epi8(' ')));
                if (mask) {p+=std::countr_zero(mask);break;}
                p+=32;
            }
            while (*p!=' ') ++p;
            uint16_t tag''')
    save('a-simd3',a)
    save('a-simd3-sort16',a.replace('if (n<=128)','if (n<=16)'))
    a=replace(a,'        unsigned turn=0;','        std::vector<std::string> spares;\n        unsigned turn=0;')
    a=replace(a,'                output.reserve(160*1024);','''                {
                    std::lock_guard<std::mutex> lock(output_mutex);
                    if (!spares.empty()) {output=std::move(spares.back());spares.pop_back();}
                }
                output.reserve(160*1024);''')
    a=replace(a,'                    std::string{}.swap(s);','                    s.clear();spares.push_back(std::move(s));')
    save('a-recycle3',a)

if __name__=='__main__':
    main()
