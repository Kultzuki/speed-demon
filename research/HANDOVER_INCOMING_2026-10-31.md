# Speed Demon handover for the next chat - October 31, 2026

Continue this entry. Do not restart, reset, force-push, or re-register.
This chat continued from d069bfdf99b24c9c6f9823d4af6e0c1562a55a8f after reading
its complete handover. The user has now explicitly stopped optimization and
requested only this handover. Resume implementation only when the next chat
asks to continue.

## Checkpoint and working tree

- Workspace: `C:\Users\kultzuki\Coding\Speed-demon`.
- Watched branch: **speed-demon**.
- Origin: `https://github.com/Kultzuki/speed-demon.git`, private.
- Local HEAD and last pushed implementation:
  **12aa1a4b22c970d7ce41700594fb8561f981dccd**.
- Earlier measured implementation: **7321615dd4b7f43d35cd71d45c607541b0fd73af**.
- All four tracks remain entered, C++20, runtime dependencies zero, D=1.
  Solo entrant: Prashant Krishan Bharti, CodeScythe. English docs.
- Earlier authorization covered implementation, tests, commits and ordinary
  pushes. The latest user instruction stopped that work to prepare this file.
- Do not create a new user-owned chat or spawn agents unless separately asked.

**The working tree is intentionally not clean.** After the official result,
`track-c/main.cpp` was restored locally to the stronger mapped C source from
7321615 (`research/prototypes/c-compactbyte3.cpp`). This rollback is **not
committed or pushed**. Remote 12aa1a4 still contains the losing buffered C trial.
The board retains the stronger older C best independently of the branch tip.
`track-c/README.md` still describes buffering and needs correction when work
resumes. Do not mistake that README for the current local implementation.

Uncommitted official-result records are in the four PERF.md files,
`research/CONTINUATION3.md`, `validation/continuation4-official-summary.json`,
and `validation/leaderboard-continuation4.json`. An extra exact A copy is
`research/prototypes/a-measured-12aa1a4.cpp`. Preserve these changes.

## Official result

Latest captured best-three aggregate: **67.167388** (67.167 displayed), rank
**12**, up from the refreshed starting **63.489897 / rank 19**. A/C/D count;
B is dropped. The user's latest screenshot confirms 67.167 and rank 12.
Captured leader: **Cause Of Death, 75.793365**. We remain behind first place.
These are public practice results, not final hidden-seed/judging results.
Refresh live figures before quoting them in a later chat.

| Track | Best points | K | T seconds | M bytes | S | Best commit | Run |
|---|---:|---:|---:|---:|---:|---|---|
| A | 75.748841 | 32.732322 | 0.042816 | 27090944 | 290 | 12aa1a4 | run-08da06690eea |
| B | 57.544808 | 14.154553 | 0.549548 | 102383616 | 583 | 12aa1a4 | run-dc6e65a747ff |
| C | 67.373389 | 22.257059 | 0.077342 | 13303808 | 349 | 7321615 | run-d5814037f358 |
| D | 59.376007 | 15.399979 | 0.361719 | 114028544 | 385 | 7321615 | run-5eb2205782b0 |

All four tracks passed every official gate at BOTH 7321615 and 12aa1a4.
Exact snapshots/summaries: `validation/leaderboard-continuation3.json`,
`continuation3-official-summary.json`, `leaderboard-continuation4.json`, and
`continuation4-official-summary.json`.

At 7321615 all four coefficients improved and aggregate reached 65.975209,
rank 14. At 12aa1a4, packed A improved again and is retained. Buffered C is
rejected: K=22.098103 / 67.217749 points, below mapped C's K=22.257059 /
67.373389. The small runtime gain did not cover source/memory costs.
B/D runtime sources are unchanged between these two commits; their rerun
variation is not another kernel optimization. The earlier 63.343397 handover
snapshot predates an unchanged-code rerun that lifted the starting best to
63.489897.

## Current local kernels

- **A, retained:** twelve line-aligned parsers, exact shared endpoint registry
  with release/acquire publication. The binding 1,842 endpoints fit 11 bits and
  a 2,048-key registry. Hour buckets use 32-bit records: 20 latency bits, 11
  endpoint bits and one error bit. A reserved latency sentinel uses an ordered
  full-uint32 overflow stream, including the sentinel's own value. No latency
  is truncated. Bounded SIMD, exact nearest ranks, released input buckets and
  ordered streaming hour output. Source: `a-packed4.cpp`.
