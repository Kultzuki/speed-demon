"""Put each term's segment metadata in one cache line and skip empty workers."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
source = (PROTO / 'trackb9-boundary-crc.cpp').read_text()
source = source.replace('    std::vector<std::vector<u32>> seg_end;',
    '    std::vector<uint16_t> active_threads;\n    std::vector<u32> seg_end;')
source = source.replace('    ix.seg_end = std::move(count);', '''    ix.seg_end.resize(size_t(nterms) * nthreads);
    ix.active_threads.resize(nterms);
    for (u32 id = 0; id < nterms; ++id) {
        u32 previous = ix.start[id];
        for (int t = 0; t < nthreads; ++t) {
            const u32 end = count[t][id];
            ix.seg_end[size_t(id) * nthreads + t] = end;
            if (end != previous) ix.active_threads[id] |= uint16_t(1u << t);
            previous = end;
        }
    }
    count.clear(); count.shrink_to_fit();''')
old = '''        for (int t = 0; t < ix_.threads; ++t)
            for (u32 e = ix_.seg_end[t][id]; i < e; ++i) list_[n++] = ix_.first[t] + ix_.post[i];'''
new = '''        const u32* ends = ix_.seg_end.data() + size_t(id) * ix_.threads;
        for (u32 active = ix_.active_threads[id]; active; active &= active - 1) {
            const unsigned t = __builtin_ctz(active);
            for (u32 e = ends[t]; i < e; ++i) list_[n++] = ix_.first[t] + ix_.post[i];
        }'''
assert old in source
source = source.replace(old, new)
(PROTO / 'trackb9-segments.cpp').write_text(source)
owned = source.replace('            const u32 first = ix.first[t] = begin < end ? parse_id(begin) : 0;',
    '            const u32 first = ix.first[t] = begin < end ? parse_id(begin) : 0;\n            const u32 stop_doc = end < base + size ? parse_id(end) : ix.docs;')
old = '''                    std::atomic_ref<u64>(ix.bits[d * ix.words + doc / 64])
                        .fetch_or(1ull << (doc % 64), std::memory_order_relaxed);'''
new = '''                    u64& word = ix.bits[d * ix.words + doc / 64];
                    const u64 bit = 1ull << (doc % 64);
                    if (doc / 64 > first / 64 && doc / 64 < stop_doc / 64) word |= bit;
                    else std::atomic_ref<u64>(word).fetch_or(bit, std::memory_order_relaxed);'''
assert old in owned
owned = owned.replace(old, new)
(PROTO / 'trackb9-segments-owned.cpp').write_text(owned)
used = [0]
marker = '    std::vector<std::vector<BlockList<Doc>>> seen(nthreads);'
adaptive = owned.replace(marker, '''    std::vector<u32> uses(nterms);
    for (u32 id : query_terms) ++uses[id];
''' + marker)
adaptive = adaptive.replace('if (df[order[rank]] * 32 > docs)',
    'if (df[order[rank]] * 32 > docs || (uses[order[rank]] >= 16 && df[order[rank]] * 128 > docs))')
(PROTO / 'trackb9-segments-adaptive.cpp').write_text(adaptive)
print('Created term-major segment metadata, ownership and query-use density candidates.')
