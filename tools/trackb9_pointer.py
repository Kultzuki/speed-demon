"""Avoid materializing padded 32-byte keys for corpus tokens."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
source = (PROTO / 'trackb9-short.cpp').read_text()
marker = 'private:\n    void rehash(size_t cap) {'
method = '''    // Token bytes remain in the owned mapping. A fingerprint miss needs no
    // key construction; a possible hit compares every normalized token byte.
    u32 find(const uint8_t* p, size_t len, u64 h) const {
        for (size_t i = h & mask_;; i = (i + 1) & mask_) {
            const u64 s = slots_[i];
            if (s == 0) return NONE;
            if ((s >> 32) != (h >> 32)) continue;
            const u32 id = u32(s) - 1;
            if (lens_[id] != len) continue;
            const Key& key = keys_[id];
            bool equal = true;
            for (size_t j = 0; j < (len + 7) / 8; ++j) {
                u64 raw;
                memcpy(&raw, p + 8 * j, 8);
                raw = _bzhi_u64(raw | 0x2020202020202020ull, unsigned((len - 8 * j) * 8));
                if (raw != key.w[j]) { equal = false; break; }
            }
            if (equal) return id;
        }
    }

'''
assert marker in source
source = source.replace(marker, method + marker, 1)
source = source.replace('    Key keys[LAG];', '    const uint8_t* positions[LAG];\n    uint8_t lengths[LAG];')
start = source.index('        Key k;', source.index('inline void for_each_token'))
end = source.index('        terms.prefetch(h);', start)
source = source[:start] + '''        u64 a, b = 0;
        memcpy(&a, s, 8);
        a = _bzhi_u64(a | 0x2020202020202020ull, unsigned(len * 8));
        if (len > 8) {
            memcpy(&b, s + 8, 8);
            b = _bzhi_u64(b | 0x2020202020202020ull, unsigned((len - 8) * 8));
        }
        const u64 h = _mm_crc32_u64(_mm_crc32_u64(0, a), b) * 0x9E3779B97F4A7C15ull;
''' + source[end:]
source = source.replace('terms.find(keys[slot], hashes[slot])', 'terms.find(positions[slot], lengths[slot], hashes[slot])')
source = source.replace('        keys[slot] = k;', '        positions[slot] = s;\n        lengths[slot] = len;')
source = source.replace('terms.find(keys[i % LAG], hashes[i % LAG])',
    'terms.find(positions[i % LAG], lengths[i % LAG], hashes[i % LAG])')
(PROTO / 'trackb9-pointer.cpp').write_text(source)
# Also compare one wide vector for candidate equality, instead of a word loop.
start = source.index('            const Key& key = keys_[id];', source.index('u32 find(const uint8_t*'))
end = source.index('            if (equal) return id;', start) + len('            if (equal) return id;')
simd = source[:start] + '''            const __m256i indexes = _mm256_setr_epi8(0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,
                                                        16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31);
            const __m256i raw = _mm256_or_si256(_mm256_loadu_si256(reinterpret_cast<const __m256i*>(p)), _mm256_set1_epi8(0x20));
            const __m256i keep = _mm256_cmpgt_epi8(_mm256_set1_epi8(char(len)), indexes);
            const __m256i key = _mm256_load_si256(reinterpret_cast<const __m256i*>(&keys_[id]));
            const __m256i diff = _mm256_xor_si256(_mm256_and_si256(raw, keep), key);
            if (_mm256_testz_si256(diff, diff)) return id;''' + source[end:]
(PROTO / 'trackb9-pointer-simd.cpp').write_text(simd)
for lag in [0, 4, 16]:
    text = simd
    if lag:
        text = text.replace('constexpr size_t LAG = 8;', f'constexpr size_t LAG = {lag};')
    else:
        start = text.index('        terms.prefetch(h);', text.index('inline void for_each_token'))
        end = text.index('\n}', start)
        text = text[:start] + '''        emit(terms.find(s, len, h));
    }''' + text[end:]
    (PROTO / f'trackb9-pointer-lag{lag}.cpp').write_text(text)
print('Created pointer-pipeline exact lookup variants.')
