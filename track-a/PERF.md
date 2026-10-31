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


## Final official measurement at 154e195

Run `run-5129f4051865`: T=0.095759s, M=48582656 bytes, S=250, D=1, K=19.912571, points=64.956367. All official gates passed.

Runtime source is the stronger restored 0c89c6e implementation; the small improvement over its previous score is run variability, not a new A optimization.

Best-three aggregate is 63.343397; captured rank 19. Exact data: `validation/leaderboard-refinement-final.json`. Public practice scoring remains separate from final holdouts and judging.


## Continuation from d069bfd: selected local refinement

A shared exact endpoint registry and separate latency/tag hour buckets replace six large endpoint/group catalogs and their serial merge. Twelve workers gather/select/format hours, release consumed buckets, and stream completed hours in order. All SIMD loads stay within the input range; the full uint32 latency and nearest-rank behavior remain.

Five alternating full-hash-checked Linux-local runs of the actual selected source: checkpoint 0.146446s, selected 0.062678s trimmed mean. See `research/results/continuation3-paired-a.json`. These are AMD/WSL2 timings; RSS includes mapped input and is not official cgroup memory.

Both release and ASan/UBSan pass 83 dataset comparisons, four direct A/C/D boundary/concurrency/state programs, and a forced uint64-offset B full-hash build. A also passes 1,750 guard-page parses and twelve-way endpoint publication. Provenance is in `validation/continuation3-*-build.json`. Offline rebuilt images pass all four public full hashes in the read-only/no-network/unprivileged sandbox; see `validation/sandbox-continuation3.txt` and `image-sizes-continuation3.json`. Official promotion is decided separately from these local measurements.


## Official continuation measurement at 7321615

Run `run-14a15eda11d9`: T=0.056243s, M=34742272 bytes, S=283, D=1, K=27.272851, points=71.786527. All official gates passed.

Compared with the refreshed starting best K=19.912571: **retained**. This is one public-practice run; local paired gains and unchanged-code rerun variation are separate from hidden-seed/final judging results.


## Packed A follow-up to measured 7321615

One 32-bit record replaces the separate uint32 latency/uint16 tag vectors:
20 latency bits, 11 endpoint bits and one error bit. The binding 1,842-key
catalogue fits in 11 bits. The latency sentinel has an exact ordered uint32
overflow stream, including the sentinel's own numeric value. No input latency
is truncated and no frequency/distribution assumption decides the answers.

Seven alternating full-hash runs: measured source 0.058654s, packed source
0.057950s trimmed mean. Runtime is effectively tied locally; process RSS falls
by about 6-7 MiB. This is a memory tradeoff to measure officially, not an
established coefficient gain. Raw evidence: research/results/a-packed4-paired.json.

Both release and ASan/UBSan pass 85 dataset comparisons (the prior 83 plus two
sentinel/overflow-heavy fixtures), four direct programs and forced uint64 B
offset verification. A's guard program now checks 4,375 parses, with latencies
0, 2^20-2, 2^20-1, 2^20 and UINT32_MAX, and twelve-way endpoint publication.
The new A image passes its offline build and full-hash sandbox. B/D sources
and images are unchanged from 7321615; new builds retain their exact hashes.
Compiler/source/binary provenance: validation/continuation4ac-*-build.json.


## Official packed-A follow-up at 12aa1a4

Run `run-08da06690eea`: T=0.042816s, M=27090944 bytes, S=290, D=1, K=32.732322, points=75.748841. All official gates passed.

Packed A is retained: K=32.732322 versus measured 7321615 K=27.272851.


## Continuation 5 local validation

See research/CONTINUATION5.md and the exact paired reports. Current production
sources pass 89 release and 89 ASan/UBSan dataset comparisons, both full seeds,
four direct programs and the forced uint64 B-offset full hash. Rebuilt offline
images pass the starter sandbox and match the release binary hashes. These are
local checks, not official coefficient gains. Official run IDs are pending.


## Official continuation measurement 160e4dd

Run `run-258ef14a9368` at `160e4dd03a5210afd31ba01af791c03d1907da7b`: gates=True,
T=0.052783s, M=29478912 bytes, S=290,
D=1, K=28.986473, points=73.109768.
Previous recorded best K=32.732322. Decision: **unchanged A kernel; retain source and historical best**.
A runtime source is unchanged; any result difference is rerun variation.

Captured best-three aggregate 69.077744, rank 16; leader 79.190878. Snapshot: validation/leaderboard-continuation5-official.json. Public practice, not final judging.
