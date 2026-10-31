"""Exact SIMD token-key construction experiments; no dictionary shortcuts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
old = '''        for (size_t i = 0; i < 4; ++i) {
            size_t b = len > 8 * i ? std::min<size_t>(len - 8 * i, 8) : 0;
            u64 w;
            memcpy(&w, s + 8 * i, 8);
            k.w[i] = (w | 0x2020202020202020ull) & (b == 8 ? ~0ull : (1ull << (8 * b)) - 1);
        }'''
new = '''        const __m256i index=_mm256_setr_epi8(0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,
                                                   16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31);
        __m256i raw=_mm256_loadu_si256(reinterpret_cast<const __m256i*>(s));
        __m256i keep=_mm256_cmpgt_epi8(_mm256_set1_epi8(char(len)),index);
        _mm256_store_si256(reinterpret_cast<__m256i*>(&k),
            _mm256_and_si256(_mm256_or_si256(raw,_mm256_set1_epi8(0x20)),keep));'''

for name, source in [('simdkey', 'continuation7-base-b'), ('key-ownedbits', 'continuation7-ownedbits-b')]:
    s = (PROTO / (source + '.cpp')).read_text()
    assert s.count(old) == 1
    path = PROTO / f'continuation7-{name}-b.cpp'
    assert not path.exists()
    path.write_text(s.replace(old, new))
print('Created exact SIMD key variants.')
