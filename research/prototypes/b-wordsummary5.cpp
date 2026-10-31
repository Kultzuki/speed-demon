#pragma GCC target("avx2,popcnt")
#include "common.hpp"
#include <array>
#include <atomic>
#include <bit>
#include <immintrin.h>
#include <thread>
#include <unordered_map>

constexpr uint32_t NONE = UINT32_MAX;
inline unsigned normalized(unsigned char c) { return c >= 'A' && c <= 'Z' ? c + 32 : c; }
inline bool token_byte(unsigned c) { return (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9'); }
inline bool raw_token(unsigned char c) { return token_byte(normalized(c)); }

struct Term {
    std::string_view word;
    uint64_t sampled = 0;
    uint32_t boolean = NONE, anchor = NONE;
};

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

struct Query {
    bool phrase;
    uint32_t anchor = 0;
    InlineList<uint32_t,8> terms;
    InlineList<char,5> operators;
};

struct Lookup {
    struct Slot { uint32_t hash = 0, id = NONE; };
    const std::vector<Term>& terms;
    std::vector<Slot> slots;
    size_t mask;
    std::array<uint64_t,8192> filter{};
    static uint64_t filter_bits(uint32_t h) {return (uint64_t(1)<<((h>>13)&63))|(uint64_t(1)<<((h>>19)&63));}
    explicit Lookup(const std::unordered_map<std::string_view, uint32_t>& dictionary, const std::vector<Term>& words) : terms(words) {
        size_t capacity = 1;
        while (capacity < dictionary.size() * 2) capacity *= 2;
        slots.resize(capacity); mask = capacity - 1;
        for (auto [word, id] : dictionary) {
            uint32_t hash = std::hash<std::string_view>()(word); size_t at = hash & mask;
            filter[hash&8191]|=filter_bits(hash);
            while (slots[at].id != NONE) at = (at + 1) & mask;
            slots[at] = {hash, id};
        }
    }
    uint32_t find(std::string_view word) const {
        uint32_t hash = std::hash<std::string_view>()(word); size_t at = hash & mask;
        uint64_t wanted=filter_bits(hash);
        if ((filter[hash&8191]&wanted)!=wanted) return NONE;
        for (;;) {
            const auto& slot = slots[at];
            if (slot.id == NONE) return NONE;
            if (slot.hash == hash && terms[slot.id].word == word) return slot.id;
            at = (at + 1) & mask;
        }
    }
};

// A vector load is permitted only when all 32 bytes are within the mapping.
// Non-ASCII bytes are separators, including the bytes inside UTF-8 letters.
uint32_t read_token(const char*& p, const char* end, const Lookup& lookup) {
    char word[32];
    unsigned length = 0;
    if (end - p >= 32) {
        auto bytes = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(p));
        auto lower = _mm256_or_si256(bytes, _mm256_set1_epi8(32));
        auto letters = _mm256_and_si256(_mm256_cmpgt_epi8(lower, _mm256_set1_epi8('a' - 1)), _mm256_cmpgt_epi8(_mm256_set1_epi8('z' + 1), lower));
        auto digits = _mm256_and_si256(_mm256_cmpgt_epi8(bytes, _mm256_set1_epi8('0' - 1)), _mm256_cmpgt_epi8(_mm256_set1_epi8('9' + 1), bytes));
        uint32_t mask = _mm256_movemask_epi8(_mm256_or_si256(letters, digits));
        length = std::countr_zero(~mask);
        _mm256_storeu_si256(reinterpret_cast<__m256i*>(word), lower);
        p += length;
    }
    while (p < end && raw_token(*p)) {
        if (length < sizeof(word)) word[length] = normalized(*p);
        ++length; ++p;
    }
    return length <= sizeof(word) ? lookup.find(std::string_view(word, length)) : NONE;
}

template<class Doc,class Offset> struct Occurrences {
    std::vector<Offset> offsets;
    std::vector<Doc> documents;
};
// Promote a frequent list during construction, avoiding two complete indexes.

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
        if (dense()) {if (count!=doc) {storage.bits[(doc-base)/64]|=uint64_t(1)<<((doc-base)%64);count=doc;}return;}
        if (count && data()[count-1]==doc) return;
        if (uint64_t(count)+1>=std::max<uint64_t>(1,(uint64_t(total)+8*sizeof(Doc)-1)/(8*sizeof(Doc)))) {
            auto* bits=new uint64_t[(size_t(total)+63)/64]{};
            for (uint32_t i=0;i<count;++i) {uint32_t id=data()[i];bits[(id-base)/64]|=uint64_t(1)<<((id-base)%64);}
            bits[(doc-base)/64]|=uint64_t(1)<<((doc-base)%64);
            if (capacity) delete[] storage.documents;
            storage.bits=bits; capacity=UINT32_MAX;count=doc; return;
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
template<class Doc,class Offset> struct Block {
    const char* begin=nullptr;
    uint32_t base = 0, count = 0;
    std::vector<Posting<Doc>> postings;
    std::vector<Occurrences<Doc,Offset>> occurrences;
};
struct Answer {
    uint64_t count = 0, sum = 0;
    std::array<uint32_t, 10> first{};

    void add_word(uint32_t base,uint64_t bits) {
        uint64_t n=std::popcount(bits), positions=0;
        constexpr uint64_t masks[]={0xAAAAAAAAAAAAAAAAULL,0xCCCCCCCCCCCCCCCCULL,0xF0F0F0F0F0F0F0F0ULL,0xFF00FF00FF00FF00ULL,0xFFFF0000FFFF0000ULL,0xFFFFFFFF00000000ULL};
        for (unsigned i=0;i<6;++i) positions+=uint64_t(std::popcount(bits&masks[i]))<<i;
        size_t at=std::min<uint64_t>(count,first.size());
        for (uint64_t left=bits;left && at<first.size();left&=left-1) first[at++]=base+std::countr_zero(left);
        count+=n;sum+=n*base+positions;
    }
    void add(uint32_t doc) {
        if (count < first.size()) first[count] = doc;
        ++count; sum += doc;
    }
};

bool matches(const char* at, const char* begin, const char* end, const Query& q, const std::vector<Term>& terms) {
    // Recover the phrase start by token boundaries, never by fixed byte widths.
    for (uint32_t i = 0; i < q.anchor; ++i) {
        while (at > begin && !raw_token(at[-1])) {
            if (at[-1] == '\t' || at[-1] == '\n') return false;
            --at;
        }
        if (at == begin) return false;
        while (at > begin && raw_token(at[-1])) --at;
    }
    for (size_t i = 0; i < q.terms.size(); ++i) {
        if (i) {
            while (at < end && !raw_token(*at)) {
                if (*at == '\t' || *at == '\n') return false;
                ++at;
            }
        }
        auto word = terms[q.terms[i]].word;
        if (size_t(end - at) < word.size()) return false;
        for (unsigned char c : word) if (normalized(*at++) != c) return false;
        if (at < end && raw_token(*at)) return false;
    }
    return true;
}

template<class Doc,class Offset> void solve(const Paths& paths) {
        MappedFile query_file(paths.data + "/queries.txt"), corpus(paths.data + "/docs.txt");
        std::unordered_map<std::string_view, uint32_t> dictionary;
        dictionary.reserve(131072);
        std::vector<Term> terms;
        std::vector<Query> queries;
        uint32_t boolean_count = 0, anchor_count = 0;
        const char* p = query_file.data;
        while (p < query_file.end()) {
            Query q{};
            q.phrase = *p == 'P'; p += q.phrase ? 8 : 5;
            for (;;) {
                const char* start = p;
                while (token_byte(static_cast<unsigned char>(*p))) ++p;
                std::string_view word(start, p - start);
                auto [it, inserted] = dictionary.try_emplace(word, terms.size());
                if (inserted) terms.push_back(Term{word});
                q.terms.push_back(it->second);
                auto& term = terms[it->second];
                if (!q.phrase && term.boolean == NONE) term.boolean = boolean_count++;
                if (q.phrase && *p == '"') { p += 2; break; }
                if (*p == '\n') { ++p; break; }
                ++p;
                if (!q.phrase) {
                    q.operators.push_back(*p);
                    while (*p++ != ' ') {}
                }
            }
            queries.push_back(std::move(q));
        }
        Lookup lookup(dictionary, terms);
        dictionary.clear(); dictionary.rehash(0);
        // Sampling affects only anchor choice; every chosen anchor is indexed
        // in a complete exact pass. A poor estimate costs time, never matches.
        size_t samples = corpus.size < 2 * 1024 * 1024 ? 1 : 8;
        for (size_t sample = 0; sample < samples; ++sample) {
            const char* current = corpus.data + corpus.size * sample / samples;
            if (current != corpus.data) while (current < corpus.end() && current[-1] != '\n') ++current;
            const char* limit = current + std::min<size_t>(corpus.end() - current, 256 * 1024);
            while (current < limit) {
                integer(current); ++current;
                while (*current != '\n') {
                    if (!raw_token(*current)) { ++current; continue; }
                    uint32_t id = read_token(current, corpus.end(), lookup);
                    if (id != NONE) ++terms[id].sampled;
                }
                ++current;
            }
        }
        for (auto& q : queries) if (q.phrase) {
            for (uint32_t i = 1; i < q.terms.size(); ++i)
                if (terms[q.terms[i]].sampled < terms[q.terms[q.anchor]].sampled) q.anchor = i;
            auto& term = terms[q.terms[q.anchor]];
            if (term.anchor == NONE) term.anchor = anchor_count++;
        }
        unsigned workers = std::min(12u, std::max(1u, std::thread::hardware_concurrency()));
        if (corpus.size < 2 * 1024 * 1024) workers = 1;
        std::vector<const char*> cuts(workers + 1);
        cuts[0] = corpus.data; cuts[workers] = corpus.end();
        for (unsigned i = 1; i < workers; ++i) {
            const char* current = corpus.data + corpus.size * i / workers;
            while (current < corpus.end() && current[-1] != '\n') ++current;
            cuts[i] = current;
        }
        uint32_t document_count = 0;
        if (corpus.size) {
            const char* last = corpus.end() - 1;
            while (last > corpus.data && last[-1] != '\n') --last;
            document_count = integer(last) + 1;
        }

        // Local document IDs are narrow only when every real block fits.
        if constexpr (sizeof(Doc)==2) {
            for (unsigned i=0;i<workers;++i) {
                const char* a=cuts[i]; const char* b=cuts[i+1];
                uint32_t first=a==corpus.end()?document_count:integer(a);
                uint32_t stop=b==corpus.end()?document_count:integer(b);
                if (uint64_t(stop)-first>65536) return solve<uint32_t,Offset>(paths);
            }
        }

        if constexpr (sizeof(Offset)==4) {
            for (unsigned i=0;i<workers;++i) if (uint64_t(cuts[i+1]-cuts[i])>UINT32_MAX) return solve<Doc,uint64_t>(paths);
        }
        std::vector<Block<Doc,Offset>> blocks(workers);
        std::vector<std::thread> threads;
        for (unsigned worker = 0; worker < workers; ++worker) threads.emplace_back([&, worker] {
            auto& block = blocks[worker];block.begin=cuts[worker];
            block.postings.resize(boolean_count); block.occurrences.resize(anchor_count);
            const char* current = cuts[worker];
            const char* header = current;
            block.base = header == corpus.end() ? document_count : integer(header);
            header = cuts[worker + 1];
            uint32_t stop = header == corpus.end() ? document_count : integer(header);
            block.count = stop - block.base;
            while (current < cuts[worker + 1]) {
                uint32_t doc = integer(current); ++current;
                while (*current != '\n') {
                    if (!raw_token(*current)) { ++current; continue; }
                    const char* start = current;
                    uint32_t id = read_token(current, cuts[worker + 1], lookup);
                    if (id == NONE) continue;
                    const auto& term = terms[id];
                    if (term.boolean != NONE) {
                        auto& list = block.postings[term.boolean];
                        list.add(doc-block.base, 0, block.count);
                    }
                    if (term.anchor != NONE) {
                        auto& occurrences = block.occurrences[term.anchor];
                        occurrences.offsets.push_back(start-block.begin);
                        occurrences.documents.push_back(doc-block.base);
                    }
                }
                ++current;
            }
        });
        for (auto& thread : threads) thread.join();
        threads.clear();
        std::vector<Answer> answers(queries.size());
        std::atomic<size_t> next{0};
        for (unsigned worker = 0; worker < workers; ++worker) threads.emplace_back([&] {
            std::vector<Doc> result, scratch;
            for (;;) {
                size_t batch = next.fetch_add(16, std::memory_order_relaxed);
                if (batch >= queries.size()) break;
                for (size_t index = batch; index < std::min(batch + 16, queries.size()); ++index) {
                    const auto& q = queries[index]; auto& answer = answers[index];
                    // Blocks are disjoint document domains. Left-fold set algebra
                    // distributes across them, so no global postings merge is needed.
                    for (const auto& block : blocks) {
                        if (!q.phrase) {
                            bool dense = false;
                            for (uint32_t id : q.terms) dense |= block.postings[terms[id].boolean].dense();
                            if (dense) {
                                std::array<size_t, 6> cursors{};
                                for (size_t w = 0; w < (size_t(block.count) + 63) / 64; ++w) {
                                    uint64_t bits = block.postings[terms[q.terms[0]].boolean].word(w, cursors[0], 0);
                                    for (size_t i = 1; i < q.terms.size(); ++i) {
                                        uint64_t other = block.postings[terms[q.terms[i]].boolean].word(w, cursors[i], 0);
                                        if (q.operators[i - 1] == 'A') bits &= other;
                                        else if (q.operators[i - 1] == 'O') bits |= other;
                                        else bits &= ~other;
                                    }
                                    // OR operands contain only real document bits;
                                    // AND and binary NOT cannot set any padding bit.
                                    answer.add_word(block.base+w*64,bits);
                                }
                                continue;
                            }
                            const auto& first=block.postings[terms[q.terms[0]].boolean];
                            result.assign(first.data(),first.data()+first.count);
                            for (size_t i = 1; i < q.terms.size(); ++i) {
                                const auto& other = block.postings[terms[q.terms[i]].boolean];
                                scratch.clear();
                                auto dest = std::back_inserter(scratch);
                                if (q.operators[i - 1] == 'A') std::set_intersection(result.begin(), result.end(), other.data(), other.data()+other.count, dest);
                                else if (q.operators[i - 1] == 'O') std::set_union(result.begin(), result.end(), other.data(), other.data()+other.count, dest);
                                else std::set_difference(result.begin(), result.end(), other.data(), other.data()+other.count, dest);
                                result.swap(scratch);
                            }
                            for (uint32_t doc : result) answer.add(block.base+doc);
                        } else {
                            const auto& occurrences = block.occurrences[terms[q.terms[q.anchor]].anchor];
                            uint32_t previous = NONE;
                            for (size_t i = 0; i < occurrences.offsets.size(); ++i) {
                                uint32_t doc = block.base+occurrences.documents[i];
                                if (doc == previous) continue;
                                if (matches(block.begin+occurrences.offsets[i], corpus.data, corpus.end(), q, terms)) {
                                    answer.add(doc); previous = doc;
                                }
                            }
                        }
                    }
                }
            }
        });
        for (auto& thread : threads) thread.join();
        std::string output;
        for (const auto& answer : answers) {
            number(output, answer.count); output += ' '; number(output, answer.sum);
            for (size_t i = 0; i < std::min<uint64_t>(10, answer.count); ++i) { output += ' '; number(output, answer.first[i]); }
            output += '\n';
        }
        write_output(paths.out + "/results.txt", output);
}

int main(int argc,char** argv) {
    try { Paths paths(argc,argv); solve<uint16_t,uint32_t>(paths); }
    catch (const std::exception& e) {fprintf(stderr,"%s\n",e.what());return 1;}
}
