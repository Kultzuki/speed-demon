# Review of the second supplied A/B/C/D set

All four files were read completely after the first set's experiments and
official `b30392c` measurement completed. Exact copies are in `supplied-second`.
They are C11 implementations. Test adapters only add `--data`/`--out` paths;
the original files and their hashes are preserved.

All four compile with GCC 16, AVX2 and no runtime dependencies, and match both
the full public seed and independently referenced full seed 20261031. Results
are in `validation/supplied-second-review.json`. Passing these datasets does
not prove all boundary conditions or the advertised performance mechanisms.

## Confirmed defects

- **A, empty input:** zero-length `mmap` fails instead of writing the required
  empty summary. **A, unbounded SIMD load:** `next_space` reads 32 bytes from a
  mapping without checking its remaining length. The mapping has no explicitly
  reserved slack. A guard-page test at the last short endpoint exits with SIGSEGV.
  Fixed 260 KiB hour-output buffers also need a proven bound or growth handling;
  no buffer-overflow reproduction is claimed for those buffers.
- **C, unchecked suffix arena:** a fixed 512 KiB allocation receives all bytes
  beyond the first 24 of every name, without a capacity check. An input with just
  100 distinct names, each with 6,000 significant trailing spaces, triggers an
  ASan heap-buffer-overflow. Every field stays below the frozen CSV reference's
  field limit, and the reference successfully parses this fixture. C also has
  a fixed 512-byte escape scratch buffer with no bound check, and fixed name
  storage of 115,000 entries. The 135,000-name growth stress test segfaults;
  that stress exceeds the ordinary generated name-pool size and is reported as
  a robustness test, not a prediction that the public generator fails.
- **C, final EOF:** `record(..., p == end)` always receives false inside the
  `while (p < end)` loop. The optional-final-terminator test is rejected. The
  generator itself always terminates its last record, so this affects the broader
  section-2.1 parsing rule rather than either tested full generated dataset.

The guard-page and sanitizer evidence is in
`validation/supplied-second-boundaries.json`; `tools/second_boundary_checks.py`
reproduces it. No supplied implementation is promoted unchanged.

## B and D

B also passes the previous Rust implementation's 1,024-token counterexample and
the token/block/boolean-fold fixture. Its contiguous posting stream, exact term
equality, shared bitmap ownership and sparse/bitmap algebra are credible ideas.
However, the advertised shared pass for common phrases is not activated:
`heavy_pass` remains zero, and no setup invokes the heavy path. Actual phrase
queries still scan candidate documents separately. No new correctness failure
was reproduced in the tested B cases.

D passes both full seeds, the worked example and five arbitrary directed
multigraph/all-pairs cases. The uint32 fast path does restart in uint64 when an
examined label reaches the sentinel, so wide distances are not silently truncated.
Its comment says frontier balancing, but direction selection still compares
`min0 <= min1`, retaining the high-weight imbalance addressed in our implementation.
It also retains full uint32 arrays plus any allocated uint64 arrays per worker.
No new correctness failure was reproduced in those D cases.

## Ideas measured in our implementation

The C boundary shortcut is sound under section 2.2: names have no LF and notes
contain no digits or BOM bytes. Thus LF followed by a digit/BOM starts a record.
Applied to our exact decoded-name catalog with dynamically growing storage,
alternating five-run measurements improve 0.085193s to 0.073064s, with every full
output hash matching. This is a local result; promotion requires the complete
release/sanitizer/fresh-seed/offline-sandbox gate and official measurement.

A's allocator control was also isolated on the packed-record trial. It changed
0.100006s to 0.098459s locally and did not establish a process-RSS reduction.
The previous packed-record A push lost official coefficient because of memory,
so the stronger measured A implementation is restored. The additional bounded
four-digit/parser trial tied and is preserved without promotion.
