#include "common.hpp"
#include <atomic>
#include <array>
#include <bit>
#include <numeric>
#include <thread>

struct Edge { uint32_t node, weight; };
struct Graph {
    std::vector<uint32_t> offset[2];
    std::vector<Edge> edges[2];
    uint32_t n;
    explicit Graph(const std::string& path) {
        MappedFile file(path);
        const char* p = file.data;
        n = integer(p); ++p;
        uint32_t m = integer(p); ++p;
        const char* start = p;
        for (auto& offsets : offset) offsets.resize(size_t(n) + 1);
        for (uint32_t i = 0; i < m; ++i) {
            uint32_t u = integer(p); ++p;
            uint32_t v = integer(p); ++p;
            integer(p); ++p;
            ++offset[0][u + 1]; ++offset[1][v + 1];
        }
        for (int dir = 0; dir < 2; ++dir) {
            std::partial_sum(offset[dir].begin(), offset[dir].end(), offset[dir].begin());
            edges[dir].resize(m);
        }
        auto forward = offset[0], reverse = offset[1];
        p = start;
        for (uint32_t i = 0; i < m; ++i) {
            uint32_t u = integer(p); ++p;
            uint32_t v = integer(p); ++p;
            uint32_t w = integer(p); ++p;
            edges[0][forward[u]++] = {v, w};
            edges[1][reverse[v]++] = {u, w};
        }
    }
};

// Non-negative edges make extracted distances monotone. A radix heap groups
// keys by the highest bit differing from the last extracted distance.
struct RadixHeap {
    using Item = std::pair<uint64_t, uint32_t>;
    std::array<std::vector<Item>, 65> buckets;
    uint64_t last = 0;
    size_t size = 0;
    void clear() { for (auto& b : buckets) b.clear(); last = 0; size = 0; }
    bool empty() const { return size == 0; }
    void push(uint64_t key, uint32_t node) {
        buckets[std::bit_width(key ^ last)].emplace_back(key, node); ++size;
    }
    const Item& top() {
        if (buckets[0].empty()) {
            unsigned i = 1;
            while (buckets[i].empty()) ++i;
            last = UINT64_MAX;
            for (auto [key, node] : buckets[i]) last = std::min(last, key);
            for (auto item : buckets[i]) buckets[std::bit_width(item.first ^ last)].push_back(item);
            buckets[i].clear();
        }
        return buckets[0].back();
    }
    Item pop() { Item item = top(); buckets[0].pop_back(); --size; return item; }
};

struct Search {
    std::vector<uint64_t> distance[2];
    std::vector<uint32_t> stamp[2];
    RadixHeap heap[2];
    static constexpr uint64_t INF = UINT64_MAX / 2;
    explicit Search(uint32_t n) {
        for (int d = 0; d < 2; ++d) {
            distance[d].resize(n); stamp[d].resize(n);
        }
    }
    void push(int dir, uint64_t d, uint32_t v) {
        heap[dir].push(d, v);
    }
    int64_t run(const Graph& graph, uint32_t s, uint32_t t, uint32_t epoch) {
        if (s == t) return 0;
        if (graph.offset[0][s] == graph.offset[0][s + 1] || graph.offset[1][t] == graph.offset[1][t + 1]) return -1;
        for (auto& h : heap) h.clear();
        distance[0][s] = distance[1][t] = 0;
        stamp[0][s] = stamp[1][t] = epoch;
        push(0, 0, s); push(1, 0, t);
        uint64_t best = INF;
        for (;;) {
            for (int d = 0; d < 2; ++d)
                while (!heap[d].empty() && heap[d].top().first != distance[d][heap[d].top().second]) heap[d].pop();
            if (heap[0].empty() || heap[1].empty()) break;
            // Every unfinished s-t path costs at least the two frontier minima.
            if (heap[0].top().first + heap[1].top().first >= best) break;
            int dir = heap[0].top().first <= heap[1].top().first ? 0 : 1;
            auto [du, u] = heap[dir].pop();
            if (stamp[1 - dir][u] == epoch) best = std::min(best, du + distance[1 - dir][u]);
            for (uint32_t i = graph.offset[dir][u]; i < graph.offset[dir][u + 1]; ++i) {
                auto [v, w] = graph.edges[dir][i];
                uint64_t nd = du + w;
                if (stamp[dir][v] != epoch || nd < distance[dir][v]) {
                    stamp[dir][v] = epoch; distance[dir][v] = nd;
                    push(dir, nd, v);
                    if (stamp[1 - dir][v] == epoch) best = std::min(best, nd + distance[1 - dir][v]);
                }
            }
        }
        return best == INF ? -1 : static_cast<int64_t>(best);
    }
};

int main(int argc, char** argv) {
    try {
        Paths paths(argc, argv);
        Graph graph(paths.data + "/graph.txt");
        MappedFile file(paths.data + "/queries.txt");
        std::vector<std::pair<uint32_t, uint32_t>> queries;
        const char* p = file.data;
        while (p < file.end()) {
            uint32_t s = integer(p); ++p;
            uint32_t t = integer(p); ++p;
            queries.emplace_back(s, t);
        }
        std::vector<int64_t> answers(queries.size());
        std::atomic<size_t> next{0};
        unsigned workers = std::min(6u, std::max(1u, std::thread::hardware_concurrency()));
        if (queries.size() < 100) workers = 1;
        std::vector<std::thread> threads;
        for (unsigned i = 0; i < workers; ++i) threads.emplace_back([&] {
            Search search(graph.n);
            for (;;) {
                size_t q = next.fetch_add(1, std::memory_order_relaxed);
                if (q >= queries.size()) break;
                answers[q] = search.run(graph, queries[q].first, queries[q].second, q + 1);
            }
        });
        for (auto& thread : threads) thread.join();
        std::string output;
        for (auto answer : answers) { number(output, answer); output += '\n'; }
        write_output(paths.out + "/distances.txt", output);
    } catch (const std::exception& e) { fprintf(stderr, "%s\n", e.what()); return 1; }
}
