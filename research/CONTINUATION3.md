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
