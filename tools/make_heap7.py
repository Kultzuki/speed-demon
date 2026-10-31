"""Keep full uint64 keys while removing radix-entry alignment padding."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
for name in ['base', 'compact-shards']:
    source = (PROTO / f'continuation7-{name}-d.cpp').read_text()
    old = 'using Item = std::pair<uint64_t, uint32_t>;'
    assert source.count(old) == 1
    new = '''struct __attribute__((packed)) Item {uint64_t first;uint32_t second;};
    static_assert(sizeof(Item)==12);'''
    target = PROTO / f'continuation7-{name}-heap12-d.cpp'
    assert not target.exists()
    source = source.replace(old, new)
    source = source.replace('for (auto [key, node] : buckets[i]) last = std::min(last, key);',
                            'for(auto item:buckets[i]) last=std::min(last,uint64_t(item.first));')
    target.write_text(source)
print('Created full-width 12-byte radix heap entry variants.')
