"""Record validated local evidence, then the exact implementation's board result."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def read(path):
    return json.loads((ROOT/path).read_text())

def local():
    builds={mode:read(f'validation/continuation3-{mode}-build.json') for mode in ['release','sanitized']}
    for mode in builds:
        for suffix,count in [('',69),('-full',4),('-extra',10)]:
            assert len(read(f'validation/continuation3-{mode}{suffix}.json')['results'])==count
        for track in 'abcd':
            assert builds[mode][track]['source_sha256']==hashlib.sha256((ROOT/f'track-{track}/main.cpp').read_bytes()).hexdigest()
    images=read('validation/image-sizes-continuation3.json')
    assert len(images)==4 and all(item['size_bytes']<2*1024**3 for item in images.values())
    notes={
        'a':'A shared exact endpoint registry and separate latency/tag hour buckets replace six large endpoint/group catalogs and their serial merge. Twelve workers gather/select/format hours, release consumed buckets, and stream completed hours in order. All SIMD loads stay within the input range; the full uint32 latency and nearest-rank behavior remain.',
        'b':'Twelve block workers, an exact-safe negative dictionary filter, and duplicate-write suppression for dense postings are selected. Every possible filter hit still goes through exact byte equality. Query folds, phrase verification, uint16/uint32 document fallback and uint32/uint64 relative-offset fallback remain.',
        'c':'Owned name nodes retain length and exact bytes without redundant stored hashes/string-view descriptors. The lookup uses uint8 country IDs under the binding 240-country plus unmatched bound. Growing arenas, full decoded-name equality, contract-safe boundaries, release/acquire publication and atomic membership remain.',
        'd':'Only the query-worker cap changes from six to twelve. Six-worker CSR construction, full uint64 sparse labels, overflow weights, radix heaps and balanced bidirectional search remain. Private counters, direct-address labels and narrow sparse labels did not justify replacing this kernel.'}
    rows=[]
    for track in 'abcd':
        trial=read(f'research/results/continuation3-paired-{track}.json')['results']
        old,new=trial['checkpoint']['trimmed_mean_s'],trial['selected']['trimmed_mean_s']
        rows.append(f'| {track.upper()} | {old:.6f} | {new:.6f} | {(1-new/old)*100:.1f}% |')
        path=ROOT/f'track-{track}/PERF.md'
        text=path.read_text()
        marker='## Continuation from d069bfd: selected local refinement'
        assert marker not in text
        text+='\n\n'+marker+'\n\n'+notes[track]+'\n\n'
        text+=f'Five alternating full-hash-checked Linux-local runs of the actual selected source: checkpoint {old:.6f}s, selected {new:.6f}s trimmed mean. See `research/results/continuation3-paired-{track}.json`. These are AMD/WSL2 timings; RSS includes mapped input and is not official cgroup memory.\n\n'
        text+='Both release and ASan/UBSan pass 83 dataset comparisons, four direct A/C/D boundary/concurrency/state programs, and a forced uint64-offset B full-hash build. A also passes 1,750 guard-page parses and twelve-way endpoint publication. Provenance is in `validation/continuation3-*-build.json`. Offline rebuilt images pass all four public full hashes in the read-only/no-network/unprivileged sandbox; see `validation/sandbox-continuation3.txt` and `image-sizes-continuation3.json`. Official promotion is decided separately from these local measurements.\n'
        path.write_text(text)
    report='''# Continuation from d069bfd

The original four-track entry and watched speed-demon branch were continued.
The live starting snapshot was 63.489897, rank 19, with leader 73.812408.
These include unchanged-code rerun variation after the previous handover.

## Exact selected-source paired local timings

| Track | Checkpoint seconds | Selected seconds | Local reduction |
|---|---:|---:|---:|
'''+ '\n'.join(rows)+'''

Every run matches the full public output hash. Each row is its own alternating
five-run batch; cross-track/batch timings must not be combined into a synthetic
official score. The public machine measures cgroup peak memory, not process RSS.

## Selected changes and rejected alternatives

'''+ '\n\n'.join(f'- **{track.upper()}:** {notes[track]}' for track in 'abcd')+'''

Individual raw trials remain under research/results and research/prototypes.
In particular, A output-buffer recycling, B block scanning/custom word hashing,
C mapped-name views/larger flat tables, and D serial/private CSR counters and
direct-address labels were not selected. Small differences between narrow and
wide sparse D labels were inconclusive; full-width labels are retained.

## Validation and supplied code

Release and ASan/UBSan each pass 69 differential datasets, four public full
hashes, six extra boundary/reproduction datasets and four independently
referenced fresh full outputs: 83 comparisons each. Four direct programs check
A guard pages/publication, C 64 boundary alignments and concurrent membership,
and D wrap/rehash/overflow/search state. B's forced uint64-offset build passes
the full public hash. All offline images pass the starter sandbox and size cap.
Actual compiler flags/source/common/binary hashes are saved with each build.

The two new pasted sets were preserved and reviewed separately in
SUPPLIED_CONTINUATION_REVIEW.md. Correctness failures, collision-path concerns,
and successful tested fixtures are distinguished. None was copied wholesale.

Anonymous GitHub access returns 404 for the user-confirmed private repository;
a fresh successful board watch reads the same remote head. Evidence is in
validation/private-repository-access.json. Scoring the new implementation will
add a direct private-clone/build check.
'''
    (ROOT/'research/CONTINUATION3.md').write_text(report)
    print('PASS actual source hashes, both 83-comparison gates, images and paired-source records')

def official(commit):
    subprocess.run([sys.executable,str(ROOT/'tools/refinement_snapshot.py'),'--name','leaderboard-continuation3'],check=True)
    snapshot=read('validation/leaderboard-continuation3.json')
    own=snapshot['codescythe']
    current=next(item for item in snapshot['ranking'] if item['team'].lower()=='codescythe')
    leader=snapshot['ranking'][0]
    for track,item in own['tracks'].items():
        run=item['latest']
        assert run['commit']==commit and run['ok'] and all(run['gates'].values())
        old=read('validation/leaderboard-continuation-start.json')['codescythe']['tracks'][track]['best']
        decision='retained' if run['K']>=old['K'] else 'regression: restore the prior stronger kernel'
        path=ROOT/f'track-{track}/PERF.md'
        text=path.read_text()+f"\n\n## Official continuation measurement at {commit[:7]}\n\n"
        text+=f"Run `{run['run_id']}`: T={run['T_s']:.6f}s, M={run['M_bytes']} bytes, S={run['S']}, D={run['D']}, K={run['K']:.6f}, points={run['points']:.6f}. All official gates passed.\n\n"
        text+=f"Compared with the refreshed starting best K={old['K']:.6f}: **{decision}**. This is one public-practice run; local paired gains and unchanged-code rerun variation are separate from hidden-seed/final judging results.\n"
        path.write_text(text)
        print(track,decision,'K',old['K'],'->',run['K'])
    (ROOT/'research/CONTINUATION3.md').write_text((ROOT/'research/CONTINUATION3.md').read_text()+f"\n## Official result\n\nImplementation `{commit}` passed every official gate on all four tracks. Best-three public aggregate: **{current['aggregate']:.6f}**, captured rank **{current['rank']}**; leader **{leader['aggregate']:.6f}**. Exact run IDs and per-track promotion decisions are in PERF.md and validation/leaderboard-continuation3.json.\n")
    summary={'commit':commit,'aggregate':current['aggregate'],'rank':current['rank'],'leader':leader['aggregate'],
             'latest':{track:item['latest'] for track,item in own['tracks'].items()},'watch':own['watch']}
    (ROOT/'validation/continuation3-official-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['latest','watch']},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--local',action='store_true');parser.add_argument('--official',default='');args=parser.parse_args()
    local() if args.local else official(args.official)
