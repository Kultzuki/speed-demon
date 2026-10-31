"""Write measured continuation notes without altering earlier PERF evidence."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
root = ROOT / 'README.md'
text = root.read_text().replace('C++20 implementations for **all four tracks**.', 'Rust implementations for **A/D** and C++20 for **B/C**.')
text = text.replace('Exact shared endpoint registry, packed hour records', 'Buffered parallel reads, owned exact endpoint registry, packed hour records')
text = text.replace('generation-tagged sparse uint64 distances', 'separate uint64 distances and width-derived node/generation tags')
root.write_text(text)
(ROOT / 'track-a/README.md').write_text('''# Track A: Ingest

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

Eight workers read independent ranges with pread and reusable 256 KiB buffers.
Range boundaries align forward to LF. The binding grammar limits a whole line
to 177 bytes, so every record is owned once and each incomplete chunk suffix
(at most 176 bytes) can be reread safely. Small inputs use one worker.

An exact shared registry owns all endpoint bytes. The first/last-eight-byte plus
length hash selects a probe sequence; full equality resolves every collision.
Release/acquire publication makes keys immutable before readers use their IDs.
A local ID cache persists across each worker's reads. The 2,048-key and 125-byte
capacities cover the binding 1,842-endpoint catalogue and maximum path length.

Each hour record has 20 latency bits, 11 endpoint bits and one error bit. The
latency sentinel has an ordered, exact uint32 overflow stream. Group counters
cover the binding 3,100,000 records; error-ppm arithmetic uses uint64. SIMD loads
stay within complete-record slices. No hash is used as endpoint identity.

Workers gather individual hours and compute exact nearest-rank percentiles.
Groups of at most 16 values are sorted; larger groups use restricted successive
select_nth_unstable calls. Output streams in hour and full endpoint byte order.
Duplicates count separately. Empty input creates a zero-byte summary. Successful
output is checked closed before _exit; kernel cleanup remains timed.

## Build and dependencies

Rust 2021 edition, standard library and Linux system calls only. No third-party
runtime dependencies: dependency_count = 0, D = 1. Rust 1.99.1 and Debian images
are pinned to allowlisted digests. The offline build targets x86-64-v3 (AVX2,
no AVX-512) and links statically. Exactly /out/summary.txt is written.

## Validation and measurements

The continuation-8 mix passes 97 comparisons in release, AddressSanitizer and
checked-arithmetic builds, including both full seeds. Direct tests cover 4,375
guard-page parses, concurrent exact publication, range alignment at every byte
of a fixture, decimal widths and percentile ranks. A rebuilt-standard-library
ThreadSanitizer test also passes exact publication. The rebuilt offline image
passes the official starter sandbox and full hash. See PERF.md and
research/CONTINUATION8_RUST.md for exact artifacts and official decisions.

## Further work

Profile buffered parsing, exact lookup, gathering and ordered output on the
scoring CPU. Compare the complete coefficient before retaining a change.
''')
(ROOT / 'track-d/README.md').write_text('''# Track D: Traverse

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

Six parsers build forward and reverse compact CSR in two passes. Node width is
derived from n; sentinel weights use a sorted, exact uint32 overflow table.
Every edge and duplicate multiplicity is retained.

Twelve query workers run balanced bidirectional radix Dijkstra. The radix heap
builds on the user's supplied Rust work, preserved in ../track-d-rust/.
Heap entries retain aligned full uint64 keys. Each worker owns separate aligned
uint64-distance and uint32 node/generation-tag arrays. Tag widths derive from n;
epoch exhaustion clears every tag before reusing epoch 1. Distances are never
narrowed. The stopping condition uses valid frontier-minimum lower bounds.
Answers retain input order, including duplicate and unreachable queries.

The supplied BFS/forward-search and packed one-pass intermediate variants were
measured separately and preserved. The selected kernel uses the established
two-pass CSR without BFS remapping, sharding or packed heap entries. Small inputs
and query sets use one worker. Output is checked closed before _exit; process
and kernel cleanup remain timed.

## Build and dependencies

Rust 2021 edition, standard library and Linux system calls only. No third-party
runtime dependencies: dependency_count = 0, D = 1. Rust 1.99.1 and Debian images
are pinned to allowlisted digests. The offline build targets x86-64-v3 and links
statically. Exactly /out/distances.txt is written.

## Validation and measurements

The continuation-8 mix passes 97 comparisons in release, AddressSanitizer and
checked-arithmetic builds, including both full seeds. Direct Rust tests cover
rehash, membership, derived epoch widths and forced wrap, full uint32 weights,
full uint64 distances, and repeated zero/unreachable paths. An independent text
parser verifies every forward/reverse edge and duplicate in two 200,000-edge
parallel-build fixtures. The rebuilt offline image passes the official starter
sandbox and full public hash. See PERF.md and research/CONTINUATION8_RUST.md for
measured outcomes and official retention decisions.

## Further work

Measure sparse lookup, heap work and construction on the scoring CPU. Preserve
all exact width/epoch fallbacks and compare complete coefficients.
''')

rows = []
for track, stem, label in [('a', 'a-rust8-scalar', 'a-rust8-scalar-release'),
                           ('d', 'd-rust8-finalist', 'd-simple8')]:
    for seed in ['public', 'fresh']:
        report = json.loads((ROOT / f'research/results/{stem}-{seed}.json').read_text())
        base = report['entries'][f'{track}-cpp8']; trial = report['entries'][label]
        rows.append(f'| {track.upper()} | {seed} | {base["T_s"]:.6f} | {trial["T_s"]:.6f} | {trial["M_bytes"]} | {trial["S"]} | {trial["local_K_ratio"]:.6f} |')
report = '''# Continuation 8: Rust A and D - October 31, 2026

Continued the existing private CodeScythe entry and speed-demon branch from
e9deec07fa38f9abf0c167d6768c41c388e37ba5. No restart, registration, reset,
force-push or agent delegation. The complete incoming handover is preserved as
HANDOVER_INCOMING_RUST8.md. All 12 incoming dirty files were archived byte for
byte in .out/continuation8-rust-incoming; original user D and the interim tree
are also preserved in .out/continuation8-user-d-rust. Earlier evidence is retained.

The fresh starting feed is validation/leaderboard-rust8-start.json: aggregate
69.780860, rank 26, leader 81.805732. These are dated public practice results.
First place remains outstanding; no local timing is an official score.

## User-supplied Rust D

Read every file under track-d-rust/track-d. Original files are unchanged and
their hashes are checked in final provenance. The source accepts positional
paths instead of --data/--out, and its manifest says "your team name". Its
PERF notes describe a separate 2-core machine and have no official run IDs.
Those historical times are not independently verified here.

A CLI-only adapter is research/prototypes/d-user-cli8.rs. It matches the public
full hash. In an alternating local full comparison it takes 0.810449 s and
299,954,176 cgroup bytes (S=316), versus the established C++ entry's 0.762841 s,
123,367,424 bytes and S=385: local K ratio 0.836661. The radix heap was adapted
into the exact bidirectional port; BFS/forward search was not promoted.

## Frozen candidates and local measurements

A owns full endpoint bytes, uses persistent worker caches and small buffered
parallel reads, retains exact packed-record overflow and selects percentiles
in parallel. D preserves the established compact two-pass forward/reverse CSR
and bidirectional radix search while separating aligned full uint64 distances
from width-derived uint32 node/generation tags. Epoch wrap clears tags safely.
No distance narrowing, cached answers or hash-only equality is introduced.

The complete local coefficient uses fresh cgroups, exec-to-exit timing, 8 GB/no
swap, twelve pinned CPUs, read-only root/data, no network, measured memory.peak,
canonical rustfmt 1.10.0/scc 4.1.0 source counts and D=1. Alternating full runs
check every output hash. Results are noisy; the table does not establish a
stable gain on the official CPU. D's earlier local-to-official failure remains
the reason official measurement decides retention.

| Track | Full seed | C++ T s | Rust T s | Rust M bytes | Rust S | Local K ratio |
|---|---|---:|---:|---:|---:|---:|
''' + '\n'.join(rows) + '''

Canonical selected S is A=449, D=485, with zero third-party runtime dependencies.
Selection: rust8-selection.json. Prior exact C++ sources are in baseline8/.
B/C submitted sources remain unchanged and their validated binaries are reused.

## Rejected or unselected work

All raw reports remain under results/ and exact sources under prototypes/.
Mapped Rust A, owned-key-only changes, simple early exit, the dedicated writer,
six/twelve-worker alternatives and SWAR decimal parsing did not provide a
consistent complete-coefficient advantage. The simpler buffered scalar version
was selected. The SWAR version remains validated research, not the submitted path.

D's full-width packed one-pass intermediate raises peak construction memory and
source cost without a stable K gain. Single-probe relaxation and six query
workers also lose the matched final comparison. The simpler two-pass, twelve-
query-worker sparse state wins locally on both full seeds. No rejected owner-
sharded builder, narrow label or 12-byte packed heap was repeated.

Initial monotonic instrumentation records A parsing near 30-35 ms, plus gather,
selection/formatting and serialized output. D spends roughly 120-135 ms counting,
45-55 ms prefixing/allocating, 245-295 ms scattering, and 400-485 ms searching.
These are separate instrumented WSL2 binaries and diagnostic phase intervals,
not deployable timing or source-size evidence. Final instrumented sources and
measurements are recorded separately when available.

## Validation and offline artifacts

build/rust8-final-{release,asan,checked}/track-* each pass all previous 93
comparisons plus four fresh reference cases (97 total), including both full seeds.
Rust direct tests cover 4,375 guard-page parses, concurrent exact endpoint
publication, every byte of an alignment fixture, decimal widths, duplicate
percentile ranks, sparse growth/epoch wrap, full-width weights/distances and
complete forward/reverse CSR multiplicities on both 200,000-edge fixtures.

Rust A/D use AddressSanitizer and a separate checked-arithmetic build; unchanged
C++ B/C use their validated ASan/UBSan executables. No Rust UBSan claim is made.
The extra TSan publication test rebuilt std/test with the same sanitizer ABI.
The default container blocked TSan's process-local ASLR control; the dedicated
race-test container permits it, with network none and a read-only binary mount.
That check passes. No global ASLR or official sandbox setting was changed.

All four offline images pass the official starter sandbox and public hashes.
Every image executable exactly matches its validated release binary. Provenance:
validation/rust8-final-artifact-provenance.json, validation/image-sizes-rust8-final.json,
validation/rust8-final-safety-gates.txt and validation/rust8-tsan-publication.json.
The existing B forced-uint64-offset and C direct checks retain their unchanged
source/binary provenance from continuation 7.

Official submission and retention decisions follow below. No first-place claim.
'''
with (ROOT / 'research/CONTINUATION8_RUST.md').open('x') as stream: stream.write(report)
for track in 'ad':
    path = ROOT / f'track-{track}/PERF.md'
    marker = '## Continuation 8 Rust candidate'
    text = path.read_text(); assert marker not in text
    path.write_text(text + '\n\n' + marker + '\n\nRust port selected for official measurement after the complete local gate. '
        'All 97 comparisons pass in release, ASan and checked-arithmetic modes; both full seeds and direct tests pass. '
        'Rebuilt offline images match the validated release executables exactly. '
        'Canonical S=' + ('449' if track == 'a' else '485') + ', D=1. '
        'Matched local measurements and rejected trials: research/CONTINUATION8_RUST.md. '
        'Official retention is pending; local results are not official scores.\n')
print('Wrote current Rust documentation and appended measured evidence; prior PERF entries retained.')
