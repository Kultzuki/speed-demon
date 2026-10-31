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
s = (ROOT/'research/prototypes/a-fastpath6.cpp').read_text()
s = s.replace('#include "common.hpp"', '#include "common.hpp"\n'+HEADER, 1)
s = s.replace('EndpointTable endpoints;', 'phase("cuts"); EndpointTable endpoints;')
s = s.replace('uint32_t count=endpoints.count.load();', 'phase("parse"); uint32_t count=endpoints.count.load();')
s = s.replace('std::array<std::string,72> outputs;', 'phase("sort-names"); std::array<std::string,72> outputs;')
s = s.replace('if (fclose(file)!=0', 'phase("select-format-output"); if (fclose(file)!=0')
(ROOT/'research/prototypes/profile-afast.cpp').write_text(s)
