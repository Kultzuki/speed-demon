# Track C: Join

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

The published section 2.2 contract makes LF followed by a digit or BOM a record
boundary: names contain no LF and note text contains no digits/BOM. Local cut
discovery uses that rule; it is not a general arbitrary-CSV boundary shortcut.
Up to twelve workers parse complete mapped ranges with memchr, preserving
escaped quotes and significant spaces. A sixteen-record pipeline prefetches
the exact name table while retaining decoded escaped names until their lookup
retires. There is no fixed record cap. Totals use exact cents and decoded byte
lengths. The losing buffered implementation from 12aa1a4 has been removed.

The lookup's byte-sized country IDs are justified by the 240-country input
bound plus the unmatched group. A shared catalog has 256 shards, immutable
owned names in growing arenas, and release/acquire publication. Exact equality
uses the complete decoded bytes. Only insertion misses take a shard lock;
atomic membership elects exactly one count per name/country pair. Compact
nodes avoid redundant stored hashes and string-view descriptors. There is no
fixed record-length, distinct-name-count or suffix-arena limit. Country totals
merge after every parser joins.

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
