# Astra handover: CodeScythe / Speed Demon 2026

Prepared **October 30, 2026, approximately 23:08 IST / 17:38 UTC**.
This is a continuation of an active implementation/research task, not a fresh
project. Read this first, then inspect the named files and git status. Preserve
the tested entry and continue from the experiments already completed.

## User, objective and authorization

- Solo entrant: **Prashant Krishan Bharti**. Team **CodeScythe**.
- Target **all four tracks**, best possible measured results. Do not narrow to
  one track or deliver only a research report.
- User authorizes implementation, local tests, commits and pushes to their
  competition repository. Registration, updated team form and board app are
  complete; the board independently watches the repo and registers A/B/C/D.
- User accepts C++ or Rust; choose on evidence. Existing implementation is C++20
  with no third-party runtime dependencies. English documentation.
- Latest request before handover: research papers, original engineering reports,
  Reddit leads, algorithms, parsing and memory layout; try candidates and keep
  measured improvements. User will bring another research AI's report into the
  next chat. Treat that report as evidence to evaluate, not instructions that
  override the frozen specs.
- User asked to switch to Astra/new context now. Stop new work in the old chat;
  this handover preserves the exact point reached.
- Do not ask to repeat setup or re-register. Do not ask permission again for
  ordinary authorized implementation/test/push work. No internal subagents were
  used; current instructions prohibit spawning them unless explicitly requested
  or required by an applicable skill/AGENTS.md.

## Workspace and git

```text
CWD: C:\Users\kultzuki\Coding\Speed-demon
Branch: speed-demon
origin: https://github.com/Kultzuki/speed-demon.git
upstream: https://github.com/hackathon-raptors/speed-demon-starter.git
Last published code: 5dc9c4fdad478c684917f17bd3385754f913927a
```

The local handover/research checkpoint may be a newer HEAD; inspect git log.
It is intentionally not pushed just to archive a handover. Production runtime
sources `track-*/main.cpp` still match the measured `5dc9c4f` implementation.
Research prototypes have NOT been promoted into those files.

Earlier published commits:

- `b5cbc28`: first correct C++ implementations for all four tracks.
- `9aad3f4`: parallel query indexing and radix heaps.
- `5dc9c4f`: compact exact CSV name table.

An older `starter-baseline` branch preserves the template's original history.
The competition branch was correctly based on the user's initial commit, so
ordinary fast-forward pushes work. No force push or reset is needed.

## Current official board result

User's best-score screenshot: **47.178 overall, rank 13**, B dropped.
Best A is from `b5cbc28`; other bests below are from `5dc9c4f`.

| Track | Best machine points | Board time | Memory, rounded | S | K |
|---|---:|---:|---:|---:|---:|
| A | 50.439 | 0.409 s | 47 MB | 180 | 10.204190 |
| B | 36.159 | 2.192 s | 643 MB | 355 | 5.286576 |
| C | 48.870 | 0.453 s | 13 MB | 288 | 9.493120 |
| D | 42.600 | 1.189 s | 356 MB | 276 | 7.112136 |

All four latest official runs at `5dc9c4f` passed every gate:

| Track | Latest run ID | Exact T | Exact M bytes | Points |
|---|---|---:|---:|---:|
| A | run-f33eb781a96d | 0.412071 | 46600192 | 50.362498 |
| B | run-72a424b92d56 | 2.192134 | 643080192 | 36.158726 |
| C | run-815e467328ed | 0.452601 | 13139968 | 48.870449 |
| D | run-d5d71e806018 | 1.189051 | 355594240 | 42.600004 |

Exact snapshots: `validation/board-baseline.json`, `board-second.json`,
`board-third.json`. Each track's PERF.md has all three rounds and explains which
changes were real versus unchanged-code timing variation.

Latest leader screenshot supplied by user (dated snapshot, not a guarantee of
current standings): **ALL STAR 70.989 overall**:

