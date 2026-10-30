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
