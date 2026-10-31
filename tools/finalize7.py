"""Reconcile the officially selected mix, then write the measured final handover."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def write_json(path, value):
    (ROOT / path).write_text(json.dumps(value, indent=2) + '\n')


def local():
    output = ROOT / 'validation/continuation7-final-artifact-provenance.json'
    assert not output.exists()
    selection = read('research/continuation7-final-selection.json')
    images = read('validation/image-sizes-continuation7.json')
    images['d'] = read('validation/image-sizes-continuation7-final-d.json')['d']
    result = {'scope': 'Final retained A/B/C plus exact restored D; no rejected D trial is used.',
              'images_origin': {'abc': 'validation/sandbox-continuation7.txt',
                                'd': 'validation/sandbox-continuation7-final-d.txt'},
              'tracks': {}, 'gates': {}}
    for mode in ['release', 'sanitized']:
        name = f'continuation7-final-{mode}'
        counts = {s: len(read(f'validation/{name}{s}.json')['results'])
                  for s in ['', '-full', '-extra', '-additional', '-new']}
        assert sum(counts.values()) == 93
        result['gates'][mode] = counts
        builds = read(f'validation/{name}-build.json')
        for track, build in builds.items():
            assert build['source_sha256'] == digest(f'track-{track}/main.cpp')
            assert build['source_sha256'] == selection['selected'][track]['selected_sha256']
            assert build['binary_sha256'] == digest(f'build/{name}/track-{track}')
            if mode == 'release':
                assert build['binary_sha256'] == images[track]['solution_sha256']
                result['tracks'][track] = {**build, **images[track],
                    'S': selection['selected'][track]['S'], 'D': 1,
                    'source_lf_sha256': hashlib.sha256((ROOT / f'track-{track}/main.cpp').read_text().encode()).hexdigest(),
                    'Dockerfile_sha256': digest(f'track-{track}/Dockerfile'),
                    'manifest_sha256': digest(f'track-{track}/.speed-demon.toml')}
    write_json('validation/continuation7-final-artifact-provenance.json', result)
    write_json('validation/image-sizes-continuation7-final.json', images)
    old = ROOT / 'validation/image-sizes-current.json'
    if old.exists():
        (ROOT / 'validation/image-sizes-before-continuation7.json').write_bytes(old.read_bytes())
    write_json('validation/image-sizes-current.json', images)
    selection['status'] = 'Final 93+93 mixed gates and exact rebuilt images pass; final push/official rerun pending'
    write_json('research/continuation7-final-selection.json', selection)
    message = '''\n\n## Final continuation 7 local reconciliation

A/B/C retain their improved f992539 sources. D is restored exactly to the
stronger incoming source after its official coefficient regression. The final
mix passes 93 release and 93 ASan/UBSan comparisons, both full seeds, the direct
programs including both complete 200,000-edge CSR checks, and forced uint64 B
offsets. All final image executables match build/continuation7-final-release.
A/B/C images originate in sandbox-continuation7.txt; restored D was rebuilt
in sandbox-continuation7-final-d.txt. Complete final provenance is
validation/continuation7-final-artifact-provenance.json. The earlier
continuation7 builds contain the rejected D trial and remain historical only.
'''
    for track in 'abcd':
        path = ROOT / f'track-{track}/PERF.md'
        path.write_text(path.read_text() + message)
    report = ROOT / 'research/CONTINUATION7.md'
    report.write_text(report.read_text() + message)
    print('PASS final source/binary/image identities and both 93-comparison gates; ready for ordinary final push.')


def handover(snapshot_name, commit):
    board = read('validation/' + snapshot_name + '.json')
    own = board['codescythe']
    rank = next(t for t in board['ranking'] if t['team'].lower() == 'codescythe')
    leader = board['ranking'][0]
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == commit
    assert subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/speed-demon'], text=True).split()[0] == commit
    assert own['watch']['head'] == commit and own['watch']['ok']
    provenance = read('validation/continuation7-final-artifact-provenance.json')
    for track, item in own['tracks'].items():
        run = item['latest']
        assert run['commit'] == commit and run['ok'] and all(run['gates'].values())
        assert digest(f'track-{track}/main.cpp') == provenance['tracks'][track]['source_sha256']
    best_rows = []
    latest_rows = []
    for track, item in own['tracks'].items():
        for key, target in [('best', best_rows), ('latest', latest_rows)]:
            r = item[key]
            target.append(f'| {track.upper()} | {r["K"]:.6f} | {r["T_s"]:.6f} | {r["M_bytes"]} | '
                          f'{r["S"]} | {r["commit"][:7]} | {r["run_id"]} |')
    text = f'''# Speed Demon handover - October 31, 2026

Continue the existing entry. Do not restart, reset, force-push or re-register.

## Exact checkpoint and official results

- Workspace: C:/Users/kultzuki/Coding/Speed-demon.
- Private origin: https://github.com/Kultzuki/speed-demon.git; watched branch speed-demon.
- Local and pushed HEAD: **{commit}**. All five official gates pass on all four tracks at this SHA.
- Initial checkpoint: c503752efebdbebcd9c6de41a4485af8ef1776fd. Candidate f99253995d7fa9f97f825c9c8b37c4ec705d3e66
  improved A/B/C officially; its D construction trial lost and was restored.
- Captured {board['fetched_at']}: best-three practice aggregate **{rank['aggregate']:.6f}**,
  rank **{rank['rank']}**, leader {leader['team']} **{leader['aggregate']:.6f}**.
  Started at 69.160567 / rank 18. First place has not been reached.
  Refresh the feed before quoting current standings. This is public practice,
  separate from unseen-seed final scoring and 35% human judging.

Best records, possibly from older commits:

| Track | K | T s | M bytes | S | Commit | Run |
|---|---:|---:|---:|---:|---|---|
''' + '\n'.join(best_rows) + '''

Latest exact-HEAD rerun:

| Track | K | T s | M bytes | S | Commit | Run |
|---|---:|---:|---:|---:|---|---|
''' + '\n'.join(latest_rows) + f'''

A/B/C are unchanged since f992539; later differences on those tracks are rerun
variation. D restores the established incoming full-uint64 kernel. All four
entries remain; best-three uses A/B/C. See validation/{snapshot_name}.json and
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

Use **build/continuation7-final-{{release,sanitized}}/track-*** for the final mix.
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
/data/fresh7/{{a,b,c,d}}. codescythe-fresh-continuation7 is stopped; no original
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
'''
    (ROOT / 'HANDOVER_NEXT.md').write_text(text)
    selection = read('research/continuation7-final-selection.json')
    selection['status'] = 'Final validated, rebuilt and officially scored; retained A/B/C and restored D'
    selection['final_commit'] = commit
    selection['final_snapshot'] = snapshot_name
    write_json('research/continuation7-final-selection.json', selection)
    report = ROOT / 'research/CONTINUATION7.md'
    report.write_text(report.read_text() + f'\n\nFinal checkpoint {commit}: all official gates pass; '
        f'aggregate {rank["aggregate"]:.6f}, captured rank {rank["rank"]}, leader {leader["aggregate"]:.6f}. '
        'A/B/C retained; D restored. Final artifacts agree with both 93-comparison gates. '
        'Later unchanged-source measurements are rerun variation. First place remains outstanding.\n')
    print('FINAL', commit, rank['aggregate'], 'rank', rank['rank'], 'leader', leader['aggregate'])


parser = argparse.ArgumentParser()
parser.add_argument('--local', action='store_true')
parser.add_argument('--snapshot', default='leaderboard-continuation7-final')
parser.add_argument('--commit', default='')
args = parser.parse_args()
local() if args.local else handover(args.snapshot, args.commit)
