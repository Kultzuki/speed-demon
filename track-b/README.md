# Track B: Index

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

Read queries first and index only their terms with up to twelve workers.
An eight-token prefetch pipeline overlaps exact dictionary lookups. Sampled
frequencies choose bitmap terms; the full pass deduplicates every document.
Other postings enter bucketed packed streams, then scatter into sorted CSR
lists while their temporary pages are released. A checked 15-bit local stream
uses uint16 postings; larger real worker domains dispatch to a 32-bit document
stream and postings. Corpus byte offsets use uint32 with a checked uint64
fallback. Sample decisions affect work, never answers.

Boolean operators fold strictly left to right, switching between lists and
bitmaps as each operand requires. Phrase terms intersect rarest first, followed
by uncapped exact ASCII token checks in the mapped document. Complete term
bytes resolve every dictionary hash collision; phrase checks never use hashes.

## Build and dependencies

C++20, standard library and Linux system calls only. No direct non-stdlib
runtime dependencies: dependency_count = 0, D = 1. GCC 16 and Debian runtime
images are pinned to the organizers' allowlisted digests. The build is offline;
the executable targets x86-64-v3 and is statically linked. The mmap mapping owns all referenced input
bytes until processing ends. Exactly one output file is written to /out.

## Validation

The official full public seed-1 output hash matches locally. Worked examples,
tiny seeds 1/2/17 and additional differential cases are exercised by the root
validation harness. Consult PERF.md for measured evidence and board run IDs.

## With another 24 hours

Measure packed-stream bucket sizes, dense thresholds and batched exact phrase
checks. Compare the full coefficient, including memory and source size.
