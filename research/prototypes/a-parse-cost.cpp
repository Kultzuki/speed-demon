// Local cost attribution for the Track A parser (process CPU time). Never a candidate.
#pragma GCC target("avx2")
#include "common.hpp"
#include <array>
#include <atomic>
#include <bit>
#include <immintrin.h>
#include <cstdlib>
#include <ctime>

constexpr uint32_t WIDE=(1u<<20)-1;
static inline size_t path_hash(std::string_view name) {
    const char* p=name.data();
    size_t n=name.size();
    uint64_t a=0,b=0;
    if (n>=8) {__builtin_memcpy(&a,p,8);__builtin_memcpy(&b,p+n-8,8);}
    else {for (size_t i=0;i<n;++i) a=a<<8|uint8_t(p[i]); b=a;}
    uint64_t h=(a^std::rotl(b,29))+(n*0x9E3779B97F4A7C15ull);
    h^=h>>30;h*=0xBF58476D1CE4E5B9ull;h^=h>>27;h*=0x94D049BB133111EBull;h^=h>>31;
    return size_t(h);
}
struct EndpointTable {
    std::array<std::atomic<uint32_t>,4096> slots{};
    std::array<std::string_view,2048> names{};
    std::atomic<uint32_t> count{0};
    uint16_t find(std::string_view name) {
        size_t hash=path_hash(name);
        for (size_t at=hash&4095;;at=(at+1)&4095) {
            uint32_t value=slots[at].load(std::memory_order_acquire);
            if (!value && slots[at].compare_exchange_strong(value,UINT32_MAX,std::memory_order_acquire)) {
                uint32_t id=count.fetch_add(1,std::memory_order_relaxed);
                if (id>=names.size()) std::terminate();
                names[id]=name;
                slots[at].store(id+1,std::memory_order_release);
                return id;
            }
            while (value==UINT32_MAX) value=slots[at].load(std::memory_order_acquire);
            if (value && names[value-1]==name) return value-1;
        }
    }
};
struct Bucket { std::vector<uint32_t> records,wide; };

static double cpu_ms() {
    timespec t{}; clock_gettime(CLOCK_PROCESS_CPUTIME_ID,&t);
    return t.tv_sec*1000.0+t.tv_nsec/1e6;
}

// MODE 0: no lookup (id 0). 1: hash + probe, no byte compare. 2: full exact lookup.
template<int MODE>
static uint64_t parse(const char* p,const char* end,EndpointTable& endpoints,Bucket* hours) {
    uint64_t sink=0;
    while (p<end) {
        unsigned day=(p[8]-'0')*10+p[9]-'0';
        unsigned hour=(p[11]-'0')*10+p[12]-'0';
        unsigned bucket=(p[6]=='0'?day-30:day+1)*24+hour-18;
        p+=28;
        while (*p++!=' ') {}
        const char* start=p;
        while (end-p>=32) {
            auto bytes=_mm256_loadu_si256(reinterpret_cast<const __m256i*>(p));
            uint32_t mask=_mm256_movemask_epi8(_mm256_cmpeq_epi8(bytes,_mm256_set1_epi8(' ')));
            if (mask) {p+=std::countr_zero(mask);break;}
            p+=32;
        }
        while (*p!=' ') ++p;
        uint32_t id=0;
        if (MODE==2) id=endpoints.find({start,size_t(p-start)});
        else if (MODE==1) {
            std::string_view name{start,size_t(p-start)};
            size_t at=path_hash(name)&4095;
            uint32_t value=endpoints.slots[at].load(std::memory_order_relaxed);
            id=value?value-1:0;
            sink+=uint64_t(start[0]);
        }
        uint32_t error=p[1]=='5';
        p+=5;
        uint32_t latency=uint32_t(integer(p));
        while (*p!='\n') ++p;
        ++p;
        auto& b=hours[bucket];
        b.records.push_back((std::min(latency,WIDE)<<12)|(id<<1)|error);
    }
    return sink;
}

int main(int argc,char** argv) {
    try {
        Paths paths(argc,argv);
        MappedFile input(paths.data+"/requests.log");
        EndpointTable endpoints;
        std::vector<Bucket> hours(72*4096);
        const char* p=input.data;const char* end=input.end();
        uint64_t sink=0;
        sink+=parse<2>(p,end,endpoints,hours.data());
        for (auto& b:hours) {b.records.clear();b.wide.clear();}
        const char* names[]={"no-lookup","hash-probe","full"};
        double best[3]={1e9,1e9,1e9};
        for (int rep=0;rep<5;++rep) for (int mode=0;mode<3;++mode) {
            double t0=cpu_ms();
            uint64_t s=mode==0?parse<0>(p,end,endpoints,hours.data())
                     :mode==1?parse<1>(p,end,endpoints,hours.data())
                             :parse<2>(p,end,endpoints,hours.data());
            double ms=cpu_ms()-t0;
            sink+=s;
            if (ms<best[mode]) best[mode]=ms;
            fprintf(stderr,"CASE %-10s rep=%d ms=%.3f\n",names[mode],rep,ms);
            for (auto& b:hours) {b.records.clear();b.wide.clear();}
        }
        fprintf(stderr,"BEST no-lookup=%.3f hash-probe=%.3f full=%.3f (lookup=%.3f hash=%.3f compare=%.3f)\n",
                best[0],best[1],best[2],best[2]-best[0],best[1]-best[0],best[2]-best[1]);
        fprintf(stderr,"endpoints=%u sink=%llu\n",endpoints.count.load(),(unsigned long long)sink);
    } catch (const std::exception& e) {fprintf(stderr,"%s\n",e.what());return 1;}
}
