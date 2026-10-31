# Track D: Traverse

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

Six workers parse the text once into compact temporary edges. They bucket each
direction into 64 disjoint node ranges; each range owns its degree counts,
prefixes and scatter cursors, so construction needs no atomic cursor updates.
Ordinary temporary edges occupy eight bytes. A sentinel indexes a growing
per-worker stream containing complete endpoints and uint32 weights, with no
fixed wide-edge cap. Parsed storage is released after reverse bucketing.

The final forward and reverse CSR retain compact edge words derived from n;
sentinel weights use exact sorted overflow entries. There is no BFS remapping.
Up to twelve query workers own independent generation-tagged
sparse hash tables with full uint64 distances and safe epoch wrap. Bidirectional
radix Dijkstra expands the smaller frontier and stops only at the valid sum of
frontier-minimum lower bounds. Answers retain input order. Zero and wide weights,
duplicates, parallel edges, isolated nodes and every component remain exact.

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
