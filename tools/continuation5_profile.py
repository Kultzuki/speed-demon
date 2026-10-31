"""Hash-checked phase profiles of the actual incoming kernels, not submissions."""
import json
from pathlib import Path
import subprocess
import tempfile

import validate

ROOT = validate.ROOT
HEADER = '''
#include <chrono>
static auto phase_start=std::chrono::steady_clock::now();
static void phase(const char* label) {
 auto now=std::chrono::steady_clock::now();
 fprintf(stderr,"PHASE %s %.9f\\n",label,std::chrono::duration<double>(now-phase_start).count());
 phase_start=now;
}
'''

def instrument(track):
    s = (ROOT / f'research/prototypes/continuation5-start-{track}.cpp').read_text()
    s = s.replace('#include "common.hpp"', '#include "common.hpp"\n' + HEADER)
    if track == 'a':
        s = s.replace('uint32_t count=endpoints.count.load();', 'phase("parse"); uint32_t count=endpoints.count.load();')
        s = s.replace('if (fclose(file)!=0', 'phase("select-format-output"); if (fclose(file)!=0')
    if track == 'b':
        s = s.replace('unsigned workers = std::min', 'phase("queries-sample-plan"); unsigned workers = std::min')
        s = s.replace('threads.clear();', 'phase("index"); threads.clear();')
        s = s.replace('std::string output;', 'phase("evaluate"); std::string output;')
    if track == 'c':
        s = s.replace('auto cuts = boundaries', 'phase("region-lookup"); auto cuts = boundaries')
        s = s.replace('SharedNames names;', 'phase("boundaries"); SharedNames names;')
        s = s.replace('for (unsigned i = 0; i < workers; ++i) {\n            for (size_t j', 'phase("parse-names"); for (unsigned i = 0; i < workers; ++i) {\n            for (size_t j')
    if track == 'd':
        s = s.replace('Graph graph(paths.data + "/graph.txt");', 'Graph graph(paths.data + "/graph.txt"); phase("parse-csr");')
        s = s.replace('for (unsigned d=0;d<2;++d)', 'phase("count-edges"); for (unsigned d=0;d<2;++d)')
        s = s.replace('std::string output;', 'phase("search"); std::string output;')
    s = s.replace('} catch (const std::exception& e)', 'phase("cleanup"); } catch (const std::exception& e)')
    return s

def main():
    results = {}
    manifest = json.loads((ROOT / '.competition/SHA256SUMS.json').read_text())['tracks']
    with tempfile.TemporaryDirectory() as folder:
        temp = Path(folder)
        for track in 'dcba':
            source = temp / f'{track}.cpp'
            source.write_text(instrument(track))
            binary = temp / track
            subprocess.run(['g++', '-std=c++20', '-O3', '-DNDEBUG', '-pthread', '-static', '-s', '-I', str(ROOT / f'track-{track}'), str(source), '-o', str(binary)], check=True)
            results[track] = []
            for _ in range(3):
                run = subprocess.run([str(binary), '--data', f'/benchdata/{track}', '--out', folder], capture_output=True, text=True, check=True)
                assert validate.digest(temp / validate.OUTPUT[track]) == manifest[track]['expected_output_sha256'][0]
                results[track].append(run.stderr)
                print(track, run.stderr, flush=True)
    (ROOT / 'research/results/continuation5-start-profile.json').write_text(json.dumps(results, indent=2) + '\n')

if __name__ == '__main__':
    main()
