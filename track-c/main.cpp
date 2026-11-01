#include <unistd.h>
#include "common.hpp"
#include <array>
#include <limits>
#include <thread>
#include <mutex>
#include <immintrin.h>
#include <bit>
#include <atomic>
#include <memory>
#include <vector>
#include <cstring>

static inline const char* find_quote(const char* p, const char* end) {
    const __m128i q = _mm_set1_epi8('"');
    while (p + 16 <= end) {
        __m128i v = _mm_loadu_si128(reinterpret_cast<const __m128i*>(p));
        uint32_t mask = _mm_movemask_epi8(_mm_cmpeq_epi8(v, q));
        if (mask) return p + std::countr_zero(mask);
        p += 16;
    }
    while (p < end && *p != '"') ++p;
    return (p < end) ? p : nullptr;
}

static inline size_t fast_hash_and_prefix(std::string_view name, uint64_t& out_prefix) {
    const char* p = name.data();
    size_t n = name.size();
    uint64_t a = 0, b = 0;
    if (n >= 8) {
        __builtin_memcpy(&a, p, 8);
        __builtin_memcpy(&b, p + n - 8, 8);
    } else {
        for (size_t i = 0; i < n; ++i) a = (a << 8) | uint8_t(p[i]);
        b = a;
    }
    out_prefix = a;
    uint64_t h = (a ^ std::rotl(b, 29)) + (n * 0x9E3779B97F4A7C15ull);
    h ^= h >> 30; h *= 0xBF58476D1CE4E5B9ull;
    h ^= h >> 27; h *= 0x94D049BB133111EBull;
    h ^= h >> 31;
    return size_t(h);
}

struct Field {
    std::string_view value;
    size_t bytes;
};

static inline Field name_field(const char*& p, const char* end, std::string& decoded) {
    if (*p != '"') {
        const char* start = p;
        while (p < end && *p != ',') ++p;
        return {std::string_view(start, p - start), size_t(p - start)};
    }
    const char* start = ++p;
    const char* segment = p;
    size_t escaped = 0;
    for (;;) {
        p = find_quote(p, end);
        if (!p) throw std::runtime_error("Unclosed CSV quote");
        if (p + 1 < end && p[1] == '"') {
            if (!escaped) decoded.clear();
            decoded.append(segment, p + 1);
            ++escaped;
            p += 2;
            segment = p;
        } else {
            size_t bytes = p - start - escaped;
            std::string_view value(start, p - start);
            if (escaped) {
                decoded.append(segment, p);
                value = decoded;
            }
            ++p;
            return {value, bytes};
        }
    }
}

static inline size_t note_bytes(const char*& p, const char* end) {
    if (*p != '"') {
        const char* start = p;
        while (p < end && *p != ',') ++p;
        return p - start;
    }
    const char* start = ++p;
    size_t escaped = 0;
    for (;;) {
        p = find_quote(p, end);
        if (!p) throw std::runtime_error("Unclosed CSV quote");
        if (p + 1 < end && p[1] == '"') {
            ++escaped;
            p += 2;
        } else {
            size_t bytes = p - start - escaped;
            ++p;
            return bytes;
        }
    }
}

constexpr size_t BUCKETS = 262144;
constexpr size_t BUCKET_MASK = BUCKETS - 1;
constexpr size_t NUM_SHARDS = 256;

struct Node {
    Node* next;
    uint32_t tag;
    uint32_t length;
    uint64_t prefix;
    std::atomic<uint64_t> membership[4]{};
    std::string_view name() const {
        return {reinterpret_cast<const char*>(this) + sizeof(Node), length};
    }
};

struct SharedNames {
    std::atomic<Node*> heads[BUCKETS]{};

    struct alignas(64) Shard {
        std::mutex mutex;
        std::vector<std::unique_ptr<char[]>> arenas;
        size_t used = 8192;
        Node* insert(std::string_view name, uint32_t tag, uint64_t prefix, Node* next) {
            size_t bytes = sizeof(Node) + name.size();
            size_t at = (used + alignof(Node) - 1) & ~(alignof(Node) - 1);
            if (arenas.empty() || at + bytes > 8192) {
                arenas.push_back(std::make_unique<char[]>(std::max<size_t>(8192, bytes)));
                at = 0;
            }
            char* data = arenas.back().get() + at;
            auto* node = new(data) Node{next, tag, (uint32_t)name.size(), prefix};
            memcpy(data + sizeof(Node), name.data(), name.size());
            used = at + bytes;
            return node;
        }
    };
    std::array<Shard, NUM_SHARDS> shards;

