# Track A: Ingest

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

Up to twelve workers parse complete line ranges. A shared endpoint registry
publishes immutable keys with release/acquire ordering and compares their full
bytes; the 4,096-entry capacity exceeds the binding 1,842-endpoint catalogue.
Each parser stores uint32 latencies and separate uint16 endpoint/error tags in
72 hour buckets. SIMD endpoint scans load only within their mapped range.

Workers gather one hour at a time into reusable latency storage, release its
parser buckets, and compute exact nearest-rank p50/p95/p99 values. Later nth
selections exclude earlier selected positions. Each hour formats endpoints in
byte order; the writer streams completed hours in chronological order and frees
their buffers. Empty input produces a zero-byte summary. Duplicates, 499/500,
uint32 extremes and all hour/month boundaries retain exact integer behavior.

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

Profile parsing and allocation on the scoring CPU, then compare output-buffer
reuse and percentile thresholds using the full coefficient. Keep all parsing,
selection, output and cleanup inside every timed run.
