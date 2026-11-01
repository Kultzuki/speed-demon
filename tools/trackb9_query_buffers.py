"""Fill bounded set-operation buffers directly, without per-element growth checks."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
source = (PROTO / 'trackb9-hybrid-owner2.cpp').read_text()
begin = source.index('void assign(std::vector<u32>& out, Postings b)')
end = source.index('}  // namespace', begin)
segment = source[begin:end].replace('std::vector<u32>', 'QueryBuffer')
allocator = '''// resize() creates unsigned objects without zeroing scratch elements.
// Each operation writes its complete result prefix before shrinking the size.
template<class T> struct QueryAllocator : std::allocator<T> {
    template<class U> struct rebind { using other = QueryAllocator<U>; };
    template<class U> void construct(U* p) { ::new (static_cast<void*>(p)) U; }
    template<class U> bool operator==(const QueryAllocator<U>&) const noexcept { return true; }
};
using QueryBuffer = std::vector<u32, QueryAllocator<u32>>;

'''
source = source[:begin] + allocator + segment + source[end:]
start = source.index('void assign(QueryBuffer& out, Postings b)')
finish = source.index('// First index i >= lo', start)
source = source[:start] + '''void assign(QueryBuffer& out, Postings b) {
    if (!b.n) { out.clear(); return; }
    if (b.bits) {
        out.resize(b.n);
        u32* p = out.data();
        for_each_bit(b.bits, b.words, [&](u32 x) { *p++ = x; });
    } else out.assign(b.p, b.p + b.n);
}

''' + source[finish:]
start = source.index('void op_and(const QueryBuffer& a, Postings b, QueryBuffer& out)')
finish = source.index('// Sum of the positions', start)
source = source[:start] + '''void op_and(const QueryBuffer& a, Postings b, QueryBuffer& out) {
    if (a.empty() || !b.n) { out.clear(); return; }
    out.resize(b.bits ? a.size() : std::min(a.size(), b.n));
    u32* p = out.data();
    if (b.bits) {
        for (u32 x : a) if (has(b.bits, x)) *p++ = x;
    } else if (a.size() * 16 < b.n) {
        size_t j = 0;
        for (u32 x : a) {
            j = gallop(b.p, j, b.n, x);
            if (j == b.n) break;
            if (b.p[j] == x) *p++ = x;
        }
    } else if (b.n * 16 < a.size()) {
        size_t i = 0;
        for (size_t j = 0; j < b.n; ++j) {
            i = gallop(a.data(), i, a.size(), b.p[j]);
            if (i == a.size()) break;
            if (a[i] == b.p[j]) *p++ = b.p[j];
        }
    } else p = std::set_intersection(a.begin(), a.end(), b.p, b.p + b.n, p);
    out.resize(p - out.data());
}

void op_not(const QueryBuffer& a, Postings b, QueryBuffer& out) {
    if (a.empty()) { out.clear(); return; }
    if (!b.n) { out.assign(a.begin(), a.end()); return; }
    out.resize(a.size());
    u32* p = out.data();
    if (b.bits) {
        for (u32 x : a) if (!has(b.bits, x)) *p++ = x;
    } else if (a.size() * 16 < b.n) {
        size_t j = 0;
        for (u32 x : a) {
            j = gallop(b.p, j, b.n, x);
            if (j == b.n || b.p[j] != x) *p++ = x;
        }
    } else p = std::set_difference(a.begin(), a.end(), b.p, b.p + b.n, p);
    out.resize(p - out.data());
}

void op_or(const QueryBuffer& a, Postings b, QueryBuffer& out) {
    if (!b.n) { out.assign(a.begin(), a.end()); return; }
    out.resize(a.size() + b.n);
    const u32* end = std::set_union(a.begin(), a.end(), b.p, b.p + b.n, out.data());
    out.resize(end - out.data());
}

''' + source[finish:]
(PROTO / 'trackb9-query-buffers.cpp').write_text(source)
print('Created bounded direct-write query scratch buffers.')
