"""Partition CSR construction by node ranges instead of shared atomic cursors."""
from pathlib import Path
from continuation7_trials import profile

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
CONSTRUCTOR = r'''
    explicit Graph(const std::string& path) {
        MappedFile file(path);
        const char* p=file.data;
        n=integer(p);++p;
        uint32_t m=integer(p);++p;
        constexpr unsigned SHARDS=64;
        unsigned shift=unsigned(std::max(0,int(std::bit_width(n-1))-6));
        unsigned workers=std::min(6u,std::max(1u,std::thread::hardware_concurrency()));
        if(file.size<2*1024*1024) workers=1;
        std::vector<const char*> cuts(workers+1);
        cuts[0]=p;cuts[workers]=file.end();
        for(unsigned i=1;i<workers;++i) {
            auto at=p+(file.end()-p)*i/workers;
            while(at<file.end() && at[-1]!='\n') ++at;
            cuts[i]=at;
        }
        struct Triple {uint32_t u,v,w;};
        std::vector<std::vector<Triple>> parsed(workers);
        std::vector<std::array<uint32_t,SHARDS>> counts[2];
        for(auto& side:counts) side.resize(workers);
        std::vector<std::thread> threads;
        for(unsigned t=0;t<workers;++t) threads.emplace_back([&,t] {
            auto& part=parsed[t];
            part.reserve(size_t(m)/workers+4096);
            const char* at=cuts[t];
            while(at<cuts[t+1]) {
                uint32_t u=integer(at);++at;
                uint32_t v=integer(at);++at;
                uint32_t w=integer(at);++at;
                part.push_back({u,v,w});
                ++counts[0][t][u>>shift];++counts[1][t][v>>shift];
            }
        });
        for(auto& thread:threads) thread.join();
        threads.clear();
        std::unique_ptr<Triple[]> bucket(new Triple[m]);
        std::vector<uint32_t> cursor(n);
        for(auto& side:offset) side.resize(size_t(n)+1);
        for(unsigned d=0;d<2;++d) {
            std::array<uint32_t,SHARDS+1> first{};
            auto positions=counts[d];
            uint32_t total=0;
            for(unsigned b=0;b<SHARDS;++b) {
                first[b]=total;
                for(unsigned t=0;t<workers;++t) {
                    uint32_t count=counts[d][t][b];
                    positions[t][b]=total;total+=count;
                }
            }
            first[SHARDS]=total;
            if(total!=m) throw std::runtime_error("Edge count mismatch");
            for(unsigned t=0;t<workers;++t) threads.emplace_back([&,t] {
                auto at=positions[t];
                for(auto edge:parsed[t]) bucket[at[(d?edge.v:edge.u)>>shift]++]=edge;
            });
            for(auto& thread:threads) thread.join();
            threads.clear();
            if(d) std::vector<std::vector<Triple>>{}.swap(parsed);
            edges[d].configure(n);edges[d].resize(m);
            std::atomic<unsigned> next{0};
            for(unsigned t=0;t<workers;++t) threads.emplace_back([&] {
                for(unsigned b;(b=next.fetch_add(1,std::memory_order_relaxed))<SHARDS;) {
                    uint32_t lo=std::min<uint64_t>(n,uint64_t(b)<<shift);
                    uint32_t hi=std::min<uint64_t>(n,uint64_t(b+1)<<shift);
                    for(uint32_t i=first[b];i<first[b+1];++i) {
                        auto edge=bucket[i];
                        ++offset[d][(d?edge.v:edge.u)+1];
                    }
                    uint32_t sum=first[b];
                    for(uint32_t u=lo;u<hi;++u) {
                        cursor[u]=sum;sum+=offset[d][u+1];offset[d][u+1]=sum;
                    }
                    for(uint32_t i=first[b];i<first[b+1];++i) {
                        auto edge=bucket[i];
                        uint32_t u=d?edge.v:edge.u,v=d?edge.u:edge.v;
                        edges[d].set(cursor[u]++,{v,edge.w});
                    }
                }
            });
            for(auto& thread:threads) thread.join();
            threads.clear();
            edges[d].finish();
        }
    }
'''

base = (PROTO / 'continuation7-base-d.cpp').read_text()
start = base.index('    explicit Graph(const std::string& path) {')
end = base.index('\n};\n\n// Non-negative edges', start)
source = base[:start] + CONSTRUCTOR + base[end:]
sources = {'shards': source,
           'shards12': source.replace('std::min(6u,', 'std::min(12u,', 1),
           'profile-shards': profile(source, 'd')}
for name, text in sources.items():
    path = PROTO / f'continuation7-{name}-d.cpp'
    assert not path.exists()
    path.write_text(text.replace('#include <mutex>', '#include <mutex>\n#include <memory>'))
print('Created owner-partitioned CSR variants with exact weights.')
