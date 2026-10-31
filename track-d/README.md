# Track D: Traverse

Solo entry: CodeScythe / Prashant Krishan Bharti.

## Approach

Six parsers build forward and reverse compact CSR in two passes. Node width is
derived from n; sentinel weights use a sorted, exact uint32 overflow table.
Every edge and duplicate multiplicity is retained.

Twelve query workers run balanced bidirectional radix Dijkstra. The radix heap
builds on the user's supplied Rust work, preserved in ../track-d-rust/.
Heap entries retain aligned full uint64 keys. Each worker owns separate aligned
uint64-distance and uint32 node/generation-tag arrays. Tag widths derive from n;
epoch exhaustion clears every tag before reusing epoch 1. Distances are never
narrowed. The stopping condition uses valid frontier-minimum lower bounds.
Answers retain input order, including duplicate and unreachable queries.

The supplied BFS/forward-search and packed one-pass intermediate variants were
measured separately and preserved. The selected kernel uses the established
two-pass CSR without BFS remapping, sharding or packed heap entries. Small inputs
and query sets use one worker. Output is checked closed before _exit; process
and kernel cleanup remain timed.

## Build and dependencies

Rust 2021 edition, standard library and Linux system calls only. No third-party
runtime dependencies: dependency_count = 0, D = 1. Rust 1.99.1 and Debian images
are pinned to allowlisted digests. The offline build targets x86-64-v3 and links
statically. Exactly /out/distances.txt is written.

## Validation and measurements

The continuation-8 mix passes 97 comparisons in release, AddressSanitizer and
checked-arithmetic builds, including both full seeds. Direct Rust tests cover
rehash, membership, derived epoch widths and forced wrap, full uint32 weights,
full uint64 distances, and repeated zero/unreachable paths. An independent text
parser verifies every forward/reverse edge and duplicate in two 200,000-edge
parallel-build fixtures. The rebuilt offline image passes the official starter
sandbox and full public hash. See PERF.md and research/CONTINUATION8_RUST.md for
measured outcomes and official retention decisions.

## Further work

Measure sparse lookup, heap work and construction on the scoring CPU. Preserve
all exact width/epoch fallbacks and compare complete coefficients.
