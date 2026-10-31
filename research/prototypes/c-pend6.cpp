#include "common.hpp"
#include <array>
#include <limits>
#include <unordered_map>
#include <thread>
#include <mutex>
#include <immintrin.h>
#include <bit>
#include <atomic>
#include <memory>

static inline size_t fast_hash(std::string_view name) {
    const char* p=name.data();
    size_t n=name.size();
    uint64_t a=0,b=0;
    if (n>=8) {__builtin_memcpy(&a,p,8);__builtin_memcpy(&b,p+n-8,8);}
    else {for (size_t i=0;i<n;++i) a=a<<8|uint8_t(p[i]); b=a;}
    uint64_t h=(a^std::rotl(b,29))+(n*0x9E3779B97F4A7C15ull);
    h^=h>>30;h*=0xBF58476D1CE4E5B9ull;h^=h>>27;h*=0x94D049BB133111EBull;h^=h>>31;
    return size_t(h);
}
struct Field {
    std::string_view value;
    size_t bytes;
};

// memchr jumps between quotes. Embedded LF and commas are ordinary bytes here.
Field text_field(const char*& p, const char* end, std::string* decoded) {
    const char* start = p;
    if (*p != '"') {
        while (p < end && *p != ',') ++p;
        return {std::string_view(start, p - start), size_t(p - start)};
    }
    start = ++p;
    const char* segment = p;
    size_t escaped = 0;
    if (decoded) decoded->clear();
    for (;;) {
        p = static_cast<const char*>(memchr(p, '"', end - p));
        if (!p) throw std::runtime_error("Unclosed CSV quote");
        if (p + 1 < end && p[1] == '"') {
            if (decoded) decoded->append(segment, p + 1);
            ++escaped;
            p += 2;
            segment = p;
        } else {
            size_t bytes = p - start - escaped;
            std::string_view value(start, p - start);
            if (escaped && decoded) { decoded->append(segment, p); value = *decoded; }
            ++p;
            return {value, bytes};
        }
    }
}



// Nodes never move. Release publication makes immutable names/links visible;
// an atomic membership update elects exactly one distinct-count increment.
struct SharedNames {
    struct Node {
        Node* next;
        size_t length;
        std::string_view name() const {return {reinterpret_cast<const char*>(this)+sizeof(Node),length};}
        std::atomic<uint64_t> membership[4]{};
    };
    struct alignas(64) Shard {
        std::mutex mutex;
        std::array<std::atomic<Node*>,512> heads{};
        std::vector<std::unique_ptr<char[]>> arenas;
        size_t used=8192;
        Node* insert(std::string_view name,Node* next) {
            size_t bytes=sizeof(Node)+name.size();
            size_t at=(used+alignof(Node)-1)&~(alignof(Node)-1);
            if (arenas.empty() || at+bytes>8192) {
                arenas.push_back(std::make_unique<char[]>(std::max<size_t>(8192,bytes)));
                at=0;
            }
            char* data=arenas.back().get()+at;
            auto* node=new(data) Node{next,name.size()};
            memcpy(data+sizeof(Node),name.data(),name.size());
            used=at+bytes;
            return node;
        }
    };
    std::array<Shard,256> shards;

    size_t prefetch(std::string_view name) {
        size_t hash=fast_hash(name);
        auto& head=shards[(hash>>32)&255].heads[hash&511];
        __builtin_prefetch(&head,0,3);
        if (auto* node=head.load(std::memory_order_acquire)) __builtin_prefetch(node,0,3);
        return hash;
    }
    bool add(std::string_view name,uint16_t country) {return add(name,country,prefetch(name));}
    bool add(std::string_view name,uint16_t country,size_t hash) {
        auto& shard=shards[(hash>>32)&255];
        auto& head=shard.heads[hash&511];
        auto find=[&](Node* node) {
            while (node && (node->name()!=name)) node=node->next;
            return node;
        };
        Node* node=find(head.load(std::memory_order_acquire));
        if (!node) {
            std::lock_guard<std::mutex> lock(shard.mutex);
            auto first=head.load(std::memory_order_relaxed);
            node=find(first);
            if (!node) {
                node=shard.insert(name,first);
                head.store(node,std::memory_order_release);
            }
        }
        uint64_t bit=uint64_t(1)<<(country%64);
        auto& word=node->membership[country/64];
        if (word.load(std::memory_order_relaxed)&bit) return false;
        return !(word.fetch_or(bit,std::memory_order_relaxed)&bit);
    }
};

struct Country {
    std::string key;
    uint64_t count = 0, id_sum = 0, distinct = 0, name_bytes = 0, note_bytes = 0;
    int64_t sum = 0, minimum = INT64_MAX, maximum = INT64_MIN;
};

void money(std::string& out, int64_t value) {
    if (value < 0) { out += '-'; value = -value; }
    number(out, value / 100);
    out += '.';
    out += char('0' + value % 100 / 10);
    out += char('0' + value % 10);
}

