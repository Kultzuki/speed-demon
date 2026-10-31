"""Independent algorithm trials; never writes a production track."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/prototypes'

def base(track):
    return (OUT / f'continuation5-start-{track}.cpp').read_text()

def save(label, source):
    (OUT / f'{label}.cpp').write_text(source, encoding='utf-8', newline='\n')

def once(source, old, new):
    assert source.count(old) == 1, (old, source.count(old))
    return source.replace(old, new)

def main():
    a = base('a')
    a = a.replace('#pragma GCC target("avx2")', '#pragma GCC target("avx2,sse4.2")')
    a = once(a, 'size_t hash=std::hash<std::string_view>()(name);', r'''
        uint64_t first=0,last=0;
        memcpy(&first,name.data(),std::min<size_t>(8,name.size()));
        if (name.size()>8) memcpy(&last,name.data()+name.size()-8,8);
        size_t hash=_mm_crc32_u64(_mm_crc32_u64(name.size(),first),last);''')
    save('a-crc5', a)
    a = base('a')
    a = once(a, 'struct Partial {', 'struct Partial {\n    EndpointTable local;\n    std::array<uint16_t,2048> remap{};')
    a = once(a, 'parts[i].parse(cuts[i],cuts[i+1],endpoints);', 'parts[i].parse(cuts[i],cuts[i+1],parts[i].local);')
    a = once(a, 'uint32_t count=endpoints.count.load();', '''for (auto& part:parts) for (uint32_t i=0;i<part.local.count;++i)
            part.remap[i]=endpoints.find(part.local.names[i]);
        uint32_t count=endpoints.count.load();''')
    a = a.replace('++counts[(word>>1)&2047];errors[(word>>1)&2047]+=word&1;', '++counts[part.remap[(word>>1)&2047]];errors[part.remap[(word>>1)&2047]]+=word&1;')
    a = a.replace('values[positions[(word>>1)&2047]++]', 'values[positions[part.remap[(word>>1)&2047]]++]')
    save('a-private5', a)

    b = base('b').replace('#pragma GCC target("avx2")', '#pragma GCC target("avx2,popcnt")')
    b = once(b, '    void add(uint32_t doc) {', r'''
    void add_word(uint32_t base,uint64_t bits) {
        uint64_t n=std::popcount(bits), positions=0;
        constexpr uint64_t masks[]={0xAAAAAAAAAAAAAAAAULL,0xCCCCCCCCCCCCCCCCULL,0xF0F0F0F0F0F0F0F0ULL,0xFF00FF00FF00FF00ULL,0xFFFF0000FFFF0000ULL,0xFFFFFFFF00000000ULL};
        for (unsigned i=0;i<6;++i) positions+=uint64_t(std::popcount(bits&masks[i]))<<i;
        for (uint64_t left=bits;left && count<first.size();left&=left-1) first[count++]=base+std::countr_zero(left);
        // The first-ten collection above increments count only while filling.
        count-=std::min<uint64_t>(n,first.size()-std::min<uint64_t>(first.size(),count-n));
        count+=n;sum+=n*base+positions;
    }
    void add(uint32_t doc) {''')
    # Keep first-ten collection separate from total count.
    start = b.index('        for (uint64_t left=bits;')
    end = b.index('    }\n    void add(', start)
    b = b[:start] + '''        size_t at=std::min<uint64_t>(count,first.size());
        for (uint64_t left=bits;left && at<first.size();left&=left-1) first[at++]=base+std::countr_zero(left);
        count+=n;sum+=n*base+positions;
''' + b[end:]
    b = once(b, 'while (bits) { answer.add(block.base + w * 64 + std::countr_zero(bits)); bits &= bits - 1; }', 'answer.add_word(block.base+w*64,bits);')
    save('b-wordsummary5', b)

    c = base('c')
    c = once(c, '    bool add(std::string_view name,uint16_t country) {\n        size_t hash=std::hash<std::string_view>()(name);', r'''
    size_t prefetch(std::string_view name) {
        size_t hash=std::hash<std::string_view>()(name);
        auto& head=shards[(hash>>32)&255].heads[hash&511];
        __builtin_prefetch(&head,0,3);
        if (auto* node=head.load(std::memory_order_acquire)) __builtin_prefetch(node,0,3);
        return hash;
    }
    bool add(std::string_view name,uint16_t country) {return add(name,country,prefetch(name));}
    bool add(std::string_view name,uint16_t country,size_t hash) {''')
    c = once(c, '        std::string scratch;', '''        struct Pending {std::string scratch;std::string_view name;uint16_t country;size_t hash;};
        std::array<Pending,16> pending;
        size_t serial=0;
        auto retire=[&](Pending& old) {countries[old.country].distinct+=names.add(old.name,old.country,old.hash);};''')
    c = once(c, '            Field name = text_field(p, end, &scratch);', '''            auto& next=pending[serial%pending.size()];
            if (serial>=pending.size()) retire(next);
            ++serial;
            Field name = text_field(p, end, &next.scratch);''')
    c = once(c, '            group.distinct += names.add(name.value, country);', '            next.name=name.value;next.country=country;next.hash=names.prefetch(name.value);')
    c = once(c, '''            group.note_bytes += note.bytes;
        }
    }
};''', '''            group.note_bytes += note.bytes;
        }
        for (size_t i=serial>pending.size()?serial-pending.size():0;i<serial;++i) retire(pending[i%pending.size()]);
    }
};''')
    save('c-prefetch5', c)

    d = base('d')
    queue = r'''
// Most edge relaxations stay within a short monotone window. The radix heap
// retains every farther uint64 key exactly, without narrowing or restarting.
struct WindowHeap {
    static constexpr uint64_t WIDTH=4096;
    std::array<std::vector<uint32_t>,WIDTH> ring;
    RadixHeap far;
    uint64_t last=0;
    size_t size=0,near=0;
    using Item=RadixHeap::Item;
    void clear() {for(auto& b:ring)b.clear();far.clear();last=0;size=near=0;}
    bool empty() const {return !size;}
    void push(uint64_t d,uint32_t v) {
        if(d-last<WIDTH) {ring[d&(WIDTH-1)].push_back(v);++near;}
        else far.push(d,v);
        ++size;
    }
    Item top() {
        uint64_t candidate=last;
        if(near) while(ring[candidate&(WIDTH-1)].empty()) ++candidate;
        else candidate=UINT64_MAX;
        if(!far.empty() && far.top().first<candidate) return far.top();
        last=candidate;
        return {last,ring[last&(WIDTH-1)].back()};
    }
    Item pop() {
        auto item=top();
        if(!far.empty() && far.top().first==item.first && (!near || item.first<last)) {
            item=far.pop();last=item.first;
        } else {ring[last&(WIDTH-1)].pop_back();--near;}
        --size;return item;
    }
};
'''
    # Record the chosen queue explicitly; equal-distance ring/far keys are legal.
    queue = queue.replace('    using Item=RadixHeap::Item;', '    using Item=RadixHeap::Item;\n    bool use_far=false;')
    queue = queue.replace('if(!far.empty() && far.top().first<candidate) return far.top();', 'if(!far.empty() && far.top().first<candidate) {use_far=true;return far.top();}\n        use_far=false;')
    queue = queue.replace('if(!far.empty() && far.top().first==item.first && (!near || item.first<last))', 'if(use_far)')
    d = once(d, 'struct SparseState {', queue + '\nstruct SparseState {')
    d = once(d, '    RadixHeap heap[2];', '    WindowHeap heap[2];')
    save('d-window5', d)

if __name__ == '__main__':
    main()
