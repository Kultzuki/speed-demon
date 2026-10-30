"""Freeze d069bfd kernels, preserve new attachments, and profile current phases."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ATTACHMENTS = {
    'a': '2716c290-2863-4d02-9552-52df9d5ec913',
    'b': 'ae4152bf-d285-4496-a044-9e1897710728',
    'c': '9884cb23-162a-4672-b1ec-82a7a108a0f2',
    'c-duplicate': '4a70d0d1-a4ef-444d-8901-6909b3c250a7',
}

def prepare():
    folder = ROOT / 'research/supplied-third'
    folder.mkdir(exist_ok=True)
    evidence = {}
    for label, attachment in ATTACHMENTS.items():
        source = Path.home() / '.codex/attachments' / attachment / 'Pasted text.txt'
        data = source.read_bytes()
        (folder / f'track-{label}.c').write_bytes(data)
        evidence[label] = {'attachment': attachment, 'bytes': len(data),
                           'sha256': hashlib.sha256(data).hexdigest()}
        prior = ROOT / f'research/supplied-second/track-{label}.c'
        if prior.is_file():
            evidence[label]['identical_to_second'] = data == prior.read_bytes()
    for track in 'abcd':
        source = ROOT / f'track-{track}/main.cpp'
        (ROOT / f'research/prototypes/checkpoint3-{track}.cpp').write_bytes(source.read_bytes())
    (ROOT / 'validation/supplied-third-inputs.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence, indent=2))

HEADER = r'''
#include <chrono>
static auto phase_clock = std::chrono::steady_clock::now();
static void phase(const char* name) {
    auto now = std::chrono::steady_clock::now();
    fprintf(stderr, "PHASE %s %.6f\n", name, std::chrono::duration<double>(now-phase_clock).count());
    phase_clock = now;
}
'''

def diagnostic(track):
    source = (ROOT / f'research/prototypes/checkpoint3-{track}.cpp').read_text()
    source = source.replace('#include "common.hpp"', '#include "common.hpp"\n' + HEADER)
    changes = {
        'a': [('auto& ids = partials[0].ids;', 'phase("parse"); auto& ids = partials[0].ids;'),
              ('std::vector<uint32_t> order(endpoints.size());', 'phase("merge"); std::vector<uint32_t> order(endpoints.size());'),
              ('FILE* file = fopen', 'phase("select-format"); FILE* file = fopen')],
        'b': [('unsigned workers = std::min', 'phase("queries-sample-plan"); unsigned workers = std::min'),
              ('threads.clear();', 'phase("index"); threads.clear();'),
              ('std::string output;', 'phase("evaluate"); std::string output;')],
        'c': [('auto cuts = boundaries', 'phase("lookup"); auto cuts = boundaries'),
              ('SharedNames names;', 'phase("boundaries"); SharedNames names;'),
              ('for (unsigned i = 0; i < workers; ++i) {\n            for (size_t j', 'phase("parse-names"); for (unsigned i = 0; i < workers; ++i) {\n            for (size_t j')],
        'd': [('Graph graph(paths.data + "/graph.txt");', 'Graph graph(paths.data + "/graph.txt"); phase("parse-csr");'),
              ('std::string output;', 'phase("search"); std::string output;')],
    }
    for old, new in changes[track]:
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    return source.replace('} catch (const std::exception& e)', 'phase("output-cleanup"); } catch (const std::exception& e)')

def profile():
    evidence = {}
    with tempfile.TemporaryDirectory() as directory:
        temp = Path(directory)
        for track in 'abcd':
            source, binary = temp / 'main.cpp', temp / 'profile'
            source.write_text(diagnostic(track))
            subprocess.run(['g++', '-std=c++20', '-O3', '-DNDEBUG', '-pthread', '-static', '-s',
                            '-I', str(ROOT / f'track-{track}'), str(source), '-o', str(binary)], check=True)
            evidence[track] = []
            for run in range(3):
                result = subprocess.run([str(binary), '--data', f'/benchdata/{track}', '--out', directory],
                                        capture_output=True, text=True, check=True)
                evidence[track].append(result.stderr)
                print(track, run + 1, result.stderr, flush=True)
    (ROOT / 'research/results/checkpoint3-profile.json').write_text(json.dumps(evidence, indent=2) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    prepare() if args.prepare else profile()
