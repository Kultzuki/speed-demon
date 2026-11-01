#pragma GCC target("avx2")
#include "common.hpp"
#include <array>
#include <atomic>
#include <bit>
#include <cstdlib>
#include <immintrin.h>
#include <mutex>
#include <numeric>
#include <thread>

// A record is 20 latency bits, 11 endpoint bits and one error bit. The latency
// sentinel has an exact, ordered uint32 overflow stream per hour bucket.
constexpr uint32_t WIDE = (1u << 20) - 1;

// Exact endpoint registry. The arena keeps a private copy of every name, so a
// lookup never touches the scattered input again; the table compares whole
// bytes, so a hash collision only costs a probe.
struct Names {
    struct Slot { std::atomic<uint32_t> id; uint32_t len, off; };
    static constexpr uint32_t SLOTS = 4096, MAX = 2048, WIDTH = 256;
    std::vector<Slot> slots = std::vector<Slot>(SLOTS);
    std::vector<char> arena = std::vector<char>(size_t(MAX) * WIDTH);
    std::vector<uint32_t> offs = std::vector<uint32_t>(MAX), lens = std::vector<uint32_t>(MAX);
    std::atomic<uint32_t> count{0}, used{0};
    static uint64_t hash(const char* p, size_t n) {
        uint64_t a = 0, b = 0;
        if (n >= 8) { __builtin_memcpy(&a, p, 8); __builtin_memcpy(&b, p + n - 8, 8); }
        else { for (size_t i = 0; i < n; ++i) a = a << 8 | uint8_t(p[i]); b = a; }
        uint64_t h = (a ^ std::rotl(b, 29)) + n * 0x9E3779B97F4A7C15ull;
        h ^= h >> 30; h *= 0xBF58476D1CE4E5B9ull;
        h ^= h >> 27; h *= 0x94D049BB133111EBull;
        return h ^ (h >> 31);
    }
    static bool equal(const char* a, const char* b, size_t n, const char* limit) {
        if (n >= 32 && limit - b >= 32) {
            __m256i x = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(a));
            __m256i y = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(b));
            if (_mm256_movemask_epi8(_mm256_cmpeq_epi8(x, y)) != -1) return false;
            a += 32; b += 32; n -= 32;
        }
        return __builtin_memcmp(a, b, n) == 0;
    }
    uint16_t find(const char* p, size_t n, const char* limit) {
        uint32_t at = uint32_t(hash(p, n)) & (SLOTS - 1);
        for (;; at = (at + 1) & (SLOTS - 1)) {
            uint32_t id = slots[at].id.load(std::memory_order_acquire);
            if (!id) {
                uint32_t vacant = 0;
                if (slots[at].id.compare_exchange_strong(vacant, UINT32_MAX, std::memory_order_acquire)) {
                    uint32_t mine = count.fetch_add(1, std::memory_order_relaxed);
                    if (mine >= MAX || n >= WIDTH) std::terminate();
                    uint32_t off = used.fetch_add(uint32_t(n), std::memory_order_relaxed);
                    __builtin_memcpy(arena.data() + off, p, n);
                    slots[at].len = uint32_t(n);
                    slots[at].off = off;
                    offs[mine] = off;
                    lens[mine] = uint32_t(n);
                    slots[at].id.store(mine + 1, std::memory_order_release);
                    return uint16_t(mine);
                }
                while ((id = slots[at].id.load(std::memory_order_acquire)) == UINT32_MAX) {}
                if (!id) continue;
            }
            if (slots[at].len == n && equal(arena.data() + slots[at].off, p, n, limit)) return uint16_t(id - 1);
        }
    }
};

// Lengths of the seven specified methods, keyed by their first three bytes.
static inline uint32_t method_len(const char* p) {
    switch (uint32_t(uint8_t(p[0])) << 16 | uint32_t(uint8_t(p[1])) << 8 | uint8_t(p[2])) {
        case 0x474554: case 0x505554: return 3;   // GET PUT
        case 0x504f53: case 0x484541: return 4;   // POS HEA
        case 0x504154: return 5;                  // PAT
        case 0x44454c: return 6;                  // DEL
        case 0x4f5054: return 7;                  // OPT
        default: { const char* s = p; while (*s != ' ') ++s; return uint32_t(s - p); }
    }
}

// Reads 1..8 decimal digits at p; eight means the field may continue.
static inline uint32_t digits8(const char* p, uint32_t& count) {
    uint64_t w; __builtin_memcpy(&w, p, 8);
    uint64_t x = w ^ 0x3030303030303030ull;
    uint64_t stop = (x + 0x7676767676767676ull) & ~x & 0x8080808080808080ull;
    uint32_t n = uint32_t(std::countr_zero(stop)) >> 3;
    uint32_t v = 0;
    for (uint32_t i = 0; i < n; ++i) v = v * 10 + uint32_t(p[i] - '0');
    count = n;
    return v;
}

