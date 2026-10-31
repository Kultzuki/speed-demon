from pathlib import Path
ROOT = Path('.')
HEADER = '''
#include <chrono>
static auto phase_start=std::chrono::steady_clock::now();
static void phase(const char* label) {
 auto now=std::chrono::steady_clock::now();
 fprintf(stderr,"PHASE %s %.9f\\n",label,std::chrono::duration<double>(now-phase_start).count());
 phase_start=now;
}
'''
s = (ROOT/'research/prototypes/b-state7.cpp').read_text()
s = s.replace('#include "common.hpp"', '#include "common.hpp"\n'+HEADER, 1)
s = s.replace('TermTable terms;\n    Queries queries', 'phase("queries-start"); TermTable terms;\n    Queries queries')
s = s.replace('auto ix = build_index', 'phase("queries"); auto ix = build_index')
s = s.replace('// Turn the per-thread counts', 'phase("index-scan");\n    // Turn the per-thread counts')
s = s.replace('ix.seg_end = std::move(count);', 'ix.seg_end = std::move(count);\n    phase("scatter");')
s = s.replace('// Answer queries in parallel', 'phase("index-finish");\n    // Answer queries in parallel')
s = s.replace('std::string out;\n    out.reserve', 'phase("evaluate"); std::string out;\n    out.reserve')
s = s.replace('return;\n}\nint main', 'phase("output"); return;\n}\nint main')
(ROOT/'research/prototypes/profile-state7.cpp').write_text(s)
