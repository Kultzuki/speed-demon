"""Diagnostic-only phase/allocation measurements of the measured checkpoint."""
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HEADER = r'''
#include <chrono>
static auto phase_clock = std::chrono::steady_clock::now();
static void phase(const char* name) {
    auto now = std::chrono::steady_clock::now();
    fprintf(stderr, "PHASE %s %.6f\n", name, std::chrono::duration<double>(now-phase_clock).count());
    phase_clock = now;
}
'''

def replace(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new)

def diagnostic(track):
    source = (ROOT / f"track-{track}/main.cpp").read_text()
    source = source.replace('#include "common.hpp"', '#include "common.hpp"\n' + HEADER)
    if track == "a":
        source = replace(source, 'auto& ids = partials[0].ids;', 'phase("parse"); auto& ids = partials[0].ids;')
        source = replace(source, 'std::vector<uint32_t> order(endpoints.size());', 'phase("merge"); std::vector<uint32_t> order(endpoints.size());')
        source = replace(source, 'FILE* file = fopen', 'phase("select-format"); FILE* file = fopen')
    elif track == "b":
        source = replace(source, 'unsigned workers = std::min', 'phase("queries-sample-plan"); unsigned workers = std::min')
        source = replace(source, 'threads.clear();', r'''
        phase("index");
        size_t sparse=0, bits=0, offsets=0, docs=0, metadata=0;
        for (auto& b : blocks) {
            metadata += b.postings.capacity()*sizeof(Posting) + b.occurrences.capacity()*sizeof(Occurrences);
            for (auto& p : b.postings) { sparse += p.documents.capacity()*4; bits += p.bits.capacity()*8; }
            for (auto& o : b.occurrences) { offsets += o.offsets.capacity()*8; docs += o.documents.capacity()*4; }
        }
        fprintf(stderr, "ALLOC terms=%zu boolean=%u anchors=%u sparse=%zu bits=%zu offsets=%zu docs=%zu metadata=%zu lookup=%zu\n",
                terms.size(), boolean_count, anchor_count, sparse,bits,offsets,docs,metadata,lookup.slots.capacity()*sizeof(Lookup::Slot));
        threads.clear();''')
        source = replace(source, 'std::string output;', 'phase("evaluate"); std::string output;')
    elif track == "c":
        source = replace(source, 'auto cuts = boundaries', 'phase("lookup"); auto cuts = boundaries')
        source = replace(source, 'SharedNames names;', 'phase("boundaries"); SharedNames names;')
        source = replace(source, 'for (unsigned i = 0; i < workers; ++i) {\n            for (size_t j', 'phase("parse-names"); for (unsigned i = 0; i < workers; ++i) {\n            for (size_t j')
    else:
        source = replace(source, 'graph.reorder();', 'phase("parse-csr"); graph.reorder(); phase("reorder");')
        source = replace(source, 'std::string output;', 'phase("search"); std::string output;')
    source = source.replace('} catch (const std::exception& e)', 'phase("output-cleanup"); } catch (const std::exception& e)')
    return source

def main():
    result = {}
    with tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        for track in "abcd":
            path, binary = temp / "main.cpp", temp / "profile"
            path.write_text(diagnostic(track))
            subprocess.run(["g++", "-std=c++20", "-O3", "-DNDEBUG", "-pthread", "-static", "-s",
                            "-I", str(ROOT / f"track-{track}"), str(path), "-o", str(binary)], check=True)
            result[track] = []
            for run in range(3):
                completed = subprocess.run([str(binary), "--data", f"/benchdata/{track}", "--out", temporary],
                                           capture_output=True, text=True, check=True)
                result[track].append(completed.stderr)
                print(track, run+1, completed.stderr, flush=True)
    (ROOT / "research/results/refine-checkpoint-profile.json").write_text(json.dumps(result, indent=2)+"\n")

if __name__ == "__main__":
    main()
