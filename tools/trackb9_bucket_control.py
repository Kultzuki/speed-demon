"""Separate the effect of wider buckets from scatter ownership."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
with_owner = (PROTO / 'trackb9-owner-bucket12.cpp').read_text()
start = with_owner.index('    std::atomic<u32> next_bucket{0};')
end = with_owner.index('    for (auto& th : pool) th.join();', start)
old = '''    for (int t = 0; t < nthreads; ++t) {
        pool.emplace_back([&, t] {
            for (u32 b = 0; b < nbuckets; ++b)
                seen[t][b].drain([&](u64 x) {
                    u32 id = b << BUCKET_BITS | x >> DOC_BITS;
                    ix.post[count[t][id]++] = x & ((u64(1) << DOC_BITS) - 1);
                });
        });
    }
'''
for bits in [10, 11, 12, 13]:
    text = with_owner[:start] + old + with_owner[end:]
    text = text.replace('constexpr u32 BUCKET_BITS = 12;', f'constexpr u32 BUCKET_BITS = {bits};')
    (PROTO / f'trackb9-bucket{bits}.cpp').write_text(text)
print('Created producer-scatter controls for wider compressed buckets.')
