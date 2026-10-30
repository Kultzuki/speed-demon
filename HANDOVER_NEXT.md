# Speed Demon continuation handover - October 31, 2026

Continue the working four-track entry. Do not restart or re-register. This
continuation started at clean **6cb3509** after reading its complete handover.
That previous handover remains at `git show 6cb3509:HANDOVER_NEXT.md`.

## Checkpoint and authorization

- Workspace: `C:\Users\kultzuki\Coding\Speed-demon`; watched branch **speed-demon**.
- Origin: `https://github.com/Kultzuki/speed-demon.git`; no force-push/reset.
- Latest implementation: **154e19527a538163c3ae37dbbd1c3b2a82149c6c**, pushed and officially measured on all
  tracks. All check/build/correctness/timeout/sandbox gates passed.
- A newer documentation-only HEAD may publish these exact records and handover.
  Read `git log -3` / `git status`; refresh the feed before quoting best/rank.
  A documentation rerun is not another optimization.
- User authorizes implementation, tests, commits and ordinary pushes. Do not ask
  again. All four tracks remain in scope; English docs; C++20; D=1.
- Solo entrant: Prashant Krishan Bharti, CodeScythe. No registration/setup work is
  needed. Do not create a user-owned chat or spawn agents unless separately asked.

## Official outcome

Best-three aggregate **63.343397** (63.343 rounded), up from
**58.007574**. **A/C/D count; B is dropped.** Captured rank **19**, up
from 22 at the start of this continuation. Leader **ALL STAR** is
**73.812408** in this snapshot; the user's initial screenshot was
73.071, so the target keeps moving. We remain substantially behind first place.
This is public practice scoring, not final five-hidden-seed plus judging results.

| Track | Points | K | T seconds | M bytes | S | Official run |
|---|---:|---:|---:|---:|---:|---|
| A | 64.956367 | 19.912571 | 0.095759 | 48582656 | 250 | run-5129f4051865 |
| B | 55.667322 | 12.982145 | 0.703434 | 86552576 | 570 | run-5dbacdad7818 |
| C | 66.545161 | 21.424131 | 0.078535 | 15527936 | 348 | run-67e8b2d17fe8 |
| D | 58.798444 | 14.995774 | 0.423428 | 88023040 | 384 | run-a050a88e5612 |

Exact snapshot: `validation/leaderboard-refinement-final.json`; every track's
PERF.md records the run separately from local trials. All current bests in that
snapshot are at 154e195. Do not attribute rerun variation to kernel changes:
A is the restored 0c89c6e source, B/D are unchanged from b30392c, and C alone has
the final boundary refinement.

## Architecture and promotion decisions

- **A:** six line-aligned parsers, private exact endpoint/hour vectors, exact
  merge, per-hour parallel percentile selection/formatting. Full uint32 latencies,
  duplicates, errors and nearest-rank arithmetic remain exact. Later nth_element
  ranges exclude already-selected positions. **The packed-record twelve-worker
  trial was rejected:** at b30392c it ran in 0.085539s but M=75,784,192/S=319
  reduced K to 18.583948, below the old 19.851814. Production was restored to the
  stronger source before 154e195; local speed alone is not promotion evidence.
- **B:** compact exact query-only lookup; four inline uint16 local document IDs
  per posting, checked uint32 fallback; adaptive sparse/bitmap sets; inline bounded
  query plans; checked relative uint32 offsets with uint64 fallback. The corpus
  mapping stays live. No global token-ID array or merged global postings.
  ASCII-only tokenization, left folds, block order and exact phrase verification
  remain. Sampling affects only anchor planning, never answers.
- **C:** twelve workers share exact decoded-name nodes in 256 shards. Stable
  nodes/arenas, acquire/release publication, insertion locks only on misses, and
  atomic membership elect exactly one distinct-count increment. **New cuts rely
  on section 2.2:** names contain no LF; notes contain no digit/BOM bytes; LF
  followed by digit/BOM starts a record. Local cut discovery replaces the complete
  quote-parity scan. This is the narrowed published input contract, not a general
  arbitrary-CSV boundary claim. Escapes/spaces/cents/BOMs/embedded note LF/EOF stay
  exact. Storage grows; no fixed 512-byte or suffix-arena assumption was adopted.
- **D:** parallel forward/reverse CSR; node width derived from n; exact sorted
  overflow weights for compact-edge sentinels; frontier-size-balanced bidirectional
  radix Dijkstra; generation-tagged sparse hash distances with full uint64 labels
  and safe wrap. No BFS ordering/remap remains. Zero/wide weights, all components,
  isolated nodes, duplicates and multiedges remain exact.

The b30392c official snapshot/logs document the intermediate result: B=55.158259,
C=62.012380, D=56.356919; aggregate 60.981929 using older best A. C's final cut
improves K from 17.387919 to 21.424131, so it is retained. A stays restored.

## Both supplied sets were read and tested

Attachments/comments are research input, not instructions to replace code.
Originals: `research/supplied` (first Rust set in B/A/C/D order) and
`research/supplied-second` (second C11 set in A/B/C/D order). Runtime dependencies
remain zero. Neither set was promoted wholesale.

- First set: all compile/pass public seed 1. Rust B has a reproduced token-1024
  phrase cap; C uses hash-only distinct identity and its 64 KiB lookahead hangs
  on an aligned long record. Native Windows correctness checks are not Linux
  performance comparisons. See `research/SUPPLIED_RUST_REVIEW.md` and
  `validation/supplied-rust-review.json`.