- **B, retained:** twelve query-only block indexes; negative dictionary filter
  has no false negatives and all possible hits compare complete bytes. Inline
  uint16 postings with checked uint32 widening, adaptive lists/bitmaps and
  duplicate bitmap-write suppression. Exact uncapped mapped-text phrase checks,
  strict left folds, and checked uint32/uint64 relative offsets. Source:
  `b-bloom3.cpp`.
- **C, locally restored:** mapped input, twelve workers, byte region lookup
  justified by 240 countries plus unmatched. Compact owned name nodes in
  growing arenas, full decoded-name equality, 256 shards, acquire/release
  publication, insertion locks only on misses, atomic country membership.
  Section 2.2 proves LF+digit/BOM record cuts: names have no LF and notes have
  no digits/BOM. This is not a general arbitrary-CSV shortcut. No fixed record,
  distinct-name or suffix-arena cap. Source: `c-compactbyte3.cpp`.
- **D, retained:** six-worker forward/reverse compact CSR, exact overflow weights,
  twelve query workers, balanced bidirectional radix Dijkstra, sparse full-uint64
  distances and safe generation wrap. No BFS remapping or narrow-distance
  fallback in production. Source: `d-wide3-twelve.cpp`.

The first refinement's exact-source paired local reductions were approximately
A=57%, B=29%, C=9%, D=17%. Official gains differ; B/D memory increased.
The packed A follow-up subsequently improved officially to the table above.
Larger C buffers, mapped-name views, flat name tables, custom B word hashes,
A buffer recycling, D serial/private-counter CSR and direct-address distances
were not selected. Narrow sparse D labels were inconclusive. Research trials
are not production or universally validated replacements.

## Validation and correct artifacts

**The current mixed local sources match `continuation4-release` for ALL four
tracks**, verified by source SHA-256 after restoring C. The corresponding
release and ASan/UBSan gates passed **85 comparisons each**: 69 differential
cases, four public full hashes, six extra boundary cases, four independently
referenced full-seed-20261031 outputs, and two new A sentinel/overflow fixtures.
Four direct programs cover A's 4,375 guarded parses/concurrent publication,
C's 64 boundary alignments/1-12 workers/concurrent membership, and D's sparse
rehash/wrap/overflow searches. Forced uint64 B offsets pass the full public hash.

Use **build/continuation4-{release,sanitized}/track-*** for this restored local
combination. The later **continuation4ac-*** builds/gates also passed 85, but
contain the REJECTED streaming C. Their A/B/D binaries match; their C does not.
`*-build.json` records actual source/common/binary hashes and compiler flags.
Old final/refined/build/track-* binaries are older checkpoints.

**Current Docker C image is still the rejected buffered image.** Its tag and
`validation/image-sizes-current.json` reflect the A/C trial. Rebuild C from the
restored source, or deliberately restore the previously verified C image from
`validation/image-sizes-continuation3.json`, before claiming current sandbox
validation. A's current image is correct; B/D are unchanged. All tested images
are about 119 MB. Offline sandbox records: `sandbox-continuation3.txt` (all four)
and `sandbox-continuation4ac.txt` (new A/C). Git line-ending normalization can
change source byte hashes without changing the kernel.

`codescythe-research` remains running: GCC 16, network none, memory/swap 5g,
cpuset 0-11, /work mounts this workspace. Public Linux-local data:
`/benchdata/a` ... `/d`; fresh full data:
`/benchfresh/seed20261031/a` ... `/d`. Do not delete these casually. Frozen
organizer checkout: adb931623de2bcd3e12ab696f392a281783a3b43.

```powershell
docker exec codescythe-research python3 tools/refinement_checks.py --name <unique-release> --packed-a
docker exec codescythe-research python3 tools/refinement_checks.py --name <unique-sanitized> --sanitized --packed-a
python tools/refinement_sandbox.py --name <unique-name>
python tools/board_status.py --commit <implementation-sha> --wait 600
python tools/verify_private_watch.py
python tools/refinement_snapshot.py --name <unique-snapshot>
```

