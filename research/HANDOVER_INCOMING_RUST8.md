# Speed Demon handover - October 31, 2026

Continue the existing entry. Do not restart, reset, force-push or re-register.

Fresh handover refresh: validation/leaderboard-handover7-refresh.json confirms
69.780860 / rank 17, leader 80.253740. NEXT_CHAT_PROMPT.md is the copy-ready
continuation prompt. No kernel, build or submission was changed during this
handover-only refresh. Prioritize A/C then B; the current gap requires substantial
runtime improvements rather than assuming the recent small gains are enough.

## Exact checkpoint and official results

- Workspace: C:/Users/kultzuki/Coding/Speed-demon.
- Private origin: https://github.com/Kultzuki/speed-demon.git; watched branch speed-demon.
- Local and pushed HEAD: **e9deec07fa38f9abf0c167d6768c41c388e37ba5**. All five official gates pass on all four tracks at this SHA.
- Initial checkpoint: c503752efebdbebcd9c6de41a4485af8ef1776fd. Candidate f99253995d7fa9f97f825c9c8b37c4ec705d3e66
  improved A/B/C officially; its D construction trial lost and was restored.
- Captured 2026-10-31T08:45:14.417964+00:00: best-three practice aggregate **69.780860**,
  rank **17**, leader Cause Of Death **80.253740**.
  Started at 69.160567 / rank 18. First place has not been reached.
  Refresh the feed before quoting current standings. This is public practice,
  separate from unseen-seed final scoring and 35% human judging.

Best records, possibly from older commits:

| Track | K | T s | M bytes | S | Commit | Run |
|---|---:|---:|---:|---:|---|---|
| A | 33.234541 | 0.039374 | 29446144 | 310 | f992539 | run-49fde5df3d4e |
| B | 19.373796 | 0.295209 | 71454720 | 922 | f992539 | run-55ec3a94a1e5 |
| C | 24.427280 | 0.062636 | 12754944 | 401 | f992539 | run-6b85ee32eee3 |
| D | 15.399979 | 0.361719 | 114028544 | 385 | 7321615 | run-5eb2205782b0 |

Latest exact-HEAD rerun:

| Track | K | T s | M bytes | S | Commit | Run |
|---|---:|---:|---:|---:|---|---|
| A | 29.654383 | 0.050025 | 28614656 | 310 | e9deec0 | run-3313bc9b6eb0 |
| B | 19.243317 | 0.299818 | 71102464 | 922 | e9deec0 | run-6d82f9e889d8 |
| C | 24.343070 | 0.062062 | 13279232 | 401 | e9deec0 | run-aaa6f10b1e14 |
| D | 14.469309 | 0.400875 | 120442880 | 385 | e9deec0 | run-b9af384939b6 |

A/B/C are unchanged since f992539; later differences on those tracks are rerun
variation. D restores the established incoming full-uint64 kernel. All four
entries remain; best-three uses A/B/C. See validation/leaderboard-continuation7-final.json and
validation/continuation7-final-official-summary.json for complete records.

## Current implementations

- A: the retained packed hour records, exact uint32 overflow stream and complete
  endpoint equality, now using the incoming first/last-eight-byte plus length
  hash. No partial hash is used as identity. Twelve workers and ordered output
  remain; all SIMD loads stay bounded. S=310.
- B: query-aware exact dictionary, eight-token pipeline, adaptive list/bitmap
  CSR, exact phrase checks and checked uint16/uint32 documents plus uint32/uint64
  offsets. Lazy packed posting blocks grow from 4096 to 65536 entries; this
  reduces mapping calls/page-rounding cost. x86-64-v3; S=922.
- C: mapped parser, growing owned names, exact decoded-name equality, 256 shards
  and atomic country membership. The incoming partial-byte hash and four-record
  ring retain escaped-name scratch until retirement. After checked-close output,
  _exit(0) skips C++ destruction; kernel cleanup is still timed. Contract-safe
  LF+digit/BOM cuts and byte country IDs remain. No record/name/arena cap. S=401.
- D: exact restored six-worker two-pass forward/reverse compact CSR, sorted
  full-uint32 weight overflow entries, twelve query workers, full-uint64 sparse
  labels, safe epoch wrap and balanced bidirectional radix Dijkstra. No sharded
  builder, inline adjacency, packed heap entries, BFS remap or narrow labels. S=385.

All runtime dependencies remain zero (D=1), C++20. No cached/seed-recognized,
approximate, hash-only or unproved narrow answer path is present.

## Final validation and artifact provenance

Use **build/continuation7-final-{release,sanitized}/track-*** for the final mix.
Both pass **93 dataset comparisons**: the previous 89 plus A/C deliberate
partial-hash collisions and two >2 MB parallel D cases with many wide weights.
Both full seeds pass. Existing direct A guard/publication, C boundary/concurrent
membership and D wrap/rehash/wide-distance programs pass. A separate iostream
oracle checks every forward/reverse edge and duplicate multiplicity in two
200,000-edge graphs. Forced uint64 B offsets pass the full public hash.

