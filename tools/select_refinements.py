"""Stage the measured candidates; validation and push remain separate steps."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
selected={'a':'a-parallel-output.cpp','b':'b-inline-query.cpp','c':'c-contract-cuts.cpp','d':'d-hash.cpp'}
for track,name in selected.items():
    source=(ROOT/'research/prototypes'/name).read_text()
    if track=='d':
        start=source.index('    void reorder() {')
        stop=source.index('\n};',start)
        source=source[:start]+source[stop:]
        source=source.replace('    std::vector<uint32_t> remap;\n','')
        source=source.replace('        graph.remap.resize(graph.n);std::iota(graph.remap.begin(),graph.remap.end(),0);\n','')
        source=source.replace('queries.emplace_back(graph.remap[s], graph.remap[t]);','queries.emplace_back(s,t);')
        source=source.replace('    uint32_t node(uint32_t i) const {return words[i]>>shift;}\n','')
    (ROOT/f'track-{track}/main.cpp').write_text(source)
(ROOT/'research/refinement-selection.json').write_text(json.dumps({'checkpoint':'6cb35093ef9de4babf07b6ed58347e40da6fa76d','sources':selected,'status':'staged for validation'},indent=2)+'\n')
