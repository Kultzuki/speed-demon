# Speed Demon handover - October 31, 2026

Continue this entry. Do not restart, reset, force-push or re-register.

## Continuation 7 final combination ready for its official rerun

This section supersedes the older kernel description below while the next
ordinary commit/push is prepared. HEAD is f992539 at this instant; local D has
been restored after that commit's official regression. The older checkpoint
description below is historical and will be replaced after the final rerun.
All incoming dirty state is archived byte for byte in .out/continuation7-incoming;
the full incoming handover is research/HANDOVER_INCOMING_CONTINUATION7.md.

- A: incoming exact first/last-byte endpoint hash; full equality remains.
- B: 65,536-entry lazy posting blocks, with both checked width fallbacks.
- C: incoming exact hash/four-record ring, then checked-close _exit(0).
- D: restored exact incoming two-pass CSR/full-uint64 search. The owner-sharded
  trial loses officially: K=14.710088 versus historical 15.399979.

The frozen bundle passes 93 release and 93 ASan/UBSan dataset comparisons,
both full seeds, the prior direct tests, two complete independent 200,000-edge
CSR checks and forced uint64 B offsets. All four rebuilt offline images pass
the starter sandbox and match build/continuation7-final-release binaries exactly.
Use build/continuation7-final-{release,sanitized}, not earlier trial binaries.
Provenance: validation/continuation7-final-artifact-provenance.json.

Read research/CONTINUATION7.md, research/continuation7-selection.json and each
PERF.md for paired full coefficients and rejected experiments. A/C effects
vary by repeat; PGO, parallel prefault, reservation, split membership, inline
graph storage and packed heap entries are unselected/rejected. No PGO enters
the submitted builds. Do not rerun selector/generator scripts blindly.

At f992539 all official gates passed: A K=33.234541, B K=19.373796,
C K=24.427280; each improves its recorded best. Practice aggregate rises from
69.160567 / rank 18 to 69.780860 / rank 17, leader 80.244238. D is rejected and
restored. The next push changes only D's runtime source; wait for its exact
four-track official results before another kernel edit. A/B/C rerun differences
are variation. No agents were spawned.

## Current checkpoint

- Workspace: C:/Users/kultzuki/Coding/Speed-demon.
- Same private origin https://github.com/Kultzuki/speed-demon.git and branch speed-demon.
- Local and pushed HEAD: **c503752efebdbebcd9c6de41a4485af8ef1776fd**. The final restored combination passed all
  five official gates on all four tracks at this SHA.
- Meaningful B/C improvements were first officially measured at
  160e4dd03a5210afd31ba01af791c03d1907da7b. D's losing overflow-label trial at
  that commit was rejected and restored before the final push. A stayed unchanged.
- Started at 12aa1a4b22c970d7ce41700594fb8561f981dccd, preserving its intentionally
  dirty files and result records. Exact incoming copies remain in ignored
  .out/continuation5-incoming with status/diff/SHA-256. The full incoming handover
  is committed at research/HANDOVER_INCOMING_2026-10-31.md.
- Final official records and this refreshed handover are generated after the
  final push and may be dirty/untracked. Preserve them. No submitted kernel is
  dirty. Check git status rather than assuming a clean tree.
- Existing authorization covers implementation, tests, commits and ordinary
  pushes. Do not ask again for setup or App access. Do not create user-owned
  chats or spawn agents unless separately requested. Solo entrant remains
  CodeScythe / Prashant Krishan Bharti; English docs; all four tracks entered.

## Official results

Refreshed at 2026-10-31T05:48:24.092372+00:00: best-three aggregate
**69.160567**, rank **16**. Starting live snapshot was
67.167388 / rank 20, not the older rank-12 snapshot. Current captured leader is
Cause Of Death at **79.338836**. First place has not been reached.
Refresh the feed before quoting current standings. These are public practice
speed results, separate from final holdout seeds and judging.

Best per track, which can come from older commits:

