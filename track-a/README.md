# Track A: Ingest

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

Parse only the fixed UTC hour, endpoint, error-status digit and integer latency. Ignore method and sub-hour timestamp fields. Intern endpoints and keep 72 groups per endpoint; the complete span is fixed by the spec. Sort small groups and select the three nearest ranks in large groups, preserving previously selected ranks. Sort output endpoint keys lexicographically for each hour. All percentile and error-ppm arithmetic uses integers.

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

Parallel parsing, packed latency storage and output formatting should be measured independently before adding complexity.
