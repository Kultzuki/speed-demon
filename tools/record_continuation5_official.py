"""Record official results and per-track coefficient retention decisions."""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--commit',required=True);parser.add_argument('--snapshot',required=True);parser.add_argument('--name',default='continuation5-official');parser.add_argument('--restored-final',action='store_true');args=parser.parse_args()
board=json.loads((ROOT/'validation'/args.snapshot).read_text())
start=json.loads((ROOT/'validation/leaderboard-continuation5-start.json').read_text())
own=board['codescythe'];ranked=next(t for t in board['ranking'] if t['team']=='CodeScythe')
previous=start['codescythe']['tracks']
summary={'commit':args.commit,'fetched_at':board['fetched_at'],'aggregate':ranked['aggregate'],'rank':ranked['rank'],
         'leader':board['ranking'][0]['aggregate'],'latest':{},'decisions':{},'watch':own.get('watch')}
rows=[]
for track in 'abcd':
    run=own['tracks'][track]['latest'];assert run['commit']==args.commit
    assert run.get('ended_at') is not None
    old=previous[track]['best']
    passed=run.get('ok') and all((run.get('gates') or {}).get(g) for g in ['check','build','correctness','timeout','sandbox'])
    better=bool(passed and run['K']>old['K'])
    decision='unchanged A kernel; retain source and historical best' if track=='a' else ('retain' if better else 'reject and restore incoming source')
    if args.restored_final:
        assert passed
        if track=='d':decision='restored incoming full-uint64 kernel; retain proven source'
        elif track in 'bc':decision='unchanged retained 160e4dd kernel; rerun variation'
    summary['latest'][track]=run
    summary['decisions'][track]={'decision':decision,'all_gates_passed':bool(passed),'previous_best_K':old['K'],'new_K':run.get('K'),'K_ratio':run['K']/old['K'] if passed else None}
    path=ROOT/f'track-{track}/PERF.md';text=path.read_text();marker=f'## Official continuation measurement {args.commit[:7]}'
    assert marker not in text
    text+=f'''\n\n{marker}

Run `{run['run_id']}` at `{args.commit}`: gates={bool(passed)},
T={run.get('T_s')}s, M={run.get('M_bytes')} bytes, S={run.get('S')},
D={run.get('D')}, K={run.get('K')}, points={run.get('points')}.
Previous recorded best K={old['K']}. Decision: **{decision}**.
'''
    if track=='a':text+='A runtime source is unchanged; any result difference is rerun variation.\n'
    text+=f"\nCaptured best-three aggregate {ranked['aggregate']:.6f}, rank {ranked['rank']}; leader {board['ranking'][0]['aggregate']:.6f}. Snapshot: validation/{args.snapshot}. Public practice, not final judging.\n"
    path.write_text(text,encoding='utf-8',newline='\n')
    rows.append(f"| {track.upper()} | {run.get('T_s')} | {run.get('M_bytes')} | {run.get('S')} | {run.get('K')} | {run.get('points')} | {run['run_id']} | {decision} |")
(ROOT/f'validation/{args.name}-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
path=ROOT/'research/CONTINUATION5.md'
text=path.read_text()+f'''\n\n## Official result at {args.commit[:7]}

Exact pushed commit: {args.commit}. Captured at {board['fetched_at']}.
Best-three aggregate **{ranked['aggregate']:.6f}**, rank **{ranked['rank']}**;
leader **{board['ranking'][0]['aggregate']:.6f}**. This remains public practice.

| Track | T seconds | M bytes | S | K | Points | Official run | Decision |
|---|---:|---:|---:|---:|---:|---|---|
'''+ '\n'.join(rows)
text+=('\n\nThe rejected D trial has been restored to the stronger incoming full-uint64 kernel. A/B/C are unchanged since 160e4dd, so their new measurements are rerun variation, not additional kernel optimizations. All final official gates passed.\n' if args.restored_final else '\n\nA has no new runtime change. Each other decision compares the full official coefficient with the starting historical best, not the most recent losing rerun. Rejected candidates must be restored and changed images rebuilt before closing the handover.\n')
path.write_text(text,encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['latest','watch']},indent=2))
