#ifndef CANDIDATE_SOURCE
#define CANDIDATE_SOURCE "../../track-d/main.cpp"
#endif
#define main candidate_main
#include CANDIDATE_SOURCE
#undef main
#include <fstream>
#include <cstdlib>

int main(int argc,char** argv) {
    if(argc!=2) return 2;
    std::ifstream input(argv[1]);
    uint32_t n,m;
    input>>n>>m;
    using Pair=std::pair<uint32_t,uint32_t>;
    std::vector<std::vector<Pair>> expected[2];
    for(auto& side:expected) side.resize(n);
    for(uint32_t i=0;i<m;++i) {
        uint32_t u,v,w;
        input>>u>>v>>w;
        if(!input) std::abort();
        expected[0][u].emplace_back(v,w);
        expected[1][v].emplace_back(u,w);
    }
    Graph graph(argv[1]);
    if(graph.n!=n) std::abort();
    for(unsigned d=0;d<2;++d) {
        if(graph.offset[d].size()!=size_t(n)+1 || graph.offset[d].back()!=m) std::abort();
        for(uint32_t u=0;u<n;++u) {
            auto& want=expected[d][u];
            std::sort(want.begin(),want.end());
            if(graph.offset[d][u+1]-graph.offset[d][u]!=want.size()) std::abort();
            std::vector<Pair> actual;
            for(uint32_t i=graph.offset[d][u];i<graph.offset[d][u+1];++i) {
                auto edge=graph.edges[d][i];
                actual.emplace_back(edge.node,edge.weight);
            }
            std::sort(actual.begin(),actual.end());
            if(actual!=want) std::abort();
        }
    }
    puts("PASS complete exact forward/reverse CSR contents, duplicate multiplicities and full uint32 weights");
}
