"""Write a compact current handover from saved official evidence, never guesses."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--snapshot',default='');args=parser.parse_args()
file=args.snapshot or ('leaderboard-continuation4.json' if (ROOT/'validation/leaderboard-continuation4.json').exists() else 'leaderboard-continuation3.json')
snapshot=json.loads((ROOT/'validation'/file).read_text())
own=snapshot['codescythe'];rank=next(x for x in snapshot['ranking'] if x['team'].lower()=='codescythe')
leader=snapshot['ranking'][0]
latest={track:item['latest'] for track,item in own['tracks'].items()}
commits={run['commit'] for run in latest.values()};assert len(commits)==1
commit=next(iter(commits))
pending=[]
for track in 'abcd':
    source=(ROOT/f'track-{track}/main.cpp').read_text()
    measured=subprocess.check_output(['git','show',f'{commit}:track-{track}/main.cpp'],cwd=ROOT).decode().replace('\r\n','\n')
    if source!=measured:pending.append(track.upper())
rows=[]
for track,item in own['tracks'].items():
    run=item['best']
    rows.append(f"| {track.upper()} | {run['points']:.6f} | {run['K']:.6f} | {run['T_s']:.6f} | {run['M_bytes']} | {run['S']} | {run['commit'][:7]} | {run['run_id']} |")
status=('The working tree has a follow-up in '+','.join(pending)+'. Its local gates precede official promotion; do not call it measured until the feed shows its commit.'
        if pending else 'Current runtime sources match this fully measured implementation. A newer documentation-only HEAD may record the results without another kernel optimization.')
text=r'''# Speed Demon continuation handover - October 31, 2026

Continue the existing four-track entry. Do not restart or re-register. This
continuation began at clean **d069bfdf99b24c9c6f9823d4af6e0c1562a55a8f** after
reading its complete handover. The previous version remains in Git.

## Workspace and authorization

- Workspace `C:\Users\kultzuki\Coding\Speed-demon`; watched branch **speed-demon**.
- Origin `https://github.com/Kultzuki/speed-demon.git`, now private. No reset or
  force-push. User authorizes implementation, tests, commits and ordinary pushes.
- All four tracks remain entered. Solo entrant Prashant Krishan Bharti,
  CodeScythe. C++20, English docs, no runtime dependencies, D=1.
- Do not create another user chat or spawn agents unless separately asked.

## Official outcome and checkpoint

Latest measured implementation: **@COMMIT@**; all four tracks passed every official gate.
@STATUS@

Best-three aggregate **@AGGREGATE@**, captured rank **@RANK@**. A/C/D count; B
is dropped. The leader is **@LEADER@**, **@LEADER_SCORE@**. We remain behind
first place. These are public practice measurements, separate from hidden seeds
and human judging. Refresh the feed before quoting live figures.

| Track | Best points | K | T seconds | M bytes | S | Best commit | Official run |
|---|---:|---:|---:|---:|---:|---|---|
@ROWS@

Exact snapshot: `validation/@SNAPSHOT@`. The refreshed starting score was
63.489897/rank 19, including unchanged-code rerun variation after the old
handover's 63.343397. At **7321615**, each track's coefficient improved, reaching
65.975209/rank 14. Its summary and exact runs are in
`validation/continuation3-official-summary.json` and per-track PERF.md.
The later follow-up changes A/C only; B/D kernels remain unchanged from 7321615.
Do not attribute their rerun variation to another optimization.

## Current candidate architecture

- **A:** twelve line-aligned parsers share an exact release/acquire endpoint
  registry. The binding 1,842-key catalogue fits 11 bits and a 2,048-key registry.
  Each hour bucket holds 32-bit records: 20 latency bits, 11 endpoint bits and
  one 5xx bit. The reserved latency value has an ordered full-uint32 overflow
  stream, including that sentinel itself. Nothing is truncated. Workers gather,
  select and format one hour, release its input buckets, and stream ready hours
  in order. SIMD loads are bounded; later selections exclude prior selected
  positions. Measured 7321615 used separate 4+2-byte latency/tag vectors.
- **B:** twelve query-only block indexes. The dictionary's negative filter has
  no false negatives; every possible hit still compares all bytes. Four inline
  uint16 IDs per posting, checked uint32 fallback, adaptive lists/bitmaps, and
  skipped duplicate bitmap writes. Exact mapped-text phrase checks remain
  uncapped and respect TAB/LF. Relative offsets have a checked uint64 fallback.
- **C:** twelve workers and a byte lookup justified by 240 countries plus the
  unmatched group. Compact stable nodes own complete decoded names in growing
  arenas. 256 shards, acquire/release publication, insertion locks only on misses
  and atomic membership give exact distinct counts. Current workers use private
  64 KiB pread buffers: incomplete records carry forward, and buffers grow with
  no fixed record cap. Section 2.2 proves LF+digit/BOM boundaries: names have no
  LF and notes have no digits/BOM. This is not a general arbitrary-CSV shortcut.
- **D:** six-worker forward/reverse compact CSR, exact sentinel overflow weights,
  twelve independent query workers, balanced bidirectional radix Dijkstra and
  sparse generation-tagged full-uint64 labels with safe wrap. No BFS remap or
  narrow-distance fallback is in production. Zero/wide/parallel/unreachable
  cases remain exact.

## Experiments and promotion decisions

`research/CONTINUATION3.md` and PERF.md separate local trials, official results
and rejected variants. Exact-source five-run paired comparisons against d069bfd
reduced local runtime about A=57%, B=29%, C=9%, D=17%; these are not official
ratios. B/D official memory increased, reducing their coefficient gains.

The later packed A ties local runtime and saves about 6-7 MiB RSS; only the
official coefficient prices that tradeoff. Buffered C improves the local public
full mean 0.068021s -> 0.056815s; larger buffers lose. Its large RSS reduction
mostly removes mapped input, not anonymous/cgroup memory. Official retention
or rejection is recorded separately in each PERF.md and continuation4 summary.

Rejected/not-promoted trials include A output recycling/percentile thresholds,
B bulk token scans/custom hashes, C mapped-name views/larger flat tables, and
D serial/private-counter CSR and direct-address distances. Narrow sparse D
labels did not establish enough benefit to justify their complexity. Research
prototypes are not production or universally validated replacements.

## Supplied files

All seven new attachments were read and preserved. The first four are A/B/C/C,
not A/B/C/D: B duplicates the second supplied B, and both C files are identical.
The later three are corrected A, cache-dropping C and D. See
`research/SUPPLIED_CONTINUATION_REVIEW.md` and
`validation/supplied-continuation-review.json` for hashes and exact scope.

- Earlier new A fails both full hashes because it skips the endpoint field.
  Later A fixes it, reserves real anonymous mapping slack, and passes both full
  seeds plus empty/percentile/parallel fixtures.
- New C versions fix the previous suffix-arena reproduction and optional EOF,
  but reject long valid names. The growth stress exceeds their fixed name
  budget. Their small cache also omits complete equality on a collision path;
  this was identified in code, not reproduced as a natural full-data collision.
- New D passes both full hashes, wide/zero/unreachable and five all-pairs random
  graph fixtures. No complete supplied implementation was promoted wholesale.
- Earlier Rust/second C reviews remain. A's architecture and C's boundary insight
  were useful inputs; runtime dependencies remain zero.

## Validation and environment

Current follow-up reports use **continuation4ac-release** and
**continuation4ac-sanitized**: 85 comparisons each (the previous 83 plus A's
sentinel/overflow-heavy datasets). Four direct programs check A's 4,375 guarded
parses and concurrent publication, C's 64 boundary alignments/1-12 workers and
concurrent membership, and D's rehash/wrap/overflow/search state. The forced
uint64 B-offset build passes the public full hash. Both full seeds are checked.

Actual source/common/binary hashes and flags are in `*-build.json`. Use
**build/continuation4ac-{release,sanitized}/track-*** for current candidate
sources. Older continuation4-* is packed A with mapped C; continuation3-* is
the measured 7321615 source set. Old final/refined/build/track-* binaries must
not be mistaken for current production. If a follow-up is rolled back, match
the per-track actual hashes before choosing a binary.

A/C follow-up offline sandbox records: `sandbox-continuation4ac.txt` and
`image-sizes-continuation4ac.json`. B/D images are unchanged from the all-track
continuation3 sandbox. `image-sizes-current.json` merges current image IDs,
about 119 MB each. Git line-ending normalization can change source byte hashes
without a semantic kernel change.

`codescythe-research` remains running: GCC 16, network none, memory/swap 5g,
cpuset 0-11, /work mounts the workspace. Linux-local public inputs are
`/benchdata/a` ... `/d`; independently referenced full seed 20261031 is under
`/benchfresh/seed20261031/a` ... `/d`. Do not casually delete these. Frozen
official checkout remains adb931623de2bcd3e12ab696f392a281783a3b43.

```powershell
docker exec codescythe-research python3 tools/refinement_checks.py --name <unique-release> --packed-a
docker exec codescythe-research python3 tools/refinement_checks.py --name <unique-sanitized> --sanitized --packed-a
python tools/refinement_sandbox.py --name <unique-name>
python tools/board_status.py --commit <implementation-sha> --wait 600
python tools/verify_private_watch.py
python tools/refinement_snapshot.py --name <unique-snapshot>
```

Do not blindly rerun old selectors/generators: `select_checkpoint3.py` restores
the older six-byte A source. Prototype generators target frozen sources, not
arbitrary later code. Record scripts append once; rerunning may duplicate facts
or intentionally reject duplicate sections. `prepare.py` overwrites Dockerfiles;
`check_all.py` reuses images. Rebuild changed images before sandbox claims.

## Private access and rules

Private access is verified: anonymous GitHub 404, fresh successful board watch
at the authenticated remote head, and all four scored 7321615 runs. The App
successfully cloned, built and scored the private repository. No registration
or permission change was needed. Refresh `validation/private-repository-access.json`
after the next push; its per-run evidence distinguishes watch from scoring.

Deadline November 2, 2026, 20:30 IST / 15:00 UTC. CPU: i5-13500, six P-cores/12
threads, turbo off, AVX2, no AVX-512. Entire exec-to-exit process is timed.
Official M is cgroup memory.peak, not mapped-input-inclusive RSS. 8 GB/no swap,
read-only roots/data, required output only, 1 GB charged tmpfs, offline build
under 600s, pinned allowlisted images under 2 GB. Last live rules: one run per
push, 300s interval, one in-flight job; a new queued push replaces queued work.
Wait for measurement before altering a submitted implementation.

Keep all four entered. Verify full hashes, fresh seeds, long records, widths,
sanitizers and sandbox, then measure K. No cached/seed-recognized/approximate
answers or unknown-key hardcoding. Source count is canonical per track; moving
identical reference files does not help. Next large gaps are B indexing and D
graph/search time: profile the current kernels, not the initial checkpoint.
Context7 outside the sandbox applies to actual library/SDK/CLI documentation
questions, not ordinary code-review or algorithm work.
'''
for key,value in {'COMMIT':commit,'STATUS':status,'AGGREGATE':f"{rank['aggregate']:.6f}",
                  'RANK':str(rank['rank']),'LEADER':leader['team'],'LEADER_SCORE':f"{leader['aggregate']:.6f}",
                  'ROWS':'\n'.join(rows),'SNAPSHOT':file}.items():text=text.replace('@'+key+'@',value)
(ROOT/'HANDOVER_NEXT.md').write_text(text)
print({'measured_commit':commit,'pending_runtime_tracks':pending,'aggregate':rank['aggregate'],'rank':rank['rank']})
