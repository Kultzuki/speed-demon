"""Preserve separate C experiments for exact concurrent names and boundaries."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "track-c/main.cpp").read_text()
start = source.index("// Compact names")
stop = source.index("struct Country")
names = r'''
// Nodes never move. Release publication makes immutable names/links visible;
// an atomic membership update elects exactly one distinct-count increment.
struct SharedNames {
    struct Node {
        Node* next;
        size_t hash;
        std::string_view name;
        std::atomic<uint64_t> membership[4]{};
    };
    struct alignas(64) Shard {
        std::mutex mutex;
        std::array<std::atomic<Node*>,512> heads{};
        std::vector<std::unique_ptr<char[]>> arenas;
        size_t used=65536;
        Node* insert(std::string_view name,size_t hash,Node* next) {
            size_t bytes=sizeof(Node)+name.size();
            size_t at=(used+alignof(Node)-1)&~(alignof(Node)-1);
            if (arenas.empty() || at+bytes>65536) {
                arenas.push_back(std::make_unique<char[]>(std::max<size_t>(65536,bytes)));
                at=0;
            }
            char* data=arenas.back().get()+at;
            auto* node=new(data) Node{next,hash,std::string_view(data+sizeof(Node),name.size())};
            memcpy(data+sizeof(Node),name.data(),name.size());
            used=at+bytes;
            return node;
        }
    };
    std::array<Shard,256> shards;
    bool add(std::string_view name,uint16_t country) {
        size_t hash=std::hash<std::string_view>()(name);
        auto& shard=shards[(hash>>32)&255];
        auto& head=shard.heads[hash&511];
        auto find=[&](Node* node) {
            while (node && (node->hash!=hash || node->name!=name)) node=node->next;
            return node;
        };
        Node* node=find(head.load(std::memory_order_acquire));
        if (!node) {
            std::lock_guard<std::mutex> lock(shard.mutex);
            auto first=head.load(std::memory_order_relaxed);
            node=find(first);
            if (!node) {
                node=shard.insert(name,hash,first);
                head.store(node,std::memory_order_release);
            }
        }
        uint64_t bit=uint64_t(1)<<(country%64);
        auto& word=node->membership[country/64];
        if (word.load(std::memory_order_relaxed)&bit) return false;
        return !(word.fetch_or(bit,std::memory_order_relaxed)&bit);
    }
};

'''
source = source[:start]+names+source[stop:]
source = source.replace('#include <bit>', '#include <bit>\n#include <atomic>\n#include <memory>')
(root / "research/prototypes/c-concurrent.cpp").write_text(source)
start = source.index('// A doubled quote')
stop = source.index('int main(',start)
cuts = r'''
__attribute__((target("avx2,popcnt")))
bool quote_parity(const char* p,const char* end) {
    unsigned parity=0;
    while (end-p>=32) {
        auto bytes=_mm256_loadu_si256(reinterpret_cast<const __m256i*>(p));
        parity^=std::popcount(uint32_t(_mm256_movemask_epi8(_mm256_cmpeq_epi8(bytes,_mm256_set1_epi8('"')))))&1;
        p+=32;
    }
    while (p<end) parity^=*p++=='"';
    return parity;
}

// First determine the quote parity of disjoint byte ranges in parallel.
// Prefix parities then give the exact CSV state at every proposed cut.
std::vector<const char*> boundaries(const char* begin,const char* end,unsigned workers) {
    std::vector<const char*> result(workers+1,end);
    result[0]=begin;
    if (workers==1) return result;
    std::vector<unsigned char> parity(workers);
    std::vector<std::thread> threads;
    for (unsigned i=0;i<workers;++i) threads.emplace_back([&,i] {
        parity[i]=quote_parity(begin+(end-begin)*i/workers,begin+(end-begin)*(i+1)/workers);
    });
    for (auto& t:threads) t.join();
    bool quoted=false;
    for (unsigned i=1;i<workers;++i) {
        quoted^=parity[i-1];
        bool inside=quoted;
        const char* p=begin+(end-begin)*i/workers;
        while (p<end) {
            inside^=*p=='"';
            if (*p++=='\n' && !inside) break;
        }
        result[i]=p;
    }
    return result;
}

'''
source = source[:start]+cuts+source[stop:]
(root / "research/prototypes/c-concurrent-cuts.cpp").write_text(source)
source=source.replace('65536','8192')
(root / "research/prototypes/c-concurrent-small.cpp").write_text(source)
source=source.replace('Field name = text_field(p, end, &scratch);','Field name = text_field(p, end, nullptr);')
source=source.replace('size_t bytes=sizeof(Node)+name.size();','size_t bytes=sizeof(Node);')
source=source.replace('auto* node=new(data) Node{next,hash,std::string_view(data+sizeof(Node),name.size())};\n            memcpy(data+sizeof(Node),name.data(),name.size());',
                      'auto* node=new(data) Node{next,hash,name};')
source=source.replace('// Nodes never move.', '''// CSV's internal quoted representation doubles every quote; unquoted fields
// cannot contain quotes. Thus these raw internal slices are exact equality
// keys, including quoted/unquoted empty values. Decoded byte lengths stay exact.
// Nodes and the mapped name slices never move.''')
(root / "research/prototypes/c-raw-names.cpp").write_text(source)
