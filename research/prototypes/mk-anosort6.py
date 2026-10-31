from pathlib import Path
p=Path('research/prototypes/a-nosort6.cpp')
s=p.read_text()
s=s.replace('''                    if (n<=128) std::sort(begin,end);
                    else {
                        std::nth_element(begin,begin+r50,end);
                        if (r95>r50) std::nth_element(begin+r50+1,begin+r95,end);
                        if (r99>r95) std::nth_element(begin+r95+1,begin+r99,end);
                    }
''','')
p.write_text(s)
