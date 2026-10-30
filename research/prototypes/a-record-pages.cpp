#include "common.hpp"
#include <array>
#include <atomic>
#include <numeric>
#include <thread>
#include <unordered_map>
#include <memory>

struct Group { uint32_t count = 0, errors = 0; size_t cursor = 0; };
struct Endpoint { std::string_view name; std::array<Group, 72> hours{}; };

struct Partial {
    std::unordered_map<std::string_view,uint32_t> ids;
    std::vector<Endpoint> endpoints;
    std::array<std::string,72> hour_names;
    std::vector<std::unique_ptr<uint64_t[]>> pages;
    size_t count=0;
    void parse(const char* p,const char* end) {
        ids.reserve(2048);endpoints.reserve(2048);
        while (p<end) {
            unsigned day=(p[8]-'0')*10+p[9]-'0',hour=(p[11]-'0')*10+p[12]-'0';
            unsigned bucket=(p[6]=='0'?day-30:day+1)*24+hour-18;
            if (hour_names[bucket].empty()) hour_names[bucket]=std::string(p,13)+":00:00Z";
            p+=28;
            while (*p++!=' ') {}
            const char* start=p;
            while (*p!=' ') ++p;
            std::string_view key(start,p-start);
            auto [it,fresh]=ids.try_emplace(key,endpoints.size());
            if (fresh) endpoints.push_back(Endpoint{key});
            uint32_t group=it->second*72+bucket;
            auto& g=endpoints[it->second].hours[bucket];
            ++g.count;++p;g.errors+=*p=='5';p+=4;
            uint32_t latency=integer(p);++p;
            if (count%8192==0) pages.push_back(std::unique_ptr<uint64_t[]>(new uint64_t[8192]));
            pages[count/8192][count%8192]=(uint64_t(group)<<32)|latency;
            ++count;
        }
    }
    void scatter(uint32_t* values) {
        for (size_t page=0;page<pages.size();++page) {
            size_t length=std::min<size_t>(8192,count-page*8192);
            for (size_t i=0;i<length;++i) {
                uint64_t record=pages[page][i];
                uint32_t group=record>>32;
                values[endpoints[group/72].hours[group%72].cursor++]=uint32_t(record);
            }
            pages[page].reset();
        }
    }
};

int main(int argc, char** argv) {
    try {
        Paths paths(argc,argv);
        MappedFile input(paths.data+"/requests.log");
        unsigned workers = std::min(6u,std::max(1u,std::thread::hardware_concurrency()));
        if (input.size < 2*1024*1024) workers = 1;
        std::vector<const char*> cuts(workers+1);
        cuts[0]=input.data; cuts[workers]=input.end();
        for (unsigned i=1;i<workers;++i) {
            auto p=input.data+input.size*i/workers;
            while (p<input.end() && p[-1]!='\n') ++p;
            cuts[i]=p;
        }
        std::vector<Partial> parts(workers);
        std::vector<std::thread> threads;
        for (unsigned i=0;i<workers;++i) threads.emplace_back([&,i]{parts[i].parse(cuts[i],cuts[i+1]);});
        for (auto& t:threads) t.join();
        std::unordered_map<std::string_view,uint32_t> ids;
        std::vector<Endpoint> endpoints;
        std::array<std::string,72> hours;
        ids.reserve(2048); endpoints.reserve(2048);
        std::vector<std::vector<uint32_t>> remap(workers);
        for (unsigned i=0;i<workers;++i) {
            for (unsigned h=0;h<72;++h) if (hours[h].empty()) hours[h]=parts[i].hour_names[h];
            for (auto& e:parts[i].endpoints) {
                auto [it,fresh]=ids.try_emplace(e.name,endpoints.size());
                if (fresh) endpoints.push_back(Endpoint{e.name});
                remap[i].push_back(it->second);
                for (unsigned h=0;h<72;++h) {
                    auto& dest=endpoints[it->second].hours[h];
                    dest.count+=e.hours[h].count; dest.errors+=e.hours[h].errors;
                }
            }
        }
        size_t total=0;
        for (auto& e:endpoints) for (auto& g:e.hours) {g.cursor=total; total+=g.count;}
        // Counts allocate exactly once; every parser gets disjoint scatter ranges.
        std::unique_ptr<uint32_t[]> values(new uint32_t[total]);
        std::vector<size_t> next(endpoints.size()*72);
        for (size_t e=0;e<endpoints.size();++e) for (unsigned h=0;h<72;++h) next[e*72+h]=endpoints[e].hours[h].cursor;
        for (unsigned i=0;i<workers;++i) for (size_t e=0;e<parts[i].endpoints.size();++e) for (unsigned h=0;h<72;++h) {
            auto& g=parts[i].endpoints[e].hours[h];
            auto& pos=next[size_t(remap[i][e])*72+h];
            g.cursor=pos; pos+=g.count;
        }
        threads.clear();
        for (unsigned i=0;i<workers;++i) threads.emplace_back([&,i]{parts[i].scatter(values.get());});
        for (auto& t:threads) t.join();
        parts.clear(); remap.clear(); next.clear();
        std::vector<uint32_t> order(endpoints.size());
        std::iota(order.begin(),order.end(),0);
        std::sort(order.begin(),order.end(),[&](auto a,auto b){return endpoints[a].name<endpoints[b].name;});
        std::array<std::string,72> outputs;
        std::atomic<unsigned> next_hour{0};
        threads.clear();
        for (unsigned i=0;i<workers;++i) threads.emplace_back([&]{
            for (;;) {
                unsigned h=next_hour.fetch_add(1,std::memory_order_relaxed);
                if (h>=72) break;
                auto& out=outputs[h]; out.reserve(192*1024);
                for (auto id:order) {
                    auto& g=endpoints[id].hours[h]; uint64_t n=g.count;
                    if (!n) continue;
                    size_t r50=(50*n+99)/100-1,r95=(95*n+99)/100-1,r99=(99*n+99)/100-1;
                    auto begin=values.get()+g.cursor, end=begin+n;
                    if (n<=128) std::sort(begin,end);
                    else {
                        std::nth_element(begin,begin+r50,end);
                        if (r95>r50) std::nth_element(begin+r50+1,begin+r95,end);
                        if (r99>r95) std::nth_element(begin+r95+1,begin+r99,end);
                    }
                    out+=hours[h]; out+=' '; out+=endpoints[id].name;
                    for (uint64_t v:{n,uint64_t(begin[r50]),uint64_t(begin[r95]),uint64_t(begin[r99]),uint64_t(g.errors),uint64_t(g.errors)*1000000/n}) {
                        out+=' '; number(out,v);
                    }
                    out+='\n';
                }
            }
        });
        for (auto& t:threads) t.join();
        FILE* file=fopen((paths.out+"/summary.txt").c_str(),"wb");
        if (!file) throw std::runtime_error("Cannot open summary");
        bool ok=true;
        for (auto& out:outputs) ok &= fwrite(out.data(),1,out.size(),file)==out.size();
        if (fclose(file)!=0 || !ok) throw std::runtime_error("Output write failed");
    } catch (const std::exception& e) {fprintf(stderr,"%s\n",e.what());return 1;}
}
