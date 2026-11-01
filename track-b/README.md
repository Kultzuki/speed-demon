# Track B: Index

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

Read queries first and index only their terms with up to twelve workers.
Paired token-start/end masks classify 64 input bytes at a time; a masked AVX2
load builds each exact lowercase key. An eight-token prefetch pipeline overlaps
CRC32C dictionary lookups, with complete byte equality resolving collisions. Sampled
frequencies choose bitmap terms; the full pass deduplicates every document.
Other postings enter bucketed packed streams, then scatter into sorted CSR
lists while their temporary pages are released. A checked 15-bit local stream
uses uint16 postings; larger real worker domains dispatch to a 32-bit document
stream and postings. Corpus byte offsets use uint32 with a checked uint64
fallback. Sample decisions affect work, never answers.
The narrow temporary streams put a 12-bit term offset and 4-bit document gap in
one 16-bit word. An explicit escape carries a larger absolute document id;
decoder state crosses block boundaries without truncation. Lazy anonymous
blocks hold 262,144 words and return their pages as they drain. The full-width
stream remains exact when a worker covers more than 32,768 documents.
The two largest bucket ranges scatter as separate producer jobs. Other ranges
have one scatter owner, reducing shared cache lines while balancing the work.

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

Profile on the scoring CPU, test full 16-bit local domains with fewer builders,
and train compiler profiles only on organizer-generator output.
Compare the full coefficient, including memory and source size.
