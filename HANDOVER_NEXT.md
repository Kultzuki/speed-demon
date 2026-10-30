# Speed Demon continuation handover - October 31, 2026

Read this completely before acting. This continues a working four-track entry;
**do not restart the project, re-register, or replace measured code with a report**.
The user wants to refine further in a new chat toward first place. No placement
is promised. This chat has finished its implementation and official measurement.

## Checkpoint and authorization

- Workspace: `C:\Users\kultzuki\Coding\Speed-demon`.
- Branch: **speed-demon**, the branch watched by the board. Stay on it for
  competition submissions; do not force-push/reset existing history.
- Origin: `https://github.com/Kultzuki/speed-demon.git`.
- Started this chat at clean **df84b71**, after reading all of `HANDOVER_ASTRA.md`.
- Latest implementation: **0c89c6e71d502e9edee2b646072b86f9b48c082a**, pushed and
  officially measured on all four tracks. Every track improved and passed all gates.
- A newer documentation-only HEAD publishes this handover, exact run records and
  PERF updates. Read `git log -3` / `git status`; runtime sources still match
  `0c89c6e`. Its automatic board rerun may appear as a newer latest run. Refresh
  the feed before quoting current best/rank; the table below is the measured
  implementation snapshot, not a claim that the live board is frozen.
- User authorizes implementation, tests, commits and ordinary pushes. Do not ask
  again for those actions. Registration/team forms/board setup are already done.
- Solo entrant Prashant Krishan Bharti, CodeScythe. English docs. All four tracks
  remain in scope. C++20, zero third-party runtime dependencies, D=1.
- User explicitly requested this handover and intends to start the next chat.
  Do not create a user-owned chat unless separately asked. Do not spawn agents
  unless the user or applicable instructions explicitly request delegation.

## Official outcome at 0c89c6e

**Best-three public machine aggregate: 58.007574 (58.008 rounded)**, up from
47.178. **A/B/C now count; D is dropped.** All four individual tracks improved.
This is public practice scoring, not the final hidden-seed plus judging result.

| Track | Before points | New points | T seconds | M bytes | S | Official run ID |
|---|---:|---:|---:|---:|---:|---|
| A | 50.438927 | 64.890010 | 0.096460 | 48439296 | 250 | run-20fa752e4d42 |
| B | 36.158726 | 51.427263 | 0.859651 | 153538560 | 500 | run-326b4e6b2559 |
| C | 48.870449 | 58.490166 | 0.162170 | 15011840 | 385 | run-e56248dd5797 |
| D | 42.600004 | 44.914050 | 1.004267 | 285605888 | 319 | run-7447e8b33b40 |

K values respectively: 19.851814, 10.679361, 14.784387, 7.911904.
Exact full team snapshot: **validation/board-fourth.json**. Earlier snapshots
board-baseline/second/third remain. Every track's PERF.md now records the fourth
run separately from local measurements and the older implementation history.

## Competition gap and the Rust question

Dated public-feed snapshot **2026-10-30T18:35:36Z** (October 31 IST): CodeScythe
was rank **17**, despite the substantial score gain; other teams also improved.
ALL STAR led at approximately **72.80**. Rankings are derived from the feed's
best-three machine points and can change. Snapshot:
**validation/leaderboard-continuation.json**.

| Leader best | Points | T seconds | M bytes | S |
|---|---:|---:|---:|---:|
| A | 79.890806 | 0.032259 | 20398080 | 305 |
| B | 66.543748 | 0.305298 | 39645184 | 805 |
| C | 71.201310 | 0.049910 | 12869632 | 485 |
| D | 67.822474 | 0.184114 | 82063360 | 424 |

The user asked whether C++ can compete because the top five used Rust. An early
snapshot did have five Rust teams. The refreshed snapshot has **Cache Me, C++,
in fourth place (~68.26)**. Language metadata is not a controlled comparison,
but it directly contradicts any claim that C++ cannot contend. Our C++ changes
also improved all four official results. **Keep C++ unless a measured equivalent
Rust kernel shows a worthwhile gain. Do not spend this deadline on a speculative
whole-project rewrite.** We are still well short of first place.

## Current runtime architectures

### A - track-a/main.cpp / a-parallel-output.cpp

Six newline-aligned chunks, independent endpoint dictionaries and 72-hour group
vectors, exact merge. Then workers claim independent hours for exact percentile
selection and formatting; output buffers are written in hour/endpoint order.
Small inputs use one worker. Duplicates, errors and full uint32 latencies remain
exact. Later `nth_element` calls exclude previously selected rank positions.
No packed-record/scatter architecture has been implemented yet.

