"""Create isolated phase and process-lifetime experiments from the checkpoint."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
TIMER = '''
#include <chrono>
static auto phase_start=std::chrono::steady_clock::now();
static void phase(const char* label) {
 auto now=std::chrono::steady_clock::now();
 fprintf(stderr,"PHASE %s %.9f\\n",label,std::chrono::duration<double>(now-phase_start).count());
 phase_start=now;
}
'''


def save(name, source):
    path = PROTO / (name + '.cpp')
    if path.exists():
        raise FileExistsError(path)
    path.write_text(source)


def profile(s, track):
    s = s.replace('#include "common.hpp"', '#include "common.hpp"\n' + TIMER, 1)
    if track == 'a':
        s = s.replace('EndpointTable endpoints;', 'phase("cuts"); EndpointTable endpoints;')
        s = s.replace('uint32_t count=endpoints.count.load();', 'phase("parse"); uint32_t count=endpoints.count.load();')
        s = s.replace('std::array<std::string,72> outputs;', 'phase("sort-names"); std::array<std::string,72> outputs;')
        s = s.replace('if (fclose(file)!=0', 'phase("select-format-output"); if (fclose(file)!=0')
        s = s.replace('} catch (const std::exception& e)', 'phase("close"); } catch (const std::exception& e)')
    elif track == 'b':
        s = s.replace('TermTable terms;\n    Queries queries', 'phase("map-check-widths"); TermTable terms;\n    Queries queries')
        s = s.replace('auto ix = build_index', 'phase("queries"); auto ix = build_index')
        s = s.replace('// Turn the per-thread counts', 'phase("index-scan");\n    // Turn the per-thread counts')
        s = s.replace('ix.seg_end = std::move(count);', 'ix.seg_end = std::move(count);\n    phase("scatter");')
        s = s.replace('// Answer queries in parallel', 'phase("index-finish");\n    // Answer queries in parallel')
        s = s.replace('std::string out;\n    out.reserve', 'phase("evaluate"); std::string out;\n    out.reserve')
        s = s.replace('fclose(f);\n    return;', 'fclose(f); phase("format-output");\n    return;')
        s = s.replace('solve<uint16_t,uint32_t>(paths);}', 'solve<uint16_t,uint32_t>(paths);phase("cleanup");}')
    elif track == 'c':
        s = s.replace('MappedFile regions', 'phase("paths"); MappedFile regions')
        s = s.replace('auto cuts = boundaries', 'phase("region-lookup"); auto cuts = boundaries')
        s = s.replace('SharedNames names;', 'phase("boundaries"); SharedNames names;')
        s = s.replace('for (unsigned i = 0; i < workers; ++i) {\n            for (size_t j', 'phase("parse-names"); for (unsigned i = 0; i < workers; ++i) {\n            for (size_t j')
        s = s.replace('std::sort(countries.begin()', 'phase("merge"); std::sort(countries.begin()')
        s = s.replace('write_output(paths.out', 'phase("sort-format"); write_output(paths.out')
        s = s.replace('} catch (const std::exception& e)', 'phase("output"); } catch (const std::exception& e)')
    else:
        s = s.replace('for (unsigned d=0;d<2;++d) {\n            std::partial_sum', 'phase("map-degree-count"); for (unsigned d=0;d<2;++d) {\n            std::partial_sum')
        s = s.replace('auto forward=offset[0],reverse=offset[1];', 'phase("prefix-allocate"); auto forward=offset[0],reverse=offset[1];')
        s = s.replace('for (auto& side:edges) side.finish();', 'phase("parse-scatter"); for (auto& side:edges) side.finish();')
        s = s.replace('Graph graph(paths.data + "/graph.txt");', 'Graph graph(paths.data + "/graph.txt"); phase("build-cleanup");')
        s = s.replace('std::vector<int64_t> answers', 'phase("parse-queries"); std::vector<int64_t> answers')
        s = s.replace('std::string output;', 'phase("search"); std::string output;')
        s = s.replace('write_output(paths.out', 'phase("format"); write_output(paths.out')
        s = s.replace('} catch (const std::exception& e)', 'phase("output"); } catch (const std::exception& e)')
    return s


def quick_exit(s, track):
    s = '#include <unistd.h>\n' + s
    if track == 'a':
        s = s.replace('throw std::runtime_error("Summary write failed");',
                      'throw std::runtime_error("Summary write failed");\n        _exit(0);')
    elif track == 'b':
        s = s.replace('fclose(f);\n    return;', 'if(fclose(f)!=0) throw std::runtime_error("Output close failed");\n    _exit(0);')
    else:
        output = 'aggregates.txt' if track == 'c' else 'distances.txt'
        s = s.replace('write_output(paths.out + "/'+output+'", output);',
                      'write_output(paths.out + "/'+output+'", output);\n        _exit(0);')
    return s


def main():
    for track in 'abcd':
        base = subprocess.check_output(['git', 'show', f'HEAD:track-{track}/main.cpp'], cwd=ROOT).decode()
        save(f'continuation7-base-{track}', base)
        save(f'continuation7-profile-{track}', profile(base, track))
        save(f'continuation7-exit-{track}', quick_exit(base, track))
        if track in 'ac':
            incoming = (ROOT / f'track-{track}/main.cpp').read_text()
            save(f'continuation7-incoming-{track}', incoming)
            save(f'continuation7-incoming-exit-{track}', quick_exit(incoming, track))
        if track == 'a':
            populate = base.replace('void parse(const char* p,const char* end,EndpointTable& endpoints) {', '''void parse(const char* p,const char* end,EndpointTable& endpoints) {
        if(end>p) {
            size_t page=size_t(sysconf(_SC_PAGESIZE));
            auto* start=reinterpret_cast<char*>(reinterpret_cast<uintptr_t>(p)&~(page-1));
            madvise(start,size_t(end-start),MADV_POPULATE_READ);
        }''')
            save('continuation7-populate-a', populate)
            reserve = base.replace('void parse(const char* p,const char* end,EndpointTable& endpoints) {', '''void parse(const char* p,const char* end,EndpointTable& endpoints) {
        for(auto& hour:hours) hour.records.reserve(size_t(end-p)/72/80+16);''')
            save('continuation7-reserve-a', reserve)
        if track == 'd':
            save('continuation7-build12-d', base.replace('std::min(6u,', 'std::min(12u,', 1))
    print('Created checkpoint, incoming, phase, exit, A population/reserve and D worker trials.')


if __name__ == '__main__':
    main()
