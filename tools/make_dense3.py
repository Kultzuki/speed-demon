"""Exact direct-address narrow labels, with sparse full-width query fallback."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'research/prototypes'
source=(folder/'d-wide3-twelve.cpp').read_text()
source=source.replace('struct SparseState {','struct SparseState {\n    static constexpr uint64_t LIMIT=UINT64_MAX;\n    explicit SparseState(uint32_t=0) {}')
state=r'''
struct DenseState {
    static constexpr uint64_t LIMIT=65534;
    std::vector<uint16_t> distances;
    std::vector<uint32_t> touched;
    explicit DenseState(uint32_t n):distances(n,65535) {}
    void clear() {for (uint32_t node:touched) distances[node]=65535;touched.clear();}
    uint64_t get(uint32_t node) const {return distances[node]==65535?UINT64_MAX/2:distances[node];}
    void set(uint32_t node,uint64_t distance) {
        if (distances[node]==65535) touched.push_back(node);
        distances[node]=distance;
    }
};

'''
source=source.replace('struct Search {\n    SparseState state[2];',state+'template<class Labels=SparseState> struct SearchT {\n    Labels state[2];')
source=source.replace('explicit Search(uint32_t) {}','explicit SearchT(uint32_t n):state{Labels(n),Labels(n)} {}')
source=source.replace('if (nd<state[dir].get(v)) {','if (nd<state[dir].get(v)) {\n                    if constexpr (Labels::LIMIT<UINT64_MAX) if (nd>Labels::LIMIT) return INT64_MIN;')
source=source.replace('int main(int argc, char** argv) {','using Search=SearchT<>;\n\nint main(int argc, char** argv) {')
source=source.replace('Search search(graph.n);','SearchT<DenseState> search(graph.n);Search wide(graph.n);')
source=source.replace('answers[q] = search.run(graph, queries[q].first, queries[q].second);','answers[q] = search.run(graph, queries[q].first, queries[q].second);\n                if (answers[q]==INT64_MIN) answers[q]=wide.run(graph,queries[q].first,queries[q].second);')
(folder/'d-dense3-twelve.cpp').write_text(source)
source=source.replace('workers=std::min(12u,std::max(1u,std::thread::hardware_concurrency()));','workers=std::min(6u,std::max(1u,std::thread::hardware_concurrency()));')
(folder/'d-dense3-six.cpp').write_text(source)