static inline char* put_u64(char* o, uint64_t v) {
    char tmp[20]; int n = 0;
    do { tmp[n++] = char('0' + v % 10); v /= 10; } while (v);
    while (n) *o++ = tmp[--n];
    return o;
}

struct Partial {
    std::array<std::vector<uint32_t>, 72> records, wide;
    void parse(const char* p, const char* end, Names& names) {
        const __m256i space = _mm256_set1_epi8(' ');
        while (p < end) {
            unsigned day = (p[8] - '0') * 10 + (p[9] - '0');
            unsigned clock = (p[11] - '0') * 10 + (p[12] - '0');
            uint32_t bucket = uint32_t((p[6] == '0' ? day - 30 : day + 1) * 24 + clock - 18);
            const char* start = p + 28;
            start += method_len(start) + 1;
            const char* q = start;
            for (;;) {
                if (end - q >= 64) {
                    uint32_t a = _mm256_movemask_epi8(_mm256_cmpeq_epi8(
                        _mm256_loadu_si256(reinterpret_cast<const __m256i*>(q)), space));
                    uint32_t b = _mm256_movemask_epi8(_mm256_cmpeq_epi8(
                        _mm256_loadu_si256(reinterpret_cast<const __m256i*>(q + 32)), space));
                    if (a) { q += std::countr_zero(a); break; }
                    if (b) { q += 32 + std::countr_zero(b); break; }
                    q += 64;
                } else { while (*q != ' ') ++q; break; }
            }
            uint32_t id = names.find(start, size_t(q - start), end);
            uint32_t error = q[1] == '5';
            const char* digits = q + 5;
            uint32_t latency;
            if (end - digits >= 8) {
                uint32_t count = 0;
                latency = digits8(digits, count);
                if (count == 8) { p = digits; latency = uint32_t(integer(p)); }
                else p = digits + count;
            } else { p = digits; latency = uint32_t(integer(p)); }
            if (p < end && *p == '\n') ++p;
            records[bucket].push_back((std::min(latency, WIDE) << 12) | (id << 1) | error);
            if (latency >= WIDE) wide[bucket].push_back(latency);
        }
    }
};

// Exact nearest-rank values for ranks r0<r1<r2 of a group of n latencies.
// Large groups bucket by value first, so the ranks are resolved with
// sequential passes instead of three cache-hostile partitions.
static void ranks3(uint32_t* v, size_t n, const size_t* r, uint32_t* out) {
    if (n <= 64) {
        for (size_t i = 1; i < n; ++i) {
            uint32_t x = v[i]; size_t j = i;
            while (j && v[j - 1] > x) { v[j] = v[j - 1]; --j; }
            v[j] = x;
        }
        for (int t = 0; t < 3; ++t) out[t] = v[r[t]];
        return;
    }
    if (n < 512) {
        for (int t = 0; t < 3; ++t) {
            size_t from = t ? r[t - 1] + 1 : 0;
            std::nth_element(v + from, v + r[t], v + n);
            out[t] = v[r[t]];
        }
        return;
    }
    uint32_t top = 0;
    for (size_t i = 0; i < n; ++i) top = std::max(top, v[i]);
    unsigned bits = 32 - unsigned(std::countl_zero(top));
    unsigned shift = bits > 11 ? bits - 11 : 0;
    uint32_t count[2048] = {};
    for (size_t i = 0; i < n; ++i) ++count[v[i] >> shift];
    std::vector<uint32_t> cand;
    for (int t = 0; t < 3; ++t) {
        uint32_t acc = 0, b = 0;
        while (acc + count[b] <= r[t]) { acc += count[b]; ++b; }
        size_t need = r[t] - acc;
        cand.clear();
        for (size_t i = 0; i < n; ++i) { uint32_t x = v[i]; if ((x >> shift) == b) cand.push_back(x); }
        std::nth_element(cand.begin(), cand.begin() + need, cand.end());
        out[t] = cand[need];
    }
}

