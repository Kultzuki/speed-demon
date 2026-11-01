"""Assign CSR scatter by term bucket, so workers own complete output ranges."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
old = '''    for (int t = 0; t < nthreads; ++t) {
        pool.emplace_back([&, t] {
            for (u32 b = 0; b < nbuckets; ++b)
                seen[t][b].drain([&](u64 x) {
                    u32 id = b << BUCKET_BITS | x >> DOC_BITS;
                    ix.post[count[t][id]++] = x & ((u64(1) << DOC_BITS) - 1);
                });
        });
    }'''
new = '''    std::atomic<u32> next_bucket{0};
    for (int worker = 0; worker < nthreads; ++worker) {
        pool.emplace_back([&] {
            for (u32 b; (b = next_bucket.fetch_add(1, std::memory_order_relaxed)) < nbuckets;) {
                for (int t = 0; t < nthreads; ++t) {
                    seen[t][b].drain([&](u64 x) {
                        const u32 id = b << BUCKET_BITS | x >> DOC_BITS;
                        ix.post[count[t][id]++] = x & ((u64(1) << DOC_BITS) - 1);
                    });
                }
            }
        });
    }'''
for label in ['boundary-crc', 'gapstream18']:
    source = (PROTO / f'trackb9-{label}.cpp').read_text()
    assert source.count(old) == 1
    source = source.replace(old, new)
    (PROTO / f'trackb9-owner-{label}.cpp').write_text(source)
    if label != 'gapstream18':
        continue
    for bucket_bits in [10, 11, 12]:
        text = source.replace('constexpr u32 BUCKET_BITS = 9;', '')
        text = text.replace('template<class Doc> class BlockList {',
            f'constexpr u32 BUCKET_BITS = {bucket_bits};\n\ntemplate<class Doc> class BlockList {{\n    static constexpr u32 DELTA_BITS = 16 - BUCKET_BITS, DELTA_MASK = (1u << DELTA_BITS) - 1;')
        text = text.replace('delta < 127', 'delta < DELTA_MASK')
        text = text.replace('term << 7', 'term << DELTA_BITS')
        text = text.replace('| 127)', '| DELTA_MASK)')
        text = text.replace('x & 127', 'x & DELTA_MASK').replace('== 127', '== DELTA_MASK')
        text = text.replace('x >> 7', 'x >> DELTA_BITS')
        (PROTO / f'trackb9-owner-bucket{bucket_bits}.cpp').write_text(text)
print('Created output-owner scatter and compressed wider-bucket experiments.')