struct Partial {
    std::vector<Country> countries;
    template<class Id> void parse(const char* begin, const char* end, const std::vector<Id>& lookup, size_t count, SharedNames& names) {
        countries.resize(count);
        const char* p = begin;
        struct Pending {std::string scratch;std::string_view name;uint16_t country;size_t hash;};
        std::array<Pending,6> pending;
        size_t serial=0;
        auto retire=[&](Pending& old) {countries[old.country].distinct+=names.add(old.name,old.country,old.hash);};
        while (p < end) {
            if (static_cast<unsigned char>(*p) == 0xef) p += 3;
            uint64_t id = integer(p);
            ++p;
            auto& next=pending[serial%pending.size()];
            if (serial>=pending.size()) retire(next);
            ++serial;
            Field name = text_field(p, end, &next.scratch);
            ++p;
            Field note = text_field(p, end, nullptr);
            ++p;
            uint32_t region = integer(p);
            ++p;
            bool negative = *p == '-';
            p += negative;
            int64_t amount = integer(p) * 100;
            ++p;
            amount += (p[0] - '0') * 10 + p[1] - '0';
            p += 2;
            if (p < end && *p == '\r') ++p;
            if (p < end && *p == '\n') ++p;
            if (negative) amount = -amount;
            uint16_t country = region < lookup.size() ? lookup[region] : 0;
            auto& group = countries[country];
            next.name=name.value;next.country=country;next.hash=names.prefetch(name.value);
            ++group.count;
            group.id_sum += id;
            group.sum += amount;
            group.minimum = std::min(group.minimum, amount);
            group.maximum = std::max(group.maximum, amount);
            group.name_bytes += name.bytes;
            group.note_bytes += note.bytes;
        }
        for (size_t i=serial>pending.size()?serial-pending.size():0;i<serial;++i) retire(pending[i%pending.size()]);
    }
};



// Section 2.2: names contain no LF; a note contains only lowercase words,
// spaces, commas, quotes and LF. Thus a digit/BOM after LF begins a record.
std::vector<const char*> boundaries(const char* begin,const char* end,unsigned workers) {
    std::vector<const char*> result(workers+1,end);
    result[0]=begin;
    for (unsigned i=1;i<workers;++i) {
        const char* p=begin+(end-begin)*i/workers;
        while (p<end && !(p>begin && p[-1]=='\n' &&
               ((unsigned(*p-'0')<10) || static_cast<unsigned char>(*p)==0xef))) ++p;
        result[i]=p;
    }
    return result;
}

int main(int argc, char** argv) {
    try {
        Paths paths(argc, argv);
        MappedFile regions(paths.data + "/regions.csv"), records(paths.data + "/records.csv");
        std::vector<Country> countries(1);
        countries[0].key = "_UNMATCHED";
        std::unordered_map<std::string_view, uint16_t> country_ids;
        // The lookup has IDs <= 999999. Out-of-range record IDs are unmatched.
        std::vector<uint8_t> lookup(1000000);
        const char* p = regions.data;
        while (p < regions.end() && *p++ != '\n') {}
        while (p < regions.end()) {
            uint32_t region = integer(p);
            ++p;
            std::string_view key(p, 3);
            auto [it, inserted] = country_ids.try_emplace(key, countries.size());
            if (inserted) { countries.emplace_back(); countries.back().key = key; }
            if (region >= lookup.size()) lookup.resize(size_t(region) + 1);
            lookup[region] = it->second;
            p += 4;
        }
        p = records.data;
        while (p < records.end() && *p++ != '\n') {}
        unsigned workers = std::min(12u, std::max(1u, std::thread::hardware_concurrency()));
        if (records.size < 2 * 1024 * 1024) workers = 1;
        auto cuts = boundaries(p, records.end(), workers);
        SharedNames names;
        std::vector<Partial> parts(workers);
        std::vector<std::thread> threads;
        for (unsigned i = 0; i < workers; ++i) threads.emplace_back([&, i] { parts[i].parse(cuts[i], cuts[i+1], lookup, countries.size(), names); });
        for (auto& thread : threads) thread.join();
        for (unsigned i = 0; i < workers; ++i) {
            for (size_t j = 0; j < countries.size(); ++j) {
                const auto& from = parts[i].countries[j]; auto& to = countries[j];
                to.count += from.count; to.id_sum += from.id_sum; to.sum += from.sum; to.distinct += from.distinct;
                to.minimum = std::min(to.minimum, from.minimum); to.maximum = std::max(to.maximum, from.maximum);
                to.name_bytes += from.name_bytes; to.note_bytes += from.note_bytes;
            }
        }
        std::sort(countries.begin(), countries.end(), [](auto& a, auto& b) { return a.key < b.key; });
        std::string output;
        for (const auto& g : countries) {
            if (!g.count) continue;
            output += g.key;
            for (auto value : {g.count, g.id_sum}) { output += ' '; number(output, value); }
            for (auto value : {g.sum, g.minimum, g.maximum}) { output += ' '; money(output, value); }
            for (auto value : {g.distinct, g.name_bytes, g.note_bytes}) { output += ' '; number(output, value); }
            output += '\n';
        }
        write_output(paths.out + "/aggregates.txt", output);
    } catch (const std::exception& e) { fprintf(stderr, "%s\n", e.what()); return 1; }
}