    void prefetch_bucket(size_t hash) {
        __builtin_prefetch(&heads[hash & BUCKET_MASK], 0, 3);
    }

    void prefetch_node(size_t hash) {
        Node* node = heads[hash & BUCKET_MASK].load(std::memory_order_relaxed);
        if (node) __builtin_prefetch(node, 0, 3);
    }

    bool add(std::string_view name, uint16_t country, size_t hash, uint64_t prefix) {
        uint32_t tag = (uint32_t)(hash >> 32);
        uint32_t len = (uint32_t)name.size();
        auto& head = heads[hash & BUCKET_MASK];

        auto find = [&](Node* node) {
            while (node) {
                if (node->tag == tag && node->length == len && node->prefix == prefix) {
                    if (len <= 8 || memcmp(node->name().data() + 8, name.data() + 8, len - 8) == 0)
                        return node;
                }
                node = node->next;
            }
            return static_cast<Node*>(nullptr);
        };

        Node* node = find(head.load(std::memory_order_acquire));
        if (!node) {
            auto& shard = shards[(hash >> 32) % NUM_SHARDS];
            std::lock_guard<std::mutex> lock(shard.mutex);
            auto first = head.load(std::memory_order_relaxed);
            node = find(first);
            if (!node) {
                node = shard.insert(name, tag, prefix, first);
                head.store(node, std::memory_order_release);
            }
        }
        uint64_t bit = uint64_t(1) << (country % 64);
        auto& word = node->membership[country / 64];
        if (word.load(std::memory_order_relaxed) & bit) return false;
        return !(word.fetch_or(bit, std::memory_order_relaxed) & bit);
    }
};

struct Country {
    std::string key;
    uint64_t count = 0, id_sum = 0, distinct = 0, name_bytes = 0, note_bytes = 0;
    int64_t sum = 0, minimum = INT64_MAX, maximum = INT64_MIN;
};

void money(std::string& out, int64_t value) {
    if (value < 0) { out += '-'; value = -value; }
    number(out, value / 100);
    out += '.';
    out += char('0' + value % 100 / 10);
    out += char('0' + value % 10);
}

struct Partial {
    std::vector<Country> countries;
    template<class Id> void parse(const char* begin, const char* end, const std::vector<Id>& lookup, size_t count, SharedNames& names) {
        countries.resize(count);
        const char* p = begin;
        struct Pending {
            std::string scratch;
            std::string_view name;
            uint16_t country;
            size_t hash;
            uint64_t prefix;
        };
        constexpr size_t PIPE = 8;
        std::array<Pending, PIPE> pending;
        size_t serial = 0;
        auto retire = [&](Pending& old) {
            countries[old.country].distinct += names.add(old.name, old.country, old.hash, old.prefix);
        };
        while (p < end) {
            if (static_cast<unsigned char>(*p) == 0xef) p += 3;
            uint64_t id = 0;
            while (static_cast<unsigned>(*p - '0') < 10) id = id * 10 + (*p++ - '0');
            ++p; // comma
            auto& next = pending[serial % PIPE];
            if (serial >= PIPE) retire(next);
            ++serial;
            Field name = name_field(p, end, next.scratch);
            ++p; // comma
            size_t nbytes = note_bytes(p, end);
            ++p; // comma
            uint32_t region = 0;
            while (static_cast<unsigned>(*p - '0') < 10) region = region * 10 + (*p++ - '0');
            ++p; // comma
            bool negative = (*p == '-');
            p += negative;
            int64_t amount = 0;
            while (*p != '.') amount = amount * 10 + (*p++ - '0');
            amount = amount * 100 + (p[1] - '0') * 10 + (p[2] - '0');
            p += 3;
            p += (*p == '\r');
            ++p; // newline
            if (negative) amount = -amount;

            uint16_t country = region < lookup.size() ? lookup[region] : 0;
            auto& group = countries[country];
            next.name = name.value;
            next.country = country;
            next.hash = fast_hash_and_prefix(name.value, next.prefix);

            names.prefetch_bucket(next.hash);
            if (serial >= 4) {
                auto& mid = pending[(serial - 4) % PIPE];
                names.prefetch_node(mid.hash);
            }

            ++group.count;
            group.id_sum += id;
            group.sum += amount;
            group.minimum = std::min(group.minimum, amount);
            group.maximum = std::max(group.maximum, amount);
            group.name_bytes += name.bytes;
            group.note_bytes += nbytes;
        }
        for (size_t i = serial > PIPE ? serial - PIPE : 0; i < serial; ++i)
            retire(pending[i % PIPE]);
    }
};

