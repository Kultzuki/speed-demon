"""Use 64-bit temporary edges, with an unbounded exact wide-edge stream."""
from pathlib import Path
from continuation7_trials import profile

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
source = (PROTO / 'continuation7-shards-d.cpp').read_text()


def replace(old, new):
    global source
    assert source.count(old) == 1, old
    source = source.replace(old, new)


replace('std::vector<std::vector<Triple>> parsed(workers);', '''std::vector<std::vector<uint64_t>> parsed(workers);
        std::vector<std::vector<Triple>> wide(workers);
        for(auto& side:edges) side.configure(n);
        unsigned weight_bits=edges[0].shift;
        uint64_t sentinel=edges[0].mask;
        // A sentinel record indexes a growing per-worker stream, preserving
        // all endpoints and uint32 weights. Normal records need eight bytes.
        auto decode=[&](uint64_t word) -> Triple {
            if((word&sentinel)==sentinel) {
                uint64_t index=word>>weight_bits;
                return wide[index%workers][index/workers];
            }
            return {uint32_t(word>>32),uint32_t(word)>>weight_bits,uint32_t(word&sentinel)};
        };''')
replace('part.push_back({u,v,w});', '''if(w>=sentinel) {
                    uint64_t index=uint64_t(wide[t].size())*workers+t;
                    if(index>(UINT64_MAX>>weight_bits)) std::terminate();
                    part.push_back((index<<weight_bits)|sentinel);
                    wide[t].push_back({u,v,w});
                } else part.push_back((uint64_t(u)<<32)|(uint64_t(v)<<weight_bits)|w);''')
replace('std::unique_ptr<Triple[]> bucket(new Triple[m]);', 'std::unique_ptr<uint64_t[]> bucket(new uint64_t[m]);')
replace('for(auto edge:parsed[t]) bucket[at[(d?edge.v:edge.u)>>shift]++]=edge;', '''for(uint64_t word:parsed[t]) {
                    auto edge=decode(word);
                    bucket[at[(d?edge.v:edge.u)>>shift]++]=word;
                }''')
replace('if(d) std::vector<std::vector<Triple>>{}.swap(parsed);', 'if(d) std::vector<std::vector<uint64_t>>{}.swap(parsed);')
assert source.count('auto edge=bucket[i];') == 2
source = source.replace('auto edge=bucket[i];', 'auto edge=decode(bucket[i]);')
for name, text in [('compact-shards', source), ('profile-compact-shards', profile(source, 'd'))]:
    path = PROTO / f'continuation7-{name}-d.cpp'
    assert not path.exists()
    path.write_text(text)
print('Created compact owner-partitioned CSR and phase variant; wide stream has no fixed cap.')
