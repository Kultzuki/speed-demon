from pathlib import Path
base=Path('research/prototypes/c-fasthash6.cpp').read_text()
for n in (4,8,32):
    s=base.replace('std::array<Pending,16> pending;',f'std::array<Pending,{n}> pending;')
    Path(f'research/prototypes/c-pend{n}.cpp').write_text(s)
s=base.replace('''        auto& head=shards[(hash>>32)&255].heads[hash&511];
        __builtin_prefetch(&head,0,3);
        if (auto* node=head.load(std::memory_order_acquire)) __builtin_prefetch(node,0,3);
        return hash;''','''        return hash;''')
Path('research/prototypes/c-noprefetch6.cpp').write_text(s)
