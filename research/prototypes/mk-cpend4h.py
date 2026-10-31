from pathlib import Path
base=Path('research/prototypes/c-pend4.cpp').read_text()
s=base.replace('if (auto* node=head.load(std::memory_order_acquire)) __builtin_prefetch(node,0,3);','if (auto* node=head.load(std::memory_order_acquire)) __builtin_prefetch(node,0,2);')
Path('research/prototypes/c-pend4-n2.cpp').write_text(s)
s=base.replace('__builtin_prefetch(&head,0,3);','__builtin_prefetch(&head,0,2);').replace('__builtin_prefetch(node,0,3);','__builtin_prefetch(node,0,2);')
Path('research/prototypes/c-pend4-a2.cpp').write_text(s)
