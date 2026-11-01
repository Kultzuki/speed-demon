"""Reject impossible dictionary probes and fast-path exact frequent words."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
for label in ['base', 'crc', 'pointer-lag0']:
    source = (PROTO / f'trackb9-{label}.cpp').read_text()
    marker = '    void prefetch(u64 h) const'
    source = source.replace(marker, '''    bool may_contain(u64 h) const {
        return (filter_[h & 8191] >> ((h >> 16) & 63)) & 1;
    }
    void prefetch(u64 h) const''', 1)
    source = source.replace('                keys_.push_back(k);',
        '                filter_[h & 8191] |= 1ull << ((h >> 16) & 63);\n                keys_.push_back(k);', 1)
    source = source.replace('    std::vector<u64> slots_;',
        '    u64 filter_[8192]{};\n    std::vector<u64> slots_;', 1)
    # A hash-only filter is a negative test. Every possible hit still reaches
    # the established exact comparison; renumbering changes no word/hash.
    if '        terms.prefetch(h);' in source:
        source = source.replace('        terms.prefetch(h);',
            '        if (!terms.may_contain(h)) continue;\n        terms.prefetch(h);')
    else:
        source = source.replace('        emit(terms.find(s, len, h));',
            '        if (terms.may_contain(h)) emit(terms.find(s, len, h));')
    (PROTO / f'trackb9-filter-{label}.cpp').write_text(source)

source = (PROTO / 'trackb9-pointer-lag0.cpp').read_text()
marker = '    void prefetch(u64 h) const'
source = source.replace(marker, '''    u32 fast_word(u64 a, u64 h) const {
        const auto& s = fast_[h & 2047];
        return s.word == a ? s.id : NONE;
    }
    void prefetch(u64 h) const''', 1)
source = source.replace('        rehash(slots_.size());\n    }', '''        rehash(slots_.size());
        for (u32 id = 0; id < std::min<size_t>(keys_.size(), 1024); ++id) {
            if (lens_[id] > 8) continue;
            auto& s = fast_[hash_key(keys_[id]) & 2047];
            if (!s.word) s = {keys_[id].w[0], id};
        }
    }''', 1)
source = source.replace('    std::vector<u64> slots_;',
    '    struct FastSlot { u64 word = 0; u32 id = NONE; };\n    FastSlot fast_[2048];\n    std::vector<u64> slots_;', 1)
source = source.replace('        emit(terms.find(s, len, h));', '''        u32 id = len <= 8 ? terms.fast_word(a, h) : NONE;
        emit(id != NONE ? id : terms.find(s, len, h));''')
(PROTO / 'trackb9-fastwords.cpp').write_text(source)
print('Created one-sided filters and an exact frequent-word fast path.')