| Track | Points | K | T seconds | M bytes | S | Best commit | Best run |
|---|---:|---:|---:|---:|---:|---|---|
| A | 75.748841 | 32.732322 | 0.042816 | 27090944 | 290 | 12aa1a4 | run-08da06690eea |
| B | 63.510615 | 18.629977 | 0.304950 | 80130048 | 922 | c503752 | run-23826c7d60fc |
| C | 68.762763 | 23.727679 | 0.066210 | 13393920 | 379 | 160e4dd | run-6c8aae8ae5d2 |
| D | 59.376007 | 15.399979 | 0.361719 | 114028544 | 385 | 7321615 | run-5eb2205782b0 |

At 160e4dd, B K improved 14.154553 -> 18.435477 (+30.2%) and C improved
22.257059 -> 23.727679 (+6.6%). Both are retained. D K regressed
15.399979 -> 14.963401 despite lower M, so the exact full-uint64 source was
restored. A's lower rerun was unchanged-code variation, not a kernel change.
The final restored commit changes only D's runtime source relative to 160e4dd;
new A/B/C result differences are rerun variation. Best-three now uses A/B/C;
D remains entered. Exact latest and best records are in
validation/leaderboard-continuation5-{official,final}.json and the two official
summary JSONs. Every PERF.md cites the individual run IDs.

C's unchanged final rerun was slower: 0.087797s / K=20.806314, versus
0.066210s / K=23.727679 at 160e4dd and the old mapped best K=22.257059.
It is retained by its higher official best and modest paired/local coefficient
gain; a stable 6.6% improvement across repeated runs has not been established.
Controlled C repeat/phase measurements remain useful before another promotion.

## Current kernels

- A: retained shared exact endpoint registry, bounded SIMD, 32-bit packed hour
  records, exact sentinel/uint32 latency overflow stream, nearest ranks, ordered
  streaming output. Source equals the incoming packed A at 12aa1a4.
- B: query-only exact key dictionary; eight-token prefetch; sampled frequency
  affects layout only. Dense terms are bitmaps; sparse postings enter bucketed
  packed streams and scatter into sorted CSR while temporary pages are released.
  A checked 15-bit worker domain uses uint16 postings; larger real ranges use
  a 32-bit document stream/postings. File offsets dispatch to uint64 when needed.
  Adaptive lists/bitmaps preserve strict left folds. Phrases intersect rarest
  terms and verify uncapped exact ASCII token bytes in mapped documents. Hash
  collisions always compare complete keys. This derives from pending B, with
  correctness and width repairs. Docker compilation explicitly uses x86-64-v3.
- C: mapped input and twelve workers; exact decoded-name equality, compact owned
  nodes, growing arenas, 256 shards, acquire/release publication and atomic
  country membership. A sixteen-record prefetch ring keeps escaped-name scratch
  alive until retirement. Byte country IDs follow the 240-country bound. LF
  followed by digit/BOM cuts rely on section 2.2: names have no LF and notes no
  digits/BOM. This is not an arbitrary-CSV boundary shortcut. No fixed name,
  record, distinct-name or arena cap. C's README and rebuilt image are reconciled.
- D: restored six-worker forward/reverse compact CSR, exact overflow weights,
  twelve query workers, balanced bidirectional radix Dijkstra, full uint64 sparse
  labels and safe generation wrap. No narrow-distance fallback, BFS remap or
  paged labels remains. Source equals the stronger incoming D / 7321615 kernel.

All runtime dependencies remain zero (D=1), C++20. No cached, seed-recognized,
approximate or hash-only answers, unknown-key hardcoding or unproved truncation.

## Validation and images

Use build/continuation5-final-{release,sanitized}/track-* for this final mix.
Both pass **89 dataset comparisons**, including 69 differential cases, four
public full hashes, six earlier boundary cases, four independently referenced
full-seed-20261031 outputs, two A overflow cases, and four new regressions:
real B wide-domain dispatch, D sentinel/wide labels, C escaped ring reuse and
the reproduced A CRC collision. Four direct programs check A's 4,375 guarded
parses/publication, C's 64 boundary alignments/1-12 workers/concurrent membership,
and D rehash/wrap/wide-edge searches. Forced uint64 B offsets pass full public hash.

