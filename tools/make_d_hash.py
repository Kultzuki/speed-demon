"""Exact generation-tagged sparse hash state for D's balanced searches."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'research/prototypes/d-compact-identity.cpp').read_text()
start=s.index('struct Search {')
stop=s.index('    void push(',start)
state=r'''
struct SparseState {
    struct Slot {uint64_t distance=0;uint32_t node=0,epoch=0;};
    std::vector<Slot> slots=std::vector<Slot>(1024);
    uint32_t epoch=0;
    size_t used=0;
    void clear() {
        used=0;
        if (!++epoch) {for (auto& slot:slots) slot.epoch=0;epoch=1;}
    }
    uint64_t get(uint32_t node) const {
        size_t at=(node*2654435761u)&(slots.size()-1);
        while (slots[at].epoch==epoch) {
            if (slots[at].node==node) return slots[at].distance;
            at=(at+1)&(slots.size()-1);
        }
        return UINT64_MAX/2;
    }
    void set(uint32_t node,uint64_t distance) {
        if ((used+1)*2>=slots.size()) {
            std::vector<Slot> grown(slots.size()*2);
            for (auto slot:slots) if (slot.epoch==epoch) {
                size_t at=(slot.node*2654435761u)&(grown.size()-1);
                while (grown[at].epoch==epoch) at=(at+1)&(grown.size()-1);
                grown[at]=slot;
            }
            slots.swap(grown);
        }
        size_t at=(node*2654435761u)&(slots.size()-1);
        while (slots[at].epoch==epoch && slots[at].node!=node) at=(at+1)&(slots.size()-1);
        if (slots[at].epoch!=epoch) ++used;
        slots[at]={distance,node,epoch};
    }
};

struct Search {
    SparseState state[2];
    RadixHeap heap[2];
    static constexpr uint64_t INF=UINT64_MAX/2;
    explicit Search(uint32_t) {}
'''
s=s[:start]+state+s[stop:]
s=s.replace('for (auto& side:labels) side.clear();\n        set(0,s,0);set(1,t,0);',
            'for (auto& side:state) side.clear();\n        state[0].set(s,0);state[1].set(t,0);')
s=s.replace('get(d,heap[d].top().second)','state[d].get(heap[d].top().second)')
s=s.replace('if (has(1-dir,u)) best = std::min(best, du + get(1-dir,u));','best=std::min(best,du+state[1-dir].get(u));')
s=s.replace('!has(dir,v) || nd<get(dir,v)', 'nd<state[dir].get(v)')
s=s.replace('set(dir,v,nd);','state[dir].set(v,nd);')
s=s.replace('if (has(1-dir,v)) best = std::min(best, nd + get(1-dir,v));','best=std::min(best,nd+state[1-dir].get(v));')
# INF plus any legal path label stays below UINT64_MAX; it cannot improve best.
(root/'research/prototypes/d-hash.cpp').write_text(s)
