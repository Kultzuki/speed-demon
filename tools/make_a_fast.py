"""Isolate A parser refinements while the submitted architecture is measured."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
base=(root/'track-a/main.cpp').read_text()
helper=r'''
// Four ASCII digits are recognized without reading outside the mapped chunk.
// The competition's x86-64 machine is little endian; latency is still uint32.
uint32_t read_latency(const char*& p,const char* end) {
    uint32_t value=0;
    while (end-p>=4) {
        uint32_t raw;memcpy(&raw,p,4);
        if (((raw+0x46464646u)|(raw-0x30303030u))&0x80808080u) break;
        uint32_t digits=raw-0x30303030u;
        uint32_t pairs=(digits&0x00ff00ffu)*10+((digits>>8)&0x00ff00ffu);
        value=value*10000+(pairs&65535)*100+(pairs>>16);p+=4;
    }
    while (p<end && unsigned(*p-'0')<10) value=value*10+(*p++-'0');
    return value;
}
void skip_method(const char*& p) {
    switch (*p) {
        case 'G':p+=4;break;
        case 'P':p+=p[1]=='O'?5:p[1]=='A'?6:4;break;
        case 'D':p+=7;break;
        case 'H':p+=5;break;
        case 'O':p+=8;break;
    }
}
'''
def faster(s):
    s=s.replace('struct Group {',helper+'\nstruct Group {',1)
    s=s.replace("while (*p++!=' ') {}",'skip_method(p);')
    s=s.replace("while (*p++ != ' ') {}",'skip_method(p);')
    s=s.replace("while (*p!=' ') ++p;", "p=static_cast<const char*>(memchr(p,' ',std::min<size_t>(126,end-p)));")
    s=s.replace("while (*p != ' ') ++p;", "p=static_cast<const char*>(memchr(p,' ',std::min<size_t>(126,end-p)));")
    s=s.replace('uint32_t latency=integer(p);','uint32_t latency=read_latency(p,end);')
    s=s.replace('values[group.cursor++] = integer(p);','values[group.cursor++] = read_latency(p,end);')
    return s
(root/'research/prototypes/a-fast-pages.cpp').write_text(faster(base))
s=(root/'research/prototypes/a-scatter.cpp').read_text().replace('std::min(6u,','std::min(12u,')
lookup=base[base.index('struct EndpointLookup {'):base.index('struct Partial {')]
s=s.replace('struct Partial {',lookup+'\nstruct Partial {',1)
s=s.replace('std::unordered_map<std::string_view, uint32_t> ids;', 'EndpointLookup ids;',1)
s=s.replace('ids.reserve(2048); endpoints.reserve(2048);','endpoints.reserve(2048);',1)
start=s.index('            uint32_t id;')
stop=s.index('            auto& group =',start)
s=s[:start]+'            uint32_t id=ids.intern(key,endpoints);\n'+s[stop:]
(root/'research/prototypes/a-fast-scatter.cpp').write_text(faster(s))
