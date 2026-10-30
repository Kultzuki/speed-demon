# Review of the October 31 continuation attachments

The exact third set is preserved in `research/supplied-third/`; the later three
files are in `research/supplied-fourth/`. SHA-256 provenance and observed results
are in `validation/supplied-third-inputs.json` and
`validation/supplied-continuation-review.json`. Path-only adapters are separate
under `research/prototypes/`. No pasted implementation was substituted wholesale.

## Third set: A, B, C and a duplicate C

- **A (9,027 bytes): rejected.** Compiles, but both full-seed hashes and the
  percentile/parallel boundary fixtures fail. After computing the endpoint start,
  `parse` skips another space-delimited field, so it interns the status instead
  of the endpoint and starts reading latency at the wrong offset. Empty input
  passed. Its unbounded `next_space` also lacks a valid general tail contract;
  this version maps file bytes beyond EOF rather than reserving anonymous slack.
- **B:** byte-identical to the second supplied B. Its earlier two full-seed
  passes and bounded review findings still apply. The described shared heavy
  phrase scan remains unactivated. There is no new B optimization in this paste.
- **C:** both full-seed hashes, optional final EOF, parallel hostile CSV and the
  previous 6,000-space suffix-arena reproduction pass. Allocating suffix storage
  from file size fixes that particular old arena overflow. A valid name longer
  than its 64 KiB input buffer is rejected as malformed. The 135,000-name growth
  stress case is rejected by its fixed name budget; this is above the usual
  documented 100,000-name planning pool, not evidence that a public seed fails.
- The two C attachments have the same SHA-256. There is no Track D in this set.

## Fourth set: corrected A, cache-dropping C, and D

- **A (11,893 bytes):** both full seeds, explicit empty input, percentile ranks
  and parallel-boundary fixtures pass. The extra field skip is removed. It now
  reserves an anonymous zero-filled mapping before overlaying the file, which
  provides real tail slack for its wide loads. These are meaningful fixes over
  the preceding A. Passing these five fixtures is the scope of this review;
  this exact original has not passed our complete sanitizer/concurrency gate.
- **C (11,501 bytes):** adds `posix_fadvise(..., POSIX_FADV_DONTNEED)` to the
  preceding C. Its tested pass/fail pattern is the same, including rejection of
  the long-name and name-growth fixtures. Cache-dropping calls do not remove
  those bounds. No performance claim is inferred from these correctness runs.
- **D (9,713 bytes):** both full hashes, the worked wide/zero/unreachable example
  and five arbitrary directed all-pairs fixtures pass. It uses one forward CSR,
  BFS renumbering and one-way four-ary-heap Dijkstra, with a checked uint64 redo.
  Those are different tradeoffs from our bidirectional sparse-state search;
  its correctness results alone are not a reason to replace the measured kernel.

Both new C files retain a collision-exactness concern found by reading
`name_id`: the small cache accepts equal hash/length/first-eight bytes without
comparing all remaining inline bytes. The main hash table does compare them.
This is a missing exactness check in a collision path, not a naturally generated
hash collision reproduced in the full datasets. The selected C++ kernel always
compares the complete decoded name and has no fixed record/name arena limit.

## Ideas used in the continuation

The shared endpoint dictionary, separate latency/tag hour buckets, and ordered
hour output in the supplied A motivated the new C++ A trial. It uses bounded
SIMD loads, exact byte equality, all uint32 latencies, and ordered output with
normal ownership. C trials kept exact owned name bytes, reduced node metadata,
and used the binding 240-country bound for a byte-sized region lookup. Rejected
views, flat tables, custom B hashes, private D counters and narrow D labels are
recorded as experiments, not promoted improvements.