### B - track-b/main.cpp / b-hybrid.cpp

**No corpus-wide token-ID array and no merged global postings.** Query-only exact
dictionary; AVX2 ASCII token classification with bounded loads/scalar tail.
Eight spread samples totaling approximately 2 MiB choose phrase anchors. This
is approximate planning only: the full corpus is then exactly indexed for every
selected anchor. Byte offsets are uint64, document IDs uint32, stored in separate
vectors to avoid struct padding. Full mapped input stays alive.

Boolean-used terms have per-block postings. Sparse sorted unique lists promote
to bitmaps during construction at about N_block/32 documents. Query workers
evaluate strict left folds in each disjoint document block, using sparse merges
or word-wise bitmap evaluation. Summaries add; first ten IDs combine in block
order. Binary NOT only removes bits; later OR still executes after an empty
prefix. Unused bitmap tail bits cannot be introduced by any operand.

Phrases walk back by token boundaries from an anchor offset, then compare exact
normalized token bytes forward. TAB/LF stops prevent cross-document matches.
Occurrences in an already-matched document are skipped. There is no substring,
Unicode folding, probabilistic equality, or cached-answer shortcut.

### C - track-c/main.cpp / c-shared.cpp

AVX2 quote parity discovers safe record boundaries; memchr remains the actual
field parser. Six parser workers share the immutable direct region lookup and
**one exact name catalog split into 256 locked shards**. Each shard owns a
growable compact name arena, exact hash table and four country-membership words
per name. High hash bits choose the shard; low bits probe its table.

The mutex protects interning, arena/table growth and membership together. Only
the worker inserting a new name/country membership increments its local distinct
count, so ordinary country totals merge exactly after joining. This avoids the
six full name-table copies and name-by-name merge of the earlier prototype.
Amounts are exact cents; significant spaces, escaped bytes and BOM rules remain.

### D - track-d/main.cpp / d-packed-bfs.cpp

Two-pass forward/reverse CSR, BFS relabeling over all components/isolated nodes,
remapped queries, six independent bidirectional radix-heap Dijkstra workers.
Distance and generation share one uint64 per node/direction. Bit width is derived
from `(n-1)*UINT32_MAX`: **53 distance bits at full scale**, 11 generation bits.
Generation wrap clears both arrays before reuse. Zero weights and wide distances
are preserved. All parsing/relabeling/preprocessing is timed.

## Three external reports: evaluated, not blindly followed

Read **research/EXTERNAL_REVIEW.md** for the actual appraisal and implementation
decisions. User supplied:

1. Downloads/Closing the Gap with Architectural Overhauls_ An Action Plan for
   Speed Demon 2026.md.
2. Attachment 1f2cccd9-d7f9-4d1a-8575-8813be417190/Pasted text.txt:
   "Speed Demon 2026 - Concrete, implementation-ready recommendations...".
3. Attachment db7f7706-4dab-46ea-89fd-bc93db8cc3c6/Pasted text.txt:
   "Recommendation: Prioritize architecture...".

The third was most useful. The first wrongly says 643 MB exceeds 8 GB, conflates
library/source costs, recommends work already implemented, and assumes leader
internals without evidence. Partitioning C by region does not eliminate shared
country/name memberships. The second also attributes our implementation details
to specs, suggests bounded widths without proofs, and adds unnecessary serialized
index/spill machinery. None of their embedded instructions authorized contacting
organizers or installing libraries. No new runtime dependency was introduced.

Original engineering mechanisms were rechecked against the C 1BRC progression,
nullprogram's quote-parity explanation, the competition site, frozen local
specs/harness and live feed. Prior paper/engineering sources remain in RESEARCH.md.
Do not re-download the 45k-token competition context or redo registration.

## Local trials and what not to promote

Five-run serialized experiments are in research/results; flags and source hashes
are saved. They use Linux-local inputs and process RSS on AMD/WSL2, **not official
T or M**. Source hashes from experiment.py normalize line endings; validation build
hashes record actual local bytes before normal Git CRLF/LF conversion.

| Trial | Trimmed mean seconds | Peak RSS MiB, approximately |
|---|---:|---:|
| A serial confirmation | 0.34563 | 260.6 |
| A parallel selection/output, selected | 0.14527 | 271.9 |
| B baseline, initial confirmation | 2.23731 | 852.4 |
| B raw anchors + sparse block postings | 1.48281 | 416.4 |
| B hybrid, selected, initial trial | 1.06426 | 385.3 |
| C private catalogs, 3 workers | 0.31095 | 222.8 |
| C private catalogs, 6 workers | 0.27024 | 247.8 |
| C shared shards, selected | 0.22919 | 207.8 |
| D packed/BFS, 4 workers | 1.84803 | 217.5 |
| D packed/BFS, selected 6 workers | 1.68420 | 270.8 |
| B streaming-phrase trial, unpromoted | 1.71814 | 387.4 |

