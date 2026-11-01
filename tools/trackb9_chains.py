"""Build sparse postings directly in inline descriptors and slab chains."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
source = (PROTO / 'trackb9-direct.cpp').read_text()
start = source.index('// A tiny sorted list per (worker, term).')
end = source.index('// Doc-level postings for every query term.', start)
types = '''// Fixed-size posting blocks come from worker-owned slabs. Small lists fit
// in the descriptor; larger lists append without reallocating or scattering.
template<class Doc> class ChainArena {
public:
    static constexpr u32 CAP = 60 / sizeof(Doc), PER_SLAB = 1024;
    struct Block { u32 next; Doc values[CAP]; };
    static_assert(sizeof(Block) == 64);
    ~ChainArena() { for (Block* p : slabs_) munmap(p, sizeof(Block) * PER_SLAB); }
    u32 allocate() {
        if (!(used_ % PER_SLAB)) {
            void* p = mmap(nullptr, sizeof(Block) * PER_SLAB, PROT_READ | PROT_WRITE,
                           MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
            if (p == MAP_FAILED) throw std::bad_alloc();
            slabs_.push_back(static_cast<Block*>(p));
        }
        const u32 id = used_++;
        block(id).next = NONE;
        return id;
    }
    Block& block(u32 id) { return slabs_[id / PER_SLAB][id % PER_SLAB]; }
    const Block& block(u32 id) const { return slabs_[id / PER_SLAB][id % PER_SLAB]; }
private:
    std::vector<Block*> slabs_;
    u32 used_ = 0;
};

template<class Doc> struct ChainList {
    u64 storage = 0;
    u32 size = 0;
    void push(ChainArena<Doc>& arena, Doc doc) {
        constexpr u32 INLINE = 8 / sizeof(Doc), CAP = ChainArena<Doc>::CAP;
        if (size < INLINE) {
            storage |= u64(doc) << (size++ * sizeof(Doc) * 8);
            return;
        }
        if (size == INLINE) {
            const u64 old = storage;
            const u32 block = arena.allocate();
            memcpy(arena.block(block).values, &old, 8);
            storage = u64(block) << 32 | block;
        } else if (!(size % CAP)) {
            const u32 block = arena.allocate();
            arena.block(storage >> 32).next = block;
            storage = u64(block) << 32 | u32(storage);
        }
        arena.block(storage >> 32).values[size++ % CAP] = doc;
    }
    template<class F> void each(const ChainArena<Doc>& arena, F&& f) const {
        constexpr u32 INLINE = 8 / sizeof(Doc), CAP = ChainArena<Doc>::CAP;
        if (size <= INLINE) {
            for (u32 i = 0; i < size; ++i) f(Doc(storage >> (i * sizeof(Doc) * 8)));
        } else {
            u32 id = u32(storage), remaining = size;
            while (remaining) {
                const auto& b = arena.block(id);
                const u32 count = std::min(remaining, CAP);
                for (u32 i = 0; i < count; ++i) f(b.values[i]);
                remaining -= count;
                id = b.next;
            }
        }
    }
};

'''
source = source[:start] + types + source[end:]
source = source.replace('DirectList<Doc>', 'ChainList<Doc>')
source = source.replace('    std::vector<std::unique_ptr<ChainList<Doc>[]>> lists;',
    '    std::vector<std::unique_ptr<ChainList<Doc>[]>> lists;\n    std::vector<std::unique_ptr<ChainArena<Doc>>> arenas;')
source = source.replace('    ix.lists.resize(nthreads);',
    '    ix.lists.resize(nthreads);\n    ix.arenas.resize(nthreads);')
source = source.replace('            out.reset(new ChainList<Doc>[nterms]);',
    '            out.reset(new ChainList<Doc>[nterms]);\n            ix.arenas[t] = std::make_unique<ChainArena<Doc>>();\n            auto& arena = *ix.arenas[t];')
source = source.replace('out[id].push(Doc(doc - first));', 'out[id].push(arena, Doc(doc - first));')
old = '''            const auto& list = ix_.lists[t][id];
            const Doc* p = list.data();
            for (u32 j = 0; j < list.size; ++j) list_[n++] = ix_.first[t] + p[j];'''
new = '''            ix_.lists[t][id].each(*ix_.arenas[t], [&](Doc doc) { list_[n++] = ix_.first[t] + doc; });'''
assert old in source
source = source.replace(old, new)
(PROTO / 'trackb9-chains.cpp').write_text(source)
for cap in [28, 124, 252]:
    text = source.replace('CAP = 60 / sizeof(Doc)', f'CAP = {cap} / sizeof(Doc)')
    text = text.replace('sizeof(Block) == 64', f'sizeof(Block) == {cap + 4}')
    (PROTO / f'trackb9-chains{cap+4}.cpp').write_text(text)
print('Created inline/slab-chained postings without per-list allocation or CSR scatter.')