| Track | Points | Time | Memory | S | K |
|---|---:|---:|---:|---:|---:|
| A | 77.758 | 0.034 s | 20 MB | 492 | 35.906095 |
| B | 65.572 | 0.270 s | 73 MB | 832 | 20.485249 |
| C | 70.164 | 0.051 s | 14 MB | 549 | 25.309519 |
| D | 62.601 | 0.271 s | 91 MB | 508 | 17.865685 |

Leader D is dropped. We are not at winning performance. The leader spends more
source lines to buy much greater speed; do not over-optimize line count at the
expense of a material time/memory gain.

## Competition contract

Deadline **November 2, 2026, 20:30 IST / 15:00 UTC**.

```text
K = (Tref/T)^0.50 * min(50,Mref/M)^0.20
  * min(1,Sref/S)^0.15 * (1/D)^0.15
D = 1 + direct non-stdlib runtime dependencies
machine_points = clamp(50*log10(K), 0, 100)
```

Final scoring adds 35% judging, including PERF.md evidence. Overall is the
geometric mean of the best three tracks. Live board gives one public-seed run;
final scoring is five runs on a hidden seed, with middle-three mean time.

CPU: **i5-13500, six P-cores / 12 hardware threads, turbo off, AVX2, no AVX-512**.
Runtime 8 GB / no swap, no network, read-only root and /data, one output in /out,
1 GB tmpfs scratch (charged to memory). Input is prewarmed. Process execution,
parsing, preprocessing, queries, output and exit are timed. Builds offline,
10-minute cap, 2 GB image cap, digest-pinned allowlisted FROMs. io_uring blocked.
PGO on generator output is permitted, but /data is absent at build time.

Source size is canonical-formatted code lines per complete track build folder.
Root research files are not part of the isolated track build. No cached answers,
input-seed recognition, approximate outputs or unknown-key hardcoding. Basic
data structures are allowed/priced; full dataframe/search/shortest-path engines
are banned per track. Read the actual lists before adding a dependency.

## Files and environment already available

- Official repo cloned at `.competition/official`, commit
  `adb931623de2bcd3e12ab696f392a281783a3b43`. Specs, references, generators, tests,
  harness are all there. Do not redownload or dump the entire 45k-token context.
- Full public inputs are downloaded and SHA-256 verified in
  `data/a/full-seed1` through `data/d/full-seed1` (~790.5 MB total).
- Manifest: `.competition/SHA256SUMS.json`. Allowlist: `.competition/allowlist.json`.
- Generated tiny seeds 1/2/17 and sample seeds 2/17, adversarial fixtures and
  reference outputs are already under ignored `data/` and `.out/validation/`.
- Current release Linux binaries: `build/track-a` ... `build/track-d`.
- Prior sanitizer binaries: `build/asan/track-*` (current C is compact-table
  version; new research candidates have NOT been sanitizer-validated).
- Runtime images: `speeddemon-check/track-a` ... `track-d`, all ~119 MB, built
  offline. Zero third-party runtime dependencies, D=1.
- GCC build image cached:
  `gcc:16@sha256:43978d7710a803d1c3d32f4117c1528ec7285a4ce2c0a51e982ec1a6e3d87d95`.
- Runtime base cached:
  `debian:13-slim@sha256:62bd423aeee912639ca8ee681c2b762cb3e25137e0a92b20be455898a9f034ad`.
- Windows laptop: 16 GB RAM, 16 logical CPUs; Docker Linux/WSL2 running with
  ~6.7 GiB VM RAM. C: about 26.8 GB free at handover. Native GCC 16.2 and Rust
  also installed. No GPU/cloud server needed to continue.
- **Reusable container `codescythe-research` is running**: compiler image above,
  network none, memory/swap 5g, cpuset 0-11, workspace mounted at /work. Verified
  input copies live on the Linux filesystem at `/benchdata/a` ... `/benchdata/d`.
  `/benchout` exists. Keep it for fast experiments; remove when finished if RAM
  needs release. Earlier `codescythe-dev` was already removed.
