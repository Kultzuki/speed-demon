# Track A: Ingest

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

Up to twelve workers parse complete line ranges. A shared endpoint registry
publishes immutable keys with release/acquire ordering and compares their full
bytes; its 2,048-key capacity exceeds the binding 1,842-endpoint catalogue.
The registry hashes the first and last eight bytes plus length, then resolves
every collision with full byte equality. Middle-byte and hash collisions never
merge endpoints; this is an indexing choice, not an identity shortcut.
Each parser stores a 32-bit record with 20 latency bits, 11 endpoint bits and
one error bit in each of 72 hour buckets. The reserved latency sentinel has an
ordered uint32 overflow stream, so every latency retains all 32 bits exactly.
SIMD endpoint scans load only within their mapped range.

Workers gather one hour at a time into reusable latency storage and release its
parser buckets. Exact nearest-rank p50/p95/p99 values come from one of three
paths: groups of 64 or fewer are sorted in place, medium groups use the
partition sequence, and groups of 512 or more first bucket the observed value
range and then partition only the candidate bucket, which keeps the rank search
sequential instead of three passes of scattered comparisons. Each hour formats
endpoints in byte order into one prepared buffer; the writer streams completed
hours in chronological order and frees their buffers, and the process exits as
soon as the summary is closed. Empty input produces a zero-byte summary.
Duplicates, 499/500, uint32 extremes and all hour/month boundaries retain exact
integer behavior.

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


The validated continuation-8 Rust version is preserved independently in
../research/rust8-validated/track-a/. Both official Rust runs pass every gate,
but neither exceeds the established best coefficient, so the stronger C++
entry is retained. See ../research/CONTINUATION8_RUST.md for complete evidence.