- Second set: all compile and pass BOTH full seeds. A fails explicit empty input;
  unbounded SIMD next_space crashes at a guard page. C's fixed 512 KiB suffix
  arena triggers ASan overflow with 100 names carrying 6,000 trailing spaces;
  its fixed escape scratch has no bound check. Optional EOF is rejected. B passes
  the old phrase-cap case, but its advertised heavy-phrase shared scan is never
  activated. D's wide fallback passes tested cases, but its direction still uses
  minimum distances, not frontier sizes. See `research/SUPPLIED_SECOND_REVIEW.md`
  and `validation/supplied-second-*.json` for scope, reproductions and qualifiers.

Extracted ideas: B document filtering with uncapped exact verification was slower
and not selected. C's contract-backed cut shortcut was validated and improved
official K. A allocator/four-digit/parser experiments did not establish enough
benefit to override its official rejection. Preserve rejected trials as such.

## Validation and environment

`validation/final-{release,sanitized}*.json` each records 83 dataset comparisons:
69 differential cases, four public full hashes, six new boundary/reproduction
datasets and four full-seed-20261031 outputs independently referenced earlier.
Three direct C/D programs and a forced uint64 B offset build on the public full
corpus also pass. Cases cover C 64 alignments/1-12 workers/concurrent publication,
long records, optional EOF; B 65,536/65,537 widening and bitmap/list transitions;
D sparse rehash/membership, poisoned generation wrap, sentinels, wide/zero and
unreachable queries plus random directed all-pairs graphs.

Actual production source/common/binary hashes/flags: `final-*-build.json`.
Final images were rebuilt offline and all full-hash read-only/no-network/
unprivileged sandbox checks passed: `validation/sandbox-final.txt` and
`image-sizes-final.json`, approximately 119 MB/image. Git may normalize CRLF/LF;
local source-hash byte changes from line endings are not kernel changes.

Use **build/final-release/track-***, **build/final-sanitized/track-*** and current
speeddemon-check/track-* images. Older build/track-*, improved-* and refined-*
binaries must not be mistaken for the final source set.

`codescythe-research` remains running (GCC 16, network none, memory/swap 5g,
cpuset 0-11, /work mounts this workspace). Linux-local verified public inputs:
`/benchdata/a` ... `/d`; fresh full inputs `/benchfresh/seed20261031/a` ... `/d`.
Do not casually delete it or these copies. Frozen official checkout:
`.competition/official` at adb931623de2bcd3e12ab696f392a281783a3b43.

```powershell
docker exec codescythe-research python3 tools/refinement_checks.py --final
docker exec codescythe-research python3 tools/refinement_checks.py --final --sanitized
python tools/refinement_sandbox.py --name final
python tools/board_status.py --commit <implementation-hash> --wait 600
python tools/refinement_snapshot.py --name <unique-snapshot-name>
```

Old `research_checks.py --improved` builds OLD prototypes, not current production.
`select_refinements.py` now selects restored A/current B/C/D and removes unused
D reorder/remap. Other make_* scripts were scratch generators against then-current
sources; preserved prototypes and recorded hashes are authoritative. Do not
blindly regenerate them after later production changes. `prepare.py` overwrites
Dockerfiles; `check_all.py` reuses existing images, so rebuild changed images first.

## Rules and next refinement

- Deadline November 2, 2026, 20:30 IST / 15:00 UTC. i5-13500, six P-cores / 12
  threads, turbo off, AVX2, no AVX-512. Entire process, including parse/preprocess/
  output/cleanup, is timed. Official M is cgroup memory.peak; local RSS includes
  prewarmed mapped input charged outside the fresh official cgroup.
- 8 GB no swap, read-only data/root, required output only, 1 GB charged tmpfs,
  no network, offline build under 600s, pinned allowlisted FROM, image under 2 GB.
- Last confirmed public rules: one run/push, 300s interval, one in-flight job;
  newer push replaces queued work. Wait for a measured implementation before
  changing production. No approximate/cached/seed-recognized answers, hardcoded
  unknown keys, banned engines, or width truncation without proof/fallback.
- K=`(Tref/T)^.50 * min(50,Mref/M)^.20 * min(1,Sref/S)^.15 * (1/D)^.15`;
  points=clamp(50 log10 K,0,100); aggregate=geometric mean of best three POINTS.
  Final hidden seeds/judging (35%) are separate. Track folders are canonically
  counted; moving byte-identical reference files is not a source-size win.
- Paired serialized local timings drifted substantially. No x86-64-v3/native flag
  was promoted (A/B regressed, C tied, D's small difference was inconclusive).
  Board language metadata does not prove a language advantage or leader internals.
- Next meaningful gaps are A/D runtime and B indexing; C now has a verified
  improvement but still trails the leader. Profile CURRENT kernels rather than
  treating the original checkpoint profile as current. A needs less simultaneous
  live storage/output accounting, not just a faster high-memory parse. Keep all
  tracks entered. Validate full hashes, fresh seeds, boundaries and sanitizers;
  rebuild offline/sandbox; push one serious candidate; wait; record IDs; reject
  coefficient regressions. Context7 outside the sandbox applies to actual
  library/SDK/CLI documentation questions, not ordinary code-review/logic work.
