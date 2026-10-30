# Research request: help CodeScythe close the Speed Demon 2026 performance gap

You are my research partner for a live systems-performance competition. Do
source-backed research, check the actual frozen specs, and give implementation-ready
recommendations for all four tracks. I need ideas that can improve our measured
score, not a generic list of optimization tips. Be direct about what is proven,
what another author measured, what you infer, and what still needs an experiment.

Research as of **October 30, 2026**. Deadline: **November 2, 2026, 15:00 UTC /
20:30 IST**. Team: **CodeScythe**, solo entrant **Prashant Krishan Bharti**, assisted
by Codex. We are implementing and benchmarking while you research.

## 1. Read these authoritative sources first

- Competition and coefficient: https://speeddemon.dev/#coefficient
- Datasets and public output hashes: https://speeddemon.dev/board/#datasets
- Frozen specs, generators, references, scoring and sandbox harness:
  https://github.com/hackathon-raptors/speed-demon-2026
- Track A: https://github.com/hackathon-raptors/speed-demon-2026/blob/main/specs/a-ingest.md
- Track B: https://github.com/hackathon-raptors/speed-demon-2026/blob/main/specs/b-index.md
- Track C: https://github.com/hackathon-raptors/speed-demon-2026/blob/main/specs/c-join.md
- Track D: https://github.com/hackathon-raptors/speed-demon-2026/blob/main/specs/d-traverse.md
- Calibration: https://github.com/hackathon-raptors/speed-demon-2026/blob/main/harness/calibration-seed1.json
- Toolchain allowlist: https://speeddemon.dev/allowlist.json
- Our source and optimization logs: https://github.com/Kultzuki/speed-demon/tree/speed-demon

The frozen specs and executable harness take precedence over website summaries
or old discussions. Report discrepancies instead of silently choosing a rule.
Do not pretend you inspected a source or ran code if you could not access it.

## 2. What the score rewards

For each track:

```text
K = (Tref/T)^0.50
  * min(50, Mref/M)^0.20
  * min(1, Sref/S)^0.15
  * (1/D)^0.15

D = 1 + direct non-standard-library runtime dependencies
speed_points = clamp(50 * log10(K), 0, 100)
```

S is code lines after the organizers' formatter and line counter, per track's
complete build folder. Minification does not help. Smaller-than-reference code
earns no bonus. Extra source or dependencies can be worth their cost if speed
or memory improves enough. Do not prioritize tiny code over a much faster exact
implementation.

Final track score is 65% machine score and 35% human judging, covering code
quality, technique and an honest PERF.md with actual board run IDs. The overall
title uses the geometric mean of the best three track totals. We enter all four.
The public board shows machine scores, not final judging/holdout results.

Published calibration:

| Track | Tref, seconds | Mref, bytes | Sref, formatted code lines |
|---|---:|---:|---:|
| A | 32.047276 | 227983360 | 56 |
| B | 56.352376 | 2199961600 | 91 |
| C | 14.444059 | 367435776 | 108 |
| D | 72.692655 | 892915712 | 43 |

All reference dependency weights are 1.

## 3. Our measured position and the leader's snapshot

These are public-board measurements/screenshots, not final results. Displayed
times and memory below are rounded. Use exact run records in our repo if needed.

Our best public score snapshot: **47.178 overall, rank 13**.

| Track | Machine points | Time | Memory | Source lines | K |
|---|---:|---:|---:|---:|---:|
| A | 50.439 | 0.409 s | 47 MB | 180 | 10.204190 |
| B | 36.159 | 2.192 s | 643 MB | 355 | 5.286576 |
| C | 48.870 | 0.453 s | 13 MB | 288 | 9.493120 |
| D | 42.600 | 1.189 s | 356 MB | 276 | 7.112136 |

B is currently dropped from our overall calculation. All four pass correctness,
timeout and sandbox gates. These per-track bests may come from different commits.

Leader ALL STAR, user-provided screenshot: **70.989 overall**.

| Track | Machine points | Time | Memory | Source lines | K |
|---|---:|---:|---:|---:|---:|
| A | 77.758 | 0.034 s | 20 MB | 492 | 35.906095 |
| B | 65.572 | 0.270 s | 73 MB | 832 | 20.485249 |
| C | 70.164 | 0.051 s | 14 MB | 549 | 25.309519 |
| D | 62.601 | 0.271 s | 91 MB | 508 | 17.865685 |

Their D is dropped. Treat this as a dated snapshot, not a guarantee the leader
has stopped improving. Explain how the time/memory gaps change our priorities.
Do not invent their implementation from these numbers.

## 4. Hardware, build and fairness constraints

- Scoring CPU: Intel Core i5-13500, six P-cores / 12 hardware threads pinned,
  turbo disabled. AVX2 available; AVX-512 unavailable. Verify cache topology if
  your recommendation depends on exact cache sizes.
- Runtime: Linux x86-64 container, 8 GB memory cap, no swap, 512 processes,
  no network, read-only root and /data. Write exactly the required file in /out.
  Scratch /tmp is 1 GB tmpfs and its memory costs count.
