#include <unistd.h>
#pragma GCC target("avx2")
#include "common.hpp"
#include <array>
#include <atomic>
#include <bit>
#include <immintrin.h>
#include <mutex>
#include <numeric>
#include <thread>

// The binding catalogue has 1,842 endpoints, so 11 ID bits are sufficient.
// A record uses 20 latency bits, 11 endpoint bits and one error bit. The
// latency sentinel has an exact, ordered uint32 overflow stream per bucket.
constexpr uint32_t WIDE=(1u<<20)-1;
// Paths repeat from a fixed catalogue of 1,842 route templates averaging 34
// bytes. Hashing only the first and last 8 bytes (plus the length) is much
// cheaper than a full-string hash; the table still compares whole names, so a
// collision only costs a probe.
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
struct Bucket {
    std::vector<uint32_t> records,wide;
};
struct Partial {
    std::array<Bucket,72> hours;
    void parse(const char* p,const char* end,EndpointTable& endpoints) {
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
            uint32_t id=endpoints.find({start,size_t(p-start)});
            uint32_t error=p[1]=='5';
            p+=5;
            uint32_t latency=integer(p);++p;
            auto& b=hours[bucket];
            b.records.push_back((std::min(latency,WIDE)<<12)|(id<<1)|error);
            if (latency>=WIDE) b.wide.push_back(latency);
        }
    }
};

int main(int argc,char** argv) {
    try {
        Paths paths(argc,argv);
        MappedFile input(paths.data+"/requests.log");
        unsigned workers=std::min(12u,std::max(1u,std::thread::hardware_concurrency()));
        if (input.size<2*1024*1024) workers=1;
        std::vector<const char*> cuts(workers+1);
        cuts[0]=input.data;cuts[workers]=input.end();
        for (unsigned i=1;i<workers;++i) {
            auto p=input.data+input.size*i/workers;
            while (p<input.end() && p[-1]!='\n') ++p;
            cuts[i]=p;
        }
        EndpointTable endpoints;
        std::vector<Partial> parts(workers);
        std::vector<std::thread> threads;
        for (unsigned i=0;i<workers;++i) threads.emplace_back([&,i]{parts[i].parse(cuts[i],cuts[i+1],endpoints);});
        for (auto& thread:threads) thread.join();
        uint32_t count=endpoints.count.load();
        std::vector<uint32_t> order(count);
        std::iota(order.begin(),order.end(),0);
        std::sort(order.begin(),order.end(),[&](auto a,auto b){return endpoints.names[a]<endpoints.names[b];});
        FILE* file=fopen((paths.out+"/summary.txt").c_str(),"wb");
        if (!file) throw std::runtime_error("Cannot write summary");
        std::array<std::string,72> outputs;
        std::array<bool,72> ready{};
        std::mutex output_mutex;
        unsigned turn=0;
        bool ok=true;
        std::atomic<unsigned> next{0};
        threads.clear();
        for (unsigned worker=0;worker<workers;++worker) threads.emplace_back([&] {
            std::vector<uint32_t> counts(count),errors(count),positions(count),values;
            for (;;) {
                unsigned hour=next.fetch_add(1,std::memory_order_relaxed);
                if (hour>=72) break;
                std::fill(counts.begin(),counts.end(),0);
                std::fill(errors.begin(),errors.end(),0);
                size_t total=0;
                for (auto& part:parts) {
                    auto& b=part.hours[hour];
                    total+=b.records.size();
                    for (uint32_t word:b.records) {++counts[(word>>1)&2047];errors[(word>>1)&2047]+=word&1;}
                }
                uint32_t at=0;
                for (uint32_t i=0;i<count;++i) {positions[i]=at;at+=counts[i];}
                values.resize(total);
                for (auto& part:parts) {
                    auto& b=part.hours[hour];
                    size_t wide=0;
                    for (uint32_t word:b.records) {
                        uint32_t latency=word>>12;
                        if (latency==WIDE) latency=b.wide[wide++];
                        values[positions[(word>>1)&2047]++]=latency;
                    }
                    b=Bucket{};
                }
                auto& output=outputs[hour];
                output.reserve(160*1024);
                unsigned day=(hour+18)/24;
                char stamp[32];
                snprintf(stamp,sizeof(stamp),"2026-%02u-%02uT%02u:00:00Z",day<2?10:11,day<2?30+day:day-1,(hour+18)%24);
                for (uint32_t id:order) {
                    uint64_t n=counts[id];
                    if (!n) continue;
                    auto begin=values.begin()+positions[id]-n,end=begin+n;
                    size_t r50=(50*n+99)/100-1,r95=(95*n+99)/100-1,r99=(99*n+99)/100-1;
                    if (n<=128) std::sort(begin,end);
                    else {
                        std::nth_element(begin,begin+r50,end);
                        if (r95>r50) std::nth_element(begin+r50+1,begin+r95,end);
                        if (r99>r95) std::nth_element(begin+r95+1,begin+r99,end);
                    }
                    output+=stamp;output+=' ';output+=endpoints.names[id];
                    for (uint64_t value:{n,uint64_t(begin[r50]),uint64_t(begin[r95]),uint64_t(begin[r99]),uint64_t(errors[id]),uint64_t(errors[id])*1000000/n}) {
                        output+=' ';number(output,value);
                    }
                    output+='\n';
                }
                std::lock_guard<std::mutex> lock(output_mutex);
                ready[hour]=true;
                while (turn<72 && ready[turn]) {
                    auto& s=outputs[turn++];
                    ok&=fwrite(s.data(),1,s.size(),file)==s.size();
                    std::string{}.swap(s);
                }
            }
        });
        for (auto& thread:threads) thread.join();
        if (fclose(file)!=0 || !ok) throw std::runtime_error("Summary write failed");
        _exit(0);
    } catch (const std::exception& e) {fprintf(stderr,"%s\n",e.what());return 1;}
}
