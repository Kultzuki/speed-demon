"""Retain the supplied query-aware CSR idea with checked width instantiations."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'research/supplied-fifth/track-b.cpp').read_text()
source=source.replace('#include <algorithm>','#include "common.hpp"\n#include <algorithm>\n#include <type_traits>')
source=source.replace('struct Index {','template<class Doc,class Offset> struct Index {')
source=source.replace('std::unique_ptr<uint16_t[]> post;', 'std::unique_ptr<Doc[]> post;')
source=source.replace('std::vector<u32> text;', 'std::vector<Offset> text;')
source=source.replace('class BlockList {','template<class Doc> class BlockList {\n    static constexpr size_t STRIDE=sizeof(Doc)==2?3:8;\n    using Packed=std::conditional_t<sizeof(Doc)==2,u32,u64>;')
source=source.replace('3 * BLOCK + 1','STRIDE * BLOCK + sizeof(Packed)')
source=source.replace('void push(u32 x)', 'void push(Packed x)')
source=source.replace('memcpy(cur_ + 3 * fill_++, &x, 4);','memcpy(cur_ + STRIDE * fill_++, &x, sizeof(x));')
source=source.replace('''                u32 x;
                memcpy(&x, blocks_[b] + 3 * i, 4);
                f(x & 0xFFFFFF);''','''                Packed x;
                memcpy(&x, blocks_[b] + STRIDE * i, sizeof(x));
                if constexpr(sizeof(Doc)==2) x&=0xFFFFFF;
                f(x);''')
source=source.replace('constexpr u32 BUCKET_BITS = 9, DOC_BITS = 15;', 'constexpr u32 BUCKET_BITS = 9;')
source=source.replace('Index build_index(', 'template<class Doc,class Offset> Index<Doc,Offset> build_index(')
source=source.replace('    Index ix;', '    constexpr u32 DOC_BITS=sizeof(Doc)==2?15:32;\n    Index<Doc,Offset> ix;')
source=source.replace('std::vector<std::vector<BlockList>> seen', 'std::vector<std::vector<BlockList<Doc>>> seen')
source=source.replace('(id & ((1u << BUCKET_BITS) - 1)) << DOC_BITS | (doc - first)', 'u64(id & ((1u << BUCKET_BITS) - 1)) << DOC_BITS | (doc - first)')
source=source.replace('if (docs >> DOC_BITS)', 'if (u64(docs) > (u64(1) << DOC_BITS))')
source=source.replace('new uint16_t[total]', 'new Doc[total]')
source=source.replace('seen[t][b].drain([&](u32 x)', 'seen[t][b].drain([&](u64 x)')
source=source.replace('x & ((1u << DOC_BITS) - 1)', 'x & ((u64(1) << DOC_BITS) - 1)')
source=source.replace('class Solver {', 'template<class Doc,class Offset> class Solver {')
source=source.replace('const Index&', 'const Index<Doc,Offset>&')
# The original main becomes the same templated entry interface as our old B.
source=source.replace('int main() {','template<class Doc,class Offset> void solve(const Paths& paths) {')
source=source.replace('File qf = map_file("/data/queries.txt");','File qf = map_file(paths.data+"/queries.txt");')
source=source.replace('File df = map_file("/data/docs.txt");', '''File df = map_file(paths.data+"/docs.txt");
    if constexpr(sizeof(Offset)==4) {
        if(df.size>UINT32_MAX) return solve<Doc,uint64_t>(paths);
    }
    if constexpr(sizeof(Doc)==2) {
        u32 docs=0;
        if(df.size) {
            size_t at=df.size-1;
            while(at && df.data[at-1]!='\\n') --at;
            docs=parse_id(df.data+at)+1;
        }
        u32 first=0;
        for(int t=1;t<=nthreads;++t) {
            size_t at=df.size*t/nthreads;
            while(at && at<df.size && df.data[at-1]!='\\n') ++at;
            u32 stop=at==df.size?docs:parse_id(df.data+at);
            if(u64(stop)-first>32768) return solve<uint32_t,Offset>(paths);
            first=stop;
        }
    }''')
source=source.replace('Index ix = build_index(df, terms, queries.terms, nthreads);','auto ix = build_index<Doc,Offset>(df, terms, queries.terms, nthreads);')
source=source.replace('Solver solver(ix, terms, df);','Solver<Doc,Offset> solver(ix, terms, df);')
source=source.replace('fopen("/out/results.txt", "wb")','fopen((paths.out+"/results.txt").c_str(), "wb")')
source=source.replace('if (!f) { perror("/out/results.txt"); return 1; }','if (!f) throw std::runtime_error("Cannot create results.txt");')
source=source.replace('    return 0;\n}', '    return;\n}')
source+='''
int main(int argc,char** argv) {
    try {Paths paths(argc,argv);solve<uint16_t,uint32_t>(paths);}
    catch(const std::exception& e) {fprintf(stderr,"%s\\n",e.what());return 1;}
}
'''
(ROOT/'research/prototypes/b-csr5.cpp').write_text(source,encoding='utf-8',newline='\n')
print('Created exact CSR/list/bitmap B with 15/32-bit stream and 32/64-bit offset dispatch.')