std::vector<const char*> boundaries(const char* begin, const char* end, unsigned workers) {
    std::vector<const char*> result(workers + 1, end);
    result[0] = begin;
    for (unsigned i = 1; i < workers; ++i) {
        const char* p = begin + (end - begin) * i / workers;
        while (p < end && !(p > begin && p[-1] == '\n' &&
               ((unsigned(*p - '0') < 10) || static_cast<unsigned char>(*p) == 0xef))) ++p;
        result[i] = p;
    }
    return result;
}

int main(int argc, char** argv) {
    try {
        Paths paths(argc, argv);
        MappedFile regions(paths.data + "/regions.csv"), records(paths.data + "/records.csv");

        std::vector<Country> countries(1);
        countries[0].key = "_UNMATCHED";
        uint16_t country_map[17576] = {};
        std::vector<uint8_t> lookup(1048576, 0);

        const char* p = regions.data;
        while (p < regions.end() && *p++ != '\n') {}
        while (p < regions.end()) {
            uint32_t region = 0;
            while (*p >= '0') region = region * 10 + (*p++ - '0');
            ++p; // comma
            uint32_t code = (uint8_t(p[0] - 'A') * 26 + uint8_t(p[1] - 'A')) * 26 + uint8_t(p[2] - 'A');
            uint16_t cid = country_map[code];
            if (!cid) {
                cid = uint16_t(countries.size());
                country_map[code] = cid;
                countries.emplace_back();
                countries.back().key = std::string(p, 3);
            }
            if (region >= lookup.size()) lookup.resize(size_t(region) + 1, 0);
            lookup[region] = uint8_t(cid);
            p += 4; // 3 letters + newline
        }

        p = records.data;
        while (p < records.end() && *p++ != '\n') {}
        unsigned workers = std::min(12u, std::max(1u, std::thread::hardware_concurrency()));
        if (records.size < 2 * 1024 * 1024) workers = 1;
        auto cuts = boundaries(p, records.end(), workers);
        SharedNames names;
        std::vector<Partial> parts(workers);
        std::vector<std::thread> threads;
        for (unsigned i = 0; i < workers; ++i)
            threads.emplace_back([&, i] { parts[i].parse(cuts[i], cuts[i + 1], lookup, countries.size(), names); });
        for (auto& thread : threads) thread.join();

        for (unsigned i = 0; i < workers; ++i) {
            for (size_t j = 0; j < countries.size(); ++j) {
                const auto& from = parts[i].countries[j]; auto& to = countries[j];
                to.count += from.count; to.id_sum += from.id_sum; to.sum += from.sum; to.distinct += from.distinct;
                to.minimum = std::min(to.minimum, from.minimum); to.maximum = std::max(to.maximum, from.maximum);
                to.name_bytes += from.name_bytes; to.note_bytes += from.note_bytes;
            }
        }
        std::sort(countries.begin(), countries.end(), [](auto& a, auto& b) { return a.key < b.key; });
        std::string output;
        for (const auto& g : countries) {
            if (!g.count) continue;
            output += g.key;
            for (auto value : {g.count, g.id_sum}) { output += ' '; number(output, value); }
            for (auto value : {g.sum, g.minimum, g.maximum}) { output += ' '; money(output, value); }
            for (auto value : {g.distinct, g.name_bytes, g.note_bytes}) { output += ' '; number(output, value); }
            output += '\n';
        }
        write_output(paths.out + "/aggregates.txt", output);
        _exit(0);
    } catch (const std::exception& e) { fprintf(stderr, "%s\n", e.what()); return 1; }
}
