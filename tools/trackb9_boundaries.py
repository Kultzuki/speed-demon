"""Pair all token starts/ends from each AVX2 classification window."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
for label in ['base', 'crc', 'filter-base']:
    source = (PROTO / f'trackb9-{label}.cpp').read_text()
    begin = source.index('    u64 m = 0;', source.index('inline void for_each_token'))
    finish = source.index('    for (size_t i = n > LAG ?', begin)
    first = source.index('        Key k;', begin)
    last = source.index('        hashes[slot] = h;', first) + len('        hashes[slot] = h;')
    body = source[first:last]
    # A negative filter may skip a token, but the helper returns rather than
    # continuing the outer byte-window loop.
    body = body.replace('if (!terms.may_contain(h)) continue;', 'if (!terms.may_contain(h)) return;')
    source = source[:begin] + '''    auto token = [&](const uint8_t* s, size_t len) {
        if (len > MAX_TERM) return;
''' + body + '''
    };
    while (q < e) {
        u64 mask = token_bytes(q);
        if (e - q < 64) mask &= (1ull << (e - q)) - 1;
        u64 starts = mask & ~(mask << 1);
        u64 ends = ~mask & (mask << 1);
        while (ends) {
            const size_t start = __builtin_ctzll(starts);
            const size_t end = __builtin_ctzll(ends);
            token(q + start, end - start);
            starts &= starts - 1;
            ends &= ends - 1;
        }
        if (starts) {
            const uint8_t* s = q + __builtin_ctzll(starts);
            if (s != q) { q = s; continue; }
            // A token filling the entire window is longer than any query
            // term. Skip the complete token, including all following windows.
            q += 64;
            while (q < e && LOWER.t[*q]) ++q;
        } else q += 64;
    }
''' + source[finish:]
    (PROTO / f'trackb9-boundary-{label}.cpp').write_text(source)
print('Created window-paired exact tokenizer candidates.')
