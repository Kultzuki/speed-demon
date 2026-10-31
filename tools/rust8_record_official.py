"""Record one completed exact-commit official run without touching kernels."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument('--commit', required=True); ap.add_argument('--snapshot', required=True)
ap.add_argument('--name', required=True); ap.add_argument('--rerun', action='store_true')
args = ap.parse_args()
snapshot = json.loads((ROOT / f'validation/{args.snapshot}.json').read_text())
start = json.loads((ROOT / 'validation/leaderboard-rust8-start.json').read_text())
own = snapshot['codescythe']
rank = next(t for t in snapshot['ranking'] if t['team'].lower() == 'codescythe')
leader = snapshot['ranking'][0]
rows = []; runs = {}
for track, item in own['tracks'].items():
    run = item['latest']; historical = start['codescythe']['tracks'][track]['best']
    incoming = start['codescythe']['tracks'][track]['latest']
    assert run['commit'] == args.commit and run['ok'] and run.get('ended_at')
    assert all(run['gates'].get(g) for g in ['check', 'build', 'correctness', 'timeout', 'sandbox'])
    if track in 'ad': assert run['S'] == {'a': 437, 'd': 473}[track] and run['D'] == 1
    run = {**run, 'historical_best_K_at_start': historical['K'], 'incoming_exact_head_K': incoming['K'],
           'ratio_to_incoming_latest': run['K'] / incoming['K'],
           'ratio_to_historical_best': run['K'] / historical['K']}
    runs[track] = run
    decision = ('Unchanged B/C source; timing/coefficient differences are rerun variation.' if track in 'bc'
                else 'Rust passes every gate; compare with historical best and incoming exact-head rerun before final retention.')
    if args.rerun: decision = 'Unchanged submitted source; this run measures rerun variation. ' + decision
    path = ROOT / f'track-{track}/PERF.md'; text = path.read_text()
    marker = f'## Official Rust continuation at {args.commit[:7]}'
    assert marker not in text
    path.write_text(text + f'\n\n{marker}\n\nRun `{run["run_id"]}` at `{args.commit}`: '
        f'T={run["T_s"]:.6f}s, M={run["M_bytes"]}, S={run["S"]}, D={run["D"]}, K={run["K"]:.6f}. '
        f'All five official gates pass. Incoming exact-head K={incoming["K"]:.6f}; historical best K={historical["K"]:.6f}. '
        f'{decision}\n\nCaptured practice aggregate {rank["aggregate"]:.6f}, rank {rank["rank"]}; '
        f'leader {leader["aggregate"]:.6f}. Full snapshot: validation/{args.snapshot}.json.\n')
    rows.append(f'| {track.upper()} | {run["T_s"]:.6f} | {run["M_bytes"]} | {run["S"]} | {run["K"]:.6f} | '
                f'{incoming["K"]:.6f} | {historical["K"]:.6f} | {run["run_id"]} |')
summary = {'commit': args.commit, 'fetched_at': snapshot['fetched_at'], 'aggregate': rank['aggregate'],
           'rank': rank['rank'], 'leader': leader['aggregate'], 'watch': own['watch'], 'latest': runs,
           'unchanged_source_rerun': args.rerun, 'snapshot': args.snapshot}
with (ROOT / f'validation/{args.name}-official-summary.json').open('x') as stream:
    json.dump(summary, stream, indent=2); stream.write('\n')
path = ROOT / 'research/CONTINUATION8_RUST.md'
path.write_text(path.read_text() + f'\n\n## Official result at {args.commit[:7]}\n\n'
    f'All five gates pass on every track at {args.commit}. Captured {snapshot["fetched_at"]}: '
    f'aggregate {rank["aggregate"]:.6f}, rank {rank["rank"]}, leader {leader["aggregate"]:.6f}. '
    f'Unchanged-source rerun: {args.rerun}.\n\n'
    '| Track | T s | M bytes | S | K | Incoming exact-head K | Historical best K | Run |\n'
    '|---|---:|---:|---:|---:|---:|---:|---|\n' + '\n'.join(rows) +
    '\n\nB/C sources are unchanged. A/D historical records are not improved by the first Rust run; '
    'first place remains outstanding. Public practice is separate from final holdouts and judging.\n')
path = ROOT / 'research/rust8-selection.json'; selection = json.loads(path.read_text())
selection.setdefault('official_runs', []).append({'commit': args.commit, 'summary': f'validation/{args.name}-official-summary.json',
    'unchanged_source_rerun': args.rerun})
selection['history'].append({'at': datetime.now(timezone.utc).isoformat(), 'status': f'All official gates passed at {args.commit}; measurement recorded'})
path.write_text(json.dumps(selection, indent=2) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k not in ['watch', 'latest']}, indent=2))