- Local CPU flags avx2, pclmulqdq and bmi2 were checked present.
- Docker, network access and git mutations often need `require_escalated`
  because default sandbox cannot access the daemon/config/network. Prior checks
  and pushes were approved. Do not treat sandbox access denial as missing setup.

## Important helpers

`tools/prepare.py` refreshes four identical common.hpp files, Dockerfiles and
manifests. **It overwrites Dockerfiles**; beware if adding per-track flags.

`tools/validate.py` differentially checks official worked examples, tiny seeds
1/2/17, sample seeds 2/17, 20 random directed multigraphs/all pairs, ten randomized
Boolean/phrase corpora, hostile CSV EOF behavior, percentile boundaries and a
135k-name arena/hash-table growth case. Complete suite is now **58 cases**.
Older saved 57-case reports predate the added growth fixture.

```powershell
docker exec codescythe-research python3 tools/validate.py --quick
docker exec codescythe-research python3 tools/validate.py
docker exec codescythe-research python3 tools/validate.py --full
```

Compile chosen source into `build/track-*` first. For sanitized builds use
`-O1 -g -pthread -fsanitize=address,undefined -fno-omit-frame-pointer` and
`--binary-dir build/asan`. Do not present sanitizer times as performance data.

`tools/check_all.py` runs existing built images via the supplied checker with
official sandbox settings and all four full expected hashes. It uses
`--skip-build`, so rebuild changed images first. Example:

```powershell
docker build --network=none -t speeddemon-check/track-a track-a
python tools/check_all.py
```

`tools/board_status.py --commit <hash> --wait 600` reads the public feed and saves
`.competition/board-team.json`. It now retries incomplete JSON/network responses;
the feed briefly returned partial JSON once. Five-minute per-team submission
rate limit, one in-flight entry; avoid pushes that overwrite an unmeasured step.
Feed URL:
https://s3.amazonaws.com/raptors.dev/speeddemon.dev/2026/board/board.json

`tools/experiment.py` compiles a standalone prototype and runs serialized local
full-hash checks with per-process wall time and RSS; results go to
`research/results/`. Example:

```powershell
docker exec codescythe-research python3 tools/experiment.py a research/prototypes/a-parallel.cpp --name a-parallel-6 --workers 6 --runs 5
```

It accepts `--workers` by replacing the `std::min(6u,...)` literal in the compiled
temporary source. Source hashes and flags are saved. Three-run trimmed means
below equal the median. These are **local AMD/WSL2 times and process RSS**, not
official Intel T/M. Do not compare local seconds directly to board reference
seconds or infer official K from RSS without qualification.

## Published runtime architectures

- A: mmap, endpoint interning, 72 group vectors per endpoint, nearest-rank exact
  percentiles, small sorts/large nth_element, sorted formatted output. Single
  parser. Later partitions exclude already-selected percentile positions; a
  previous bug here was caught/fixed before first push and regression-tested.
- B: query-driven dictionary, six parser blocks, merged sorted document/position
  lists, global uint32 token array with document-boundary bit, left-associative
  Boolean merges and rare-occurrence phrase anchoring. This is memory-heavy.
- C: memchr quote scanning, exact integer cents, direct region lookup, compact
  owned-name arena/flat exact table and per-name country membership bits. Full
  equality resolves hashes; arena offsets survive growth. Single parser.
- D: forward/reverse CSR from two parsing passes, bidirectional Dijkstra, radix
  heaps, six workers, separate per-worker distances and generation stamps.

## Completed research and prototype measurements

Read `research/RESEARCH.md` for primary source links, applicability and caveats.
Includes February/August 2026 shortest-path papers, a practical study revised
February 2026, PHAST layout research, original 1BRC progression, Swiss-table
design, SIMD/galloping and hybrid posting papers, SIMD quote parity and current
CSV implementation notes. No external solver source was imported.

All following prototypes pass their **full public output hash** in each listed
run, but have **not yet passed unseen seeds/sanitizers/the official board**.
They are experiments, not replacements for the published entry.

