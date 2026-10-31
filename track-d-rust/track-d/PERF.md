# PERF.md: Track D

Local times are full scale, seed 1, on a 2-core dev VM; the scoring box has 12 threads. Board run IDs go next to each step once pushed. Every step's output matched the published sha256 `a23dbdf0…` at full scale and `a4c76ed0…` at sample scale, and matched the reference byte for byte at tiny scale.

| Step | Change | Local time | Board run |
|---|---|---|---|
| 0 | Naive Python reference | 72.69 s on the scoring box (published) | — |
| 1 | C++: parallel mmap parse, CSR, one Dijkstra per query with a binary heap, threads pull queries from an atomic counter; s == t / no in-edges / no out-edges answered without searching | 5.55 s | _run ID_ |
| 2 | Profiled: parse 0.31 s, CSR 0.47 s, queries 4.4 s. Queries were cache-miss bound because input ids are shuffled. Renumbered nodes in BFS order | 3.23 s | _run ID_ |
| 3 | Counted 23.2 M settled nodes for 2,000 queries. Replaced `std::priority_queue` with a radix heap | 2.15 s | _run ID_ |
| 4 | Distance arrays from `calloc` (distance + 1, 0 = unseen), so untouched pages are never charged. Peak anonymous memory 180 MB with 2 threads; time unchanged | 2.10 s | _run ID_ |
| 5 | Edges stored as fixed `(u, v, w)` triples instead of a flat `u32` vector with `insert`; edge loop walks local `Arc *` pointers, because `touched.push_back` forced the compiler to reload `first` and `arcs` on every edge (aliasing) | median of 8: 1.98 s | _run ID_ |

## C++ vs Rust, same algorithm

A line-for-line Rust port (same parse, CSR, BFS renumbering, radix heap) gave the same output and ran faster locally: median 1.79 s vs 1.98 s over 8 alternating runs, 168 MB vs 180 MB peak. Rust's no-aliasing guarantee helped in the query loop even after the pointer fix above. But the Rust port is 288 counted lines against 200 for C++, and under K = T^0.5 · M^0.2 · S^0.15 the two land within 1% of each other. Which one ships is decided by board runs on the scoring box: _run IDs_.
