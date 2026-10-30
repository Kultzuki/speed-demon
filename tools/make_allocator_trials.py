"""Test allocation control and contract-proven CSV cut discovery separately."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'research/prototypes/a-pages12.cpp').read_text()
s=s.replace('#include <memory>','#include <memory>\n#include <malloc.h>')
s=s.replace('int main(int argc, char** argv) {','int main(int argc, char** argv) {\n    mallopt(M_ARENA_MAX,1);')
s=s.replace('parts.clear(); remap.clear(); next.clear();','parts.clear(); remap.clear(); next.clear();malloc_trim(0);')
(root/'research/prototypes/a-one-arena.cpp').write_text(s)
s=(root/'track-c/main.cpp').read_text()
start=s.index('__attribute__((target("avx2,popcnt")))')
stop=s.index('int main(',start)
cuts=r'''
// Section 2.2: names contain no LF; a note contains only lowercase words,
// spaces, commas, quotes and LF. Thus a digit/BOM after LF begins a record.
std::vector<const char*> boundaries(const char* begin,const char* end,unsigned workers) {
    std::vector<const char*> result(workers+1,end);
    result[0]=begin;
    for (unsigned i=1;i<workers;++i) {
        const char* p=begin+(end-begin)*i/workers;
        while (p<end && !(p>begin && p[-1]=='\n' &&
               ((unsigned(*p-'0')<10) || static_cast<unsigned char>(*p)==0xef))) ++p;
        result[i]=p;
    }
    return result;
}

'''
s=s[:start]+cuts+s[stop:]
(root/'research/prototypes/c-contract-cuts.cpp').write_text(s)
