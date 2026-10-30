# Research and experiments for the frozen Speed Demon workload

Research started October 30, 2026, after the verified four-track entry reached
47.178 overall on the public board. All four tracks remain in scope. The source
of truth for correctness and allowed techniques is the frozen spec/harness;
an external benchmark is not a performance promise for our data or CPU.

## Relevant primary sources

1. [Duan et al., A Faster Directed Single-Source Shortest Path Algorithm (February 2026)](https://arxiv.org/abs/2602.07868).
   Improves a directed SSSP asymptotic bound. Our inference: a complete SSSP
   algorithm is a poor first candidate for bounded local point-to-point queries
   with parsing and preprocessing included in the timer. Not implemented merely
   because it is newer.
2. [Castro et al., experimental implementation, revised February 2026](https://arxiv.org/abs/2511.03007).
   The authors' implementations of the 2025 algorithm remained slower than
   Dijkstra on their sparse random, grid and road tests. This result concerns
   their implementation and tested graphs; it does not prove the 2026 algorithm
   cannot help. It strengthens the case for measuring constants on our workload.
3. [Bertram et al., bidirectional Dijkstra theory, August 2026](https://arxiv.org/abs/2608.24380).
   Studies positive-weight graphs and different adjacency-order models. Our
   spec also permits zero weights and multiedges. Do not claim its theorem
   directly proves our implementation optimal.
4. [Delling et al., PHAST original research report](https://www.microsoft.com/en-us/research/wp-content/uploads/2010/09/phastTR.pdf).
   Motivates the importance of locality, graph ordering and hardware use. We
   are not importing a route-planning index or claiming PHAST's full-source
   performance for our point-to-point run. Candidate: compact visited-distance
   state, then sweep worker count and measure memory against time.
5. [Danny van Kooten, original C 1BRC progression](https://www.dannyvankooten.com/blog/2024/1brc/).
   Reports a progression using a low-load flat table, mmap, custom integer
   parsing and independent parallel chunks. A shares the parsing/grouping shape,
   but adds exact percentiles, hours and significant output volume. Candidate:
   independent line-aligned parser chunks followed by an exact merge.
6. [Abseil Swiss-table design notes](https://abseil.io/about/design/swisstables).
   Describes a dense one-byte metadata array, seven hash fingerprint bits,
   SIMD candidate filtering and full equality checks. Candidate for B: a
   read-only query dictionary with separate compact metadata and IDs. Our own
   implementation from the design, not a vendored Abseil dependency.
7. [Lemire, Boytsov and Kurz, SIMD compression/intersection](https://arxiv.org/abs/1401.6399).
   Studies SIMD decoding and intersections, including galloping for skewed
   posting lengths. B permits basic bitmap/compression helpers, but bans full
   search engines. Candidate: compare adaptive sparse lists/dense bitsets;
   preserve strictly left-to-right Boolean evaluation.
8. [Culpepper and Moffat, efficient set intersection](https://jsc.github.io/publications/cm10-tois-final.pdf).
   Examines representation/access tradeoffs and hybrid integer/bitvector sets.
   Candidate: use bitsets for frequent terms instead of materializing long
   intermediate integer vectors. Construction cost remains timed here.
9. [Chris Wellons, original SIMD CSV explanation](https://nullprogram.com/blog/2021/12/04/).
   Explains quote-state masks spanning vector chunks, including doubled quotes.
   Candidate for C: quote-parity masks to find safe record boundaries before
   parallel parsing; never split on a bare LF inside a quoted note.
10. [Sep author's May 2025 measurements](https://nietras.com/2025/05/09/sep-0-10-0/).
    Its headline throughput concerns low-level row parsing on AVX-512 hardware.
    Our scoring CPU has AVX2, not AVX-512, and our timer includes joins and
    distinct names. Treat this as evidence for parser structure, not our target
    throughput or a directly transferable speedup.
11. [medialab simd-csv implementation notes](https://github.com/medialab/simd-csv).
    The authors report that wider SIMD is not universally faster and distinguish
    quoted/unquoted scanning. Our C generator quotes nonempty names and notes;
    retain a measured scalar/memchr comparator rather than assume a vector
    classifier must win.

## Candidate evaluation

| Track | Candidate | Main risk | Decision rule |
|---|---|---|---|
| A | Independent parser chunks, local groups, exact merge | extra allocations/memory and merge cost | compare full hashes, multiple seeds and coefficient |
| B | SIMD control-byte query dictionary | hash collisions and wrapped probe groups | exact byte comparison, fuzzing, whole-run measurement |
| B | Adaptive bitsets for common terms | bitmap construction/extra source may outweigh queries | profile index versus query cost first |
| C | AVX2 quote-parity boundary discovery | quotes/newlines across vector boundaries | compare every hostile CSV case and sanitizer checks |
| D | Packed distance plus generation tag | numeric range or tag wrap errors | derive bits from (n-1)*UINT32_MAX; test large weights and wrap |
| D | Worker count sweep | minimum time may have worse K due to memory | serialized repeated runs, then official board |

New experiments remain candidates until measured. Keep failed trials and their
data; do not replace a correct measured implementation based on an external
paper's or blog's headline alone. Source size and dependency costs are part of
the decision. Record official run IDs in each PERF.md.
