#define main supplied_main
#include "../prototypes/supplied-sixth-a.cpp"
#undef main
#include <unordered_map>

int main() {
    std::unordered_map<uint64_t,std::string> seen;
    uint64_t random=0x91a52cd73906ULL;
    for (unsigned k=0;k<500000;++k) {
        std::string key="/crc/";
        for(unsigned i=0;i<20;++i) {
            random^=random<<13;random^=random>>7;random^=random<<17;
            key+=char('a'+random%26);
        }
        uint64_t h1=key.size(),h2=0x517cc1b727220a95ULL;
        for(size_t i=0;i<key.size();i+=8) {
            uint64_t word=0;
            memcpy(&word,key.data()+i,std::min<size_t>(8,key.size()-i));
            h1=_mm_crc32_u64(h1,word);
            h2=_mm_crc32_u64(h2,word^0x9E3779B97F4A7C15ULL);
        }
        uint64_t hash=(h1<<32)|(h2&0xFFFFFFFFULL);
        if(!hash)hash=1;
        auto [at,inserted]=seen.try_emplace(hash,key);
        if(!inserted && at->second!=key) {
            EndpointTable table;
            auto a=table.intern(at->second.data(),at->second.size());
            auto b=table.intern(key.data(),key.size());
            if(a!=b)return 2;
            printf("REPRODUCED distinct valid endpoint bytes merge under the supplied dual CRC: %s %s\n",at->second.c_str(),key.c_str());
            return 0;
        }
    }
    return 3;
}
