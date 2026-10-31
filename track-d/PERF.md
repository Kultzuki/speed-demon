# Track D: performance log

## Published reference

The organizers' scoring-box reference takes 72.69 seconds. This is
published calibration, not our own board run.

## First C++ implementation

Read graph bytes into forward and reverse compressed sparse row arrays with two parsing passes. Each query runs bidirectional Dijkstra on the directed graph, with 64-bit distances, zero weights and parallel edges preserved. Stop when the frontier lower bound reaches the best complete path. Generation stamps avoid clearing every node per query. Six workers own independent search storage; results are written in input order after joining.

Local full public seed 1: output SHA-256 `a23dbdf0a3e49cc8901310a9ee1dc6a9a569a85297b6da75c2a7002cb2ed277e`.
The direct local process check took 4.7394 seconds on the
Windows/WSL2 laptop with input and output on a Windows bind mount. This single
run includes local process launch and file-sharing overhead and is not an
official timing. It is not comparable to the scoring-box reference.

## Board evidence

Initial C++ board measurement at commit `b5cbc28`.

| Run ID | T (s) | M (MB) | Formatted source lines | D | K | Machine points |
|---|---:|---:|---:|---:|---:|---:|
| `run-6094fca5ee88` | 1.609181 | 348.48 | 249 | 1 | 6.233915 | 39.738043 |

All correctness, timeout and sandbox gates passed. This is a single public-board
run on public seed 1, not a five-run holdout result. Full board evidence is in
`validation/board-baseline.json` at the repository root.

## Experiments and correctness

Differential checks include all pairs on 20 random directed multigraphs with zero weights and uint32-max weights, plus the official injected cases. Query parallelism preserves only output order, not execution order.

## Second implementation: local experiment

A monotone 65-bucket radix heap replaces the comparison-based binary heap in both search directions.

Five local full-seed-1 runs: 3.17631, 2.90869, 2.97161, 2.70332, 2.81567 seconds. The middle-three mean is 2.89866 seconds. Every output hash matched. These are Linux-filesystem WSL2 process timings, not board measurements. The previous local middle-three mean was 4.6207 seconds.

AddressSanitizer and UndefinedBehaviorSanitizer passed all 57 differential cases, including sample seeds 2 and 17. Sanitizer timings are not performance evidence. A new official board run is needed to price the speed gain against extra source and peak memory.

## Second official board run

Commit `9aad3f4`, run `run-b2872dcee270`: T=1.245620s, M=355.66MB, S=276, D=1, K=6.948507, machine points=42.094576. All gates passed.

Radix heaps improved board wall time from 1.609181s to 1.245620s. Memory increased slightly, and source grew from 249 to 276 lines; K improved from 6.233915 to 6.948507.

## Third official board run

Commit `5dc9c4f`, run `run-d5d71e806018`: T=1.189051s, M=355.59MB, S=276, D=1, K=7.112136, machine points=42.600004. All gates passed.

Runtime implementation code was unchanged from the second board run; differences are not attributed to another optimization.
## Continuation from df84b71: packed state and BFS locality

BFS builds a permutation over every component and isolated vertex. Both CSR
directions and all query endpoints use that permutation. This is a layout
transformation; weighted bidirectional Dijkstra still computes every distance.
Relabeling is included in the timed process.

Each worker stores distance and generation in one uint64 per node/direction.
An accepted improving label has a simple-path representative of at most n-1
edges, so `(n-1)*UINT32_MAX` bounds the required distance field. At full n this
needs 53 bits, leaving 11 generation bits. Before a wrapped tag is reused, both
state arrays are cleared. Zero distance and uint32-maximum weights are ordinary
values, not sentinels. A direct test forces wrap and checks wide distances.

Five serialized local public runs: four workers averaged 1.84803s trimmed mean
at about 217.5 MiB RSS; six workers averaged 1.68420s at about 270.8 MiB RSS.
The checkpoint baseline was 2.61708s / 337.5 MiB in an earlier batch. Retain six
workers for the first official trial; the four-worker time/memory tradeoff is
close under a local sensitivity calculation, not an established scoring gain.
See `research/results/d-packed-bfs-4.json` and `d-packed-bfs-6-confirm.json`.

Release and ASan/UBSan passed the expanded 69-case four-track suite, all public
full hashes, and the separate generation-wrap/53-bit-budget test. Arbitrary
directed multigraph all-pairs tests cover zero cycles, unreachable and isolated
nodes, self-loops, parallel edges and distances above uint32. Offline image and
official sandbox/hash checks passed. Local measurements are not official T/M.

The promoted version also matches its independently generated full-seed-20261031
reference output; input and binary hashes are in
validation/fresh-full-seed20261031.json. This is a local correctness check, not
a hidden-seed or official timing result.

## Fourth official board run: all-track architecture update

Commit `0c89c6e71d502e9edee2b646072b86f9b48c082a`, run `run-7447e8b33b40`:
T=1.004267s, M=285605888 bytes, S=319, D=1,
K=7.911904, machine points=44.914050. All check/build/correctness/
timeout/sandbox gates passed. This is one official public-seed run, not final
holdout scoring. Exact evidence is in `validation/board-fourth.json`.


