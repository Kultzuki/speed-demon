from pathlib import Path
p = Path('research/prototypes/c-noname6.cpp')
s = p.read_text()
s = s.replace('countries[old.country].distinct+=names.add(old.name,old.country,old.hash);', 'countries[old.country].distinct+=0;')
s = s.replace('next.name=name.value;next.country=country;next.hash=names.prefetch(name.value);', 'next.name=name.value;next.country=country;next.hash=0;')
p.write_text(s)
p = Path('research/prototypes/c-fasthash6.cpp')
s = p.read_text()
s = s.replace('''struct Field {''', '''static inline size_t fast_hash(std::string_view name) {
    const char* p=name.data();
    size_t n=name.size();
    uint64_t a=0,b=0;
    if (n>=8) {__builtin_memcpy(&a,p,8);__builtin_memcpy(&b,p+n-8,8);}
    else {for (size_t i=0;i<n;++i) a=a<<8|uint8_t(p[i]); b=a;}
    uint64_t h=(a^std::rotl(b,29))+(n*0x9E3779B97F4A7C15ull);
    h^=h>>30;h*=0xBF58476D1CE4E5B9ull;h^=h>>27;h*=0x94D049BB133111EBull;h^=h>>31;
    return size_t(h);
}
struct Field {''')
s = s.replace('size_t hash=std::hash<std::string_view>()(name);', 'size_t hash=fast_hash(name);')
p.write_text(s)