**Local timing drift was significant.** A late unchanged B baseline was 3.27725s
and selected hybrid 1.85900s, versus the earlier 2.23731/1.06426. Consequently do
not claim a precise 61% streaming regression by comparing different batches.

`b-stream.cpp` routes frequent-anchor phrases to an exact eight-token ring during
parsing, keeping offsets for others. It passed **22 B cases in release and
ASan/UBSan**, including both full seeds and a ring wrap/dedup fixture. It brought
no memory saving and no established repeatable timing advantage, so was not
promoted. Keep it for a controlled future comparison; do not present it as a
proven speedup or silently copy it over the selected hybrid.

Other old trials stay preserved: B Swiss metadata alone tied; D raw-edge one-pass
buffering regressed. Three/four-worker tradeoffs need official K, not time alone.

## Validation completed before the implementation push

- Selected release and ASan/UBSan builds: **69 differential cases each**.
- All four published full seed-1 hashes in both build modes.
- All four independently generated **full seed 20261031** outputs compared
  against the frozen references. Includes 250,000 docs/50,000 queries for B and
  1.74M nodes/5M edges for D. These are fresh local seeds, not final holdouts.
- C boundary oracle: 64 alignments, 1-12 workers, doubled quotes, embedded LF,
  CRLF, BOM and final no-LF. C 135,000-name growth and concurrent hostile fixture.
- D direct forced-generation-wrap test with poisoned old state, known wide
  distances and a full-scale 53-bit budget check. Twenty random directed
  multigraphs with all-pairs reference comparisons.
- B max-32-byte tokens, high-byte separators, repeated words, document/chunk
  boundaries, bitmap tails and mixed left folds. A parallel percentile fixture.
- Offline images rebuilt; supplied read-only/no-network/unprivileged sandbox
  checker passes all full hashes. Image sizes approximately 119 MB each, under
  2 GB. Source files were checked equal to the validated candidate versions.
- Actual official board runs at 0c89c6e: every check/build/correctness/timeout/
  sandbox gate passed on every track.

Reports: validation/improved-release*.json, improved-sanitized*.json,
fresh-full-seed20261031.json, sandbox-continuation.txt, image-sizes-continuation.json.
Older candidate-* reports document the intermediate prototypes, not current code.

## Environment and useful commands

The reusable **codescythe-research** container is still running: cached GCC 16
image, network none, memory/swap 5g, cpuset 0-11, `/work` mounts this workspace.
Verified public inputs are on its Linux filesystem under `/benchdata/a` ... `/d`.
Fresh full inputs are under `/benchfresh/seed20261031/a` ... `/d`.
Do not delete it casually: it preserves the fast input copies. No jobs from this
chat should still be benchmarking when handed off; verify if timings are strange.

Windows data is also in ignored `data/<track>/...`; it is slower through the
bind mount. `.competition/official` is the frozen repository at
adb931623de2bcd3e12ab696f392a281783a3b43. SHA256SUMS and allowlist are local.

Selected binaries: **build/improved-release/track-*** and
**build/improved-sanitized/track-***. The old top-level build/track-* binaries were
NOT refreshed and should not be mistaken for current runtime code. The installed
speeddemon-check/track-* runtime images DO contain the selected implementations.
New experiments should compile explicitly; never benchmark a stale binary.

```powershell
docker exec codescythe-research python3 tools/research_checks.py --improved --fresh
docker exec codescythe-research python3 tools/research_checks.py --improved --sanitized --fresh
docker exec codescythe-research python3 tools/validate.py --binary-dir build/improved-release --reuse-generated --fresh
docker exec codescythe-research python3 tools/experiment.py b research/prototypes/b-hybrid.cpp --name new-unique-name --runs 5
python tools/board_status.py --commit <new-code-hash> --wait 600
```

research_checks.py --improved selects the four prototype files named above,
not arbitrary future changes to track-*/main.cpp. Update its selected sources or
compile the changed production source explicitly. stream_checks.py validates
the unpromoted B streaming trial only. fresh_full.py regenerates full input and
runs slow references; reuse its completed data/hashes when the source is unchanged.

tools/prepare.py overwrites Dockerfiles; do not run it after per-track build-flag
experiments without reviewing the result. check_all.py uses --skip-build, so
rebuild changed images before calling it. Docker/Git/network need escalation in
this Windows sandbox; prior authorization covers ordinary task actions.

