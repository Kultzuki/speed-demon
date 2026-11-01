#include <chrono>
// Speed Demon 2026, Track B (Index).
//
// The queries are readable up front, so we read them first and index only the
// terms they mention. One parallel pass over the memory-mapped corpus builds
// doc-level posting lists for those terms (sorted, deduplicated). BOOL queries
// are then evaluated left to right on sorted arrays, galloping when one side is
// much smaller. PHRASE queries intersect their terms' postings, rarest first,
// and re-tokenize only the surviving candidates to check adjacency.
#include "common.hpp"
#include <algorithm>
#include <type_traits>
#include <atomic>
#include <barrier>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <malloc.h>
#include <immintrin.h>
#include <memory>
#include <span>
#include <string>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/stat.h>
#include <thread>
#include <unistd.h>
#include <vector>

namespace {

using u32 = uint32_t;
using u64 = uint64_t;

constexpr int MAX_TERM = 32;  // query terms are 1 to 32 bytes
constexpr u32 NONE = 0xFFFFFFFFu;

// lower[c] is the lowercased byte for [A-Za-z0-9] and 0 for every separator.
struct Lower {
    uint8_t t[256] = {};
    Lower() {
        for (int c = '0'; c <= '9'; ++c) t[c] = c;
        for (int c = 'a'; c <= 'z'; ++c) t[c] = c;
        for (int c = 'A'; c <= 'Z'; ++c) t[c] = c + 32;
    }
};
const Lower LOWER;

struct File {
    const uint8_t* data = nullptr;
    size_t size = 0;
};

// Maps the file over a spare zero page, so 64-byte loads near its end are safe.
File map_file(const std::string& path) {
    File f;
    int fd = open(path.c_str(), O_RDONLY);
    if (fd < 0) { perror(path.c_str()); _exit(1); }
    struct stat st;
    fstat(fd, &st);
    f.size = st.st_size;
    void* p = mmap(nullptr, f.size + 4096, PROT_READ, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (f.size && mmap(p, f.size, PROT_READ, MAP_PRIVATE | MAP_FIXED, fd, 0) == MAP_FAILED) {
        perror("mmap");
        _exit(1);
    }
    f.data = static_cast<const uint8_t*>(p);
    close(fd);
    return f;
}

// A term key: up to 32 lowercase bytes, zero padded, so equal keys compare as
// four 64-bit words (no term contains a zero byte, so the padding encodes length).
struct alignas(32) Key {
    u64 w[4];
};

// Two independent multiplies; almost every token fits in the first two words.
inline u64 hash_key(const Key& k) {
    u64 h = (k.w[0] + k.w[2] * 0x94D049BB133111EBull) * 0x9E3779B97F4A7C15ull ^
            (k.w[1] + k.w[3] * 0xD6E8FEB86659FD93ull) * 0xBF58476D1CE4E5B9ull;
    return h ^ h >> 29;
}

inline bool same(const Key& a, const Key& b) {
    return ((a.w[0] ^ b.w[0]) | (a.w[1] ^ b.w[1]) | (a.w[2] ^ b.w[2]) | (a.w[3] ^ b.w[3])) == 0;
}

// Open-addressing table from term key to a dense term id. Each slot holds the
// top 32 hash bits and id + 1, so most misses never touch the key array.
class TermTable {
public:
    TermTable() { rehash(1 << 16); }
    u32 size() const { return keys_.size(); }
    const uint8_t* bytes(u32 id) const { return reinterpret_cast<const uint8_t*>(keys_[id].w); }
    size_t length(u32 id) const { return lens_[id]; }

    u32 insert(const Key& k) {
        // Keep the load at or under 1/2 so probe chains stay short.
        if ((keys_.size() + 1) * 2 > slots_.size()) rehash(slots_.size() * 2);
        u64 h = hash_key(k);
        for (size_t i = h & mask_;; i = (i + 1) & mask_) {
            u64 s = slots_[i];
            if (s == 0) {
                keys_.push_back(k);
                lens_.push_back(strnlen(reinterpret_cast<const char*>(k.w), MAX_TERM));
                slots_[i] = (h & 0xFFFFFFFF00000000ull) | keys_.size();
                return keys_.size() - 1;
            }
            if ((s >> 32) == (h >> 32) && same(keys_[(u32)s - 1], k)) return (u32)s - 1;
        }
    }

    // Old id i becomes new_id[i]; keys move with their ids.
    void renumber(const std::vector<u32>& new_id) {
        std::vector<Key> keys(keys_.size());
        std::vector<uint8_t> lens(lens_.size());
        for (u32 i = 0; i < keys_.size(); ++i) keys[new_id[i]] = keys_[i], lens[new_id[i]] = lens_[i];
        keys_.swap(keys);
        lens_.swap(lens);
        rehash(slots_.size());
    }

    void prefetch(u64 h) const { _mm_prefetch(reinterpret_cast<const char*>(&slots_[h & mask_]), _MM_HINT_T0); }

    // h is hash_key(k), computed (and prefetched) earlier by the caller.
    u32 find(const Key& k, u64 h) const {
        for (size_t i = h & mask_;; i = (i + 1) & mask_) {
            u64 s = slots_[i];
            if (s == 0) return NONE;
            if ((s >> 32) == (h >> 32) && same(keys_[(u32)s - 1], k)) return (u32)s - 1;
        }
    }

private:
    void rehash(size_t cap) {
        slots_.assign(cap, 0);
        mask_ = cap - 1;
        for (u32 id = 0; id < keys_.size(); ++id) {
            u64 h = hash_key(keys_[id]);
            size_t i = h & mask_;
            while (slots_[i]) i = (i + 1) & mask_;
            slots_[i] = (h & 0xFFFFFFFF00000000ull) | (id + 1);
        }
    }

    std::vector<u64> slots_;
    std::vector<Key> keys_;
    std::vector<uint8_t> lens_;
    size_t mask_ = 0;
};

// Bit i is set when byte i of the 64 at p is a token byte, [A-Za-z0-9]: after
// OR-ing 0x20 a letter lies in 'a'..'z', and a digit lies in '0'..'9' as is.
inline u64 token_bytes(const uint8_t* p) {
    auto half = [](const uint8_t* q) {
        __m256i v = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(q));
        __m256i letter = _mm256_sub_epi8(_mm256_or_si256(v, _mm256_set1_epi8(0x20)), _mm256_set1_epi8('a'));
        __m256i digit = _mm256_sub_epi8(v, _mm256_set1_epi8('0'));
        __m256i zero = _mm256_setzero_si256();
        __m256i in = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_subs_epu8(letter, _mm256_set1_epi8(25)), zero),
                                     _mm256_cmpeq_epi8(_mm256_subs_epu8(digit, _mm256_set1_epi8(9)), zero));
        return u32(_mm256_movemask_epi8(in));
    };
    return half(p) | u64(half(p + 32)) << 32;
}

