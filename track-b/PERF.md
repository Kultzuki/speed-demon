# Track B: performance log

## Published reference

The organizers' scoring-box reference takes 56.35 seconds. This is
published calibration, not our own board run.

## First C++ implementation

Read all queries first and index only their terms. Corpus tokenization lowercases ASCII A-Z only; all other non-alphanumeric bytes are separators. Sorted document postings support strictly left-to-right Boolean set operations. For phrases, select the least frequent occurrence list as the anchor and compare exact adjacent token IDs. A boundary bit on every document's final token forbids cross-document matches. Full string equality resolves dictionary hash collisions; results are exact.

Local full public seed 1: output SHA-256 `f86973c210228141bcb6f1f1b10188ad2a9b65f71e7cd7cf4590b38de4e80927`.
The direct local process check took 14.6211 seconds on the
Windows/WSL2 laptop with input and output on a Windows bind mount. This single
run includes local process launch and file-sharing overhead and is not an
official timing. It is not comparable to the scoring-box reference.

## Board evidence

Initial C++ board measurement at commit `b5cbc28`.

| Run ID | T (s) | M (MB) | Formatted source lines | D | K | Machine points |
|---|---:|---:|---:|---:|---:|---:|
| `run-d2ad96a22ae8` | 5.822991 | 411.35 | 259 | 1 | 3.718642 | 28.519218 |

All correctness, timeout and sandbox gates passed. This is a single public-board
run on public seed 1, not a five-run holdout result. Full board evidence is in
`validation/board-baseline.json` at the repository root.

## Experiments and correctness

Differential cases include ASCII case conversion, UTF-8 separators, repeated phrase terms, sentence punctuation, absent terms, empty documents and mixed left-associative Boolean operators.

## Second implementation: local experiment

A contiguous exact dictionary replaces node-based probes. Six workers parse complete document-line blocks and merge ordered postings and translated token positions.

Five local full-seed-1 runs: 2.59227, 2.56169, 2.62141, 2.55414, 2.58628 seconds. The middle-three mean is 2.58008 seconds. Every output hash matched. These are Linux-filesystem WSL2 process timings, not board measurements. The previous local middle-three mean was 11.2331 seconds.

AddressSanitizer and UndefinedBehaviorSanitizer passed all 57 differential cases, including sample seeds 2 and 17. Sanitizer timings are not performance evidence. A new official board run is needed to price the speed gain against extra source and peak memory.

## Second official board run

Commit `9aad3f4`, run `run-3c8605ffbbe8`: T=2.301115s, M=642.91MB, S=355, D=1, K=5.160148, machine points=35.633107. All gates passed.

Parallel parsing and the flat dictionary improved board wall time from 5.822991s to 2.301115s; peak memory increased from 411.35MB to 642.91MB and formatted source grew from 259 to 355 lines. K still improved from 3.718642 to 5.160148. The coefficient prices the additional memory and code rather than treating this as a wall-time-only win.

## Third official board run

Commit `5dc9c4f`, run `run-72a424b92d56`: T=2.192134s, M=643.08MB, S=355, D=1, K=5.286576, machine points=36.158726. All gates passed.

Runtime implementation code was unchanged from the second board run; differences are not attributed to another optimization.