## Refinement from 6cb3509: validated candidate

Parallel two-pass CSR uses atomic degree/cursor updates and disjoint edge slots.
Node width is derived from n; compact edge words use an exact sorted overflow
entry for every weight at or beyond the inline sentinel. Bidirectional radix
Dijkstra expands the smaller frontier, preserving the frontier-minimum stopping
proof. Exact uint64 labels live in per-worker generation-tagged sparse hash
tables; wrap clears every tag. BFS ordering and its identity remap are removed.

Alternating full-hash-checked local runs: checkpoint 1.944286s versus the sparse
hash/compact-edge candidate 1.032172s trimmed mean; about 270.5 versus 152.9 MiB
RSS. See `d-hash-paired.json`. Mapped input is included in local RSS, so this is
not an official memory saving. D's high-weight reverse-frontier explosion was
also tested and addressed without narrowing weights or distances.

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

Commit `b30392c91f458577a4678b3d9bec4c892a3a964c`, run `run-486af353674a`: T=0.513979s, M=95133696 bytes, S=384, D=1, K=13.401036, points=56.356919. All official gates passed.

This improves the previous best coefficient and is retained. Exact board/team data is in `validation/leaderboard-refinement-b30392c.json`.


## Final official measurement at 154e195

Run `run-a050a88e5612`: T=0.423428s, M=88023040 bytes, S=384, D=1, K=14.995774, points=58.798444. All official gates passed.

Runtime source is unchanged from b30392c; this rerun improved its recorded best, without another B/D kernel change.

Best-three aggregate is 63.343397; captured rank 19. Exact data: `validation/leaderboard-refinement-final.json`. Public practice scoring remains separate from final holdouts and judging.


## Continuation from d069bfd: selected local refinement

Only the query-worker cap changes from six to twelve. Six-worker CSR construction, full uint64 sparse labels, overflow weights, radix heaps and balanced bidirectional search remain. Private counters, direct-address labels and narrow sparse labels did not justify replacing this kernel.

Five alternating full-hash-checked Linux-local runs of the actual selected source: checkpoint 0.759925s, selected 0.628559s trimmed mean. See `research/results/continuation3-paired-d.json`. These are AMD/WSL2 timings; RSS includes mapped input and is not official cgroup memory.

Both release and ASan/UBSan pass 83 dataset comparisons, four direct A/C/D boundary/concurrency/state programs, and a forced uint64-offset B full-hash build. A also passes 1,750 guard-page parses and twelve-way endpoint publication. Provenance is in `validation/continuation3-*-build.json`. Offline rebuilt images pass all four public full hashes in the read-only/no-network/unprivileged sandbox; see `validation/sandbox-continuation3.txt` and `image-sizes-continuation3.json`. Official promotion is decided separately from these local measurements.


## Official continuation measurement at 7321615

Run `run-5eb2205782b0`: T=0.361719s, M=114028544 bytes, S=385, D=1, K=15.399979, points=59.376007. All official gates passed.

Compared with the refreshed starting best K=15.139976: **retained**. This is one public-practice run; local paired gains and unchanged-code rerun variation are separate from hidden-seed/final judging results.


## Official packed-A follow-up at 12aa1a4

Run `run-777b5ee2ea52`: T=0.370052s, M=117944320 bytes, S=385, D=1, K=15.123132, points=58.982087. All official gates passed.

Runtime source is unchanged from 7321615. Any change in this rerun is measurement variation, not another kernel optimization.


## Continuation 5 local validation

See research/CONTINUATION5.md and the exact paired reports. Current production
sources pass 89 release and 89 ASan/UBSan dataset comparisons, both full seeds,
four direct programs and the forced uint64 B-offset full hash. Rebuilt offline
images pass the starter sandbox and match the release binary hashes. These are
local checks, not official coefficient gains. Official run IDs are pending.


## Official continuation measurement 160e4dd

Run `run-12519a0ceed8` at `160e4dd03a5210afd31ba01af791c03d1907da7b`: gates=True,
T=0.391017s, M=107118592 bytes, S=391,
D=1, K=14.963401, points=58.751516.
Previous recorded best K=15.399979. Decision: **reject and restore incoming source**.

Captured best-three aggregate 69.077744, rank 16; leader 79.190878. Snapshot: validation/leaderboard-continuation5-official.json. Public practice, not final judging.


## Restored full-width D after official regression

The overflow-label trial at 160e4dd is rejected. The incoming full-uint64 kernel
is restored without changing A/B/C. Both final source combinations pass 89
release and 89 sanitizer comparisons, the direct programs and forced uint64 B
offsets. D was rebuilt offline and passes the full-hash sandbox; the final
image manifest matches every final release executable. Follow-up run pending.


## Official continuation measurement c503752

Run `run-db13a80ccdcb` at `c503752efebdbebcd9c6de41a4485af8ef1776fd`: gates=True,
T=0.368451s, M=123584512 bytes, S=385,
D=1, K=15.015017, points=58.826292.
Previous recorded best K=15.399979. Decision: **restored incoming full-uint64 kernel; retain proven source**.

