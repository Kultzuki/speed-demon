# Track D: Traverse (Rust, no dependencies)

1. **Parallel parse.** `graph.txt` is memory-mapped and its edge lines are split into one piece per thread. Out- and in-degrees are counted with relaxed atomics while parsing.
2. **Compressed adjacency (CSR).** One offset per node, then each node's `(head, weight)` pairs stored together, filled by a parallel scatter.
3. **BFS renumbering.** Node ids in the input are a random shuffle, so a search on the raw ids misses cache on almost every edge. Renumbering nodes in BFS order puts road-network neighbours next to each other in memory. This alone cut the run from 5.5 s to 3.2 s on a 2-core dev machine.
4. **Dijkstra with a radix heap.** Dijkstra only ever pops increasing keys, so a radix heap (items bucketed by the highest bit where they differ from the last minimum) replaces the binary heap. 3.2 s to 2.2 s.
5. **Cheap exits.** `s == t` answers 0. A target with no in-edges, or a source with no out-edges, answers -1 without searching; the reference sweeps the entire graph for these.
6. **One query per thread at a time**, handed out from an atomic counter. Each thread keeps one distance array and resets only the entries it touched. The arrays come from `vec![0; n]`, which allocates zeroed pages, so the kernel only charges memory for pages a search visits.

Distances are 64-bit: paths can exceed 2^32 - 1.

Dependencies: none (Rust standard library; `mmap` is declared directly against libc, which std already links).

With another 24 hours: bidirectional search (roughly halves the nodes settled per query, at the cost of a reverse graph), and a parallel BFS or a cheaper locality ordering to shorten the serial build step.
