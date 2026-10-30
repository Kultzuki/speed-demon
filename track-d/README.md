# Track D: Traverse

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

Read graph bytes into forward and reverse compressed sparse row arrays with two parsing passes. Each query runs bidirectional Dijkstra on the directed graph, with 64-bit distances, zero weights and parallel edges preserved. Monotone integer keys use a radix heap with 65 buckets instead of a comparison-based binary heap. Stop when the frontier lower bound reaches the best complete path. Generation stamps avoid clearing every node per query. Six workers own independent search storage; results are written in input order after joining.

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

Measure worker count, sparse search state and graph construction separately. More workers trade lower wall time for greater memory, so compare the combined coefficient rather than time alone.
