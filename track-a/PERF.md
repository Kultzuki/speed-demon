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
