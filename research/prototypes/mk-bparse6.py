from pathlib import Path
p=Path('research/prototypes/b-parse6.cpp')
s=p.read_text()
s=s.replace('    TermTable() { rehash(1 << 16); }','    explicit TermTable(size_t hint=1<<16) { rehash(std::bit_ceil(std::max<size_t>(hint,1<<16))); }')
s=s.replace('''Queries parse_queries(const File& f, TermTable& terms) {
    Queries qs;
    const uint8_t* p = f.data;''','''Queries parse_queries(const File& f, TermTable& terms) {
    Queries qs;
    // A term needs at least one byte and a separator, so this bounds the count.
    size_t hint=f.size/8;
    qs.first.reserve(hint/3); qs.phrase.reserve(hint/3);
    qs.terms.reserve(hint); qs.ops.reserve(hint);
    const uint8_t* p = f.data;''')
s=s.replace('''    TermTable terms;
    Queries queries = parse_queries(qf, terms);''','''    TermTable terms(qf.size/8);
    Queries queries = parse_queries(qf, terms);''')
p.write_text(s)
