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
