"""Bounded block-local postings: inline ids promote lazily to small bitmaps."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
source = (PROTO / 'trackb9-stream.cpp').read_text()
old = 'struct TermState { u64 bits = 0; u32 epoch = 0; };'
new = '''template<size_t WORDS> struct WordPool {
    std::unique_ptr<u64[]> storage;
    size_t used = 0;
    explicit WordPool(size_t terms) : storage(new u64[terms * WORDS]) {}
    u64* allocate() {
        u64* p = storage.get() + used;
        used += WORDS;
        std::fill(p, p + WORDS, 0);
        return p;
    }
};

template<size_t WORDS> struct TermState {
    using Doc = std::conditional_t<(WORDS <= 4), uint8_t, uint16_t>;
    static constexpr unsigned INLINE = 8 / sizeof(Doc), DOC_BITS = 8 * sizeof(Doc);
    u64 storage = 0;
    u32 epoch = 0;
    uint16_t count = 0, last = UINT16_MAX;
    u64* promote(WordPool<WORDS>& pool) {
        const u64 old = storage;
        u64* p = pool.allocate();
        for (unsigned i = 0; i < count; ++i) {
            const u32 doc = Doc(old >> (DOC_BITS * i));
            p[doc / 64] |= 1ull << (doc % 64);
        }
        storage = reinterpret_cast<uintptr_t>(p);
        count = UINT16_MAX;
        return p;
    }
    void add(u32 doc, u32 current, WordPool<WORDS>& pool) {
        if (epoch != current) { epoch = current; storage = 0; count = 0; last = UINT16_MAX; }
        if (last == doc) return;
        last = doc;
        if (count < INLINE) storage |= u64(doc) << (DOC_BITS * count++);
        else {
            u64* p = count == INLINE ? promote(pool) : reinterpret_cast<u64*>(uintptr_t(storage));
            p[doc / 64] |= 1ull << (doc % 64);
        }
    }
    const u64* mask(u32 current, WordPool<WORDS>& pool) {
        static constexpr u64 ZERO[WORDS]{};
        if (epoch != current) return ZERO;
        if (count != UINT16_MAX) return promote(pool);
        return reinterpret_cast<const u64*>(uintptr_t(storage));
    }
};'''
assert old in source
source = source.replace(old, new)
source = source.replace('void stream_solve(const Paths& paths) {',
    'template<size_t WORDS> void stream_solve(const Paths& paths) {\n    constexpr size_t BLOCK = WORDS * 64;')
source = source.replace('        std::vector<TermState> state(nt);',
    '        std::vector<TermState<WORDS>> state(nt);\n        WordPool<WORDS> word_pool(nt);')
source = source.replace('            const u32 base = doc;',
    '            word_pool.used = 0;\n            const u32 base = doc;')
source = source.replace('begin_text[64]', 'begin_text[BLOCK]').replace('end_text[64]', 'end_text[BLOCK]')
source = source.replace('local < 64 && p < end', 'local < BLOCK && p < end')
source = source.replace('                const u64 bit = 1ull << local;\n', '')
start = source.index('                    auto& s = state[id];', source.index('WordPool<WORDS> word_pool'))
end = source.index('                });', start)
source = source[:start] + '''                    auto& s = state[id];
                    if (s.epoch != epoch && watch_first[id] != watch_first[id + 1]) active.push_back(id);
                    s.add(local, epoch, word_pool);
''' + source[end:]
source = source.replace('            auto word = [&](u32 id) { return state[id].epoch == epoch ? state[id].bits : 0; };',
    '            auto word = [&](u32 id) { return state[id].mask(epoch, word_pool); };')
start = source.index('                    u64 bits = word(q.terms[0]);')
end = source.index('\n                }\n            }\n        }\n    });', start)
source = source[:start] + '''                    u64 bits[WORDS];
                    memcpy(bits, word(q.terms[0]), sizeof(bits));
                    for (size_t j = 1; j < q.terms.size(); ++j) {
                        const u64* b = word(q.terms[j]);
                        const char op = q.phrase ? 'A' : q.ops[j - 1];
                        if (op == 'A') for (size_t w = 0; w < WORDS; ++w) bits[w] &= b[w];
                        else if (op == 'O') for (size_t w = 0; w < WORDS; ++w) bits[w] |= b[w];
                        else for (size_t w = 0; w < WORDS; ++w) bits[w] &= ~b[w];
                    }
                    for (size_t w = 0; w < WORDS; ++w) {
                        u64 result = bits[w];
                        if (q.phrase) {
                            result = 0;
                            for (u64 todo = bits[w]; todo; todo &= todo - 1) {
                                const u32 j = w * 64 + __builtin_ctzll(todo);
                                if (matcher.contains(begin_text[j], end_text[j], q.terms, phrase_anchor[qi]))
                                    result |= 1ull << (j % 64);
                            }
                        }
                        if (result) {
                            const u64 c = __builtin_popcountll(result);
                            count[qi] += c;
                            sum[qi] += c * (base + w * 64) + position_sum(result);
                            smallest[qi].add(result, base + w * 64);
                        }
                    }''' + source[end:]
source = source.replace('stream_solve(paths);', 'stream_solve<8>(paths);')
for words in [4, 8, 16, 32, 64]:
    text = source.replace('stream_solve<8>(paths);', f'stream_solve<{words}>(paths);')
    (PROTO / f'trackb9-adaptive{words*64}.cpp').write_text(text)
print('Created adaptive, query-activated streaming block variants.')