- Inputs are prewarmed. The timer covers process execution, parsing,
  preprocessing, all queries, output and exit. Container startup is excluded.
  Final T is the middle-three mean of five runs; M is measured by the kernel.
- Organizer M_bytes is authoritative. File-mapped process RSS in our local
  experiments differs substantially from the board's memory accounting.
- Builds are offline, at most 10 minutes, images at most 2 GB. Every FROM must
  be allowlisted and pinned by digest. No downloading dependencies during build.
- Native CPU compilation and build-time PGO on generator output are permitted;
  /data is not mounted at build time. Confirm the exact policy in the harness.
- Final inputs use a hidden seed from the same specified distribution. No cached
  answers, public-seed recognition, hardcoded unknown keys, or incomplete
  heuristics. Every output byte must match on every run.
- Ready-made analytics/dataframe/SQL engines are banned for A/C; search engines
  are banned for B; shortest-path/index-building libraries are banned for D.
  Basic parsers, hash maps, allocators, bitmaps, heaps and compression helpers
  may be allowed and charged. Check the actual lists before recommending one.
- We use C++20, GCC 16, static executables and zero third-party runtime
  dependencies. Rust is available if a measured advantage justifies switching.
- Development machine: Windows, 16 GB RAM, WSL2/Docker with about 6.7 GiB
  available. No GPU or paid cloud server. Official board access is connected.

## 5. Exact tasks and current implementations

### A: Ingest

3.1M ASCII space-delimited log lines, about 238.8 MB. Each line has a fixed
27-byte UTC timestamp, method, endpoint, three-digit status, uint32 latency in
microseconds. Exactly 1,842 endpoint templates at full scale; most change with
the seed. The time span is fixed at 72 hours, crossing October/November. Lines
are out of order; do not assume bounded disorder.

Group by exact endpoint bytes and UTC hour. Output count, nearest-rank
p50/p95/p99, 5xx count and floor error parts-per-million, sorted by hour then
endpoint bytes. Preserve duplicates, 499 versus 500, latency 0 and UINT32_MAX.
Percentile rank is ceil(p*n/100), with no approximation. Full output is about
10.1 MB, which is part of the timed work.

Current: mmap, direct hour parsing, endpoint interning, 72 groups per endpoint,
vectors of latencies, sort small groups / nth_element for larger ones, exact
integer formatting. Single parser. A prior percentile partition bug was fixed
and regression-tested.

Investigate: allocation-free/flat aggregation, chunk-local state, packed records,
counting/radix partitioning, exact selection versus full sorting, SIMD/SWAR
endpoint scanning, hash layouts, output buffering and worker-count tradeoffs.

### B: Index

250,000 documents, about 253.8 MB, 36.3M tokens. 50,000 queries: 31,000 Boolean
and 19,000 phrase. All queries are readable before indexing. Tokens are maximal
ASCII [a-z0-9] runs after ASCII-only lowercasing. Each byte >=128 is a separator;
no Unicode case folding, stemming or stopword removal. Corpus tokens are at
most 32 bytes. Boolean operators are strictly left-associative, with no
precedence or parentheses; NOT is binary set difference. Phrases are 2–8 exact
adjacent tokens, including repetitions and across punctuation, never documents.
Output only count, exact ID sum and up to ten smallest document IDs per query.

Current: query-term-only dictionary, six independent parser blocks, sorted
document posting lists, occurrence lists and a global token-ID array with
document boundary bits. Boolean operations merge integer lists. Phrases choose
the least frequent occurrence list and compare adjacent IDs exactly.

Important: the full uint32 token array alone is about 145 MB, already larger
than the leader's entire 73 MB memory figure. Do not assume this architecture
should remain. Research a lower-memory design: sparse/dense adaptive postings,
query-role-aware indexing, rare-anchor candidate documents, on-demand scanning
of raw mapped document text, selective positions, byte offsets, small-query
automata, direct result aggregation without materializing full result vectors,
and SIMD/galloping intersections. Include index construction and merge costs.
Mixed Boolean expressions cannot simply be reordered by document frequency.

### C: Join

3.32M CSV records, about 201.9 MB, plus a plain 200k-region lookup table. Five
fields: id, name, note, region_id, amount. Handle quoted commas, doubled quotes,
embedded LF in notes, mixed CRLF/LF, BOMs at record boundaries, empty names,
significant trailing spaces and a final record without a newline. Region misses
map to _UNMATCHED. Join and aggregate by country: count, ID sum, exact cents
sum/min/max, exact distinct unescaped names, name_bytes and note_bytes. Sort keys
bytewise. Money is signed integer cents, never floating point.

Current: memchr-based quote scanning; materialize names only for unescaping,
count note bytes without storing notes; direct region lookup; flat exact name
table with compact owned-string arena, stable offsets and four 64-bit country
membership words per name. Hash collisions compare full bytes. Dynamic growth
and escaped-name cases pass sanitizers and full hashes.

Investigate: AVX2 quote-prefix parity, selective field parsing/materialization,
chunk boundary discovery, parallel local aggregation and exact bitmap merges.
Compare full-workload coefficient, not parser-only GB/s. Low-level CSV benchmark
claims on AVX-512 hardware do not transfer directly to this AVX2 CPU.

