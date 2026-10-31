# Track A: Ingest

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

Eight workers read independent ranges with pread and reusable 256 KiB buffers.
Range boundaries align forward to LF. The binding grammar limits a whole line
to 177 bytes, so every record is owned once and each incomplete chunk suffix
(at most 176 bytes) can be reread safely. Small inputs use one worker.

An exact shared registry owns all endpoint bytes. The first/last-eight-byte plus
length hash selects a probe sequence; full equality resolves every collision.
Release/acquire publication makes keys immutable before readers use their IDs.
A local ID cache persists across each worker's reads. The 2,048-key and 125-byte
capacities cover the binding 1,842-endpoint catalogue and maximum path length.

Each hour record has 20 latency bits, 11 endpoint bits and one error bit. The
latency sentinel has an ordered, exact uint32 overflow stream. Group counters
cover the binding 3,100,000 records; error-ppm arithmetic uses uint64. SIMD loads
stay within complete-record slices. No hash is used as endpoint identity.

Workers gather individual hours and compute exact nearest-rank percentiles.
Groups of at most 16 values are sorted; larger groups use restricted successive
select_nth_unstable calls. Output streams in hour and full endpoint byte order.
Duplicates count separately. Empty input creates a zero-byte summary. Successful
output is checked closed before _exit; kernel cleanup remains timed.

## Build and dependencies

Rust 2021 edition, standard library and Linux system calls only. No third-party
runtime dependencies: dependency_count = 0, D = 1. Rust 1.99.1 and Debian images
are pinned to allowlisted digests. The offline build targets x86-64-v3 (AVX2,
no AVX-512) and links statically. Exactly /out/summary.txt is written.

## Validation and measurements

The continuation-8 mix passes 97 comparisons in release, AddressSanitizer and
checked-arithmetic builds, including both full seeds. Direct tests cover 4,375
guard-page parses, concurrent exact publication, range alignment at every byte
of a fixture, decimal widths and percentile ranks. A rebuilt-standard-library
ThreadSanitizer test also passes exact publication. The rebuilt offline image
passes the official starter sandbox and full hash. See PERF.md and
research/CONTINUATION8_RUST.md for exact artifacts and official decisions.

## Further work

Profile buffered parsing, exact lookup, gathering and ordered output on the
scoring CPU. Compare the complete coefficient before retaining a change.