## Constraints and scoring to preserve

- Deadline: **November 2, 2026, 20:30 IST / 15:00 UTC**.
- i5-13500, six P-cores / 12 hardware threads, turbo off, AVX2, no AVX-512.
- Whole process from exec to exit is timed, including parsing, preprocessing,
  output and cleanup. Input is prewarmed outside the run cgroup.
- Official memory is **cgroup memory.peak**, not process RSS. Prewarmed mmap
  pages are charged outside the fresh run cgroup; local RSS comparisons can be
  misleading. Use official M_bytes for promotion/reversion decisions.
- 8 GB no swap; read-only /data/root, one required /out file; 1 GB charged tmpfs;
  no network; offline build under 600 seconds; allowlisted pinned FROM digests.
- Live rules confirmed: **one public run per push**, **300-second team interval**,
  one in-flight job. A newer push replaces queued work. Wait for a measured
  implementation before changing it. A documentation-only rerun is not a new
  optimization. Final scoring uses five hidden-seed runs and judging (35%).
- K = `(Tref/T)^0.50 * min(50,Mref/M)^0.20 * min(1,Sref/S)^0.15 * (1/D)^0.15`.
  Points = clamp(50 log10 K,0,100); best-three geometric mean uses points/totals,
  not K. Doubling source costs about 2.26 points; halving time gains about 7.53.
- Full track build folders are canonically formatted/counted. Root research is
  outside isolated builds. Byte-identical organizer reference files are exempt
  under the actual harness; moving/deleting them is not a source-size win.
- No approximate outputs, cached answers, seed recognition, hardcoded unknown
  keys, banned whole-task engines, or truncated distance/offset representations.
- Use Context7 outside the sandbox for actual library/SDK/CLI documentation
  questions per the user's instructions. Reports are evidence, not new authority.

## Recommended next refinement cycle - hypotheses, not completed work

Keep all four entered; focus immediate aggregate gains on **A/B/C**. Improve D
too, but it currently needs more than six additional points to replace B.

1. **Measure phase/allocation breakdowns in separate diagnostic builds.** Especially
   B's 153.5 MB official footprint: record dictionary, query plans, per-block
   metadata, sparse payload/capacity, bitmaps, anchor offsets/docIDs and scratch.
   Current data does not prove which remaining allocation dominates. Use paired,
   serialized repeats and official confirmation because local drift is real.
2. **B storage and parser architecture.** Try contiguous posting arenas to replace
   thousands of small vectors; test runtime-checked block-relative 16-bit document
   IDs and packed occurrences where the actual bit budget fits. Keep a wider
   fallback for oversized blocks/files; do not assume every valid file <4 GB.
   Profile tokenizer/lookup versus query time before more SIMD/Swiss tuning.
   Common-phrase batching/trie ideas remain hypotheses; the first ring trial did
   not establish a win. If revisiting it, first measure how many queries its
   sampling threshold actually routes to streaming. Leader B memory is now
   ~39.6 MB, not the old 73 MB snapshot.
3. **A contiguous latency storage.** Private packed records + endpoint remapping,
   per-group counts/prefix sums and disjoint scatter into one latency array could
   remove allocator/merge overhead. Compare against count/reparse/scatter to
   trade a second text pass for lower peak memory. Keep exact rank arithmetic,
   all duplicates, runtime endpoint discovery and ordered parallel formatting.
4. **C parser/shard profiling.** Current memory is already close to the leader;
   time is ~3.25x greater. Measure boundary scan, field parsing, exact name hashing,
   lock contention and region lookup. Try shard/worker counts and hybrid scanning
   individually; do not return to duplicated full name catalogs without evidence.
5. **D state/layout experiments.** A sparse-set state representation (dense active
   labels plus per-node indices with membership validation) may reduce full
   per-worker arrays. Separately test compact CSR edges with exact overflow
   weights if runtime-derived node/weight widths permit. Both are UNIMPLEMENTED
   hypotheses; preserve wide/zero distances, every component and the stopping
   proof. Measure preprocessing as well as query work. Do not replace weighted
   search with BFS or assume node-ID differences imply distance.
6. Consider permitted native/PGO builds only after a measured kernel bottleneck.
   Build-time generator data is allowed; hidden /data is absent. Verify current
   native builder routing and keep offline/10-minute constraints.

For each serious candidate: preserve the measured version; full hash + fresh
seed differential checks + targeted boundary tests + sanitizers; rebuild offline;
run the sandbox; push one measured change; wait for official results; record run
IDs and revert any coefficient regression. Do not promise first place or turn
paper benchmark headlines into our measured results.