Do not blindly rerun old selectors/generators. `select_checkpoint3.py` restores
older six-byte A. `write_continuation_handover.py` describes the pre-rollback
A/C candidate and would overwrite this corrected handover; update it first.
Record scripts append once. `prepare.py` overwrites Dockerfiles and
`check_all.py` reuses existing images. Rebuild changed images first.

## Supplied material already reviewed

Earlier Rust/second C reviews remain in research. The preceding seven new files
in this chat were preserved under `research/supplied-third` and `supplied-fourth`.
See `research/SUPPLIED_CONTINUATION_REVIEW.md` and
`validation/supplied-continuation-review.json`.

The third set is A/B/C/C: B repeats the second B and both C files are identical.
The fourth is corrected A, cache-dropping C and D. Earlier new A fails full
hashes due to skipping the endpoint; later A fixes it and padding. New C fixes
old suffix-arena/EOF cases but still rejects long valid names and has fixed
name storage. Its cache omits full equality on a collision path; that concern
was identified in code, not reproduced as a natural full-data collision.
New D passes both full hashes and tested arbitrary graphs. No whole supplied
replacement was adopted in these two refinements. A's architecture and C's
boundary idea were helpful.

## Latest four attachments: pending validation

The user then supplied four more files, asked to check usefulness and prepare a
new-chat handover, and finally said to stop doing anything else and just prepare
the handover. These files were read preliminarily but **not compiled, tested,
benchmarked, copied into research, or promoted**. They remain at these paths,
in **D / C / B / A order**:

- D: `C:\Users\kultzuki\.codex\attachments\3543610f-a653-4ba5-870c-978d30c55934\Pasted text.txt`
- C: `C:\Users\kultzuki\.codex\attachments\916ef1a4-a4a6-4d13-a763-80ccf556e9d7\Pasted text.txt`
- B: `C:\Users\kultzuki\.codex\attachments\02d67f4b-96eb-4da7-91a4-7002a227365f\Pasted text.txt`
- A: `C:\Users\kultzuki\.codex\attachments\393af749-cc45-4619-88b5-7977f2babdde\Pasted text.txt`

Ideas to investigate, not validated conclusions: A uses private endpoint tables,
CRC hashing, packed 16 KiB block arenas and page discard; B uses lagged token
prefetch, bucketed packed streams and adaptive query set algebra; C uses SIMD
structural masks, decimal decoding and prefetch pipelines; D uses private CSR
counters and paged distance storage. Review caps/fallbacks carefully: B has a
15-bit per-thread document stream guard, C has fixed name-table/arena budgets,
and D retains large per-thread count/cursor matrices. Do not infer correctness
or score from comments, language, source size or resemblance to leaderboard code.

## Private repository and competition rules

The competition App's private access was verified: anonymous GitHub returned
404, fresh successful board watch matched the authenticated remote head, and
ALL four tracks cloned/built/scored at both pushed implementations. No new
registration or App permission change was needed. The dedicated access JSON
was captured at 7321615; the later official snapshot proves 12aa1a4 access too.
Refresh after the next authorized push, not as unfinished work in this stopped chat.

Deadline November 2, 2026, 20:30 IST / 15:00 UTC. Scoring CPU: i5-13500, six
P-cores/12 threads, turbo off, AVX2, no AVX-512. Whole exec-to-exit process is
timed. M is cgroup memory.peak, not mapped-input-inclusive RSS. 8 GB/no swap,
read-only root/data, required output only, 1 GB charged tmpfs, offline builds
under 600s, digest-pinned allowlisted images under 2 GB. Last live rule: one run
per push, 300s interval, one in-flight job; a new queued push replaces queued
work. Wait for measurement before altering submitted kernels.

When resumed, first inspect this dirty tree and preserve its official records;
correct/commit the C rollback and documentation as appropriate, then evaluate
the four pending files. Keep all four tracks entered. Validate exact hashes,
fresh seeds, boundaries, widths and sanitizers, rebuild changed sandbox images,
then push one serious candidate and retain improvements by measured K. No
cached/seed-recognized/approximate answers, unknown-key hardcoding or unproved
truncation. Source is canonically counted per track; moving identical reference
files is not a source-size win. B indexing and D graph/search time remain large
gaps. Context7 outside the sandbox applies to actual library/SDK/CLI docs
questions, not ordinary code-review or algorithm work.
