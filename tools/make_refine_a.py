"""An exact one-parse A trial retaining packed records in bounded pages."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=(root/"research/prototypes/a-scatter.cpp").read_text()
source=source.replace('#include <unordered_map>', '#include <unordered_map>\n#include <memory>')
start=source.index('struct Partial {')
stop=source.index('\nint main(',start)
part=r'''
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
'''
source=source[:start]+part+source[stop:]
source=source.replace('parts[i].parse<false>(cuts[i],cuts[i+1]);','parts[i].parse(cuts[i],cuts[i+1]);')
source=source.replace('std::vector<uint32_t> values(total);','std::unique_ptr<uint32_t[]> values(new uint32_t[total]);')
source=source.replace('parts[i].parse<true>(cuts[i],cuts[i+1],values.data());','parts[i].scatter(values.get());')
source=source.replace('auto begin=values.begin()+g.cursor, end=begin+n;','auto begin=values.get()+g.cursor, end=begin+n;')
(root/"research/prototypes/a-record-pages.cpp").write_text(source)
lookup=r'''
struct EndpointLookup {
    struct Slot {uint32_t hash=0,id=UINT32_MAX;};
    std::vector<Slot> slots=std::vector<Slot>(4096);
    uint32_t intern(std::string_view key,std::vector<Endpoint>& endpoints) {
        if (endpoints.size()*2>=slots.size()) {
            std::vector<Slot> grown(slots.size()*2);
            for (auto slot:slots) if (slot.id!=UINT32_MAX) {
                size_t at=slot.hash&(grown.size()-1);
                while (grown[at].id!=UINT32_MAX) at=(at+1)&(grown.size()-1);
                grown[at]=slot;
            }
            slots.swap(grown);
        }
        uint32_t hash=std::hash<std::string_view>()(key);
        size_t at=hash&(slots.size()-1);
        while (slots[at].id!=UINT32_MAX) {
            if (slots[at].hash==hash && endpoints[slots[at].id].name==key) return slots[at].id;
            at=(at+1)&(slots.size()-1);
        }
        uint32_t id=endpoints.size();
        endpoints.push_back(Endpoint{key});slots[at]={hash,id};return id;
    }
};
'''
source=source.replace('struct Partial {',lookup+'\nstruct Partial {')
source=source.replace('std::unordered_map<std::string_view,uint32_t> ids;\n    std::vector<Endpoint> endpoints;',
                      'EndpointLookup ids;\n    std::vector<Endpoint> endpoints;')
source=source.replace('ids.reserve(2048);endpoints.reserve(2048);','endpoints.reserve(2048);')
source=source.replace('''auto [it,fresh]=ids.try_emplace(key,endpoints.size());
            if (fresh) endpoints.push_back(Endpoint{key});
            uint32_t group=it->second*72+bucket;
            auto& g=endpoints[it->second].hours[bucket];''',
                      '''uint32_t id=ids.intern(key,endpoints);
            uint32_t group=id*72+bucket;
            auto& g=endpoints[id].hours[bucket];''')
(root/"research/prototypes/a-pages-lookup.cpp").write_text(source)
source=source.replace('size_t cursor = 0;', 'uint32_t cursor = 0;')
source=source.replace('size_t total=0;', '// The full specification has 3,100,000 lines, so uint32 cursors are exact.\n        size_t total=0;')
source=source.replace('std::vector<size_t> next(', 'std::vector<uint32_t> next(')
source=source.replace('std::vector<std::unique_ptr<uint64_t[]>> pages;',
                      'struct __attribute__((packed)) Record {uint32_t latency;uint32_t group:24;};\n    std::vector<std::unique_ptr<Record[]>> pages;')
source=source.replace('std::unique_ptr<uint64_t[]>(new uint64_t[8192])','std::unique_ptr<Record[]>(new Record[8192])')
source=source.replace('pages[count/8192][count%8192]=(uint64_t(group)<<32)|latency;', 'pages[count/8192][count%8192]={latency,group};')
source=source.replace('uint64_t record=pages[page][i];\n                uint32_t group=record>>32;\n                values[endpoints[group/72].hours[group%72].cursor++]=uint32_t(record);',
                      'auto record=pages[page][i];\n                uint32_t group=record.group;\n                values[endpoints[group/72].hours[group%72].cursor++]=record.latency;')
(root/"research/prototypes/a-pages-compact.cpp").write_text(source)
