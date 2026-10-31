"""Keep A's parser, packing and exact ranks; test one append per output row."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'research/prototypes/continuation5-start-a.cpp').read_text()
old='''                    output+=stamp;output+=' ';output+=endpoints.names[id];
                    for (uint64_t value:{n,uint64_t(begin[r50]),uint64_t(begin[r95]),uint64_t(begin[r99]),uint64_t(errors[id]),uint64_t(errors[id])*1000000/n}) {
                        output+=' ';number(output,value);
                    }
                    output+='\\n';'''
new='''                    char line[512];
                    char* dest=std::copy_n(stamp,20,line);*dest++=' ';
                    dest=std::copy(endpoints.names[id].begin(),endpoints.names[id].end(),dest);
                    for (uint64_t value:{n,uint64_t(begin[r50]),uint64_t(begin[r95]),uint64_t(begin[r99]),uint64_t(errors[id]),uint64_t(errors[id])*1000000/n}) {
                        *dest++=' ';dest=std::to_chars(dest,line+sizeof(line),value).ptr;
                    }
                    *dest++='\\n';output.append(line,dest);'''
assert old in source
(ROOT/'research/prototypes/a-format5.cpp').write_text(source.replace(old,new),encoding='utf-8',newline='\n')
