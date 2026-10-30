# Track C: performance log

## Published reference

The organizers' scoring-box reference takes 14.44 seconds. This is
published calibration, not our own board run.

## First C++ implementation

Scan CSV quote boundaries with memchr. Unescape names only when doubled quotes occur; preserve all significant bytes and trailing spaces. Notes need an exact decoded byte count, not a stored decoded string. Join region IDs through a direct lookup table; missing and out-of-range IDs map to _UNMATCHED. Intern exact names globally and record country membership in bitsets, so distinct counting never relies on a hash alone. Parse and aggregate amounts as signed 64-bit integer cents.

Local full public seed 1: output SHA-256 `d8088b1cd42ba1338b1345b107b55db7b96ef1f5066f3ff64fd26a8912a0f536`.
The direct local process check took 4.3912 seconds on the
Windows/WSL2 laptop with input and output on a Windows bind mount. This single
run includes local process launch and file-sharing overhead and is not an
official timing. It is not comparable to the scoring-box reference.

## Board evidence

Initial C++ board measurement at commit `b5cbc28`.

| Run ID | T (s) | M (MB) | Formatted source lines | D | K | Machine points |
|---|---:|---:|---:|---:|---:|---:|
| `run-8928a0489213` | 0.659149 | 13.82 | 260 | 1 | 7.908269 | 44.904071 |

All correctness, timeout and sandbox gates passed. This is a single public-board
run on public seed 1, not a five-run holdout result. Full board evidence is in
`validation/board-baseline.json` at the repository root.

## Experiments and correctness

Differential cases include mid-file BOMs, LF inside quoted notes, escaped name/note quotes, empty names, distinct names differing only by spaces, negative sub-unit amounts, unmatched regions and a final record without a newline.

## Second official board run

Commit `9aad3f4`, run `run-8211fa1a15fa`: T=0.814066s, M=13.92MB, S=260, D=1, K=7.105620, machine points=42.580100. All gates passed.

The implementation was unchanged from the first board run; timing differences are not attributed to an optimization.

## Compact exact-name storage: local experiment

Replace node-based string-view dictionary entries and input-file pointers with a flat exact hash table and compact owned-name arena. Membership bitsets remain exact. Hash collisions compare full bytes. Both table and arena can grow.

Five local full runs: 1.08107, 0.74373, 0.75114, 0.67658, 0.65800s; trimmed mean 0.72382s, versus 1.8086s in the first local baseline. Every full output hash matched. These are local WSL2 numbers, not board results.

AddressSanitizer and UndefinedBehaviorSanitizer passed worked-example, tiny seeds 1/2/17, sample seeds 2/17, final-no-newline and full public data. A separate 135,000-name case forces hash-table and arena growth and repeats earlier names afterward; it also matches the reference under sanitizers.
