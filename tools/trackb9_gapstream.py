"""Lossless 16-bit term/doc-gap streams, with absolute-document escapes."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
source = (PROTO / 'trackb9-boundary-crc.cpp').read_text()
start = source.index('template<class Doc> class BlockList {')
end = source.index('// The scan files each posting', start)
block = '''template<class Doc> class BlockList {
    using Entry = std::conditional_t<sizeof(Doc) == 2, uint16_t, u64>;
    using Packed = std::conditional_t<sizeof(Doc) == 2, u32, u64>;
public:
    static constexpr size_t BLOCK = 1 << 16, BYTES = sizeof(Entry) * BLOCK;
    ~BlockList() { for (Entry* b : blocks_) munmap(b, BYTES); }
    void push(Packed x) {
        if constexpr (sizeof(Doc) == 2) {
            const u32 doc = x & 32767, term = x >> 15, delta = doc - last_doc_;
            if (delta < 127) word(Entry(term << 7 | delta));
            else { word(Entry(term << 7 | 127)); word(Entry(doc)); }
            last_doc_ = doc;
        } else word(x);
    }
    template<class F> void drain(F&& f) {
        u32 doc = 0, pending = NONE;
        for (size_t b = 0; b < blocks_.size(); ++b) {
            const size_t n = b + 1 == blocks_.size() ? fill_ : BLOCK;
            for (size_t i = 0; i < n; ++i) {
                const Entry x = blocks_[b][i];
                if constexpr (sizeof(Doc) == 2) {
                    if (pending != NONE) {
                        doc = x;
                        f(pending << 15 | doc);
                        pending = NONE;
                    } else if ((x & 127) == 127) pending = x >> 7;
                    else { doc += x & 127; f(u32(x >> 7) << 15 | doc); }
                } else f(x);
            }
            munmap(blocks_[b], BYTES);
        }
        blocks_.clear();
    }
private:
    void word(Entry x) {
        if (fill_ == BLOCK) {
            cur_ = static_cast<Entry*>(mmap(nullptr, BYTES, PROT_READ | PROT_WRITE,
                MAP_PRIVATE | MAP_ANONYMOUS, -1, 0));
            if (cur_ == MAP_FAILED) throw std::bad_alloc();
            blocks_.push_back(cur_);
            fill_ = 0;
        }
        cur_[fill_++] = x;
    }
    std::vector<Entry*> blocks_;
    Entry* cur_ = nullptr;
    size_t fill_ = BLOCK;
    u32 last_doc_ = 0;
};

'''
source = source[:start] + block + source[end:]
(PROTO / 'trackb9-gapstream.cpp').write_text(source)
for bits in [17, 18, 19]:
    (PROTO / f'trackb9-gapstream{bits}.cpp').write_text(source.replace('BLOCK = 1 << 16', f'BLOCK = 1 << {bits}'))
print('Created exact short-gap posting streams with uint32-domain fallback.')
