from pathlib import Path
base=Path('research/prototypes/c-fasthash6.cpp').read_text()
for n in (2,6):
    s=base.replace('std::array<Pending,16> pending;',f'std::array<Pending,{n}> pending;')
    Path(f'research/prototypes/c-pend{n}.cpp').write_text(s)
