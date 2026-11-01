"""Reduce exact result aggregation and sparse-list decode work."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
source = (PROTO / 'trackb9-base.cpp').read_text()
zero = source.replace('                u64 bits = bm_[w];\n                u64 c',
    '                u64 bits = bm_[w];\n                if (!bits) continue;\n                u64 c')
(PROTO / 'trackb9-zero.cpp').write_text(zero)
for threshold in [16, 64, 128, 256]:
    text = zero.replace('if (df[order[rank]] * 32 > docs)',
        f'if (df[order[rank]] * {threshold} > docs)')
    assert text != zero
    (PROTO / f'trackb9-dense{threshold}.cpp').write_text(text)

helper = '''// Four bitmap words at a time: byte popcounts and local position sums
// are nibble-table shuffles. All accumulators and document sums are uint64.
void bitmap_totals(const u64* data, size_t words, u64& count, u64& sum) {
    const __m256i pc = _mm256_setr_epi8(0,1,1,2,1,2,2,3,1,2,2,3,2,3,3,4,
                                      0,1,1,2,1,2,2,3,1,2,2,3,2,3,3,4);
    const __m256i ps = _mm256_setr_epi8(0,0,1,1,2,2,3,3,3,3,4,4,5,5,6,6,
                                      0,0,1,1,2,2,3,3,3,3,4,4,5,5,6,6);
    const __m256i weights = _mm256_setr_epi8(0,8,16,24,32,40,48,56,0,8,16,24,32,40,48,56,
                                            0,8,16,24,32,40,48,56,0,8,16,24,32,40,48,56);
    const __m256i mask = _mm256_set1_epi8(15), zero = _mm256_setzero_si256();
    const __m256i low32 = _mm256_set1_epi64x(0xffffffffull);
    __m256i counts = zero, sums = zero;
    size_t w = 0;
    for (; w + 4 <= words; w += 4) {
        const __m256i bits = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(data + w));
        const __m256i lo = _mm256_and_si256(bits, mask);
        const __m256i hi = _mm256_and_si256(_mm256_srli_epi16(bits, 4), mask);
        const __m256i hc = _mm256_shuffle_epi8(pc, hi);
        const __m256i bytes = _mm256_add_epi8(_mm256_shuffle_epi8(pc, lo), hc);
        const __m256i c = _mm256_sad_epu8(bytes, zero);
        const __m256i positions = _mm256_add_epi8(_mm256_add_epi8(_mm256_shuffle_epi8(ps, lo),
            _mm256_shuffle_epi8(ps, hi)), _mm256_slli_epi16(hc, 2));
        const __m256i weighted = _mm256_madd_epi16(_mm256_maddubs_epi16(bytes, weights), _mm256_set1_epi16(1));
        const __m256i offsets = _mm256_add_epi64(_mm256_and_si256(weighted, low32), _mm256_srli_epi64(weighted, 32));
        const __m256i bases = _mm256_set_epi64x((w + 3) * 64, (w + 2) * 64, (w + 1) * 64, w * 64);
        counts = _mm256_add_epi64(counts, c);
        sums = _mm256_add_epi64(sums, _mm256_add_epi64(_mm256_mul_epu32(c, bases),
            _mm256_add_epi64(offsets, _mm256_sad_epu8(positions, zero))));
    }
    alignas(32) u64 c[4], s[4];
    _mm256_store_si256(reinterpret_cast<__m256i*>(c), counts);
    _mm256_store_si256(reinterpret_cast<__m256i*>(s), sums);
    for (int j = 0; j < 4; ++j) count += c[j], sum += s[j];
    for (; w < words; ++w) {
        const u64 bits = data[w], c = __builtin_popcountll(bits);
        count += c;
        sum += c * w * 64 + position_sum(bits);
    }
}

'''
start = source.index('template<class Doc,class Offset> class Solver')
simd = source[:start] + helper + source[start:]
start = simd.index('            for (size_t w = 0; w < bm_.size(); ++w) {', simd.index('    int format(char* out) const'))
end = simd.index('        } else {', start)
simd = simd[:start] + '''            bitmap_totals(bm_.data(), bm_.size(), count, sum);
            for (size_t w = 0; w < bm_.size() && m < 10; ++w)
                for (u64 bits = bm_[w]; bits && m < 10; bits &= bits - 1)
                    smallest[m++] = w * 64 + __builtin_ctzll(bits);
''' + simd[end:]
(PROTO / 'trackb9-simdformat.cpp').write_text(simd)
for threshold in [64, 128]:
    text = simd.replace('if (df[order[rank]] * 32 > docs)',
        f'if (df[order[rank]] * {threshold} > docs)')
    (PROTO / f'trackb9-simdformat{threshold}.cpp').write_text(text)
print('Created empty-word, AVX2 aggregation and bitmap-threshold experiments.')