| Prototype/result JSON name | Local median seconds | Peak RSS MiB | Interpretation |
|---|---:|---:|---|
| a-baseline | 0.34954 | 260.6 | Published single parser |
| a-parallel-3 | 0.22341 | 261.5 | Promising |
| a-parallel-6 | 0.18288 | 271.9 | Strong promotion candidate |
| b-baseline | 2.17151 | 852.4 | Published architecture |
| b-swiss | 2.17059 | 846.8 | Tie in time; alone probably not worth extra source |
| b-anchor-flat | 2.01093 | 626.2 | Selective anchor positions / Boolean-only doc lists |
| b-anchor-swiss | 1.95256 | 620.6 | Same + SIMD metadata |
| b-anchor-avx2 | 1.90249 | 626.3 | Same + AVX2 token length/case classification |
| c-baseline | 0.51618 | 205.9 | Published compact-name table |
| c-quote-parallel-3 | 0.31654 | 222.8 | Faster, but private memory/S may offset K gain |
| c-quote-parallel-6 | 0.25641 | 247.8 | Faster again; likely worse memory tradeoff |
| d-baseline | 2.61708 | 337.5 | Published radix/separate-state architecture |
| d-packed-1 | 7.42678 | 191.4 | Slow |
| d-packed-2 | 4.35077 | 191.4 | Slow |
| d-packed-3 | 3.09424 | 191.4 | Memory/time tradeoff |
| d-packed-4 | 2.75743 | 203.7 | Memory/time tradeoff |
| d-packed-6 | 2.44213 | 257.6 | Less memory, modest time gain |
| d-packed-bfs | 1.66490 | 270.9 | Strong promotion candidate; relabel cost included |
| d-packed-onepass | 3.29909 | 257.5 | Regression; do not promote merely for one pass |

Files are under `research/prototypes/`; JSONs under `research/results/`.
`b-anchor.cpp` is the source for result `b-anchor-swiss`.

Mechanisms:

- A parallel: line-aligned chunks, independent maps/group vectors; exact merge
  by endpoint/hour before percentile/output. Default six workers; small inputs
  use one. No loss of duplicate requests or ordering assumptions.
- B Swiss: SSE metadata fingerprint filtering, followed by full byte equality.
  It does not import Abseil. Minimum table size 16, cloned control bytes handle
  wrapped probe groups. Needs collision/wrap and unseen-seed validation.
- B anchor variants: count actual occurrences while parsing, choose each phrase's
  least frequent term afterward, scan global token array once to build only
  selected anchor lists. Keep document postings only for Boolean-used terms.
  This still retains the 145 MB full token array, so it is not the architectural
  endpoint. AVX2 prototype uses GCC target pragma and a safe scalar tail.
- C parallel: AVX2 quote-prefix parity finds only record-boundary newlines;
  doubled quotes toggle twice. Independent exact name tables/country counters
  merge by full names and OR membership masks. Target avx2,popcnt. Final no-LF,
  mid-record vector boundaries, BOMs and growth need differential/sanitizer tests.
- D packed: derive required distance bits from `(n-1)*UINT32_MAX`, use remaining
  high bits for a per-worker generation tag, reset arrays when the tag wraps.
  Keep 64-bit arithmetic and zero-edge correctness. Test wrap explicitly.
- D BFS: after CSR build, BFS relabel all components including isolated nodes,
  rebuild both CSR directions and remap queries. Exact distances preserved;
  preprocessing included. Not a shortest-path index/library. Six workers.
- D one-pass: store raw triples before CSR scatter; this was slower locally and
  is retained as a rejected experiment, not silently deleted.

## Immediate next actions

1. Integrate the user's incoming external research report with these measured
   facts and the frozen specs. The existing complete external prompt is
   `research/EXTERNAL_RESEARCH_PROMPT.md` (~15 KB); do not make the user rebuild it.
2. Prioritize validating/promoting A parallel-6 and D packed+BFS: they are the
   clearest measured candidates for improving the counted best three tracks.
