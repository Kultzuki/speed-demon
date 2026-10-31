"""Separate immutable exact name bytes from frequently written country bits."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
for variant in ['base', 'incoming']:
    source = (PROTO / f'continuation7-{variant}-c.cpp').read_text()
    source = source.replace('struct SharedNames {\n    struct Node {',
        'struct SharedNames {\n    struct Membership {std::atomic<uint64_t> words[4]{};};\n    struct Node {')
    source = source.replace('std::atomic<uint64_t> membership[4]{};', 'Membership* membership;')
    source = source.replace('size_t used=8192;\n        Node* insert', '''size_t used=8192;
        std::vector<std::unique_ptr<Membership[]>> bits;
        size_t member_used=128;
        Membership* new_membership() {
            if(member_used==128) {
                bits.push_back(std::make_unique<Membership[]>(128));member_used=0;
            }
            return &bits.back()[member_used++];
        }
        Node* insert''')
    source = source.replace('Node{next,name.size()};', 'Node{next,name.size(),new_membership()};')
    source = source.replace('node->membership[country/64]', 'node->membership->words[country/64]')
    path = PROTO / f'continuation7-{variant}-splitmembers-c.cpp'
    assert not path.exists()
    path.write_text(source)
print('Created growing split-membership C variants with exact equality and atomic membership.')
