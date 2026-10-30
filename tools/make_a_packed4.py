"""Pack common A records into 32 bits, preserving exact wide latency values."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'research/prototypes/a-simd3.cpp').read_text()
def replace(old,new):
    global source
    assert source.count(old)==1,old
    source=source.replace(old,new)

replace('std::array<std::string_view,4096> names{};','std::array<std::string_view,2048> names{};')
replace('// The binding input catalogue has 1,842 endpoints; the tag has 15 ID bits.',
'''// The binding catalogue has 1,842 endpoints, so 11 ID bits are sufficient.
// A record uses 20 latency bits, 11 endpoint bits and one error bit. The
// latency sentinel has an exact, ordered uint32 overflow stream per bucket.
constexpr uint32_t WIDE=(1u<<20)-1;''')
replace('''    std::vector<uint32_t> latencies;
    std::vector<uint16_t> tags;''','''    std::vector<uint32_t> records,wide;''')
replace('''            uint16_t tag=endpoints.find({start,size_t(p-start)});
            tag|=uint16_t(p[1]=='5')<<15;''','''            uint32_t id=endpoints.find({start,size_t(p-start)});
            uint32_t error=p[1]=='5';''')
replace('''            hours[bucket].latencies.push_back(latency);
            hours[bucket].tags.push_back(tag);''','''            auto& b=hours[bucket];
            b.records.push_back((std::min(latency,WIDE)<<12)|(id<<1)|error);
            if (latency>=WIDE) b.wide.push_back(latency);''')
replace('''                    total+=b.tags.size();
                    for (uint16_t tag:b.tags) {++counts[tag&32767];errors[tag&32767]+=tag>>15;}''','''                    total+=b.records.size();
                    for (uint32_t word:b.records) {++counts[(word>>1)&2047];errors[(word>>1)&2047]+=word&1;}''')
replace('''                    for (size_t i=0;i<b.tags.size();++i) values[positions[b.tags[i]&32767]++]=b.latencies[i];''','''                    size_t wide=0;
                    for (uint32_t word:b.records) {
                        uint32_t latency=word>>12;
                        if (latency==WIDE) latency=b.wide[wide++];
                        values[positions[(word>>1)&2047]++]=latency;
                    }''')
(ROOT/'research/prototypes/a-packed4.cpp').write_text(source)
