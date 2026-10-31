# Track D: Traverse

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

Six parsers build forward and reverse CSR in two passes. Edge words derive the
node width from n; sentinel weights use exact sorted overflow entries. There is
no BFS remapping. Up to twelve query workers own independent generation-tagged
sparse hash tables and safe epoch wrap. Common labels occupy uint32 fields;
the reserved UINT32_MAX value resolves through an exact uint64 overflow map,
including a distance of UINT32_MAX itself. No query is narrowed or restarted.
Bidirectional
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
