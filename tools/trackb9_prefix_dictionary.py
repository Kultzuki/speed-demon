"""Exact ASCII prefix keys inline in dictionary slots; owned full-byte fallback."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
source = (PROTO / 'trackb9-hybrid-owner2.cpp').read_text()
start = source.index('// Two independent multiplies;')
end = source.index('inline bool same(', start)
source = source[:start] + '''// Alphanumeric ASCII bytes need six bits: drop bit 5 (case) and bit 7.
// The canonical digit/letter codes are disjoint and nonzero, so zero padding
// encodes short-key length. Longer terms retain an exact owned-byte fallback.
inline u64 prefix_key(u64 bytes) { return _pext_u64(bytes, 0x5F5F5F5F5F5F5F5Full); }
inline u64 hash_prefix(u64 key) {
    const u64 h = key * 0x9E3779B97F4A7C15ull;
    return h ^ (h >> 29);
}
inline u64 hash_key(const Key& k) { return hash_prefix(prefix_key(k.w[0])); }

''' + source[end:]
start = source.index('class TermTable {')
end = source.index('// Bit i is set', start)
table = '''class TermTable {
public:
    TermTable() { rehash(1 << 16); }
    u32 size() const { return keys_.size(); }
    const uint8_t* bytes(u32 id) const { return reinterpret_cast<const uint8_t*>(keys_[id].w); }
    size_t length(u32 id) const { return lens_[id]; }
    u32 insert(const Key& k) {
        if ((keys_.size() + 1) * 2 > slots_.size()) rehash(slots_.size() * 2);
        const u64 prefix = prefix_key(k.w[0]), h = hash_prefix(prefix);
        for (size_t i = h & mask_;; i = (i + 1) & mask_) {
            Slot& s = slots_[i];
            if (!s.meta) {
                keys_.push_back(k);
                lens_.push_back(strnlen(reinterpret_cast<const char*>(k.w), MAX_TERM));
                s = {prefix, u64(lens_.back()) << 32 | keys_.size()};
                return keys_.size() - 1;
            }
            if (s.prefix == prefix && same(keys_[u32(s.meta) - 1], k)) return u32(s.meta) - 1;
        }
    }
    void renumber(const std::vector<u32>& new_id) {
        std::vector<Key> keys(keys_.size());
        std::vector<uint8_t> lens(lens_.size());
        for (u32 i = 0; i < keys_.size(); ++i) keys[new_id[i]] = keys_[i], lens[new_id[i]] = lens_[i];
        keys_.swap(keys); lens_.swap(lens);
        rehash(slots_.size());
    }
    void prefetch(u64 h) const { _mm_prefetch(reinterpret_cast<const char*>(&slots_[h & mask_]), _MM_HINT_T0); }
    u32 find(const Key& k, u64 h) const {
        const u64 prefix = prefix_key(k.w[0]);
        for (size_t i = h & mask_;; i = (i + 1) & mask_) {
            const Slot& s = slots_[i];
            if (!s.meta) return NONE;
            if (s.prefix == prefix && same(keys_[u32(s.meta) - 1], k)) return u32(s.meta) - 1;
        }
    }
    u32 find(u64 prefix, const uint8_t* p, size_t len, u64 h) const {
        for (size_t i = h & mask_;; i = (i + 1) & mask_) {
            const Slot& s = slots_[i];
            if (!s.meta) return NONE;
            if (s.prefix != prefix || (s.meta >> 32) != len) continue;
            const u32 id = u32(s.meta) - 1;
            bool equal = true;
            for (size_t j = 8; j < len; ++j)
                if (LOWER.t[p[j]] != bytes(id)[j]) { equal = false; break; }
            if (equal) return id;
        }
    }
private:
    struct Slot { u64 prefix = 0, meta = 0; };
    void rehash(size_t cap) {
        slots_.assign(cap, Slot{}); mask_ = cap - 1;
        for (u32 id = 0; id < keys_.size(); ++id) {
            const u64 prefix = prefix_key(keys_[id].w[0]), h = hash_prefix(prefix);
            size_t i = h & mask_;
            while (slots_[i].meta) i = (i + 1) & mask_;
            slots_[i] = {prefix, u64(lens_[id]) << 32 | (id + 1)};
        }
    }
    std::vector<Slot> slots_;
    std::vector<Key> keys_;
    std::vector<uint8_t> lens_;
    size_t mask_ = 0;
};

'''
source = source[:start] + table + source[end:]
source = source.replace('    Key keys[LAG];',
    '    u64 prefixes[LAG];\n    const uint8_t* positions[LAG];\n    uint8_t lengths[LAG];')
start = source.index('        Key k;', source.index('inline void for_each_token'))
end = source.index('        terms.prefetch(h);', start)
source = source[:start] + '''        u64 raw;
        memcpy(&raw, s, 8);
        // Clamp the BZHI index: len==32 must not wrap its 8-bit index to zero.
        raw = _bzhi_u64(raw, unsigned(std::min<size_t>(len, 8) * 8));
        const u64 prefix = prefix_key(raw), h = hash_prefix(prefix);
''' + source[end:]
source = source.replace('terms.find(keys[slot], hashes[slot])',
    'terms.find(prefixes[slot], positions[slot], lengths[slot], hashes[slot])')
source = source.replace('        keys[slot] = k;',
    '        prefixes[slot] = prefix;\n        positions[slot] = s;\n        lengths[slot] = len;')
source = source.replace('terms.find(keys[i % LAG], hashes[i % LAG])',
    'terms.find(prefixes[i % LAG], positions[i % LAG], lengths[i % LAG], hashes[i % LAG])')
(PROTO / 'trackb9-prefix.cpp').write_text(source)
for lag in [0, 4, 16]:
    text = source
    if lag:
        text = text.replace('constexpr size_t LAG = 8;', f'constexpr size_t LAG = {lag};')
    else:
        begin = text.index('        terms.prefetch(h);', text.index('inline void for_each_token'))
        end = text.index('\n    };', begin)
        text = text[:begin] + '        emit(terms.find(prefix, s, len, h));' + text[end:]
        begin = text.index('    for (size_t i = n > LAG ?', begin)
        end = text.index('\n}', begin)
        text = text[:begin] + text[end:]
    (PROTO / f'trackb9-prefix-lag{lag}.cpp').write_text(text)
print('Created inline exact six-bit ASCII prefix dictionary candidates.')