// Calls emit(term_id) for every token of text [q, e) that is a known term
// (NONE for tokens that are not; tokens longer than 32 bytes are skipped).
// Token bounds come from one class mask per 64-byte window (a token that runs
// into the window's end starts the next window). The key is read from the
// text 8 bytes at a time: token bytes are all [A-Za-z0-9], so OR-ing 0x20
// lowercases letters and leaves digits alone. Each key's table slot is
// prefetched and the key looked up LAG tokens later, so the misses overlap.
template <class F>
inline void for_each_token(const uint8_t* q, const uint8_t* e, const TermTable& terms, F&& emit) {
    constexpr size_t LAG = 8;
    Key keys[LAG];
    u64 hashes[LAG];
    size_t n = 0;
    auto token = [&](const uint8_t* s, size_t len) {
        if (len > MAX_TERM) return;
        Key k;
        for (size_t i = 0; i < 4; ++i) {
            size_t b = len > 8 * i ? std::min<size_t>(len - 8 * i, 8) : 0;
            u64 w;
            memcpy(&w, s + 8 * i, 8);
            k.w[i] = (w | 0x2020202020202020ull) & (b == 8 ? ~0ull : (1ull << (8 * b)) - 1);
        }
        const u64 h = hash_key(k);
        terms.prefetch(h);
        const size_t slot = n++ % LAG;
        if (n > LAG) emit(terms.find(keys[slot], hashes[slot]));
        keys[slot] = k;
        hashes[slot] = h;
    };
    while (q < e) {
        u64 mask = token_bytes(q);
        if (e - q < 64) mask &= (1ull << (e - q)) - 1;
        u64 starts = mask & ~(mask << 1);
        u64 ends = ~mask & (mask << 1);
        while (ends) {
            const size_t start = __builtin_ctzll(starts);
            const size_t end = __builtin_ctzll(ends);
            token(q + start, end - start);
            starts &= starts - 1;
            ends &= ends - 1;
        }
        if (starts) {
            const uint8_t* s = q + __builtin_ctzll(starts);
            if (s != q) { q = s; continue; }
            // A token filling the entire window is longer than any query
            // term. Skip the complete token, including all following windows.
            q += 64;
            while (q < e && LOWER.t[*q]) ++q;
        } else q += 64;
    }
    for (size_t i = n > LAG ? n - LAG : 0; i < n; ++i) emit(terms.find(keys[i % LAG], hashes[i % LAG]));
}