Captured best-three aggregate 69.160567, rank 16; leader 79.338836. Snapshot: validation/leaderboard-continuation5-final.json. Public practice, not final judging.


## Continuation 7: selected local candidate

Parse graph text once, encode normal temporary edges in eight bytes, and index a growing exact per-worker stream for all wider weights. Bucket each direction into 64 node ranges whose owners count/prefix/scatter without shared atomic cursors. Final CSR, full uint64 labels and balanced bidirectional radix search are retained.

public: T=0.839969->0.613400s, M=124801024->125763584 bytes, S=385->450, D=1; local K ratio 1.141378 (`research/results/d-heap-layout7.json`).

fresh: T=0.850462->0.607711s, M=114728960->125358080 bytes, S=385->450, D=1; local K ratio 1.135325 (`research/results/d-compact-fresh7.json`).

Checkpoint phase medians from the separate instrumented source: map-degree-count=121.812 ms, prefix-allocate=41.082 ms, parse-scatter=283.725 ms, build-cleanup=7.338 ms, parse-queries=0.181 ms, search=396.997 ms, format=0.111 ms, output=0.171 ms. Raw stderr is in research/results/d-lifetime-workers7.json. These diagnostic intervals omit parts of process startup/cleanup and must not be added to invent an official time.

These are alternating hot-data local WSL2 measurements with fresh cgroups, including process exit; they are not official scores. Short A/C repeats vary materially, and the gain is not a stable percentage across every batch. Every measured output hash matches.

The frozen combination passes 93 release and 93 ASan/UBSan dataset comparisons, both full seeds, the existing direct guard/publication/boundary/membership/state checks, and two new independent checks of all 200,000 forward/reverse CSR edges. Forced uint64 B offsets pass the full hash. All four rebuilt offline images pass the unprivileged read-only/no-network starter sandbox and their executables match the validated release binaries exactly. Exact source/common/compiler/binary/image identities are in validation/continuation7-artifact-provenance.json. Official retention remains pending.


## Official continuation 7 at f992539

Run `run-cf5d7be2d8af` at `f99253995d7fa9f97f825c9c8b37c4ec705d3e66`: T=0.366347s, M=123572224 bytes, S=450, D=1, K=14.710088, points=58.380763. All five official gates passed. Starting historical best K=15.399979: **candidate did not beat the starting recorded best; retention decision required**.

Captured practice aggregate 69.780860, rank 17; leader 80.244238. This is public practice, not final holdout or human judging. Full record: validation/leaderboard-continuation7-official.json.


D's owner-sharded candidate is rejected after the official run: K=14.710088,
versus the historical 15.399979 and unchanged incoming rerun 15.015017. Its
0.366347 s does not reproduce the 14-17% local coefficient gain; the incoming
kernel's latest official time was 0.368451 s at similar memory, while source
size rose from 385 to 450. The exact incoming full-uint64 kernel is restored.
A/B/C retain their officially improved implementations. Final mixed-source
gates, rebuilt D image and another exact-commit official run follow.


## Final continuation 7 local reconciliation

A/B/C retain their improved f992539 sources. D is restored exactly to the
stronger incoming source after its official coefficient regression. The final
mix passes 93 release and 93 ASan/UBSan comparisons, both full seeds, the direct
programs including both complete 200,000-edge CSR checks, and forced uint64 B
offsets. All final image executables match build/continuation7-final-release.
A/B/C images originate in sandbox-continuation7.txt; restored D was rebuilt
in sandbox-continuation7-final-d.txt. Complete final provenance is
validation/continuation7-final-artifact-provenance.json. The earlier
continuation7 builds contain the rejected D trial and remain historical only.


## Official continuation 7 at e9deec0

Run `run-b9af384939b6` at `e9deec07fa38f9abf0c167d6768c41c388e37ba5`: T=0.400875s, M=120442880 bytes, S=385, D=1, K=14.469309, points=58.022390. All five official gates passed. Starting historical best K=15.399979: **restored established full-uint64 kernel; retain; this measurement is a rerun**.

Captured practice aggregate 69.780860, rank 17; leader 80.253740. This is public practice, not final holdout or human judging. Full record: validation/leaderboard-continuation7-final.json.


## Continuation 8 Rust candidate

Rust port selected for official measurement after the complete local gate. All 97 comparisons pass in release, ASan and checked-arithmetic modes; both full seeds and direct tests pass. Rebuilt offline images match the validated release executables exactly. Canonical S=485, D=1. Matched local measurements and rejected trials: research/CONTINUATION8_RUST.md. Official retention is pending; local results are not official scores.


## Official Rust continuation at 0ca1987

Run `run-5ccc134f1b0c` at `0ca1987477223527268d60911e073ff334feb8bd`: T=0.397762s, M=102604800, S=473, D=1, K=14.542976. All five official gates pass. Incoming exact-head K=14.469309; historical best K=15.399979. Rust passes every gate; compare with historical best and incoming exact-head rerun before final retention.

Captured practice aggregate 69.780860, rank 28; leader 81.805732. Full snapshot: validation/leaderboard-rust8-candidate.json.
