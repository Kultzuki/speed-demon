"""Create a direct, thread-local sparse posting experiment, without CSR scatter."""
from pathlib import Path
import continuation7_trials

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
source = (PROTO / 'trackb9-crc.cpp').read_text()
start = source.index('// Doc-level postings for every query term.')
direct = '''// A tiny sorted list per (worker, term). Four 16-bit documents fit inline;
// longer lists grow geometrically. A worker appends in document order, so
// queries read the original lists without a temporary stream or CSR scatter.
template<class Doc> struct DirectList {
    union Storage { Doc small[8 / sizeof(Doc)]; Doc* heap; Storage() {} } storage;
    u32 size = 0, capacity = 0;
    ~DirectList() { if (capacity) free(storage.heap); }
    const Doc* data() const { return capacity ? storage.heap : storage.small; }
    void push(Doc doc) {
        constexpr u32 INLINE = 8 / sizeof(Doc);
        if (size == (capacity ? capacity : INLINE)) {
            const u32 next = size * 2;
            Doc* p = static_cast<Doc*>(malloc(sizeof(Doc) * next));
            if (!p) throw std::bad_alloc();
            memcpy(p, data(), sizeof(Doc) * size);
            if (capacity) free(storage.heap);
            storage.heap = p;
            capacity = next;
        }
        (capacity ? storage.heap : storage.small)[size++] = doc;
    }
};

'''
source = source[:start] + direct + source[start:]
source = source.replace('    std::unique_ptr<Doc[]> post;',
    '    std::vector<std::unique_ptr<DirectList<Doc>[]>> lists;\n    std::unique_ptr<Doc[]> post;')
source = source.replace('    std::vector<std::vector<BlockList<Doc>>> seen(nthreads);',
    '    ix.lists.resize(nthreads);')
source = source.replace('            auto& out = seen[t];\n            out.resize(nbuckets);',
    '            auto& out = ix.lists[t];\n            out.reset(new DirectList<Doc>[nterms]);')
source = source.replace('                    out[id >> BUCKET_BITS].push(u64(id & ((1u << BUCKET_BITS) - 1)) << DOC_BITS | (doc - first));\n                    ++cnt[id];',
    '                    out[id].push(Doc(doc - first));')
start = source.index('    // Turn the per-thread counts')
end = source.index('    ix.df.resize(nterms);', start)
source = source[:start] + source[end:]
source = source.replace('        ix.df[id] = ix.start[id + 1] - ix.start[id];',
    '        ix.df[id] = 0;\n        for (int t = 0; t < nthreads; ++t) ix.df[id] += ix.lists[t][id].size;')
old = '''        u32 i = ix_.start[id], n = 0;
        for (int t = 0; t < ix_.threads; ++t)
            for (u32 e = ix_.seg_end[t][id]; i < e; ++i) list_[n++] = ix_.first[t] + ix_.post[i];'''
new = '''        u32 n = 0;
        for (int t = 0; t < ix_.threads; ++t) {
            const auto& list = ix_.lists[t][id];
            const Doc* p = list.data();
            for (u32 j = 0; j < list.size; ++j) list_[n++] = ix_.first[t] + p[j];
        }'''
assert source.count(old) == 1
source = source.replace(old, new)
(PROTO / 'trackb9-direct.cpp').write_text(source)
(PROTO / 'trackb9-profile-direct.cpp').write_text(continuation7_trials.profile(source, 'b'))
print('Created direct sparse postings experiment.')
