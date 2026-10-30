# Refinement continued from 6cb3509

The complete `HANDOVER_NEXT.md` was read before editing. The workspace was clean
at `6cb35093ef9de4babf07b6ed58347e40da6fa76d` on the watched `speed-demon` branch.
All four entries remain C++20 with zero third-party runtime dependencies.
The supplied screenshot raises the target aggregate to 73.071; it is a target,
not a claim about our placement.

## Selected mechanisms

- A: one text parse into seven-byte exact `(latency, local group)` records,
  bounded allocation pages, count/prefix/disjoint scatter into one latency array,
  exact open-addressed endpoint equality and twelve parser/output workers.
  The specified 1,842 endpoints and 72 hours need only 18 group bits; 24 are
  retained. Full uint32 latencies remain unchanged. Full-scale 3.1M rows prove
  the uint32 group cursors cannot overflow. No endpoint strings are hardcoded.
- B: checked block-relative uint16 document IDs with a uint32 fallback, four
  inline sparse IDs per descriptor, adaptive exact bitmaps, compact hash/ID
  slots with byte equality, inline bounded query plans, and checked relative
  uint32 offsets with uint64 fallback. The immutable corpus mapping stays live.
- C: immutable exact-name nodes published with acquire/release atomics, insertion
  locks only on a miss, atomic country membership to elect a single distinct
  increment, smaller stable arenas, parallel quote-parity prefix scans and twelve
  parser workers. Decoded byte strings, including escaped quotes, remain the keys.
- D: parallel exact forward/reverse CSR, runtime-width packed edges with an exact
  sorted overflow index, frontier-size-balanced bidirectional radix search, and
  generation-tagged sparse hash distance state. No BFS reordering remains.
  All distance values are uint64; generation wrap clears the tags. The stopping
  condition still uses the sum of the two frontier minima, independently of which
  frontier is expanded. Zero weights, self-loops, multiedges and every node remain.

## Local evidence

These are alternating, serialized runs on Linux-local public inputs under WSL2,
not official timing or cgroup memory. Every individual timed run checked its full
output hash. CPU/load drift was substantial; compare within a recorded batch.

| Batch | Baseline trimmed mean | Candidate trimmed mean | Evidence |
|---|---:|---:|---|
| A checkpoint versus twelve-worker pages | 0.140581s | 0.105338s | `results/a-twelve-paired.json` |
| B checkpoint versus compact inline postings | 1.147780s | 0.857186s | `results/b-compact-paired.json` |
| B later local offsets/inline query plans | 0.756912s | 0.749726s | `results/b-occurrences-paired.json` |
| C checkpoint versus twelve-worker exact names | 0.210809s | 0.101670s | `results/c-twelve-paired.json` |
| D checkpoint versus balanced sparse hash/compact edges | 1.944286s | 1.032172s | `results/d-hash-paired.json` |

Profiling in `results/refine-checkpoint-profile.json` located B's 63 MB sparse
capacity and 20.5 MB metadata; C's serial boundary scan and per-row locking; D's
construction/reordering and the large-weight frontier imbalance. D local RSS
fell from about 270 to 153 MiB, but mapped-page accounting means this is not the
official memory gain. Final D also removes the unused identity remap allocation.

## Alternatives preserved but not selected

A two-pass count/reparse/scatter saved memory but had no clear runtime advantage.
B vector-classification caching tied/regressed. Its document-intersection phrase
trial, inspired by the supplied Rust, was slower despite passing the full hash.
C borrowing name slices from the 200 MB input lost locality; encoded raw keys did
not beat decoded keys. Six-worker C was slower than twelve. D's first sparse set
grew too large because a high-weight query expanded almost the entire reverse
graph; balancing the frontiers fixed the mechanism. Private construction counters
were slower and larger. Compact edges alone traded time for memory, so they were
retained only with the winning search/state combination. BFS ordering was no
longer worthwhile for that combination.

`results/*-v3-paired.json` compares conservative x86-64-v3 flags. A/B regressed,
C tied, and D's small gain was insufficiently established amid drift. Default
build flags remain. No native/PGO claim or runtime dependency was introduced.

## Supplied code and validation

`SUPPLIED_RUST_REVIEW.md` records the four-file review. All four supplied files
compile and pass the published seed-1 hashes, but B has a reproduced 1,024-token
phrase cap and C has hash-only distinct identity plus a reproduced fixed-lookahead
failure. No supplied implementation was substituted without measurement.

`tools/refinement_checks.py` compiles the actual production files, rather than
the older handover's prototype mapping. It checks 69 existing differential cases,
four public full hashes, six additional boundary/reproduction datasets, four
previously independently referenced full-seed-20261031 datasets, three direct C/D
tests, and the forced uint64 B offset instantiation on the full public corpus.
The same gate runs in release and ASan/UBSan. Build reports record actual source,
common-header, binary hashes and flags. A Windows-generated B fixture initially
had CRLF and was corrected to the required LF bytes before the extension gate.

Official results are recorded separately after the implementation push; local
timings do not establish its score or placement. Offline images and the supplied
read-only, no-network, unprivileged sandbox must pass before that push.


## Official b30392c outcome

All gates passed. A: 63.456899 points, K=18.583948, T=0.085539s,
M=75,784,192, S=319; B: 55.158259, K=12.681341, T=0.734635s,
M=87,310,336, S=570; C: 62.012380, K=17.387919, T=0.117573s,
M=15,142,912, S=377; D: 56.356919, K=13.401036, T=0.513979s,
M=95,133,696, S=384. Run IDs are in each track's PERF log.

B/C/D improve and are retained. A's memory/source cost loses coefficient despite
being faster; its runtime source is restored to the stronger measured 0c89c6e
version. The board retains that older A best. Aggregate becomes 60.981929 from
58.007574, using A/C/D. The captured rank remains 22 as other teams improved too;
ALL STAR is 73.212358 in that snapshot. These are public best-three machine points,
not final hidden-seed/judging results.

The second supplied set and its reproduced faults are recorded separately in
`SUPPLIED_SECOND_REVIEW.md`. Its contract-backed C boundary shortcut is faster in
an alternating local trial and is going through the final gate. A's additional
parser and allocator controls do not establish enough gain to override its
official rejection and remain unpromoted.
