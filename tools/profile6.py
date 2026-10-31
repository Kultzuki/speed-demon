"""Instrument current kernels for local phase diagnostics only."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
    s = (ROOT / f'track-{track}/main.cpp').read_text()
    s = s.replace('#include "common.hpp"', '#include "common.hpp"\n' + HEADER, 1)
    if track == 'a':
        s = s.replace('EndpointTable endpoints;', 'phase("cuts"); EndpointTable endpoints;')
        s = s.replace('uint32_t count=endpoints.count.load();', 'phase("parse"); uint32_t count=endpoints.count.load();')
        s = s.replace('std::array<std::string,72> outputs;', 'phase("sort-names"); std::array<std::string,72> outputs;')
        s = s.replace('if (fclose(file)!=0', 'phase("select-format-output"); if (fclose(file)!=0')
    if track == 'b':
        s = s.replace('TermTable terms;\n    Queries queries', 'phase("queries-start"); TermTable terms;\n    Queries queries')
        s = s.replace('auto ix = build_index', 'phase("queries"); auto ix = build_index')
        s = s.replace('// Turn the per-thread counts', 'phase("index-scan");\n    // Turn the per-thread counts')
        s = s.replace('ix.seg_end = std::move(count);', 'ix.seg_end = std::move(count);\n    phase("scatter");')
        s = s.replace('// Answer queries in parallel', 'phase("index-finish");\n    // Answer queries in parallel')
        s = s.replace('std::string out;\n    out.reserve', 'phase("evaluate"); std::string out;\n    out.reserve')
        s = s.replace('return;\n}\nint main', 'phase("output"); return;\n}\nint main')
    if track == 'c':
        s = s.replace('MappedFile regions', 'phase("map"); MappedFile regions')
        s = s.replace('auto cuts = boundaries', 'phase("region-lookup"); auto cuts = boundaries')
        s = s.replace('SharedNames names;', 'phase("boundaries"); SharedNames names;')
        s = s.replace('for (unsigned i = 0; i < workers; ++i) {\n            for (size_t j', 'phase("parse-names"); for (unsigned i = 0; i < workers; ++i) {\n            for (size_t j')
        s = s.replace('std::sort(countries.begin()', 'phase("merge"); std::sort(countries.begin()')
        s = s.replace('write_output(paths.out', 'phase("sort-output"); write_output(paths.out')
    if track == 'd':
        s = s.replace('Graph graph(paths.data + "/graph.txt");', 'Graph graph(paths.data + "/graph.txt"); phase("parse-csr");')
        s = s.replace('MappedFile file(paths.data + "/queries.txt");', 'MappedFile file(paths.data + "/queries.txt"); phase("map-queries");')
        s = s.replace('std::vector<int64_t> answers', 'phase("parse-queries"); std::vector<int64_t> answers')
        s = s.replace('std::string output;', 'phase("search"); std::string output;')
        s = s.replace('write_output(paths.out', 'phase("format"); write_output(paths.out')
    return s


def main():
    tracks = sys.argv[1] if len(sys.argv) > 1 else 'b'
    out = ROOT / 'build/bench6'
    out.mkdir(parents=True, exist_ok=True)
    for track in tracks:
        src = ROOT / f'research/prototypes/continuation6-profile-{track}.cpp'
        src.write_text(instrument(track))
        name = f'profile-{track}'
        extra = ['-march=x86-64-v3'] if track == 'b' else []
        subprocess.run(['docker', 'exec', 'codescythe-research', 'g++', '-std=c++20', '-O3', '-DNDEBUG'] + extra + [
                        '-pthread', '-static', '-s', '-I', f'/work/track-{track}', f'/work/{src.relative_to(ROOT).as_posix()}',
                        '-o', f'/work/build/bench6/{name}'], check=True)
        print('built', name, flush=True)


if __name__ == '__main__':
    main()