// One query, as views into the flat arrays below.
struct Query {
    bool phrase;
    std::span<const u32> terms;  // term ids
    std::span<const char> ops;   // BOOL only: 'A', 'O' or 'N' between terms
};

// All queries, flat: query i's terms are terms[first[i], first[i + 1]), and
// for BOOL ops[first[i] + k] joins its terms k and k + 1.
struct Queries {
    std::vector<u32> terms, first{0};
    std::vector<char> ops;
    std::vector<bool> phrase;

    size_t size() const { return phrase.size(); }
    Query operator[](size_t i) const {
        size_t b = first[i], n = first[i + 1] - b;
        return {phrase[i], {terms.data() + b, n}, {ops.data() + b, n - 1}};
    }
};

Key make_key(const uint8_t* p, size_t len) {
    Key k{{0, 0, 0, 0}};
    memcpy(k.w, p, std::min<size_t>(len, MAX_TERM));
    return k;
}

Queries parse_queries(const File& f, TermTable& terms) {
    Queries qs;
    const uint8_t* p = f.data;
    const uint8_t* end = f.data + f.size;
    while (p < end) {
        const uint8_t* nl = static_cast<const uint8_t*>(memchr(p, '\n', end - p));
        if (!nl) nl = end;
        const bool phrase = p[0] == 'P';
        const uint8_t* s = p + (phrase ? 8 : 5);  // past `PHRASE "` or `BOOL `
        const uint8_t* e = phrase ? nl - 1 : nl;  // drop the closing quote
        for (int word = 0; s < e; ++word) {
            const uint8_t* sp = static_cast<const uint8_t*>(memchr(s, ' ', e - s));
            if (!sp) sp = e;
            if (!phrase && word % 2 == 1) {
                qs.ops.back() = static_cast<char>(*s);  // the slot of the term before it
            } else {
                qs.terms.push_back(terms.insert(make_key(s, sp - s)));
                qs.ops.push_back(0);
            }
            s = sp + 1;
        }
        qs.phrase.push_back(phrase);
        qs.first.push_back(qs.terms.size());
        p = nl + 1;
    }
    return qs;
}

inline u64 position_sum(u64 m) {
    static constexpr u64 SEL[6] = {0xAAAAAAAAAAAAAAAAull, 0xCCCCCCCCCCCCCCCCull, 0xF0F0F0F0F0F0F0F0ull,
                                   0xFF00FF00FF00FF00ull, 0xFFFF0000FFFF0000ull, 0xFFFFFFFF00000000ull};
    u64 s = 0;
    for (int k = 0; k < 6; ++k) s += u64(__builtin_popcountll(m & SEL[k])) << k;
    return s;
}

class Matcher {
public:
    explicit Matcher(const TermTable& terms) : terms_(terms) {}
    // Is the token text [p, p + len) the term `id`? Compared byte by byte, so
    // phrase checks never hash.
    bool is_term(const uint8_t* p, size_t len, u32 id) const {
        if (len != terms_.length(id)) return false;
        const uint8_t* k = terms_.bytes(id);
        for (size_t i = 0; i < len; ++i)
            if (LOWER.t[p[i]] != k[i]) return false;
        return true;
    }