All final offline images pass the starter sandbox and are about 119 MB. Their
executables match the final validated release binaries exactly. Provenance:
validation/continuation7-final-artifact-provenance.json and
validation/image-sizes-continuation7-final.json (also image-sizes-current.json).
A/B/C image checks originate in sandbox-continuation7.txt; restored D was
rebuilt in sandbox-continuation7-final-d.txt. Actual source/common/compiler/
binary/image hashes are saved. Git LF normalization can change raw source byte
hashes; the provenance also gives normalized LF hashes. Earlier continuation7
builds/images include the rejected D trial and are historical only.

## Preserved state and rejected experiments

The incoming handover claimed clean submitted kernels, but A/C already had
uncommitted continuation-6 experiments. All 104 incoming changed/untracked
files, status, binary patch and SHA-256 were archived byte for byte in ignored
.out/continuation7-incoming. The full incoming handover is committed as
research/HANDOVER_INCOMING_CONTINUATION7.md. Incoming final-official records,
continuation-6 prototypes/results and the new research are preserved in f992539.
Final handover/PERF/official snapshots are updated after the last push and may
be dirty or untracked. Preserve them; submitted kernels should be clean.

Read research/CONTINUATION7.md before new work. D's compact owner-sharded build
won 14-17% on the full local coefficient but failed officially: 0.366347 s,
123572224 bytes, S=450, K=14.710088. Time was only 0.6% below the incoming
0.368451 s rerun while source size rose 17%, so K fell. It is rejected and restored.
The larger-memory inline graph also loses. Twelve build workers and 12-byte
heap entries do not justify promotion. A parallel prefault and reservation
lose locally. C split membership loses. B SIMD keys/exclusive bitmap words
give small gains and are unselected.

Generator-only PGO was actually tested on unmodified-generator sample seeds
197731/806317. A is mixed across full seeds, C adds little stable gain; neither
is submitted. Profiles/binary/input hashes remain in validation/pgo7-*-training.json.
Short A/C repeat gains vary by batch; do not claim a stable percentage from one
fast run. Paired hot-data cgroup reports and monotonic phase stderr are under
research/results; every continuation-7 benchmarked candidate matches its expected full output hash.

Both supplied-fifth and supplied-sixth sets were already reviewed. Their known
C fixed-name-table hang, B document-width failures and A hash-only endpoint
collision are reproduced in research/CONTINUATION5.md and corresponding
validation/supplied-continuation5-*.json. They are not untested replacements.

## Environment, authorization and next work

codescythe-research remains running: GCC 16, network none, 5g/no swap, CPUs 0-11,
workspace /work. Original /benchdata and /benchfresh/seed20261031 are preserved.
The codescythe-bench-continuation5 volume now also has verified copies at
/data/fresh7/{a,b,c,d}. codescythe-fresh-continuation7 is stopped; no original
data or volume was deleted. Organizer scc 4.1.0 / clang-format 23.1.3 are ELF
tools in build/static-tools: run them inside Linux, not as Windows programs.

Private App watch and all four private clone/build/scoring gates are verified
at the final pushed head. No new registration or App permission change is
needed. Existing authorization covers implementation, tests, commits and
ordinary pushes. Keep the same branch/repository/four entries. Do not spawn
agents without explicit authorization. No agent was spawned in this run.

Outstanding: first place. Profile on the scoring CPU where possible; D's large
WSL2 gain did not transfer, so do not repeat that builder without new evidence.
A selection/output, B scan/index/query costs, a growing exact C tag table and
different D locality/search work remain research directions. Preserve full
widths and compare complete K, not local time or RSS alone. Validate promising
changes with differential/full-seed/sanitizer/offline-image gates, wait for
official measurements and reject actual coefficient regressions.

One untested D direction is separate aligned uint64-distance and packed
node/generation-tag arrays, deriving tag widths from n and clearing safely on
epoch wrap. This preserves full distances and differs from the rejected narrow
labels and unaligned 12-byte heap entries. It is a proposal, not a measured win.

Deadline: November 2, 2026, 20:30 IST / 15:00 UTC. Official target: i5-13500,
six P-cores/12 threads, turbo off, AVX2/no AVX-512, exec-to-exit timing,
cgroup memory.peak, 8 GB/no swap, read-only root/data, no network, required
output only, 1 GB scratch. Offline digest-pinned allowlisted builds under 600s,
image under 2 GB. One live run per push / 300s interval / one in flight.

Do not rerun old selectors or handover writers blindly. select_continuation5.py
restores its losing D trial; select_continuation7.py selects the newly rejected
sharded D. restore_d7.py records this rollback and is intentionally one-shot.
prepare.py overwrites Dockerfiles. check_all.py reuses images. Use new evidence
prefixes and inspect scripts first. No required validation, push or official
measurement remains pending for this final checkpoint.
