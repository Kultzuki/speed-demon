"""Write the exact retained checkpoint and final handover; never edit kernels."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser(); ap.add_argument('--prepare', action='store_true')
ap.add_argument('--commit', default=''); ap.add_argument('--snapshot', default='leaderboard-rust8-retained')
args = ap.parse_args()
def read(path): return json.loads((ROOT / path).read_text())
def digest(path): return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

provenance = read('validation/rust8-retained-artifact-provenance.json')
for track, entry in provenance['tracks'].items():
    for file, sha in entry['sources'].items(): assert digest(f'track-{track}/{file}') == sha
selection_path = ROOT / 'research/rust8-selection.json'; selection = read('research/rust8-selection.json')
board = read('validation/leaderboard-rust8-repeat.json' if args.prepare else f'validation/{args.snapshot}.json')
own = board['codescythe']; rank = next(t for t in board['ranking'] if t['team'].lower() == 'codescythe')
leader = board['ranking'][0]
best_rows = []; latest_rows = []
for track, item in own['tracks'].items():
    for key, rows in [('best', best_rows), ('latest', latest_rows)]:
        r = item[key]
        rows.append(f'| {track.upper()} | {r["K"]:.6f} | {r["T_s"]:.6f} | {r["M_bytes"]} | {r["S"]} | {r["commit"][:7]} | {r["run_id"]} |')

if args.prepare:
    state = '''Last pushed/scored HEAD is 8aa8ddb8f8aeba7d5d9b2b7c32745a26e5683d6e (Rust trial).
The current working tree restores exact stronger C++ A/D and has passed all
final retained-source gates and rebuilt offline image identities. Commit/push
this restoration normally, wait for every official result, then write its exact
SHA with tools/rust8_finish.py --commit SHA --snapshot SNAPSHOT. The Rust trial
is historical; its build/rust8-final executables are not the current entry.'''
    selection['status'] = 'Exact stronger C++ restored; 97+97 retained gates and rebuilt matching offline images pass; final push/official reconciliation pending'
else:
    assert args.commit and subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == args.commit
    assert subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/speed-demon'], text=True).split()[0] == args.commit
    assert own['watch']['ok'] and own['watch']['head'] == args.commit
    assert not own['queue'].get('in_flight') and not own['queue'].get('queued')
    for track, item in own['tracks'].items():
        run = item['latest']
        assert run['commit'] == args.commit and run['ok'] and run.get('ended_at') and all(run['gates'].values())
        assert run['S'] == provenance['tracks'][track]['S'] and run['D'] == 1
    source_paths = [f'track-{t}/{file}' for t in 'abcd' for file in ['main.cpp', 'common.hpp', 'Dockerfile', '.speed-demon.toml']]
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--', *source_paths], check=True)
    state = f'''Local and pushed HEAD: **{args.commit}**. All five official gates pass on
all four tracks at this exact SHA. The submitted kernels are clean. All four
runtime sources/configurations equal the incoming e9deec0 checkpoint; A/D were
restored after the two lower-scoring Rust trials. B/C never changed. No official
measurement or required local gate remains pending.'''
    summary = {'commit': args.commit, 'fetched_at': board['fetched_at'], 'aggregate': rank['aggregate'],
        'rank': rank['rank'], 'leader': leader['aggregate'], 'watch': own['watch'],
        'latest': {t: x['latest'] for t, x in own['tracks'].items()}, 'source_equal_to': 'e9deec07fa38f9abf0c167d6768c41c388e37ba5',
        'retention': 'Established stronger C++ entry; fully validated requested Rust packages preserved independently',
        'provenance': 'validation/rust8-retained-artifact-provenance.json'}
    with (ROOT / 'validation/rust8-retained-official-summary.json').open('x') as stream:
        json.dump(summary, stream, indent=2); stream.write('\n')
    rows = []
    for track, item in own['tracks'].items():
        run = item['latest']
        marker = f'## Final restored continuation 8 at {args.commit[:7]}'
        path = ROOT / f'track-{track}/PERF.md'; text = path.read_text(); assert marker not in text
        path.write_text(text + f'\n\n{marker}\n\nRun `{run["run_id"]}`: T={run["T_s"]:.6f}s, '
            f'M={run["M_bytes"]}, S={run["S"]}, D={run["D"]}, K={run["K"]:.6f}. '
            'All five official gates pass. Exact incoming C++ source is retained; differences are rerun variation. '
            f'Captured practice aggregate {rank["aggregate"]:.6f}, rank {rank["rank"]}, leader {leader["aggregate"]:.6f}. '
            f'Full record: validation/{args.snapshot}.json.\n')
        rows.append(f'| {track.upper()} | {run["T_s"]:.6f} | {run["M_bytes"]} | {run["S"]} | {run["K"]:.6f} | {run["run_id"]} |')
    path = ROOT / 'research/CONTINUATION8_RUST.md'
    path.write_text(path.read_text() + f'\n\n## Final retained checkpoint {args.commit[:7]}\n\n'
        f'Exact local/pushed commit {args.commit}; all five official gates pass on all four tracks. '
        f'Captured {board["fetched_at"]}: aggregate {rank["aggregate"]:.6f}, rank {rank["rank"]}; '
        f'leader {leader["aggregate"]:.6f}. Runtime sources/configurations equal e9deec0. '
        'All changes to final measurements on those sources are rerun variation.\n\n'
        '| Track | T s | M bytes | S | K | Run |\n|---|---:|---:|---:|---:|---|\n' + '\n'.join(rows) +
        '\n\nBoth requested Rust implementations remain complete, buildable and officially correct in '
        'rust8-validated/track-{a,d}; they are not the active entry because they did not beat the established '
        'coefficients. The retained C++ mix passes 97 release and 97 ASan/UBSan comparisons, all direct gates, '
        'both full seeds and exact rebuilt image identities. First place remains outstanding.\n')
    selection['status'] = 'Complete Rust evaluation preserved; stronger C++ entry restored, locally revalidated, rebuilt and officially verified'
    selection['final_commit'] = args.commit; selection['final_snapshot'] = args.snapshot

selection['history'].append({'at': datetime.now(timezone.utc).isoformat(), 'status': selection['status']})
selection_path.write_text(json.dumps(selection, indent=2) + '\n')
table = '| Track | K | T s | M bytes | S | Commit | Run |\n|---|---:|---:|---:|---:|---|---|\n'
text = f'''# Speed Demon handover - October 31, 2026, continuation 8

Continue the existing private entry; do not restart, re-register, reset or
force-push. Workspace C:/Users/kultzuki/Coding/Speed-demon, private origin
https://github.com/Kultzuki/speed-demon.git, watched branch speed-demon.
Do not spawn agents without explicit authorization. None was spawned.

## Exact checkpoint

{state}

Captured {board['fetched_at']}: practice aggregate **{rank['aggregate']:.6f}**,
rank **{rank['rank']}**, leader {leader['team']} **{leader['aggregate']:.6f}**.
Refresh the public feed before quoting current standings. First place is not
achieved. Public practice is separate from unseen-seed final scoring and judging.

Best records, possibly from older commits:

{table}''' + '\n'.join(best_rows) + '''

## Requested Rust A/D work and decision

Read research/CONTINUATION8_RUST.md and research/rust8-selection.json completely.
Full standalone Rust packages are **research/rust8-validated/track-a** and
**research/rust8-validated/track-d**; their README gives independent offline builds.
The original user track-d-rust/track-d is unchanged and hash-verified. Its heap
informs the port; its positional CLI, placeholder team manifest, larger BFS/
forward-search memory and unverified historical VM timings were reviewed.

Rust A uses buffered parallel reads, owned exact endpoint bytes, local ID caches,
packed lossless records, exact percentiles and ordered output. Rust D uses the
established compact forward/reverse CSR and bidirectional radix heap with separate
aligned full uint64 distances and width-derived uint32 node/generation tags.
Epoch wrap is safe. Actual canonical S is A=437, D=473, D=1 on both tracks.

Both Rust versions pass 97 comparisons in release/ASan/checked-arithmetic modes,
both full seeds and direct guard/concurrency/alignment/full-width/complete-CSR
checks. A publication also passes TSan with std/test rebuilt for the same ABI.
All five official gates pass at 0ca1987 and the unchanged-source 8aa8ddb rerun.
Best Rust A K=31.161629 is below C++ 33.234541; best Rust D K=14.542976 is below
15.399979 (its second run falls to 12.536262). Under the explicit regression rule,
the stronger submitted C++ kernels are restored; full Rust work/evidence remains.

The initial local counter wrongly included TOML data. Raw reports are preserved,
with explicit correction in validation/rust8-canonical-source-correction.json and
validation/rust8-final-artifact-provenance-corrected.json. Official counts match
437/473. This bookkeeping change did not alter any kernel, binary or raw timing.
C's new best at 8aa8ddb comes from unchanged source and is rerun variation.

## Active submitted kernels and validated artifacts

All four active kernels are C++20 and equal the incoming e9deec0 source/configs.
A retains complete endpoint equality, exact packed uint32 overflow and ordered
output. B retains 65,536-entry lazy posting blocks and both width fallbacks.
C retains exact owned names, partial-byte hash, four-record ring and checked-close
early exit. D retains the established full-uint64 bidirectional compact CSR.
No rejected sharded builder, packed heap, narrow label or hash-only identity is active.

Use **build/rust8-retained-{release,sanitized}/track-*** for the active entry.
Both pass **97 comparisons**, both full seeds, A guard/publication, C boundary/
concurrent membership, D wrap/rehash/wide distances and complete independent
forward/reverse CSR checks. The exact unchanged B forced-uint64-offset provenance
from continuation 7 is retained. All rebuilt offline images pass the starter
sandbox/full public hashes and match these validated executables byte for byte.
Provenance: validation/rust8-retained-artifact-provenance.json and
validation/image-sizes-rust8-retained.json. Images remain about 119 MB.

**build/rust8-final-{release,asan,checked} contains the historical Rust trial.**
Those executables match the archived Rust packages, not the active C++ entry.
Earlier non-final continuation7 binaries contain a rejected D trial. Do not mix
these artifact families. Git LF-normalized Rust builds were independently shown
to match their validated images in validation/rust8-lf-artifact-provenance.json.

## Preserved work, environment and remaining optimization

Every incoming dirty file and original user Rust file was archived byte for byte
in .out/continuation8-rust-incoming and .out/continuation8-user-d-rust. Full incoming
handover: research/HANDOVER_INCOMING_RUST8.md. Exact old C++ sources: research/baseline8/.
Prior PERF, selection records and official snapshots are preserved; final handover/
PERF/official metadata may be dirty after the last push. Keep those updates.

Read research/CONTINUATION7.md and CONTINUATION8_RUST.md before revisiting trials.
Mapped/buffered Rust A variants, SWAR decimals, worker counts and dedicated output
were actually measured. D's packed one-pass intermediate, fused relaxation and
six query workers were unselected. Separate aligned full-width distances and
packed generation tags were tested in Rust and did not beat the official best.
Do not repeat rejected sharding, narrow labels or packed heaps without new evidence.
Both supplied attachment sets were already reviewed; preserve every equality/width fallback.

First place remains the goal. A/C then B still determine the best three; D stays
entered. Tiny tuning is insufficient. Prioritize profiling on the scoring CPU,
A selection/output, B token/index/query work and a growing exact C tag table.
Local WSL2 gains did not transfer reliably; compare complete coefficients with
fresh cgroups, canonical source counts and dependencies. Distinguish unchanged-
source rerun variation from actual changes. Validate before ordinary pushes and
wait for every official result before another submitted-kernel change.

codescythe-research and pinned offline codescythe-rust8 compiler environments use
/work, twelve pinned CPUs and 5g/no swap. Original data remain at /benchdata and
/benchfresh/seed20261031; /data/fresh7 remains in the original benchmark volume.
No original data/container was deleted. The extra TSan helper is stopped. Its
ASLR exception was process-local in a separate race-test container; official
sandbox settings and host ASLR were unchanged. Never blindly run old selectors,
prepare.py, restore scripts or one-shot rust8 writers.

Existing authorization covers ordinary implementation, tests, commits and pushes.
Private App access needs no new registration or permission change. Deadline:
November 2, 2026, 20:30 IST / 15:00 UTC. Target i5-13500, six P-cores/twelve
threads, turbo off, AVX2/no AVX-512, exec-to-exit time, cgroup memory.peak, 8 GB/no
swap, offline allowlisted builds under 600 s and images under 2 GB. One live run
per push, 300-second interval, one in flight.
'''
(ROOT / 'HANDOVER_NEXT.md').write_text(text)
checkpoint = args.commit if not args.prepare else 'Read HANDOVER_NEXT.md for the final restoration SHA; 8aa8ddb is the prior Rust trial.'
(ROOT / 'NEXT_CHAT_PROMPT.md').write_text(f'''Read HANDOVER_NEXT.md completely and continue the existing private Speed Demon
entry in C:/Users/kultzuki/Coding/Speed-demon. Inspect git status first. Preserve
dirty handover/PERF/selection/official records. Do not restart, re-register,
reset, force-push or spawn agents without explicit authorization.

Checkpoint: {checkpoint}
Same private https://github.com/Kultzuki/speed-demon.git and watched speed-demon
branch. Active kernels are exact restored C++ e9deec0 sources; requested Rust A/D
are complete, officially correct alternatives in research/rust8-validated/track-{{a,d}}.
Both Rust trials passed every gate but did not beat historical best coefficients,
so they were not promoted. Original track-d-rust/track-d is unchanged.

Read research/CONTINUATION8_RUST.md, research/rust8-selection.json and the final
official snapshot. Active binaries are build/rust8-retained-{{release,sanitized}}:
97 comparisons, both full seeds, direct checks and exact rebuilt offline images
pass. Provenance is validation/rust8-retained-artifact-provenance.json.
build/rust8-final-* are the historical Rust trials, not active C++.

Captured practice {rank['aggregate']:.6f}, rank {rank['rank']}; leader {leader['aggregate']:.6f}.
Refresh standings before quoting. First place remains outstanding; A/C then B
count in the best three. C's latest record came from unchanged-source variation.
Profile substantial runtime work on the target CPU and compare complete K.
Preserve exact identity, all width fallbacks and safe epochs. Validate promising
changes before committing/pushing and wait for official results before another
kernel change. Do not blindly rerun any old selector or one-shot rust8 writer.
''')
print('PREPARED' if args.prepare else 'FINAL', checkpoint, rank['aggregate'], rank['rank'], flush=True)