    // Finds phrase[j] in [b, e) with a 32-byte scan for its first letter in either
    // case (byte | 0x20), then checks the whole token, and the phrase around it,
    // only where such a byte starts a token.
    bool contains(const uint8_t* b, const uint8_t* e, std::span<const u32> phrase, size_t j) const {
        const u32 anchor = phrase[j];
        const uint8_t first = terms_.bytes(anchor)[0];
        const __m256i want = _mm256_set1_epi8(first), case_bit = _mm256_set1_epi8(0x20);
        for (const uint8_t* p = b; p < e; p += 32) {
            u32 m = 0;
            if (e - p >= 32) {
                __m256i v = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(p));
                m = _mm256_movemask_epi8(_mm256_cmpeq_epi8(_mm256_or_si256(v, case_bit), want));
            } else {
                for (int i = 0; i < e - p; ++i) m |= u32((p[i] | 0x20) == first) << i;
            }
            for (; m; m &= m - 1) {
                const uint8_t* s = p + __builtin_ctz(m);
                if (s > b && LOWER.t[s[-1]]) continue;
                const uint8_t* t = s;
                while (t < e && LOWER.t[*t]) ++t;
                if (is_term(s, t - s, anchor) && around(b, e, s, t, phrase, j)) return true;
            }
        }
        return false;
    }

    // With phrase[j] at text [s, t), do the j tokens before it and the tokens
    // after it spell the rest of the phrase?
    bool around(const uint8_t* b, const uint8_t* e, const uint8_t* s, const uint8_t* t,
                std::span<const u32> phrase, size_t j) const {
        for (size_t i = j; i-- > 0;) {
            while (s > b && !LOWER.t[s[-1]]) --s;
            const uint8_t* end = s;
            while (s > b && LOWER.t[s[-1]]) --s;
            if (s == end || !is_term(s, end - s, phrase[i])) return false;
        }
        for (size_t i = j + 1; i < phrase.size(); ++i) {
            while (t < e && !LOWER.t[*t]) ++t;
            const uint8_t* start = t;
            while (t < e && LOWER.t[*t]) ++t;
            if (t == start || !is_term(start, t - start, phrase[i])) return false;
        }
        return true;
    }

private:
    const TermTable& terms_;
};


// Only the current block's documents are represented. Epochs make clearing
// independent of vocabulary size; an epoch wrap clears every stored tag.
struct TermState { u64 bits = 0; u32 epoch = 0; };
struct Totals { std::vector<u64> count, sum; };

// Counts/sums stay private to each worker. The ten global smallest ids need
// synchronization only while a block can improve the current tenth id.
struct Smallest {
    std::atomic_flag lock = ATOMIC_FLAG_INIT;
    std::atomic<u32> limit{NONE};
    u32 ids[10]{};
    size_t size = 0;
    void add(u64 bits, u32 base) {
        if (base >= limit.load(std::memory_order_relaxed)) return;
        while (lock.test_and_set(std::memory_order_acquire)) _mm_pause();
        while (bits) {
            const u32 doc = base + __builtin_ctzll(bits);
            bits &= bits - 1;
            if (size == 10 && doc >= ids[9]) break;
            size_t at = std::lower_bound(ids, ids + size, doc) - ids;
            const size_t end = std::min<size_t>(size, 9);
            for (size_t j = end; j > at; --j) ids[j] = ids[j - 1];
            ids[at] = doc;
            if (size < 10) ++size;
        }
        if (size == 10) limit.store(ids[9], std::memory_order_relaxed);
        lock.clear(std::memory_order_release);
    }
};

u32 document_id(const uint8_t* p) {
    u32 result = 0;
    while (*p >= '0' && *p <= '9') result = result * 10 + *p++ - '0';
    return result;
}

