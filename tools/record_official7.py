"""Record one exact completed official run, without selecting or editing kernels."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument('--commit', required=True)
ap.add_argument('--snapshot', required=True)
ap.add_argument('--name', default='continuation7')
ap.add_argument('--final', action='store_true')
args = ap.parse_args()
snapshot = json.loads((ROOT / 'validation' / (args.snapshot + '.json')).read_text())
starting = json.loads((ROOT / 'validation/leaderboard-continuation7-start.json').read_text())
own = snapshot['codescythe']
current = next(t for t in snapshot['ranking'] if t['team'].lower() == 'codescythe')
leader = snapshot['ranking'][0]
rows = []
decisions = {}
for track, item in own['tracks'].items():
    run = item['latest']
    assert run['commit'] == args.commit and run['ok'] and run.get('ended_at')
    assert all(run['gates'].get(g) for g in ['check', 'build', 'correctness', 'timeout', 'sandbox'])
    previous = starting['codescythe']['tracks'][track]['best']
    decision = ('candidate exceeds the starting recorded best' if run['K'] >= previous['K']
                else 'candidate did not beat the starting recorded best; retention decision required')
    if args.final:
        decision = ('restored established full-uint64 kernel; retain; this measurement is a rerun'
                    if track == 'd' else 'unchanged retained f992539 kernel; this measurement is rerun variation')
    decisions[track] = decision
    perf = ROOT / f'track-{track}/PERF.md'
    text = perf.read_text()
    marker = f'## Official continuation 7 at {args.commit[:7]}'
    assert marker not in text
    text += (f'\n\n{marker}\n\nRun `{run["run_id"]}` at `{args.commit}`: '
             f'T={run["T_s"]:.6f}s, M={run["M_bytes"]} bytes, S={run["S"]}, D={run["D"]}, '
             f'K={run["K"]:.6f}, points={run["points"]:.6f}. All five official gates passed. '
             f'Starting historical best K={previous["K"]:.6f}: **{decision}**.\n\n'
             f'Captured practice aggregate {current["aggregate"]:.6f}, rank {current["rank"]}; '
             f'leader {leader["aggregate"]:.6f}. This is public practice, not final holdout or human judging. '
             f'Full record: validation/{args.snapshot}.json.\n')
    perf.write_text(text)
    rows.append(f'| {track.upper()} | {run["T_s"]:.6f} | {run["M_bytes"]} | {run["S"]} | '
                f'{run["K"]:.6f} | {previous["K"]:.6f} | {run["run_id"]} |')
summary = {'commit': args.commit, 'fetched_at': snapshot['fetched_at'],
           'aggregate': current['aggregate'], 'rank': current['rank'], 'leader': leader['aggregate'],
           'watch': own['watch'], 'latest': {t: v['latest'] for t, v in own['tracks'].items()},
           'decisions': decisions, 'snapshot': args.snapshot}
path = ROOT / f'validation/{args.name}-official-summary.json'
assert not path.exists()
path.write_text(json.dumps(summary, indent=2) + '\n')
report = ROOT / 'research/CONTINUATION7.md'
report.write_text(report.read_text() + f'''\n\n## Official measurement at {args.commit[:7]}

Exact commit: {args.commit}; captured {snapshot['fetched_at']}.
All four tracks passed all five official gates. Practice aggregate
**{current['aggregate']:.6f}**, rank **{current['rank']}**; leader **{leader['aggregate']:.6f}**.

| Track | T s | M bytes | S | K | Starting best K | Official run |
|---|---:|---:|---:|---:|---:|---|
''' + '\n'.join(rows) + '\n\n' + '\n'.join(f'- {t.upper()}: {d}.' for t, d in decisions.items())
                  + '\n\nThese are public practice measurements, separate from unseen-seed final scoring and judging.\n')
print(json.dumps({k: v for k, v in summary.items() if k not in ['watch', 'latest']}, indent=2))