int main(int argc, char** argv) {
    try {
        Paths paths(argc, argv);
        MappedFile input(paths.data + "/requests.log");
        unsigned workers = std::min(12u, std::max(1u, std::thread::hardware_concurrency()));
        if (input.size < 2 * 1024 * 1024) workers = 1;
        std::vector<const char*> cuts(workers + 1);
        cuts[0] = input.data; cuts[workers] = input.end();
        for (unsigned i = 1; i < workers; ++i) {
            auto p = input.data + input.size * i / workers;
            while (p < input.end() && p[-1] != '\n') ++p;
            cuts[i] = p;
        }
        Names names;
        std::vector<Partial> parts(workers);
        std::vector<std::thread> threads;
        for (unsigned i = 0; i < workers; ++i)
            threads.emplace_back([&, i] { parts[i].parse(cuts[i], cuts[i + 1], names); });
        for (auto& thread : threads) thread.join();
        uint32_t count = names.count.load();
        std::vector<uint32_t> order(count);
        std::iota(order.begin(), order.end(), 0);
        std::sort(order.begin(), order.end(), [&](uint32_t a, uint32_t b) {
            return std::string_view(names.arena.data() + names.offs[a], names.lens[a]) <
                   std::string_view(names.arena.data() + names.offs[b], names.lens[b]);
        });
        FILE* file = fopen((paths.out + "/summary.txt").c_str(), "wb");
        if (!file) throw std::runtime_error("Cannot write summary");
        std::array<std::string, 72> outputs;
        std::array<bool, 72> ready{};
        std::mutex output_mutex;
        unsigned turn = 0;
        bool ok = true;
        std::atomic<unsigned> next{0};
        threads.clear();
        for (unsigned worker = 0; worker < workers; ++worker) threads.emplace_back([&] {
            std::vector<uint32_t> counts(count), errors(count), positions(count), values;
            char row[512];
            for (;;) {
                unsigned hour = next.fetch_add(1, std::memory_order_relaxed);
                if (hour >= 72) break;
                std::fill(counts.begin(), counts.end(), 0);
                std::fill(errors.begin(), errors.end(), 0);
                size_t total = 0;
                for (auto& part : parts) {
                    auto& b = part.records[hour];
                    total += b.size();
                    for (uint32_t word : b) { uint32_t id = (word >> 1) & 2047; ++counts[id]; errors[id] += word & 1; }
                }
                uint32_t at = 0;
                for (uint32_t i = 0; i < count; ++i) { positions[i] = at; at += counts[i]; }
                values.resize(total);
                for (auto& part : parts) {
                    auto& b = part.records[hour];
                    size_t wide = 0;
                    for (uint32_t word : b) {
                        uint32_t latency = word >> 12;
                        if (latency == WIDE) latency = part.wide[hour][wide++];
                        values[positions[(word >> 1) & 2047]++] = latency;
                    }
                    std::vector<uint32_t>().swap(b);
                    std::vector<uint32_t>().swap(part.wide[hour]);
                }
                std::string& output = outputs[hour];
                output.reserve(160 * 1024);
                unsigned day = (hour + 18) / 24;
                char stamp[32];
                int stamp_len = snprintf(stamp, sizeof(stamp), "2026-%02u-%02uT%02u:00:00Z",
                                         day < 2 ? 10 : 11, day < 2 ? 30 + day : day - 1, (hour + 18) % 24);
                for (uint32_t id : order) {
                    uint64_t n = counts[id];
                    if (!n) continue;
                    uint32_t* begin = values.data() + positions[id] - n;
                    size_t r[3] = {size_t((50 * n + 99) / 100 - 1), size_t((95 * n + 99) / 100 - 1),
                                   size_t((99 * n + 99) / 100 - 1)};
                    uint32_t picked[3];
                    ranks3(begin, size_t(n), r, picked);
                    char* o = row;
                    __builtin_memcpy(o, stamp, size_t(stamp_len)); o += stamp_len; *o++ = ' ';
                    __builtin_memcpy(o, names.arena.data() + names.offs[id], names.lens[id]);
                    o += names.lens[id];
                    for (uint64_t value : {n, uint64_t(picked[0]), uint64_t(picked[1]), uint64_t(picked[2]),
                                           uint64_t(errors[id]), uint64_t(errors[id]) * 1000000 / n}) {
                        *o++ = ' '; o = put_u64(o, value);
                    }
                    *o++ = '\n';
                    output.append(row, size_t(o - row));
                }
                std::lock_guard<std::mutex> lock(output_mutex);
                ready[hour] = true;
                while (turn < 72 && ready[turn]) {
                    auto& s = outputs[turn++];
                    ok &= fwrite(s.data(), 1, s.size(), file) == s.size();
                    std::string{}.swap(s);
                }
            }
        });
        for (auto& thread : threads) thread.join();
        if (fclose(file) != 0 || !ok) throw std::runtime_error("Summary write failed");
        _exit(0);
    } catch (const std::exception& e) { fprintf(stderr, "%s\n", e.what()); return 1; }
}