void stream_solve(const Paths& paths) {
    prctl(PR_SET_THP_DISABLE, 1, 0, 0, 0);
    mallopt(M_MMAP_THRESHOLD, 1 << 16);
    const File query_file = map_file(paths.data + "/queries.txt");
    const File corpus = map_file(paths.data + "/docs.txt");
    TermTable terms;
    Queries queries = parse_queries(query_file, terms);
    const u32 nt = terms.size();
    const size_t nq = queries.size();
    if (!nq) { write_output(paths.out + "/results.txt", ""); return; }

    // Frequency estimates choose anchors and state layout only. They never
    // suppress a possible match. All documents are evaluated in a complete pass.
    std::vector<u64> frequency(nt);
    constexpr size_t SAMPLES = 16, SAMPLE_BYTES = 32768;
    for (size_t sample = 0; sample < SAMPLES; ++sample) {
        size_t at = corpus.size * sample / SAMPLES;
        while (at && at < corpus.size && corpus.data[at - 1] != '\n') ++at;
        const uint8_t* p = corpus.data + at;
        const uint8_t* stop = p + std::min(SAMPLE_BYTES, corpus.size - at);
        const uint8_t* end = corpus.data + corpus.size;
        while (p < stop) {
            const uint8_t* nl = static_cast<const uint8_t*>(memchr(p, '\n', end - p));
            const uint8_t* text = static_cast<const uint8_t*>(memchr(p, '\t', nl - p)) + 1;
            for_each_token(text, nl, terms, [&](u32 id) { if (id != NONE) ++frequency[id]; });
            p = nl + 1;
        }
    }
    std::vector<u32> order(nt), new_id(nt);
    for (u32 i = 0; i < nt; ++i) order[i] = i;
    std::stable_sort(order.begin(), order.end(), [&](u32 a, u32 b) { return frequency[a] > frequency[b]; });
    std::vector<u64> ranked(nt);
    for (u32 i = 0; i < nt; ++i) new_id[order[i]] = i, ranked[i] = frequency[order[i]];
    terms.renumber(new_id);
    for (u32& id : queries.terms) id = new_id[id];
    frequency.swap(ranked);

    // Each OR starts a conjunction in the distributed form of a left fold.
    // Its anchor is a positive term, so any true document must contain an
    // anchor of at least one clause. Binary NOT never creates new candidates.
    std::vector<std::vector<u32>> watchers(nt);
    std::vector<uint8_t> phrase_anchor(nq);
    auto rarer = [&](u32 a, u32 b) {
        return frequency[a] < frequency[b] ||
            (frequency[a] == frequency[b] && terms.length(a) > terms.length(b));
    };
    for (u32 qi = 0; qi < nq; ++qi) {
        const Query q = queries[qi];
        if (q.phrase) {
            size_t best = 0;
            for (size_t j = 1; j < q.terms.size(); ++j) if (rarer(q.terms[j], q.terms[best])) best = j;
            phrase_anchor[qi] = best;
            watchers[q.terms[best]].push_back(qi);
        } else {
            u32 anchors[6];
            size_t used = 0;
            for (size_t root = 0; root < q.terms.size(); ++root) {
                if (root && q.ops[root - 1] != 'O') continue;
                size_t best = root;
                for (size_t j = root + 1; j < q.terms.size(); ++j)
                    if (q.ops[j - 1] == 'A' && rarer(q.terms[j], q.terms[best])) best = j;
                const u32 anchor = q.terms[best];
                if (std::find(anchors, anchors + used, anchor) == anchors + used) {
                    anchors[used++] = anchor;
                    watchers[anchor].push_back(qi);
                }
            }
        }
    }
    std::vector<u32> watch_first(nt + 1), watch_ids;
    for (u32 id = 0; id < nt; ++id) {
        watch_first[id] = watch_ids.size();
        watch_ids.insert(watch_ids.end(), watchers[id].begin(), watchers[id].end());
    }
    watch_first[nt] = watch_ids.size();
    watchers.clear(); watchers.shrink_to_fit();

    const unsigned workers = std::max(1u, std::min(12u, std::thread::hardware_concurrency()));
    std::vector<size_t> cuts(workers + 1);
    for (unsigned t = 0; t <= workers; ++t) {
        size_t at = corpus.size * t / workers;
        while (at && at < corpus.size && corpus.data[at - 1] != '\n') ++at;
        cuts[t] = at;
    }
    std::unique_ptr<Smallest[]> smallest(new Smallest[nq]);
    std::vector<Totals> totals(workers);
    std::vector<std::thread> pool;
    for (unsigned t = 0; t < workers; ++t) pool.emplace_back([&, t] {
        using Clock = std::chrono::steady_clock;
        double parse_s = 0, query_s = 0;
        u64 evaluations = 0, phrase_candidates = 0;
        Matcher matcher(terms);
        std::vector<TermState> state(nt);
        std::vector<u32> active, visited(nq);
        active.reserve(8192);
        auto& count = totals[t].count;
        auto& sum = totals[t].sum;
        count.resize(nq); sum.resize(nq);
        const uint8_t* p = corpus.data + cuts[t];
        const uint8_t* end = corpus.data + cuts[t + 1];
        u32 doc = p < end ? document_id(p) : 0, epoch = 0;
        while (p < end) {
            const auto block_start = Clock::now();
            if (++epoch == 0) {
                for (auto& s : state) s.epoch = 0;
                std::fill(visited.begin(), visited.end(), 0);
                epoch = 1;
            }
            const u32 base = doc;
            const uint8_t* begin_text[64];
            const uint8_t* end_text[64];
            active.clear();
            for (u32 local = 0; local < 64 && p < end; ++local, ++doc) {
                const uint8_t* nl = static_cast<const uint8_t*>(memchr(p, '\n', end - p));
                const uint8_t* text = static_cast<const uint8_t*>(memchr(p, '\t', nl - p)) + 1;
                begin_text[local] = text; end_text[local] = nl;
                const u64 bit = 1ull << local;
                for_each_token(text, nl, terms, [&](u32 id) {
                    if (id == NONE) return;
                    auto& s = state[id];
                    if (s.epoch != epoch) {
                        s.epoch = epoch; s.bits = bit;
                        if (watch_first[id] != watch_first[id + 1]) active.push_back(id);
                    } else s.bits |= bit;
                });
                p = nl + 1;
            }
            const auto parse_end = Clock::now();
            parse_s += std::chrono::duration<double>(parse_end - block_start).count();
            auto word = [&](u32 id) { return state[id].epoch == epoch ? state[id].bits : 0; };
            for (u32 anchor : active) {
                for (u32 k = watch_first[anchor]; k < watch_first[anchor + 1]; ++k) {
                    const u32 qi = watch_ids[k];
                    if (visited[qi] == epoch) continue;
                    visited[qi] = epoch;
                    ++evaluations;
                    const Query q = queries[qi];
                    u64 bits = word(q.terms[0]);
                    if (q.phrase) {
                        for (size_t j = 1; j < q.terms.size() && bits; ++j) bits &= word(q.terms[j]);
                        phrase_candidates += __builtin_popcountll(bits);
                        u64 matches = 0;
                        for (u64 todo = bits; todo; todo &= todo - 1) {
                            const u32 j = __builtin_ctzll(todo);
                            if (matcher.contains(begin_text[j], end_text[j], q.terms, phrase_anchor[qi])) matches |= 1ull << j;
                        }
                        bits = matches;
                    } else {
                        for (size_t j = 1; j < q.terms.size(); ++j) {
                            const u64 b = word(q.terms[j]);
                            if (q.ops[j - 1] == 'A') bits &= b;
                            else if (q.ops[j - 1] == 'O') bits |= b;
                            else bits &= ~b;
                        }
                    }
                    if (bits) {
                        const u64 c = __builtin_popcountll(bits);
                        count[qi] += c;
                        sum[qi] += c * base + position_sum(bits);
                        smallest[qi].add(bits, base);
                    }
                }
            }
            query_s += std::chrono::duration<double>(Clock::now() - parse_end).count();
        }
        fprintf(stderr, "STREAM thread=%u nt=%u parse=%.6f query=%.6f evaluations=%llu phrase_candidates=%llu\n",
            t, nt, parse_s, query_s, (unsigned long long)evaluations, (unsigned long long)phrase_candidates);
    });
    for (auto& thread : pool) thread.join();
    std::string output;
    output.reserve(nq * 32);
    for (size_t qi = 0; qi < nq; ++qi) {
        u64 count = 0, sum = 0;
        for (const auto& worker : totals) count += worker.count[qi], sum += worker.sum[qi];
        number(output, count); output += ' '; number(output, sum);
        for (size_t j = 0; j < smallest[qi].size; ++j) { output += ' '; number(output, smallest[qi].ids[j]); }
        output += '\n';
    }
    write_output(paths.out + "/results.txt", output);
}

} // namespace

int main(int argc, char** argv) {
    try { const Paths paths(argc, argv); stream_solve(paths); }
    catch (const std::exception& e) { fprintf(stderr, "%s\n", e.what()); return 1; }
}
