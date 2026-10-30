# Track B: Index

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

Read queries first and index only their terms with up to twelve workers. A small
negative filter rejects only terms that cannot be in the exact dictionary;
every possible hit still receives a complete byte comparison. Boolean postings
start with four inline uint16 document IDs, grow into sorted lists, and promote
to bitmaps when dense. Dense postings skip repeated writes for the same document.
Blocks use uint32 IDs if their domain exceeds 65,536 documents. Boolean operators
fold strictly left to right, independently over disjoint document blocks.

Sampling chooses phrase anchors, followed by a complete exact index pass.
Relative byte offsets use uint32 only when the whole block fits, with a checked
uint64 fallback. Exact ASCII token comparisons around mapped anchor positions
verify phrases without crossing TAB/LF. The corpus mapping stays alive, and no
global token-ID array or merged postings are needed. Sampling and the negative
filter change work only; complete term equality resolves every hash collision.

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
