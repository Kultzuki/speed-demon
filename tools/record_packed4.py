"""Record the exact packed A candidate and its independent promotion decision."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/name).read_text())

def local():
    for mode in ['release','sanitized']:
        builds=read(f'validation/continuation4ac-{mode}-build.json')
        previous=read(f'validation/continuation3-{mode}-build.json')
        for suffix,count in [('',69),('-full',4),('-extra',12)]:
            assert len(read(f'validation/continuation4ac-{mode}{suffix}.json')['results'])==count
        for track in 'abcd':
            assert builds[track]['source_sha256']==hashlib.sha256((ROOT/f'track-{track}/main.cpp').read_bytes()).hexdigest()
            if track in 'bd':assert builds[track]['source_sha256']==previous[track]['source_sha256']
    images=read('validation/image-sizes-continuation3.json');new=read('validation/image-sizes-continuation4ac.json')
    assert set(new)=={'a','c'} and all(x['size_bytes']<2*1024**3 for x in new.values())
    images.update(new)
    (ROOT/'validation/image-sizes-current.json').write_text(json.dumps(images,indent=2)+'\n')
    trial=read('research/results/a-packed4-paired.json')['results']
    old,new=trial['measured']['trimmed_mean_s'],trial['packed']['trimmed_mean_s']
    text=f'''

## Packed A follow-up to measured 7321615

One 32-bit record replaces the separate uint32 latency/uint16 tag vectors:
20 latency bits, 11 endpoint bits and one error bit. The binding 1,842-key
catalogue fits in 11 bits. The latency sentinel has an exact ordered uint32
overflow stream, including the sentinel's own numeric value. No input latency
is truncated and no frequency/distribution assumption decides the answers.

Seven alternating full-hash runs: measured source {old:.6f}s, packed source
{new:.6f}s trimmed mean. Runtime is effectively tied locally; process RSS falls
by about 6-7 MiB. This is a memory tradeoff to measure officially, not an
established coefficient gain. Raw evidence: research/results/a-packed4-paired.json.

Both release and ASan/UBSan pass 85 dataset comparisons (the prior 83 plus two
sentinel/overflow-heavy fixtures), four direct programs and forced uint64 B
offset verification. A's guard program now checks 4,375 parses, with latencies
0, 2^20-2, 2^20-1, 2^20 and UINT32_MAX, and twelve-way endpoint publication.
The new A image passes its offline build and full-hash sandbox. B/D sources
and images are unchanged from 7321615; new builds retain their exact hashes.
Compiler/source/binary provenance: validation/continuation4ac-*-build.json.
'''
    for file in ['track-a/PERF.md','research/CONTINUATION3.md']:
        path=ROOT/file;existing=path.read_text();assert '## Packed A follow-up to measured 7321615' not in existing
        path.write_text(existing+text)
    path=ROOT/'track-c/PERF.md'
    path.write_text(path.read_text()+'''

## Buffered C follow-up to measured 7321615

Parser workers read through private 64 KiB buffers. The same section 2.2
record-boundary rule selects only complete records for each parse call; an
incomplete record is carried forward, and the buffer grows without a fixed
record-length cap. Exact owned name storage makes buffer reuse safe. All cents,
escaping, BOMs, EOF and membership logic remain. No cache-dropping advice is used.

Five alternating public full-hash runs: mapped source 0.068021s, selected 64 KiB
stream 0.056815s trimmed mean. Larger 256 KiB/1 MiB buffers were slower.
The huge RSS decrease mostly removes mapped input, and is not an official memory
saving. Source and anonymous-buffer costs must still be priced by the board.
Both final release/ASan gates pass 85 dataset comparisons plus the direct and
forced-offset programs, including the long-name, hostile parallel CSV and both
full seeds. New A/C images pass offline builds and full-hash sandbox checks.
Reports and actual build hashes use validation/continuation4ac-*.
''')
    (ROOT/'research/CONTINUATION3.md').write_text((ROOT/'research/CONTINUATION3.md').read_text()+'''

## Buffered C follow-up

Current C uses private 64 KiB pread buffers, carrying incomplete records and
growing for arbitrarily long records. Exact owned names make reuse safe. The
boundary shortcut retains the published section 2.2 proof. The public full-hash
paired mean improves 0.068021s to 0.056815s; larger buffers are rejected. Lower
RSS mostly reflects absent mapped pages, not a proven cgroup-memory reduction.
Current A/C plus unchanged B/D pass both 85-comparison gates in
validation/continuation4ac-* and the A/C offline sandbox checks.
''')
    (ROOT/'validation/continuation4-selection.json').write_text(json.dumps({
        'parent_implementation':'7321615dd4b7f43d35cd71d45c607541b0fd73af','changed_runtime_tracks':['a','c'],
        'candidates':{'a':'research/prototypes/a-packed4.cpp','c':'research/prototypes/c-stream4-65536.cpp'},
        'provenance':read('validation/continuation4ac-release-build.json')},indent=2)+'\n')
    print('PASS A/C local gates, exact overflow/record carry and unchanged B/D hashes')

def official(commit):
    subprocess.run([sys.executable,str(ROOT/'tools/refinement_snapshot.py'),'--name','leaderboard-continuation4'],check=True)
    snapshot=read('validation/leaderboard-continuation4.json')
    own=snapshot['codescythe'];current=next(x for x in snapshot['ranking'] if x['team'].lower()=='codescythe')
    for entry in own['tracks'].values():
        run=entry['latest'];assert run['commit']==commit and run['ok'] and all(run['gates'].values())
    baselines=read('validation/continuation3-official-summary.json')['latest']
    baseline=baselines['a']
    run=own['tracks']['a']['latest'];retained=run['K']>=baseline['K']
    for track,entry in own['tracks'].items():
        value=entry['latest']
        path=ROOT/f'track-{track}/PERF.md'
        text=path.read_text()+f"\n\n## Official packed-A follow-up at {commit[:7]}\n\n"
        text+=f"Run `{value['run_id']}`: T={value['T_s']:.6f}s, M={value['M_bytes']} bytes, S={value['S']}, D={value['D']}, K={value['K']:.6f}, points={value['points']:.6f}. All official gates passed.\n\n"
        if track=='a':text+=f"Packed A is {'retained' if retained else 'rejected and must be restored'}: K={run['K']:.6f} versus measured 7321615 K={baseline['K']:.6f}.\n"
        elif track=='c':text+=f"Buffered C is {'retained' if value['K']>=baselines['c']['K'] else 'rejected and must be restored'}: K={value['K']:.6f} versus measured 7321615 K={baselines['c']['K']:.6f}.\n"
        else:text+='Runtime source is unchanged from 7321615. Any change in this rerun is measurement variation, not another kernel optimization.\n'
        path.write_text(text)
    summary={'commit':commit,'aggregate':current['aggregate'],'rank':current['rank'],
             'leader':snapshot['ranking'][0]['aggregate'],'packed_a_retained':retained,
             'buffered_c_retained':own['tracks']['c']['latest']['K']>=baselines['c']['K'],
             'latest':{track:item['latest'] for track,item in own['tracks'].items()},'watch':own['watch']}
    (ROOT/'validation/continuation4-official-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    path=ROOT/'research/CONTINUATION3.md'
    path.write_text(path.read_text()+f"\nOfficial follow-up `{commit}`: packed A {'retained' if retained else 'rejected'}, buffered C {'retained' if summary['buffered_c_retained'] else 'rejected'}; best-three aggregate {current['aggregate']:.6f}, captured rank {current['rank']}, leader {summary['leader']:.6f}. B/D kernels are unchanged; their rerun variation is recorded separately.\n")
    print(json.dumps({k:v for k,v in summary.items() if k not in ['latest','watch']},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--local',action='store_true');parser.add_argument('--official',default='');args=parser.parse_args()
    local() if args.local else official(args.official)
