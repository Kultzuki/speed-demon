// Local floor experiment: process start, mapping, touching and teardown costs.
#include "common.hpp"
#include <cstdlib>
#include <cstring>
#include <thread>

int main(int argc, char** argv) {
    Paths paths(argc, argv);
    const char* mode = getenv("FLOOR_MODE");
    int m = mode ? atoi(mode) : 0;
    if (m == 3) { fprintf(stderr, "empty\n"); return 0; }
    if (m == 4) {
        MappedFile input(paths.data + "/requests.log");
        fprintf(stderr, "%zu\n", input.size);
        return 0;
    }
    if (m == 5) {
        MappedFile input(paths.data + "/requests.log");
        uint64_t s = 0;
        for (size_t i = 0; i < input.size; i += 4096) s += uint8_t(input.data[i]);
        fprintf(stderr, "%llu\n", (unsigned long long)s);
        _exit(0);
    }
    MappedFile input(paths.data + "/requests.log");
    unsigned threads = m == 6 ? 12 : 1;
    std::vector<uint64_t> sums(threads);
    std::vector<std::thread> pool;
    for (unsigned t = 0; t < threads; ++t) pool.emplace_back([&, t] {
        size_t begin = input.size * t / threads & ~7ull, end = input.size * (t + 1) / threads & ~7ull;
        const uint64_t* p = reinterpret_cast<const uint64_t*>(input.data + begin);
        size_t n = (end - begin) / 8;
        uint64_t a = 0, b = 0, c = 0, d = 0;
        for (size_t i = 0; i + 4 <= n; i += 4) { a += p[i]; b += p[i + 1]; c += p[i + 2]; d += p[i + 3]; }
        sums[t] = a + b + c + d;
    });
    uint64_t s = 0;
    for (auto& t : pool) t.join();
    for (auto v : sums) s += v;
    fprintf(stderr, "%llu\n", (unsigned long long)s);
    _exit(0);
}
