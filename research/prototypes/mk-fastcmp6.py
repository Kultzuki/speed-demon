from pathlib import Path
# A: inline word-wise name compare on top of fastpath
p=Path('research/prototypes/a-fastpath6.cpp'); s=p.read_text()
s=s.replace('''struct EndpointTable {''','''static inline bool same_name(std::string_view a,std::string_view b) {
    size_t n=a.size();
    if (n!=b.size()) return false;
    const char* x=a.data();const char* y=b.data();
    for (;n>=8;n-=8,x+=8,y+=8) {uint64_t u,v;__builtin_memcpy(&u,x,8);__builtin_memcpy(&v,y,8);if (u!=v) return false;}
    if (n) {uint64_t u=0,v=0;__builtin_memcpy(&u,x,n);__builtin_memcpy(&v,y,n);if (u!=v) return false;}
    return true;
}
struct EndpointTable {''')
s=s.replace('if (value && names[value-1]==name) return value-1;','if (value && same_name(names[value-1],name)) return value-1;')
p.write_text(s)
# C: inline word-wise name compare on top of fasthash
p=Path('research/prototypes/c-fasthash6.cpp'); s=p.read_text()
s=s.replace('''struct Field {''','''static inline bool same_name(std::string_view a,std::string_view b) {
    size_t n=a.size();
    if (n!=b.size()) return false;
    const char* x=a.data();const char* y=b.data();
    for (;n>=8;n-=8,x+=8,y+=8) {uint64_t u,v;__builtin_memcpy(&u,x,8);__builtin_memcpy(&v,y,8);if (u!=v) return false;}
    if (n) {uint64_t u=0,v=0;__builtin_memcpy(&u,x,n);__builtin_memcpy(&v,y,n);if (u!=v) return false;}
    return true;
}
struct Field {''')
s=s.replace('while (node && (node->name()!=name)) node=node->next;','while (node && !same_name(node->name(),name)) node=node->next;')
p.write_text(s)