All four current images pass offline build and the starter sandbox, are about
119 MB, and match the final validated release binaries exactly. See
validation/continuation5-final-artifact-provenance.json,
image-sizes-continuation5-final.json and image-sizes-current.json. A/B/C image
records originate in sandbox-continuation5.txt; restored D is rebuilt and checked
in sandbox-continuation5-final-d.txt. Earlier continuation5 builds/images contain
the rejected D trial; they remain historical evidence, not the final mix.
Source/common/binary hashes and actual flags are in the final build JSONs.
Git LF normalization can change byte hashes without changing kernel behavior.

## Attachments and rejected experiments

The handover's four pending files were preserved as research/supplied-fifth and
evaluated in D/C/B/A order. The four distinct files pasted in this chat are
research/supplied-sixth, compiled/tested in the same order. Original hashes and
path-only adapters are preserved; no entire unsafe replacement was promoted.

Initial supplied checks: 99/108 pass. Four new collision/width checks add one
pass and three failures. Pending D passes both full seeds and arbitrary graphs,
but loses paired time badly (0.645519s baseline versus 3.499546s supplied, with
large private matrices). Pending C is faster but hangs at its fixed name-table
limit. New C fails both full hashes. Both original B files fail the new real
wide worker range, one by explicit exit and one by silent truncation. New A
merges /crc/rpbryafunzmzlnqvybmf with /crc/hakugyqfbnehjdgljotv through hash-only
identity; the collision and wrong output are reproduced. Production passes it.
See validation/supplied-continuation5-{provenance,review,additional}.json and
research/CONTINUATION5.md for precise scope and failures versus code concerns.

Independent A CRC/private tables/formatting, B bitmap summaries, C structural
SIMD/decimal decoding, and D forward search/window queue/BFS distance pages/
one-probe relaxation were unselected or rejected. Canonical source penalties
and fresh local cgroup peaks were compared, not runtime/RSS alone. One-pass B
beats the lower-memory two-pass layout in the full local comparison. D's small
local coefficient gain failed officially and was rolled back. All raw trials
remain in research/prototypes and research/results.

## Environment and remaining work

codescythe-research is running: GCC 16, network none, 5g/no swap, CPUs 0-11,
workspace /work. Keep /benchdata/{a,b,c,d} and
/benchfresh/seed20261031/{a,b,c,d}. A separate codescythe-bench-continuation5
volume contains copied public data; helper codescythe-data-continuation5 is
stopped. Nothing deleted or regenerated the original Linux data.

Exact organizer-pinned scc 4.1.0 / clang-format 23.1.3 are in ignored
build/static-tools. Their asset hashes were verified; baseline S counts exactly
match official A=290/B=583/C=349/D=385. Current S is A=290/B=922/C=379/D=385.

The private App watch and all four private clone/build/scoring gates are verified
at the final pushed head. See validation/private-repository-access.json.
No App permission change or new registration is needed.

Useful next work: profile the retained B layout's remaining index/query phases;
test safe locality improvements to D construction/search; investigate a growing
exact version of C's faster fixed tag table; explore A selection/output and
generator-only PGO. PGO is allowed but remains untested. Do not resurrect
rejected kernels solely from source comments or a faster local wall time.

Deadline: November 2, 2026, 20:30 IST / 15:00 UTC. Scoring: i5-13500, six
P-cores/12 threads, turbo off, AVX2/no AVX-512. Whole exec-to-exit process is
timed; M is kernel cgroup memory.peak. 8 GB/no swap, read-only root/data,
required output only, 1 GB scratch, offline digest-pinned allowlisted builds
under 600s, image under 2 GB. Last captured live rule: one run per push, 300s
interval, one in-flight job; a new queued push replaces queued work. Wait for
official measurement before changing submitted kernels. Canonically formatted
source counts per track; moving identical references is not a size win.

Do not blindly rerun selectors/generators. select_continuation5.py restores the
losing D trial; restore_d_continuation5.py is the official rejection rollback.
prepare.py overwrites Dockerfiles. check_all.py reuses images. Old handover
writers overwrite newer results. Read each script first and use unique build
and evidence names. No required validation, push or measurement remains pending.
