#define main candidate_main
#ifndef CANDIDATE_SOURCE
#define CANDIDATE_SOURCE "../../track-a/main.cpp"
#endif
#include CANDIDATE_SOURCE
#undef main
#include <cstdlib>

template<class B> bool check_bucket(const B& bucket,uint32_t value,const EndpointTable& table,std::string_view endpoint) {
    if constexpr (requires {bucket.records;}) {
        if (bucket.records.size()!=1) return false;
        uint32_t word=bucket.records[0],latency=word>>12;
        if (latency==((1u<<20)-1)) latency=bucket.wide[0];
        return latency==value && (word&1) && table.names[(word>>1)&2047]==endpoint;
    } else {
        return bucket.latencies.size()==1 && bucket.latencies[0]==value && bucket.tags.size()==1 &&
            (bucket.tags[0]&32768) && table.names[bucket.tags[0]&32767]==endpoint;
    }
}

int main() {
    EndpointTable table;
    std::vector<std::string> names;
    for (unsigned i=0;i<1842;++i) names.push_back("/publication/endpoint_"+std::to_string(i));
    std::array<std::atomic<uint32_t>,1842> elected;
    for (auto& id:elected) id.store(UINT32_MAX);
    std::vector<std::thread> threads;
    for (unsigned t=0;t<12;++t) threads.emplace_back([&,t] {
        for (unsigned repeat=0;repeat<8;++repeat) for (unsigned j=0;j<names.size();++j) {
            unsigned i=(j+t*131)%names.size();
            uint32_t id=table.find(names[i]),empty=UINT32_MAX;
            if (!elected[i].compare_exchange_strong(empty,id) && empty!=id) std::abort();
            if (table.names[id]!=names[i]) std::abort();
        }
    });
    for (auto& thread:threads) thread.join();
    if (table.count!=1842) std::abort();
    std::vector<uint32_t> ids;
    for (auto& id:elected) ids.push_back(id.load());
    std::sort(ids.begin(),ids.end());
    if (std::unique(ids.begin(),ids.end())!=ids.end()) std::abort();
    char* page=static_cast<char*>(mmap(nullptr,8192,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0));
    if (page==MAP_FAILED || mprotect(page+4096,4096,PROT_NONE)) return 2;
    EndpointTable guards;
    for (unsigned n=1;n<=125;++n) for (std::string_view method:{"GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS"}) {
        std::string endpoint="/"+std::string(n-1,'x');
        for (uint32_t value:{0u,(1u<<20)-2,(1u<<20)-1,1u<<20,UINT32_MAX}) {
            std::string line="2026-11-02T17:59:59.999999Z "+std::string(method)+" "+endpoint+" 599 "+std::to_string(value)+"\n";
            char* begin=page+4096-line.size();memcpy(begin,line.data(),line.size());
            Partial partial;partial.parse(begin,page+4096,guards);
            auto& hour=partial.hours[71];
            if (!check_bucket(hour,value,guards,endpoint)) std::abort();
        }
    }
    munmap(page,8192);
    puts("PASS A twelve-way exact endpoint publication and 4,375 guard-page parses across methods, lengths, 20-bit sentinel and uint32 extremes");
}
