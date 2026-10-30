"""Test private read buffers without a record-length cap or altered CSV rules."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'research/prototypes/c-compactbyte3.cpp').read_text()
old='''        for (unsigned i = 0; i < workers; ++i) threads.emplace_back([&, i] { parts[i].parse(cuts[i], cuts[i+1], lookup, countries.size(), names); });
        for (auto& thread : threads) thread.join();'''
assert source.count(old)==1
new=r'''        int fd=open((paths.data+"/records.csv").c_str(),O_RDONLY);
        if (fd<0) throw std::runtime_error("Cannot open record stream");
        for (unsigned i=0;i<workers;++i) threads.emplace_back([&,i] {
            std::vector<char> buffer(BUFFER_SIZE);
            size_t have=0,offset=cuts[i]-records.data,stop=cuts[i+1]-records.data;
            parts[i].countries.resize(countries.size());
            while (offset<stop || have) {
                if (offset<stop) {
                    size_t want=std::min(stop-offset,buffer.size()-have);
                    ssize_t got=pread(fd,buffer.data()+have,want,offset);
                    if (got<=0) throw std::runtime_error("Record stream read failed");
                    offset+=got;have+=got;
                }
                size_t limit=have;
                if (offset<stop) {
                    while (limit && !(limit<have && buffer[limit-1]=='\n' &&
                          (unsigned(buffer[limit]-'0')<10 || static_cast<unsigned char>(buffer[limit])==0xef))) --limit;
                    if (!limit) {buffer.resize(buffer.size()*2);continue;}
                }
                parts[i].parse(buffer.data(),buffer.data()+limit,lookup,countries.size(),names);
                have-=limit;memmove(buffer.data(),buffer.data()+limit,have);
            }
        });
        for (auto& thread:threads) thread.join();
        close(fd);'''
for size in [65536,262144,1048576]:
    (ROOT/f'research/prototypes/c-stream4-{size}.cpp').write_text(source.replace(old,new.replace('BUFFER_SIZE',str(size))))
