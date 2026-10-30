# Track B: Index

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

Read all queries first and index only their terms. Six workers parse complete document lines through a read-only exact dictionary. Boolean postings start as sorted unique document lists and promote to bitmaps when dense. Queries retain strict left-to-right evaluation; disjoint document blocks are summarized without merging their indexes. Runtime sampling chooses phrase anchors, then a complete pass stores their 64-bit raw byte offsets. Exact ASCII token comparison around each anchor verifies phrases without crossing TAB/LF boundaries. There is no global token-ID array. Sampling changes work planning only, never correctness. Full byte equality resolves hash collisions.

## Build and dependencies

C++20, standard library and Linux system calls only. No direct non-stdlib
runtime dependencies: dependency_count = 0, D = 1. GCC 16 and Debian runtime
images are pinned to the organizers' allowlisted digests. The build is offline;
the executable is statically linked. The mmap mapping owns all referenced input
bytes until processing ends. Exactly one output file is written to /out.

## Validation

The official full public seed-1 output hash matches locally. Worked examples,
tiny seeds 1/2/17 and additional differential cases are exercised by the root
validation harness. Consult PERF.md for measured evidence and board run IDs.

## With another 24 hours

Measure batching or streaming common-anchor phrases to reduce occurrence storage further. Keep sparse/bitmap thresholds and sampling costs in the total measurement.
