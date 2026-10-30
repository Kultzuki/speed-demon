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

## Third official board run

Commit `5dc9c4f`, run `run-815e467328ed`: T=0.452601s, M=13.14MB, S=288, D=1, K=9.493120, machine points=48.870449. All gates passed.

Compact exact-name interning improved T from the initial 0.659149s to 0.452601s, reduced M from 13.82MB to 13.14MB and raised K from 7.908269 to 9.493120 despite S growing from 260 to 288 lines.
## Continuation from df84b71: shared exact-name shards

The quote-safe private-table prototype was validated, then compared with one
shared catalog partitioned into 256 shards. Each shard's mutex covers table/arena
growth and the exact name/country membership test. Only the first insertion of
a name/country pair increments a worker's distinct count; all country aggregates
merge after the threads join. This avoids replicated names and the expensive
name-by-name merge. Hashes still require full-byte equality.

Five serialized Linux-local full public runs:

| Variant | Trimmed mean (s) | Approximate peak process RSS (MiB) |
|---|---:|---:|
| Private name catalogs, three workers | 0.31095 | 222.8 |
| Private name catalogs, six workers | 0.27024 | 247.8 |
| Shared sharded catalog, six workers | 0.22919 | 207.8 |

The checkpoint's serial compact-table trial was 0.51618s / 205.9 MiB in an
earlier local batch. These are AMD/WSL2 measurements; mapped-input RSS is not the
official memory axis. See the `c-parallel-*-confirm` and `c-shared-6` result JSONs.

Release and ASan/UBSan passed the expanded 69-case four-track suite and public
full hashes. A separate boundary test covers 64 byte alignments and 1-12 workers,
including doubled quotes, embedded LF, mixed terminators, BOM and final no-LF.
The 135,000-name growth test and 52,000-record concurrent hostile fixture pass.
Offline image and official sandbox/hash checks passed.

The promoted version also matches its independently generated full-seed-20261031
reference output; input and binary hashes are in
validation/fresh-full-seed20261031.json. This is a local correctness check, not
a hidden-seed or official timing result.

## Fourth official board run: all-track architecture update

Commit `0c89c6e71d502e9edee2b646072b86f9b48c082a`, run `run-e56248dd5797`:
T=0.162170s, M=15011840 bytes, S=385, D=1,
K=14.784387, machine points=58.490166. All check/build/correctness/
timeout/sandbox gates passed. This is one official public-seed run, not final
holdout scoring. Exact evidence is in `validation/board-fourth.json`.
