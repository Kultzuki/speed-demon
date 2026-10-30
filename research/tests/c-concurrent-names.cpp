#define main candidate_main
#include "../../track-c/main.cpp"
#undef main
#include <cstdlib>

int main() {
    SharedNames catalog;
    std::vector<std::string> names;
    for (unsigned i=0;i<256;++i) names.push_back("same exact name "+std::to_string(i));
    std::atomic<uint64_t> fresh{0};
    std::vector<std::thread> threads;
    for (unsigned t=0;t<12;++t) threads.emplace_back([&,t] {
        uint64_t local=0;
        for (unsigned c=0;c<241;++c) for (unsigned i=0;i<256;++i)
            local+=catalog.add(names[(i+t)%256],(c+t)%241);
        fresh.fetch_add(local,std::memory_order_relaxed);
    });
    for (auto& t:threads) t.join();
    if (fresh!=uint64_t(256)*241) std::abort();
    if (!catalog.add("",255) || catalog.add("",255)) std::abort();
    puts("PASS C twelve-way concurrent publication and exactly-once country membership");
}
