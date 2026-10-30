# Track A: performance log

## Published reference

The organizers' scoring-box reference takes 32.05 seconds. This is
published calibration, not our own board run.

## First C++ implementation

Parse only the fixed UTC hour, endpoint, error-status digit and integer latency. Ignore method and sub-hour timestamp fields. Intern endpoints and keep 72 groups per endpoint; the complete span is fixed by the spec. Sort small groups and select the three nearest ranks in large groups, preserving previously selected ranks. Sort output endpoint keys lexicographically for each hour. All percentile and error-ppm arithmetic uses integers.

Local full public seed 1: output SHA-256 `495ca09682b9673ef836a506496177680bb4a3af54255174befddb1f83481cd3`.
The direct local process check took 2.4244 seconds on the
Windows/WSL2 laptop with input and output on a Windows bind mount. This single
run includes local process launch and file-sharing overhead and is not an
official timing. It is not comparable to the scoring-box reference.

## Board evidence

Initial C++ board measurement at commit `b5cbc28`.

| Run ID | T (s) | M (MB) | Formatted source lines | D | K | Machine points |
|---|---:|---:|---:|---:|---:|---:|
| `run-9c31cead2b72` | 0.409238 | 46.58 | 180 | 1 | 10.204190 | 50.438927 |

All correctness, timeout and sandbox gates passed. This is a single public-board
run on public seed 1, not a five-run holdout result. Full board evidence is in
`validation/board-baseline.json` at the repository root.

## Experiments and correctness

Full-scale checking found a partition-selection bug: a later nth_element could move a previously selected percentile. Starting each later partition after the selected rank fixes it. A dedicated test covers group sizes 1, 2, 3, 99, 100, 101, 128, 129, 257 and 1001, including duplicate and extreme uint32 latencies. This correction was made before the first push.

## Second official board run

Commit `9aad3f4`, run `run-ef4d0b0f0b4c`: T=0.410932s, M=46.62MB, S=180, D=1, K=10.181704, machine points=50.391023. All gates passed.

The implementation was unchanged from the first board run; timing differences are not attributed to an optimization.

## Third official board run

Commit `5dc9c4f`, run `run-f33eb781a96d`: T=0.412071s, M=46.60MB, S=180, D=1, K=10.168337, machine points=50.362498. All gates passed.

Runtime implementation code was unchanged from the second board run; differences are not attributed to another optimization.
## Continuation from df84b71: parallel parsing and output

Six newline-aligned workers parse independent endpoint/hour groups, followed by
an exact merge. Independent hours then perform percentile selection and
formatting in parallel. Ordered buffered writes preserve the exact output.

Five serialized Linux-local public-seed runs: serial baseline trimmed mean
0.34563s, parallel selection/output 0.14527s. Peak process RSS was approximately
260.6 versus 271.9 MiB. These are AMD/WSL2 measurements, not official T or M.
Raw samples, flags and compiled-source hashes are in
`research/results/a-baseline-confirm.json` and `a-parallel-output-6.json`.

The four-track release and ASan/UBSan suites each passed 69 cases and all four
full public hashes. The added A fixture exceeds the parallel threshold and
mixes month-boundary hours, prefix endpoints, duplicates, 499/500 and uint32
latency extremes. Offline image and official sandbox/hash checks passed.

The promoted version also matches its independently generated full-seed-20261031
reference output; input and binary hashes are in
validation/fresh-full-seed20261031.json. This is a local correctness check, not
a hidden-seed or official timing result.

## Fourth official board run: all-track architecture update

Commit `0c89c6e71d502e9edee2b646072b86f9b48c082a`, run `run-20fa752e4d42`:
T=0.096460s, M=48439296 bytes, S=250, D=1,
K=19.851814, machine points=64.890010. All check/build/correctness/
timeout/sandbox gates passed. This is one official public-seed run, not final
holdout scoring. Exact evidence is in `validation/board-fourth.json`.


## Refinement from 6cb3509: validated candidate

Twelve workers parse once into exact seven-byte latency/group records in
bounded pages, then count/prefix/scatter into one contiguous latency array.
An exact open-addressed endpoint map replaces per-row unordered-map lookup.
Nearest-rank selection and ordered per-hour formatting remain parallel.
The 1,842-endpoint, 72-hour and 3.1M-row specification proves the group and
cursor widths; latency retains its entire uint32 range.

Alternating full-hash-checked local runs: checkpoint 0.140581s versus selected
twelve-worker pages 0.105338s trimmed mean (`a-twelve-paired.json`). Local RSS
increased from approximately 271.9 to 281.5 MiB; only official cgroup memory can
settle the coefficient tradeoff.

Local correctness gates passed in both release and ASan/UBSan: 69 differential
cases, all four public full hashes, six added boundary/reproduction datasets,
and all four independently referenced full-seed-20261031 outputs. Three direct
C/D state/concurrency/boundary programs and the forced uint64 B offset build
also passed. Reports: `validation/refined-{release,sanitized}*.json`.
Actual production sources were compiled. Offline image rebuilds and every
full-hash read-only/no-network/unprivileged sandbox check passed, all under the
2 GB image cap. `validation/sandbox-refined.txt` and `image-sizes-refined.json`
record the image tests. No x86-64-v3 or native flag was promoted after local trials.

Official score/placement is recorded separately after the implementation push.


## Official b30392c measurement and promotion decision

Commit `b30392c91f458577a4678b3d9bec4c892a3a964c`, run `run-b1aaf19253a1`: T=0.085539s, M=75784192 bytes, S=319, D=1, K=18.583948, points=63.456899. All official gates passed.

The candidate is rejected: faster runtime did not offset higher official memory and source cost. Its K=18.583948 is below the prior 19.851814. Production is restored byte-for-byte to the stronger `0c89c6e` A source; the packed-record and allocator/parser experiments remain in research.
