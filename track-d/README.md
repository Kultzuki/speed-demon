# Track D: Traverse

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

Build forward/reverse CSR with two parsing passes. BFS relabels every component and isolated vertex to improve locality; edges and queries use the same permutation. Exact weighted searches still use bidirectional Dijkstra and 65-bucket radix heaps. Distance and generation share one 64-bit word per vertex/direction. The distance width is derived from (n-1)*UINT32_MAX (53 bits at full scale), and generation wrap clears both arrays before tag reuse. Six workers own independent state. Stop at the valid frontier lower bound and write answers in input order. Zero weights, parallel edges and 64-bit distances are preserved; all relabeling work is timed.

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
