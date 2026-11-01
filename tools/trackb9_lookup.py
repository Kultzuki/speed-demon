"""Exact short-key, worker-cache and owned-bitmap lookup experiments."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
base = (PROTO / 'trackb9-base.cpp').read_text()
start = base.index('        for (size_t i = 0; i < 4; ++i) {', base.index('inline void for_each_token'))
end = base.index('        const u64 h = hash_key(k);', start)
short = base[:start] + '''        k = Key{{0, 0, 0, 0}};
        u64 raw;
        memcpy(&raw, s, 8);
        k.w[0] = _bzhi_u64(raw | 0x2020202020202020ull, unsigned(len * 8));
        if (len > 8) {
            memcpy(&raw, s + 8, 8);
            k.w[1] = _bzhi_u64(raw | 0x2020202020202020ull, unsigned((len - 8) * 8));
            if (len > 16) {
                memcpy(&raw, s + 16, 8);
                k.w[2] = _bzhi_u64(raw | 0x2020202020202020ull, unsigned((len - 16) * 8));
                if (len > 24) {
                    memcpy(&raw, s + 24, 8);
                    k.w[3] = _bzhi_u64(raw | 0x2020202020202020ull, unsigned((len - 24) * 8));
                }
            }
        }
''' + base[end:]
start = short.index('    u64 h = ', short.index('inline u64 hash_key'))
end = short.index('\n}', start)
short = short[:start] + '''    return _mm_crc32_u64(_mm_crc32_u64(0, k.w[0]), k.w[1]) * 0x9E3779B97F4A7C15ull;''' + short[end:]
(PROTO / 'trackb9-short.cpp').write_text(short)

cache_code = '''// This cache compares the complete short key, including its zero padding.
// Longer keys always use the full dictionary comparison. It is cleared after
// sample-driven term renumbering; cached absent results are exact too.
struct LookupCache {
    struct Slot { u64 lo = 0, hi = 0; u32 id = NONE; };
    Slot slots[512];
    u32 find(const TermTable& terms, const Key& k, u64 h) {
        if (k.w[2] | k.w[3]) return terms.find(k, h);
        Slot& s = slots[h & 511];
        if (s.lo == k.w[0] && s.hi == k.w[1]) return s.id;
        u32 id = terms.find(k, h);
        s = {k.w[0], k.w[1], id};
        return id;
    }
};

'''
start = short.index('// Bit i is set')
cached = short[:start] + cache_code + short[start:]
cached = cached.replace('const TermTable& terms, F&& emit)', 'const TermTable& terms, LookupCache& cache, F&& emit)')
cached = cached.replace('terms.find(keys[slot], hashes[slot])', 'cache.find(terms, keys[slot], hashes[slot])')
cached = cached.replace('terms.find(keys[i % LAG], hashes[i % LAG])', 'cache.find(terms, keys[i % LAG], hashes[i % LAG])')
cached = cached.replace('            auto walk =', '            LookupCache cache;\n            auto walk =')
cached = cached.replace('for_each_token(tx, nl, terms,', 'for_each_token(tx, nl, terms, cache,')
cached = cached.replace('            std::fill(cnt.begin(), cnt.end(), 0);',
    '            cache = LookupCache{};\n            std::fill(cnt.begin(), cnt.end(), 0);')
(PROTO / 'trackb9-cache.cpp').write_text(cached)

def owned(source):
    # Shift every interior byte cut to a document whose id is a multiple of
    # 64. Each bitmap word then has exactly one writer, with no atomic loads.
    old = '''        cut[t] = c;'''
    new = '''        if (t > 0 && t < nthreads) {
            while (c < size && (parse_id(base + c) & 63)) {
                const uint8_t* nl = static_cast<const uint8_t*>(memchr(base + c, '\\n', size - c));
                c = size_t(nl - base) + 1;
            }
        }
        cut[t] = c;'''
    # Ownership can change a local range's width; main's old preflight only
    # checks unsnapped cuts. Use 32-bit streams in this diagnostic variant.
    source = source.replace(old, new)
    old = '''                    std::atomic_ref<u64>(ix.bits[d * ix.words + doc / 64])
                        .fetch_or(1ull << (doc % 64), std::memory_order_relaxed);'''
    new = '''                    ix.bits[d * ix.words + doc / 64] |= 1ull << (doc % 64);'''
    assert old in source
    source = source.replace(old, new)
    # Keep narrow postings, but cap the per-thread pack to 16 bits and make
    # packed entries four bytes instead of three. Handles the wider cut safely.
    source = source.replace('sizeof(Doc)==2?3:8', 'sizeof(Doc)==2?4:8')
    source = source.replace('sizeof(Doc)==2?15:32', 'sizeof(Doc)==2?16:32')
    source = source.replace('if constexpr(sizeof(Doc)==2) x&=0xFFFFFF;', '')
    source = source.replace('>32768)', '>65536)')
    return source

(PROTO / 'trackb9-owned.cpp').write_text(owned(short))
print('Created short-key, exact worker-cache and word-owned bitmap candidates.')