### D: Traverse

Directed graph: 1,740,512 dense-ID nodes, 5M unsorted uint32-weight edges, about
92 MB, 2,000 point-to-point queries. Zero weights, duplicates, parallel edges,
self-loops, isolated vertices and unreachable pairs occur. Distances can exceed
2^32 and must be exact 64-bit values. Graph resembles a road network but node
IDs are randomly relabeled. Most queries are local: median Dijkstra settlement
rank about 512, mean about 12,300, maximum 131,071; read the precise distribution.
Preprocessing is timed, so expensive indexes may not amortize.

Current: forward/reverse CSR, two parsing passes, bidirectional Dijkstra with
radix heaps, six workers, per-worker distance arrays and generation stamps.
Early no-out/no-in checks. All arbitrary directed multigraph fuzz cases pass.

Investigate: locality-preserving relabeling, packed distance+generation state,
sparse versus dense search state, heap/bucket layouts, exact bidirectional
termination, worker-count/M tradeoffs and graph construction costs. Do not
assume all queries warrant full-source searches or contraction hierarchies.
Any proposed heuristic must remain exact with directed edges and zero weights.

## 6. Experiments already underway: do not mistake them for board results

These are three-run local WSL2 trials, with verified Linux-local full public
inputs. They are NOT directly comparable to the Intel board timings above.
Every listed trial matches its full output hash; unseen-seed/sanitizer/official
verification is still required before promotion.

- A: baseline median 0.350s; three parser workers 0.223s; six workers 0.183s.
- B: original flat dictionary 2.172s; Swiss-style SIMD metadata alone 2.171s
  (a tie within noise). Selectively building only chosen phrase-anchor positions
  gives about 2.011s and lowers peak RSS from 852 to 626 MiB. Adding metadata
  probes gives 1.953s; adding AVX2 token-length/case classification gives 1.902s.
- C: compact single-thread baseline 0.516s / 206 MiB RSS. Quote-safe AVX2
  partitioning plus three workers: 0.317s / 223 MiB; six workers: 0.256s /
  248 MiB. Extra private memory/source could cancel the time gain in K.
- D: baseline 2.617s / 338 MiB RSS; packed distance+generation with six workers
  2.442s / 258 MiB. Packed-state workers 1/2/3/4 give approximately
  7.427/4.351/3.094/2.757s. BFS relabeling plus packed state gives 1.665s /
  271 MiB, including relabeling. One-pass parsing via a raw-edge buffer regressed
  to 3.299s, so it is not an automatic improvement.

## 7. Research expectations

Search recent papers, strong older work, original engineering writeups and
reproducible implementations/benchmarks. Reddit/Hacker News can identify ideas;
trace technical claims to the original author, code or paper. Prefer primary
sources. Clearly identify benchmark CPU, data shape, compiler and timed scope.

Do not just recommend simdjson, Polars, DuckDB, Roaring, contraction hierarchies
or a new theoretical SSSP algorithm by name. Explain the exact transferable
mechanism, spec fit, dependency/license cost and expected bottleneck. A newer
asymptotic algorithm is not automatically faster on this local-query workload.

Useful leads already found:

- https://abseil.io/about/design/swisstables
- https://www.dannyvankooten.com/blog/2024/1brc/
- https://arxiv.org/abs/1401.6399
- https://jsc.github.io/publications/cm10-tois-final.pdf
- https://nullprogram.com/blog/2021/12/04/
- https://nietras.com/2025/05/09/sep-0-10-0/
- https://github.com/medialab/simd-csv
- https://arxiv.org/abs/2602.07868
- https://arxiv.org/abs/2511.03007
- https://arxiv.org/abs/2608.24380

## 8. Required deliverable

1. Diagnose our gap per track from architecture and measured resource use.
   Separate observations from guesses about the leader.
2. Rank 3–5 concrete candidates per track. Give source links/dates, transferable
   idea, exact implementation sketch or pseudocode, additional memory/lines,
   correctness risks, and confidence. Distinguish estimated gains from measured
   gains; provide plausible bounds instead of invented precise speedups.
3. Propose a complete low-memory B architecture, not just a faster hash table.
4. Provide a practical A path toward tens of milliseconds and explain how exact
   percentiles and 10 MB output are handled without excessive allocation.
5. Assess whether C parallelism and D relabeling pay after preprocessing,
   memory and formatted source are charged.
6. Give an experiment matrix: baseline, one change at a time, seeds/scales,
   edge cases, repeated serialized runs, memory measurement, and revert criteria.
   Identify what must be verified on the official runner.
7. Prioritize an implementation sequence for the next 2 hours, then the next
   8–12 hours. Account for the five-minute board submission limit and best-three
   geometric mean. Cover all tracks while maximizing overall improvement.
8. Include rejected ideas and why they are a poor fit. Flag any unresolved rule
   question that needs organizer clarification.

Be thorough enough to implement from your answer. Spend effort on the few ideas
most likely to improve K materially. Do not fabricate tests, run IDs, papers,
benchmark numbers, hidden-seed guarantees or claims that we can certainly win.
