#define main candidate_main
#ifndef CANDIDATE_SOURCE
#define CANDIDATE_SOURCE "../prototypes/d-packed-bfs.cpp"
#endif
#include CANDIDATE_SOURCE
#undef main
#include <cstdlib>

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    Graph graph(argv[1]);
    graph.reorder();
    Search search(graph.n);
    struct Case { uint32_t s, t; int64_t expected; };
    Case cases[] = {{0, 2, 7}, {4, 4, 0}, {3, 4, 0}, {4, 6, 8589934590LL},
                    {6, 0, -1}, {0, 6, 8589934594LL}, {7, 7, 0}};
    for (int round = 0; round < 3; ++round) {
        if (round) {
            // Seed ancient entries with the generation that will be reused.
            for (auto& side : search.state) std::fill(side.begin(), side.end(), search.mask + 1);
            search.epoch = UINT64_MAX & ~search.mask;
        }
        for (auto c : cases) {
            auto actual = search.run(graph, graph.remap[c.s], graph.remap[c.t]);
            if (actual != c.expected) {
                fprintf(stderr, "round=%d %u->%u expected=%lld actual=%lld\n", round, c.s, c.t,
                        static_cast<long long>(c.expected), static_cast<long long>(actual));
                std::abort();
            }
        }
    }
    Search full(1740512);
    if (full.mask < uint64_t(1740511) * UINT32_MAX || std::bit_width(full.mask) != 53) std::abort();
    puts("PASS D generation wrap, 53-bit distance budget, relabel and wide distances");
}
