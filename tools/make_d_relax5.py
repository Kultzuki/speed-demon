"""One-probe sparse relaxation, then an independent exact overflow-label trial."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/prototypes'
source=(OUT/'continuation5-start-d.cpp').read_text()
source=source.replace('    void set(uint32_t node,uint64_t distance) {', '    Slot& find_slot(uint32_t node) {')
source=source.replace('''        if (slots[at].epoch!=epoch) ++used;
        slots[at]={distance,node,epoch};
    }
};''','''        if (slots[at].epoch!=epoch) {++used;slots[at]={UINT64_MAX/2,node,epoch};}
        return slots[at];
    }
    void set(uint32_t node,uint64_t distance) {find_slot(node).distance=distance;}
    bool relax(uint32_t node,uint64_t distance) {
        auto& slot=find_slot(node);
        if(distance>=slot.distance)return false;
        slot.distance=distance;return true;
    }
};''')
source=source.replace('''                if (nd<state[dir].get(v)) {
                    state[dir].set(v,nd);''','''                if (state[dir].relax(v,nd)) {''')
(OUT/'d-relax5.cpp').write_text(source,encoding='utf-8',newline='\n')
source=(OUT/'continuation5-start-d.cpp').read_text()
source=source.replace('#include <mutex>','#include <mutex>\n#include <unordered_map>')
source=source.replace('struct Slot {uint64_t distance=0;uint32_t node=0,epoch=0;};','struct Slot {uint32_t distance=0,node=0,epoch=0;};\n    std::unordered_map<uint32_t,uint64_t> overflow;')
source=source.replace('''        used=0;
        if (!++epoch)''','''        used=0;overflow.clear();
        if (!++epoch)''')
source=source.replace('if (slots[at].node==node) return slots[at].distance;', 'if (slots[at].node==node) return slots[at].distance==UINT32_MAX?overflow.at(node):slots[at].distance;')
source=source.replace('slots[at]={distance,node,epoch};','''slots[at]={uint32_t(std::min<uint64_t>(distance,UINT32_MAX)),node,epoch};
        if(distance>=UINT32_MAX) overflow[node]=distance;''')
(OUT/'d-labelescape5.cpp').write_text(source,encoding='utf-8',newline='\n')
