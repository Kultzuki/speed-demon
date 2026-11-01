"""Inline exact short words in dictionary slots; keep full long-word equality."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
source = (PROTO / 'trackb9-boundary-base.cpp').read_text()
start = source.index('    u64 h = ', source.index('inline u64 hash_key'))
end = source.index('\n}', start)
source = source[:start] + '''    u64 h = k.w[0] * 0x9E3779B97F4A7C15ull;
    return h ^ (h >> 29);''' + source[end:]
# Preserve dense keys for phrase equality, but put the short exact key in the
# dictionary slot itself. Zero padding plus the stored length is injective.
start = source.index('            u64 s = slots_[i];', source.index('    u32 insert('))
end = source.index('\n        }\n    }', start)
source = source[:start] + '''            Slot& s = slots_[i];
            if (s.meta == 0) {
                keys_.push_back(k);
                lens_.push_back(strnlen(reinterpret_cast<const char*>(k.w), MAX_TERM));
                s = {k.w[0], u64(lens_.back()) << 32 | keys_.size()};
                return keys_.size() - 1;
            }
            if (s.first == k.w[0] && same(keys_[u32(s.meta) - 1], k)) return u32(s.meta) - 1;''' + source[end:]
start = source.index('    // h is hash_key(k),')
end = source.index('\nprivate:', start)
source = source[:start] + '''    u32 find(const uint8_t* p, size_t len, u64 a, u64 h) const {
        for (size_t i = h & mask_;; i = (i + 1) & mask_) {
            const Slot& s = slots_[i];
            if (!s.meta) return NONE;
            if (s.first != a || (s.meta >> 32) != len) continue;
            const u32 id = u32(s.meta) - 1;
            if (len <= 8) return id;
            const Key& k = keys_[id];
            bool equal = true;
            for (size_t j = 1; j < (len + 7) / 8; ++j) {
                u64 raw;
                memcpy(&raw, p + j * 8, 8);
                raw = _bzhi_u64(raw | 0x2020202020202020ull, unsigned((len - j * 8) * 8));
                if (raw != k.w[j]) { equal = false; break; }
            }
            if (equal) return id;
        }
    }
''' + source[end:]
source = source.replace('        slots_.assign(cap, 0);', '        slots_.assign(cap, Slot{});')
source = source.replace('            while (slots_[i])', '            while (slots_[i].meta)')
source = source.replace('            slots_[i] = (h & 0xFFFFFFFF00000000ull) | (id + 1);',
    '            slots_[i] = {keys_[id].w[0], u64(lens_[id]) << 32 | (id + 1)};')
source = source.replace('    std::vector<u64> slots_;',
    '    struct Slot { u64 first = 0, meta = 0; };\n    std::vector<Slot> slots_;')
source = source.replace('    Key keys[LAG];',
    '    const uint8_t* positions[LAG];\n    uint8_t lengths[LAG];\n    u64 firsts[LAG];')
start = source.index('        Key k;', source.index('inline void for_each_token'))
end = source.index('        terms.prefetch(h);', start)
source = source[:start] + '''        u64 a;
        memcpy(&a, s, 8);
        a = _bzhi_u64(a | 0x2020202020202020ull, unsigned(len * 8));
        u64 h = a * 0x9E3779B97F4A7C15ull;
        h ^= h >> 29;
''' + source[end:]
source = source.replace('terms.find(keys[slot], hashes[slot])',
    'terms.find(positions[slot], lengths[slot], firsts[slot], hashes[slot])')
source = source.replace('        keys[slot] = k;',
    '        positions[slot] = s;\n        lengths[slot] = len;\n        firsts[slot] = a;')
source = source.replace('terms.find(keys[i % LAG], hashes[i % LAG])',
    'terms.find(positions[i % LAG], lengths[i % LAG], firsts[i % LAG], hashes[i % LAG])')
(PROTO / 'trackb9-inline.cpp').write_text(source)
for lag in [0, 4, 16]:
    text = source
    if lag:
        text = text.replace('constexpr size_t LAG = 8;', f'constexpr size_t LAG = {lag};')
    else:
        begin = text.index('        terms.prefetch(h);', text.index('inline void for_each_token'))
        finish = text.index('\n    };', begin)
        text = text[:begin] + '        emit(terms.find(s, len, a, h));' + text[finish:]
        begin = text.index('    for (size_t i = n > LAG ?', begin)
        finish = text.index('\n}', begin)
        text = text[:begin] + text[finish:]
    (PROTO / f'trackb9-inline-lag{lag}.cpp').write_text(text)
print('Created inline exact-key dictionary candidates.')
