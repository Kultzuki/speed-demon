"""Generate a compact, exact B candidate with runtime widening fallbacks."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=(root/"track-b/main.cpp").read_text()
source=source.replace('struct Slot { size_t hash = 0; std::string_view word; uint32_t id = NONE; };',
                      'struct Slot { uint32_t hash = 0, id = NONE; };\n    const std::vector<Term>& terms;')
source=source.replace('explicit Lookup(const std::unordered_map<std::string_view, uint32_t>& dictionary) {',
                      'explicit Lookup(const std::unordered_map<std::string_view, uint32_t>& dictionary, const std::vector<Term>& words) : terms(words) {')
source=source.replace('size_t hash = std::hash<std::string_view>()(word), at = hash & mask;',
                      'uint32_t hash = std::hash<std::string_view>()(word); size_t at = hash & mask;')
source=source.replace('slots[at] = {hash, word, id};','slots[at] = {hash, id};')
source=source.replace('slot.word == word','terms[slot.id].word == word')
source=source.replace('Lookup lookup(dictionary);','Lookup lookup(dictionary, terms);')
source=source.replace("auto upper = _mm256_and_si256(_mm256_cmpgt_epi8(bytes, _mm256_set1_epi8('A' - 1)), _mm256_cmpgt_epi8(_mm256_set1_epi8('Z' + 1), bytes));\n        auto lower = _mm256_or_si256(bytes, _mm256_and_si256(upper, _mm256_set1_epi8(32)));",
                      'auto lower = _mm256_or_si256(bytes, _mm256_set1_epi8(32));')
source=source.replace("_mm256_cmpgt_epi8(lower, _mm256_set1_epi8('0' - 1)), _mm256_cmpgt_epi8(_mm256_set1_epi8('9' + 1), lower)",
                      "_mm256_cmpgt_epi8(bytes, _mm256_set1_epi8('0' - 1)), _mm256_cmpgt_epi8(_mm256_set1_epi8('9' + 1), bytes)")
(root/"research/prototypes/b-compact-lookup.cpp").write_text(source)
source=source.replace('struct Posting {\n    std::vector<uint32_t> documents;', 'template<class Doc> struct Posting {\n    std::vector<Doc> documents;')
source=source.replace('struct Block {','template<class Doc> struct Block {')
source=source.replace('std::vector<Posting> postings;', 'std::vector<Posting<Doc>> postings;')
source=source.replace('int main(int argc, char** argv) {\n    try {\n        Paths paths(argc, argv);', 'template<class Doc> void solve(const Paths& paths) {')
source=source.replace('std::vector<Block> blocks(workers);',r'''
        // Local document IDs are narrow only when every real block fits.
        if constexpr (sizeof(Doc)==2) {
            for (unsigned i=0;i<workers;++i) {
                const char* a=cuts[i]; const char* b=cuts[i+1];
                uint32_t first=a==corpus.end()?document_count:integer(a);
                uint32_t stop=b==corpus.end()?document_count:integer(b);
                if (uint64_t(stop)-first>65536) return solve<uint32_t>(paths);
            }
        }
        std::vector<Block<Doc>> blocks(workers);''')
source=source.replace('list.add(doc, block.base, block.count);', 'list.add(doc-block.base, 0, block.count);')
source=source.replace('std::vector<uint32_t>().swap(documents);','std::vector<Doc>().swap(documents);')
source=source.replace('std::vector<uint32_t> result, scratch;', 'std::vector<Doc> result, scratch;')
source=source.replace('.word(w, cursors[0], block.base)', '.word(w, cursors[0], 0)')
source=source.replace('.word(w, cursors[i], block.base)', '.word(w, cursors[i], 0)')
source=source.replace('for (uint32_t doc : result) answer.add(doc);', 'for (uint32_t doc : result) answer.add(block.base+doc);')
source=source.replace('    } catch (const std::exception& e) { fprintf(stderr, "%s\\n", e.what()); return 1; }\n}',
                      '}\n\nint main(int argc,char** argv) {\n    try { Paths paths(argc,argv); solve<uint16_t>(paths); }\n    catch (const std::exception& e) {fprintf(stderr,"%s\\n",e.what());return 1;}\n}')
(root/"research/prototypes/b-local16.cpp").write_text(source)
start=source.index('template<class Doc> struct Posting')
stop=source.index('template<class Doc> struct Block',start)
posting=r'''
// Four local uint16 IDs fit in the descriptor itself. The same storage becomes
// a heap list or bitmap only when needed; no duplicate capacity is retained.
template<class Doc> struct Posting {
    static constexpr unsigned INLINE=8/sizeof(Doc);
    union Storage { Doc small[INLINE]{}; Doc* documents; uint64_t* bits; } storage;
    uint32_t count=0, capacity=0;
    Posting()=default;
    Posting(const Posting&)=delete;
    Posting(Posting&& other) noexcept :storage(other.storage),count(other.count),capacity(other.capacity) {
        other.count=other.capacity=0;
    }
    ~Posting() {
        if (dense()) delete[] storage.bits;
        else if (capacity) delete[] storage.documents;
    }
    bool dense() const {return capacity==UINT32_MAX;}
    const Doc* data() const {return capacity?storage.documents:storage.small;}
    void add(uint32_t doc,uint32_t base,uint32_t total) {
        if (dense()) {storage.bits[(doc-base)/64]|=uint64_t(1)<<((doc-base)%64);return;}
        if (count && data()[count-1]==doc) return;
        if (uint64_t(count)+1>=std::max<uint64_t>(1,(uint64_t(total)+8*sizeof(Doc)-1)/(8*sizeof(Doc)))) {
            auto* bits=new uint64_t[(size_t(total)+63)/64]{};
            for (uint32_t i=0;i<count;++i) {uint32_t id=data()[i];bits[(id-base)/64]|=uint64_t(1)<<((id-base)%64);}
            bits[(doc-base)/64]|=uint64_t(1)<<((doc-base)%64);
            if (capacity) delete[] storage.documents;
            storage.bits=bits; capacity=UINT32_MAX; return;
        }
        if (count==(capacity?capacity:INLINE)) {
            uint32_t grown=(capacity?capacity:INLINE)*2;
            auto* values=new Doc[grown];
            std::copy_n(data(),count,values);
            if (capacity) delete[] storage.documents;
            storage.documents=values; capacity=grown;
        }
        if (capacity) storage.documents[count++]=doc;
        else storage.small[count++]=doc;
    }
    uint64_t word(size_t index,size_t& cursor,uint32_t base) const {
        if (dense()) return storage.bits[index];
        uint64_t result=0, end=uint64_t(base)+(index+1)*64;
        while (cursor<count && data()[cursor]<end) result|=uint64_t(1)<<((data()[cursor++]-base)%64);
        return result;
    }
};
'''
source=source[:start]+posting+source[stop:]
source=source.replace('!block.postings[terms[id].boolean].bits.empty()', 'block.postings[terms[id].boolean].dense()')
source=source.replace('result = block.postings[terms[q.terms[0]].boolean].documents;',
                      'const auto& first=block.postings[terms[q.terms[0]].boolean];\n                            result.assign(first.data(),first.data()+first.count);')
source=source.replace('const auto& other = block.postings[terms[q.terms[i]].boolean].documents;',
                      'const auto& other = block.postings[terms[q.terms[i]].boolean];')
source=source.replace('other.begin(), other.end()', 'other.data(), other.data()+other.count')
(root/"research/prototypes/b-small-posting.cpp").write_text(source)
start=source.index('// A vector load')
stop=source.index('struct Occurrences',start)
tokenizer=r'''
// Reuse each classified/lowercased vector across its contained tokens. A token
// crossing the cached boundary refills at its start. All loads stay in bounds.
struct TokenReader {
    const Lookup& lookup;
    const char* base=nullptr;
    char lower[32];
    uint32_t mask=0;
    void fill(const char* p) {
        base=p;
        auto bytes=_mm256_loadu_si256(reinterpret_cast<const __m256i*>(p));
        auto folded=_mm256_or_si256(bytes,_mm256_set1_epi8(32));
        auto letters=_mm256_and_si256(_mm256_cmpgt_epi8(folded,_mm256_set1_epi8('a'-1)),_mm256_cmpgt_epi8(_mm256_set1_epi8('z'+1),folded));
        auto digits=_mm256_and_si256(_mm256_cmpgt_epi8(bytes,_mm256_set1_epi8('0'-1)),_mm256_cmpgt_epi8(_mm256_set1_epi8('9'+1),bytes));
        mask=_mm256_movemask_epi8(_mm256_or_si256(letters,digits));
        _mm256_storeu_si256(reinterpret_cast<__m256i*>(lower),folded);
    }
    uint32_t read(const char*& p,const char* end) {
        if (end-p>=32) {
            if (!base || p<base || p-base>=32) fill(p);
            unsigned offset=p-base;
            unsigned length=std::countr_zero(~(mask>>offset));
            if (length==32-offset && p+length<end && raw_token(p[length])) {
                fill(p);offset=0;length=std::countr_zero(~mask);
            }
            const char* word=lower+offset;
            p+=length;
            if (length==32) {
                while (p<end && raw_token(*p)) {++p;++length;}
            }
            return length<=32?lookup.find(std::string_view(word,length)):NONE;
        }
        char word[32];unsigned length=0;
        while (p<end && raw_token(*p)) {
            if (length<32) word[length]=normalized(*p);
            ++length;++p;
        }
        return length<=32?lookup.find(std::string_view(word,length)):NONE;
    }
};

'''
source=source[:start]+tokenizer+source[stop:]
source=source.replace('size_t samples =', 'TokenReader sampler{lookup};\n        size_t samples =')
source=source.replace('read_token(current, corpus.end(), lookup)', 'sampler.read(current, corpus.end())')
source=source.replace('auto& block = blocks[worker];', 'TokenReader reader{lookup};\n            auto& block = blocks[worker];')
source=source.replace('read_token(current, cuts[worker + 1], lookup)', 'reader.read(current, cuts[worker + 1])')
(root/"research/prototypes/b-cached-token.cpp").write_text(source)
source=(root/"research/prototypes/b-small-posting.cpp").read_text()
source=source.replace('struct Occurrences {\n    std::vector<uint64_t> offsets;\n    std::vector<uint32_t> documents;',
                      'template<class Doc,class Offset> struct Occurrences {\n    std::vector<Offset> offsets;\n    std::vector<Doc> documents;')
source=source.replace('template<class Doc> struct Block {','template<class Doc,class Offset> struct Block {\n    const char* begin=nullptr;')
source=source.replace('std::vector<Occurrences> occurrences;', 'std::vector<Occurrences<Doc,Offset>> occurrences;')
source=source.replace('template<class Doc> void solve(', 'template<class Doc,class Offset> void solve(')
source=source.replace('return solve<uint32_t>(paths);', 'return solve<uint32_t,Offset>(paths);')
source=source.replace('std::vector<Block<Doc>> blocks(workers);', r'''
        if constexpr (sizeof(Offset)==4) {
            for (unsigned i=0;i<workers;++i) if (uint64_t(cuts[i+1]-cuts[i])>UINT32_MAX) return solve<Doc,uint64_t>(paths);
        }
        std::vector<Block<Doc,Offset>> blocks(workers);''')
source=source.replace('auto& block = blocks[worker];', 'auto& block = blocks[worker];block.begin=cuts[worker];')
source=source.replace('occurrences.offsets.push_back(start - corpus.data);', 'occurrences.offsets.push_back(start-block.begin);')
source=source.replace('occurrences.documents.push_back(doc);','occurrences.documents.push_back(doc-block.base);')
source=source.replace('uint32_t doc = occurrences.documents[i];','uint32_t doc = block.base+occurrences.documents[i];')
source=source.replace('corpus.data + occurrences.offsets[i]', 'block.begin+occurrences.offsets[i]')
source=source.replace('solve<uint16_t>(paths)', 'solve<uint16_t,uint32_t>(paths)')
(root/"research/prototypes/b-local-occurrences.cpp").write_text(source)
fixed=r'''
template<class T,size_t N> struct InlineList {
    std::array<T,N> values{};
    uint8_t count=0;
    void push_back(T value) {values[count++]=value;}
    size_t size() const {return count;}
    T& operator[](size_t i) {return values[i];}
    const T& operator[](size_t i) const {return values[i];}
    const T* begin() const {return values.data();}
    const T* end() const {return values.data()+count;}
};
'''
source=source.replace('struct Query {',fixed+'\nstruct Query {')
source=source.replace('std::vector<uint32_t> terms;\n    std::vector<char> operators;', 'InlineList<uint32_t,8> terms;\n    InlineList<char,5> operators;')
(root/"research/prototypes/b-inline-query.cpp").write_text(source)
