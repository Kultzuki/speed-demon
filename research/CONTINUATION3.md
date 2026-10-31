# Continuation from d069bfd

The original four-track entry and watched speed-demon branch were continued.
The live starting snapshot was 63.489897, rank 19, with leader 73.812408.
These include unchanged-code rerun variation after the previous handover.

## Exact selected-source paired local timings

| Track | Checkpoint seconds | Selected seconds | Local reduction |
|---|---:|---:|---:|
| A | 0.146446 | 0.062678 | 57.2% |
| B | 0.775465 | 0.549416 | 29.2% |
| C | 0.070719 | 0.064280 | 9.1% |
| D | 0.759925 | 0.628559 | 17.3% |

Every run matches the full public output hash. Each row is its own alternating
five-run batch; cross-track/batch timings must not be combined into a synthetic
official score. The public machine measures cgroup peak memory, not process RSS.

## Selected changes and rejected alternatives

- **A:** A shared exact endpoint registry and separate latency/tag hour buckets replace six large endpoint/group catalogs and their serial merge. Twelve workers gather/select/format hours, release consumed buckets, and stream completed hours in order. All SIMD loads stay within the input range; the full uint32 latency and nearest-rank behavior remain.

- **B:** Twelve block workers, an exact-safe negative dictionary filter, and duplicate-write suppression for dense postings are selected. Every possible filter hit still goes through exact byte equality. Query folds, phrase verification, uint16/uint32 document fallback and uint32/uint64 relative-offset fallback remain.

- **C:** Owned name nodes retain length and exact bytes without redundant stored hashes/string-view descriptors. The lookup uses uint8 country IDs under the binding 240-country plus unmatched bound. Growing arenas, full decoded-name equality, contract-safe boundaries, release/acquire publication and atomic membership remain.

- **D:** Only the query-worker cap changes from six to twelve. Six-worker CSR construction, full uint64 sparse labels, overflow weights, radix heaps and balanced bidirectional search remain. Private counters, direct-address labels and narrow sparse labels did not justify replacing this kernel.

Individual raw trials remain under research/results and research/prototypes.
In particular, A output-buffer recycling, B block scanning/custom word hashing,
C mapped-name views/larger flat tables, and D serial/private CSR counters and
direct-address labels were not selected. Small differences between narrow and
wide sparse D labels were inconclusive; full-width labels are retained.

## Validation and supplied code

Release and ASan/UBSan each pass 69 differential datasets, four public full
hashes, six extra boundary/reproduction datasets and four independently
referenced fresh full outputs: 83 comparisons each. Four direct programs check
A guard pages/publication, C 64 boundary alignments and concurrent membership,
and D wrap/rehash/overflow/search state. B's forced uint64-offset build passes
the full public hash. All offline images pass the starter sandbox and size cap.
Actual compiler flags/source/common/binary hashes are saved with each build.

The two new pasted sets were preserved and reviewed separately in
SUPPLIED_CONTINUATION_REVIEW.md. Correctness failures, collision-path concerns,
and successful tested fixtures are distinguished. None was copied wholesale.

Anonymous GitHub access returns 404 for the user-confirmed private repository;
a fresh successful board watch reads the same remote head. Evidence is in
validation/private-repository-access.json. Scoring the new implementation will
add a direct private-clone/build check.

## Official result

Implementation `7321615dd4b7f43d35cd71d45c607541b0fd73af` passed every official gate on all four tracks. Best-three public aggregate: **65.975209**, captured rank **14**; leader **74.784070**. Exact run IDs and per-track promotion decisions are in PERF.md and validation/leaderboard-continuation3.json.


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


## Buffered C follow-up

The rejected 12aa1a4 C trial used private 64 KiB pread buffers, carrying incomplete records and
growing for arbitrarily long records. Exact owned names make reuse safe. The
boundary shortcut retains the published section 2.2 proof. The public full-hash
paired mean improves 0.068021s to 0.056815s; larger buffers are rejected. Lower
RSS mostly reflects absent mapped pages, not a proven cgroup-memory reduction.
That A/C trial plus unchanged B/D passed both 85-comparison gates in
validation/continuation4ac-* and the A/C offline sandbox checks.

Official follow-up `12aa1a4b22c970d7ce41700594fb8561f981dccd`: packed A retained, buffered C rejected; best-three aggregate 67.167388, captured rank 12, leader 75.793365. B/D kernels are unchanged; their rerun variation is recorded separately.
