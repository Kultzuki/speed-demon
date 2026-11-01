"""Give a heavy leading bucket producer jobs, then own the remaining buckets."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
source = (PROTO / 'trackb9-owner-bucket12.cpp').read_text()
start = source.index('    std::atomic<u32> next_bucket{0};')
end = source.index('    for (auto& th : pool) th.join();', start)
for heavy in [1, 2]:
    replacement = f'''    constexpr u32 HEAVY = {heavy};
    const u32 split_buckets = std::min(HEAVY, nbuckets);
    const u32 split_jobs = split_buckets * nthreads;
    const u32 jobs = split_jobs + nbuckets - split_buckets;
    std::atomic<u32> next_job{{0}};
    auto scatter = [&](int t, u32 b) {{
        seen[t][b].drain([&](u64 x) {{
            const u32 id = b << BUCKET_BITS | x >> DOC_BITS;
            ix.post[count[t][id]++] = x & ((u64(1) << DOC_BITS) - 1);
        }});
    }};
    for (int worker = 0; worker < nthreads; ++worker) {{
        pool.emplace_back([&] {{
            for (u32 job; (job = next_job.fetch_add(1, std::memory_order_relaxed)) < jobs;) {{
                if (job < split_jobs) scatter(job % nthreads, job / nthreads);
                else for (int t = 0; t < nthreads; ++t) scatter(t, job - split_jobs + split_buckets);
            }}
        }});
    }}
'''
    text = source[:start] + replacement + source[end:]
    (PROTO / f'trackb9-hybrid-owner{heavy}.cpp').write_text(text)
print('Created heavy-bucket parallel scatter controls.')
