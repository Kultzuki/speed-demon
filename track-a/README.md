# Track A: Ingest

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

Six workers parse complete newline-aligned ranges into private endpoint/hour groups. Parse only the fixed UTC hour, endpoint, error-status digit and integer latency. Merge every request and error exactly, then schedule independent hours across workers for percentile selection and formatting. Sort small groups and select the three nearest ranks in large groups, preserving previously selected ranks. Write hour buffers in order, with endpoint keys in byte order. All percentile and error-ppm arithmetic uses integers.

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

Compare contiguous count/scatter latency storage against the remaining per-group vectors. Keep preprocessing and output inside every benchmark.
