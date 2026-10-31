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
s = (ROOT/'research/prototypes/c-fasthash6.cpp').read_text()
s = s.replace('#include "common.hpp"', '#include "common.hpp"\n'+HEADER, 1)
s = s.replace('MappedFile regions', 'phase("map"); MappedFile regions')
s = s.replace('auto cuts = boundaries', 'phase("region-lookup"); auto cuts = boundaries')
s = s.replace('SharedNames names;', 'phase("boundaries"); SharedNames names;')
s = s.replace('for (unsigned i = 0; i < workers; ++i) {\n            for (size_t j', 'phase("parse-names"); for (unsigned i = 0; i < workers; ++i) {\n            for (size_t j')
s = s.replace('std::sort(countries.begin()', 'phase("merge"); std::sort(countries.begin()')
s = s.replace('write_output(paths.out', 'phase("sort-output"); write_output(paths.out')
(ROOT/'research/prototypes/profile-cfast.cpp').write_text(s)