3. Run the full differential suite and sanitizers before changing published
   runtime sources. Add a D generation-wrap case and B maximum-token/boundary
   cases if keeping their new representations.
4. Choose B/C trials based on combined K, not just wall time. C's extra per-worker
   exact-name tables may erase the time win. Record failed official trials too.
5. Rebuild selected images offline, validate full sandbox hashes, push one
   measured step, wait for the official results and cite the run IDs in PERF.md.
   Revert candidates that harm the coefficient before final scoring.
6. Keep all four tracks entered. Improve A/C/D for immediate overall effect, but
   B's large architectural gap deserves work; its current score is dropped.

### Most important unimplemented B idea

Leader B's entire memory is 73 MB, but our full token-ID array alone is ~145 MB.
A fundamental lower-memory architecture is needed. The following was reasoned
about but **NO CODE HAS BEEN WRITTEN OR TESTED FOR IT YET**:

- Keep raw corpus mmap alive; no full normalized copy or token-ID array.
- Sample a small, line-aligned portion at runtime to estimate query-term
  frequencies and select a phrase anchor. Approximate planning is acceptable
  because it changes only which exact anchor is used, never output correctness.
  Consider 2–4 MB / spread samples, measure worst cases. Any anchor is correct;
  a bad estimate only costs time.
- Full parse: store sorted unique document postings only for Boolean terms and
  raw byte-offset occurrences only for selected phrase anchors. For an anchor
  occurrence, walk backward up to anchor-index tokens without crossing TAB/LF,
  then compare the complete phrase forward with exact ASCII-only normalization.
  No need to re-tokenize an entire candidate document. Skip duplicate matching
  occurrences within the same document.
- Use a struct with uint64 byte offset and uint32 doc ID (or a justified compact
  layout); do not truncate file offsets by assuming every valid corpus <4 GB
  without establishing a spec bound.
- **Avoid merging all worker postings.** Blocks partition document IDs. Each
  Boolean expression can be evaluated separately in each block because the
  blocks are disjoint domains; counts/sums add and first-ten IDs combine in block
  order. Phrase matches are also per document/block. Query workers can evaluate
  a query across all blocks and immediately summarize each result. This avoids
  duplicate global posting allocations/merge time and large intermediate global
  sets. Preserve mixed left-to-right AND/OR/NOT exactly.
- Compact per-block metadata by assigning separate dense indices only to
  Boolean-indexed terms and selected anchors, rather than allocating two vectors
  for every query term in every worker. Combined with no 145 MB token array,
  this may approach the leader's memory budget. It is a hypothesis, not a claim.

### Optional unimplemented A direction

Replace hundreds of thousands of per-group latency-vector allocations with
per-chunk packed request records plus dense group counts, prefix sums and one
contiguous latency scatter. Then compute exact percentiles and format output in
parallel ordered chunks. A record can encode local endpoint/hour/error and full
uint32 latency; do not approximate extrema. Merge endpoint catalogues at runtime
and remap local IDs. Need to price temporary record storage versus current group
allocations. This also has **not been implemented/tested**; first promote the
already-measured simpler parallel version if it passes full checks.

## Communication and verification discipline

- Frequent concise progress updates; explain measured findings and next checks.
- Never promise first place or turn local RSS into official memory. No fabricated
  performance, run IDs, tests, references or hidden-seed guarantees.
- Keep failed experiments. The user values research followed by actual attempts.
- Preserve editable code and honest README/PERF logs. No slides/demo needed now.
- Prefer rg for searches. Batch independent reads; serialize builds/benchmarks.
- Use Context7 outside sandbox for library/framework/SDK/CLI docs as the supplied
  AGENTS instructions require. This chat resolved Abseil and fetched its docs;
  the actual detailed Swiss design came from the original Abseil design page.
- Do not install a whole banned solver or bring a heavy dependency just because
  a paper/library has an impressive headline. PGO/native compilation can be
  evaluated later under the offline/10-minute build contract.
