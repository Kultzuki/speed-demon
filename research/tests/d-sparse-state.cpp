#define main candidate_main
#include "../../track-d/main.cpp"
#undef main
#include <cstdlib>

int main(int argc,char** argv) {
    if (argc!=2) return 2;
    SparseState state;
    state.clear();
    for (uint32_t i=0;i<100000;++i) state.set(i,8589934590ULL+i);
    for (uint32_t i=0;i<100000;++i) if (state.get(i)!=8589934590ULL+i) std::abort();
    state.clear();
    for (uint32_t i=0;i<100000;++i) if (state.get(i)!=Search::INF) std::abort();
    for (auto& slot:state.slots) slot={1,0,1};
    state.epoch=UINT32_MAX;
    state.clear();
    if (state.get(0)!=Search::INF || state.epoch!=1) std::abort();
    state.set(0,UINT64_C(1740511)*UINT32_MAX);
    if (state.get(0)!=UINT64_C(1740511)*UINT32_MAX) std::abort();
    for (uint32_t n:{1u,2u,65536u,65537u,1740512u}) {
        EdgeStore edges;edges.configure(n);edges.resize(5);
        uint32_t weights[]={0,edges.mask-1,edges.mask,edges.mask+1,UINT32_MAX};
        for (uint32_t i=0;i<5;++i) edges.set(i,{n-1,weights[i]});
        edges.finish();
        for (uint32_t i=0;i<5;++i) if (edges[i].node!=n-1 || edges[i].weight!=weights[i]) std::abort();
    }
    Graph graph(argv[1]);Search search(graph.n);
    struct Case {uint32_t s,t;int64_t expected;};
    Case cases[]={{0,2,7},{4,4,0},{3,4,0},{4,6,8589934590LL},{6,0,-1},{0,6,8589934594LL},{7,7,0}};
    for (unsigned repeat=0;repeat<100;++repeat) for (auto c:cases)
        if (search.run(graph,c.s,c.t)!=c.expected) std::abort();
    puts("PASS D sparse rehash/membership/wrap, full-width overflow edges, repeated wide/zero/unreachable searches");
}
