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
    std::vector<uint32_t> remap;
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
    void reorder() {
        remap.assign(n, UINT32_MAX);
        std::vector<uint32_t> order;
        order.reserve(n);
        for (uint32_t root = 0; root < n; ++root) if (remap[root] == UINT32_MAX) {
            remap[root] = order.size(); order.push_back(root);
            for (size_t head = order.size() - 1; head < order.size(); ++head) {
                uint32_t u = order[head];
                for (uint32_t i = offset[0][u]; i < offset[0][u + 1]; ++i) {
                    uint32_t v = edges[0][i].node;
                    if (remap[v] == UINT32_MAX) { remap[v] = order.size(); order.push_back(v); }
                }
            }
        }
        for (int dir = 0; dir < 2; ++dir) {
            std::vector<uint32_t> reordered_offsets(size_t(n) + 1);
            std::vector<Edge> reordered_edges(edges[dir].size());
            uint32_t position = 0;
            for (uint32_t u = 0; u < n; ++u) {
                reordered_offsets[u] = position;
                uint32_t original = order[u];
                for (uint32_t i = offset[dir][original]; i < offset[dir][original + 1]; ++i) {
                    const auto& edge = edges[dir][i];
                    reordered_edges[position++] = {remap[edge.node], edge.weight};
                }
            }
            reordered_offsets[n] = position;
            offset[dir].swap(reordered_offsets); edges[dir].swap(reordered_edges);
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
    std::vector<uint64_t> state[2];
    uint64_t mask, epoch = 0;
    RadixHeap heap[2];
    static constexpr uint64_t INF = UINT64_MAX / 2;
    explicit Search(uint32_t n) {
        // Every accepted shortest label has a simple path of at most n-1
        // uint32-weight edges. Remaining upper bits hold a generation tag.
        unsigned bits = std::max(1u, static_cast<unsigned>(std::bit_width(uint64_t(n - 1) * UINT32_MAX)));
        mask = (uint64_t(1) << bits) - 1;
        for (auto& side : state) side.resize(n);
    }
    void push(int dir, uint64_t d, uint32_t v) {
        heap[dir].push(d, v);
    }
    int64_t run(const Graph& graph, uint32_t s, uint32_t t) {
        if (s == t) return 0;
        if (graph.offset[0][s] == graph.offset[0][s + 1] || graph.offset[1][t] == graph.offset[1][t + 1]) return -1;
        for (auto& h : heap) h.clear();
        epoch += mask + 1;
        if (!epoch) {
            for (auto& side : state) std::fill(side.begin(), side.end(), 0);
            epoch = mask + 1;
        }
        state[0][s] = state[1][t] = epoch;
        push(0, 0, s); push(1, 0, t);
        uint64_t best = INF;
        for (;;) {
            for (int d = 0; d < 2; ++d)
                while (!heap[d].empty() && heap[d].top().first != (state[d][heap[d].top().second] & mask)) heap[d].pop();
            if (heap[0].empty() || heap[1].empty()) break;
            // Every unfinished s-t path costs at least the two frontier minima.
            if (heap[0].top().first + heap[1].top().first >= best) break;
            int dir = heap[0].top().first <= heap[1].top().first ? 0 : 1;
            auto [du, u] = heap[dir].pop();
            if ((state[1 - dir][u] & ~mask) == epoch) best = std::min(best, du + (state[1 - dir][u] & mask));
            for (uint32_t i = graph.offset[dir][u]; i < graph.offset[dir][u + 1]; ++i) {
                auto [v, w] = graph.edges[dir][i];
                uint64_t nd = du + w;
                if ((state[dir][v] & ~mask) != epoch || nd < (state[dir][v] & mask)) {
                    state[dir][v] = epoch | nd;
                    push(dir, nd, v);
                    if ((state[1 - dir][v] & ~mask) == epoch) best = std::min(best, nd + (state[1 - dir][v] & mask));
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
        graph.reorder();
        MappedFile file(paths.data + "/queries.txt");
        std::vector<std::pair<uint32_t, uint32_t>> queries;
        const char* p = file.data;
        while (p < file.end()) {
            uint32_t s = integer(p); ++p;
            uint32_t t = integer(p); ++p;
            queries.emplace_back(graph.remap[s], graph.remap[t]);
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
                answers[q] = search.run(graph, queries[q].first, queries[q].second);
            }
        });
        for (auto& thread : threads) thread.join();
        std::string output;
        for (auto answer : answers) { number(output, answer); output += '\n'; }
        write_output(paths.out + "/distances.txt", output);
    } catch (const std::exception& e) { fprintf(stderr, "%s\n", e.what()); return 1; }
}
