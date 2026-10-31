from pathlib import Path
p=Path('research/prototypes/a-fastpath6.cpp'); s=p.read_text()
s=s.replace('''constexpr uint32_t WIDE=(1u<<20)-1;
struct EndpointTable {''','''constexpr uint32_t WIDE=(1u<<20)-1;
// Paths repeat from a fixed catalogue of 1,842 route templates averaging 34
// bytes. Hashing only the first and last 8 bytes (plus the length) is much
// cheaper than a full-string hash; the table still compares whole names, so a
// collision only costs a probe.
static inline size_t path_hash(std::string_view name) {
    const char* p=name.data();
    size_t n=name.size();
    uint64_t a=0,b=0;
    if (n>=8) {__builtin_memcpy(&a,p,8);__builtin_memcpy(&b,p+n-8,8);}
    else {for (size_t i=0;i<n;++i) a=a<<8|uint8_t(p[i]); b=a;}
    uint64_t h=(a^std::rotl(b,29))+(n*0x9E3779B97F4A7C15ull);
    h^=h>>30;h*=0xBF58476D1CE4E5B9ull;h^=h>>27;h*=0x94D049BB133111EBull;h^=h>>31;
    return size_t(h);
}
struct EndpointTable {''')
s=s.replace('size_t hash=std::hash<std::string_view>()(name);','size_t hash=path_hash(name);')
p.write_text(s)
