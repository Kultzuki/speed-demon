"""Align every builder boundary to a bitmap word, giving writes one owner."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
for label, path in [('twelve', 'research/prototypes/trackb9-retained-3f527c9.cpp'),
                    ('six', 'build/trackb9-pgo-six/main.cpp')]:
    original = (ROOT / path).read_text()
    for alignment in [64, 512]:
        source = original
        marker = 'template<class Doc,class Offset> Index<Doc,Offset> build_index'
        helper = f'''// A document id divisible by {alignment} starts each worker range.
// Thus every bitmap word has one writer, including short and empty ranges.
size_t split_at(const File& file, int worker, int workers) {{
    size_t at = file.size * worker / workers;
    while (at && at < file.size && file.data[at - 1] != '\\n') ++at;
    while (at < file.size && parse_id(file.data + at) % {alignment})
        at = static_cast<const uint8_t*>(memchr(file.data + at, '\\n', file.size - at)) - file.data + 1;
    return at;
}}

'''
        source = source.replace(marker, helper + marker)
        old = '''        size_t c = size * t / nthreads;
        while (c > 0 && c < size && base[c - 1] != '\\n') ++c;
        cut[t] = c;'''
        assert source.count(old) == 1
        source = source.replace(old, '        cut[t] = split_at(f, t, nthreads);')
        old = '''            size_t at=df.size*t/nthreads;
            while(at && at<df.size && df.data[at-1]!='\\n') ++at;'''
        assert source.count(old) == 1
        source = source.replace(old, '            size_t at=split_at(df,t,nthreads);')
        old = '''                    // Neighbouring threads can share a boundary word.
                    std::atomic_ref<u64>(ix.bits[d * ix.words + doc / 64])
                        .fetch_or(1ull << (doc % 64), std::memory_order_relaxed);'''
        assert source.count(old) == 1
        source = source.replace(old, '''                    // Word-aligned builder ranges make this word private.
                    ix.bits[d * ix.words + doc / 64] |= 1ull << (doc % 64);''')
        if alignment == 512:
            source = source.replace('ix.words = (ix.docs + 63) / 64;', 'ix.words = (ix.docs + 511) / 512 * 8;')
        (PROTO / f'trackb9-align{alignment}-{label}.cpp').write_text(source)
print('Created disjoint bitmap-word ownership variants for six and twelve builders.')
