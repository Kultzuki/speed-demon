# Track B: Index

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

Read all queries first and index only their terms. Corpus tokenization lowercases ASCII A-Z only; all other non-alphanumeric bytes are separators. Sorted document postings support strictly left-to-right Boolean set operations. For phrases, select the least frequent occurrence list as the anchor and compare exact adjacent token IDs. A boundary bit on every document's final token forbids cross-document matches. Full string equality resolves dictionary hash collisions; results are exact.

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

The corpus lookup loop and common-term Boolean operations are the first profiling candidates. Evaluate a compact query dictionary and adaptive dense bitsets against the current sorted postings.
