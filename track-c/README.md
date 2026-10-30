# Track C: Join

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

AVX2 quote parity finds record-safe chunk boundaries, including doubled quotes and embedded newlines. Six workers scan fields with memchr and aggregate exact integer cents and decoded byte lengths. A read-only direct region lookup resolves the join. One shared name catalog is divided into 256 mutex-protected shards; each owns a growing exact hash table, byte arena and country-membership words. This avoids copying the entire catalog per worker. Full byte equality resolves collisions and offsets survive arena growth. The lock covers both interning and membership insertion, so each distinct name/country pair increments exactly one worker's count. Country totals are merged after joining the threads.

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

Measure shard count, parser phases and lock contention on the official CPU. Preserve exact quoted-field, name-growth and cross-worker membership tests.
