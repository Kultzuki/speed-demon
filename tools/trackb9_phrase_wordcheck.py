"""Use a conservative word-prefix filter, then exact established-token checks."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
for label in ['hybrid-owner2', 'query-buffers']:
    original = (PROTO / f'trackb9-{label}.cpp').read_text()
    word = original
    start = word.index('        const uint8_t* k = terms_.bytes(id);', word.index('    bool is_term('))
    end = word.index('        return true;', start)
    word = word[:start] + '''        // Every caller has established complete token boundaries, so these
        // bytes are ASCII alphanumeric. OR 0x20 is exact lowercase here.
        const uint8_t* k = terms_.bytes(id);
        for (size_t i = 0; i < len; i += 8) {
            u64 raw, want;
            memcpy(&raw, p + i, 8); memcpy(&want, k + i, 8);
            raw = _bzhi_u64(raw | 0x2020202020202020ull, unsigned(std::min<size_t>(len - i, 8) * 8));
            if (raw != want) return false;
        }
''' + word[end:]
    for mode, source in [('prefix', original), ('word', word), ('both', word)]:
        if mode != 'word':
            source = source.replace('''        const uint8_t first = terms_.bytes(anchor)[0];''', '''        const uint8_t first = terms_.bytes(anchor)[0];
        const size_t wanted_length = terms_.length(anchor);
        u64 wanted_prefix;
        memcpy(&wanted_prefix, terms_.bytes(anchor), 8);
        const unsigned prefix_bits = unsigned(std::min<size_t>(wanted_length, 8) * 8);''')
            old = '''                if (s > b && LOWER.t[s[-1]]) continue;
                const uint8_t* t = s;'''
            new = '''                if (s > b && LOWER.t[s[-1]]) continue;
                if (size_t(e - s) < wanted_length) continue;
                u64 raw_prefix;
                memcpy(&raw_prefix, s, 8);
                if (_bzhi_u64(raw_prefix | 0x2020202020202020ull, prefix_bits) != wanted_prefix) continue;
                // Prefix equality only admits a candidate; the established
                // complete-token and exact-byte checks below still decide it.
                const uint8_t* t = s;'''
            assert source.count(old) == 1
            source = source.replace(old, new)
        source = source.replace('// phrase checks never hash.', '// phrase checks never hash.')
        (PROTO / f'trackb9-phrase-{mode}-{label}.cpp').write_text(source)
print('Created conservative prefix filters and exact word-wise phrase checks.')
