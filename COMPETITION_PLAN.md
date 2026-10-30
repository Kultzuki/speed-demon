# CodeScythe: Speed Demon 2026

## Scope

Enter and optimize all four tracks: A Ingest, B Index, C Join, D Traverse.
Solo entrant: Prashant Krishan Bharti. Team: CodeScythe. Codex assists with
implementation and validation. Preferred initial implementation language:
C++, with standard-library-only runtime dependencies where practical. Change the
language only if implementation needs or measured results justify it.

Deadline: 2026-11-02 15:00 UTC / 20:30 IST.

## Current state

- Official starter downloaded on the `speed-demon` branch.
- Team set to CodeScythe in all four track manifests.
- All four tracks now have C++20 implementations. All four full public output
  hashes pass, and 57 additional differential cases pass (worked examples,
  tiny seeds 1/2/17, sample seeds 2/17, and adversarial cases). No C++ board
  score has been claimed yet.
- Windows laptop: 16 GB RAM reported by the entrant; 16 logical processors.
- Native C++ compiler verified: C:/msys64/ucrt64/bin/g++.exe, GCC 16.2.0.
- Rust compiler also available, version 1.95.0.
- Docker Linux engine verified running on WSL2, cgroup v2, with 16 logical CPUs
  and 7,191,322,624 bytes (approximately 6.70 GiB) of VM memory available.
- C: now has approximately 32.0 GB free. This is sufficient to begin; monitor
  space after pulling compiler images and generating additional datasets.
- Submission repository: https://github.com/Kultzuki/speed-demon (public, MIT,
  speed-demon branch verified). Local origin is connected and fetched; no local
  changes have been pushed. Upstream points to the organizers' starter.
- Participant registration and updated team form are reported complete. The
  public board independently confirms all four tracks are registered and the
  app successfully watches this repository. Solo entrant: Prashant Krishan Bharti.

## Resource plan

Use one track build or benchmark at a time. Start with a 6 GB WSL/Docker memory
budget on the 16 GB host; this is a local planning estimate, not a validated
requirement. Monitor host memory and raise toward 8 GB only if necessary and
Windows has headroom. Official scoring allows 8 GB per run and 12 hardware
threads; local Windows measurements are not official performance evidence.
The current approximately 6.70 GiB Docker VM allocation is suitable to begin;
no resource-setting change has been made.

Avoid extra compiler images until needed. No GPU or paid cloud server is needed
to start. Keep generated data and build outputs out of Git.

## Coefficient and optimization decisions

Read and verified https://speeddemon.dev/#coefficient on 2026-10-30.

K = (T_ref/T)^0.50 * min(50, M_ref/M)^0.20
    * min(1, S_ref/S)^0.15 * (1/D)^0.15

D is 1 plus the count of direct non-standard-library runtime dependencies;
the reference D is 1. S is formatted source code lines as counted by the
organizers, not unformatted/minified line count. Each track is counted
separately. Machine speed score = clamp(50 * log10(K), 0, 100).

Prioritize measured wall-time reductions and compact memory. Accept added
source or dependencies only when their performance gain justifies the score
cost and their use is permitted by the frozen track spec. Shorter-than-reference
code gives no additional size benefit, and memory gains beyond a 50x ratio give
no additional memory benefit. Preserve readability and evidence for the 35%
judging component. Best-three track totals determine the overall title; enter
all four as requested.

## Work sequence

1. Read the frozen specifications, harness, generators and references.
2. Establish the official reference outputs and local hash checks on small
   datasets for every track; verify full public downloads against their hashes.
3. Implement correct C++ solutions for all four tracks and validate exact bytes
   against the references on multiple generated seeds and edge cases.
4. Verify each Linux container builds offline from an allowlisted digest and
   passes the official execution sandbox. Native Windows checks do not replace
   these checks.
5. Connect the team's GitHub repository to the board and obtain run IDs early.
6. Optimize one measured bottleneck per experiment; record the commit, data
   seed, hash, local time, memory, board run ID and any regression. Distinguish
   local measurements from official board measurements in every PERF.md.
7. Check clean offline builds and repeated deterministic output before freeze.
   Keep README, PERF.md, manifests and OSI license accurate, and make the
   submitted repository public within the official freeze rules.

## Initial hypotheses to benchmark

- A: specialized byte parsing, endpoint/hour aggregation, exact percentiles,
  compact latency storage. Read exact percentile and rounding rules first.
- B: read queries before building the index; retain required terms/positions,
  preserve exact tokenization and Boolean semantics, order intersections by
  candidate count where semantics allow.
- C: quote-aware CSV state machine, exact integer cents, region lookup, exact
  distinct unescaped names and UTF-8 byte accounting. Never trim significant
  spaces or use approximate distinct counting.
- D: compact adjacency arrays, fast integer parsing, 64-bit distances, lean
  priority queues, and query search choices checked against zero weights,
  duplicates, directed edges and unreachable pairs.

These are hypotheses, not measured performance claims. No cached answers,
input recognition shortcuts, or assumptions tied to the public seed.

## Official sources

- https://speeddemon.dev/
- https://speeddemon.dev/kickstart/
- https://speeddemon.dev/board/#datasets
- https://github.com/hackathon-raptors/speed-demon-2026
- https://github.com/apps/speed-demon-board
