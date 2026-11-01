from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
snapshot = json.loads((ROOT / 'validation/leaderboard-trackb9-scatter-check.json').read_text())
run = snapshot['codescythe']['tracks']['b']['best']
assert run['commit'] == '3f527c9d90b2124b78d22d982a8024cf757cb847' and all(run['gates'].values())
assert run['K'] > 21.242087
summary = {k: run[k] for k in ['run_id', 'commit', 'T_s', 'M_bytes', 'S', 'D', 'K', 'points', 'gates']}
summary.update({'previous_best_K': 21.242087, 'decision': 'retain', 'goal_80_points': 'outstanding'})
(ROOT / 'validation/trackb9-scatter-official-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
selection_path = ROOT / 'research/trackb9-selection.json'
selection = json.loads(selection_path.read_text())
selection['official_status'] = 'Retained after all five official gates and improved K.'
selection['official_record'] = summary
selection_path.write_text(json.dumps(selection, indent=2) + '\n')
entry = '''

## Official balanced-scatter result: 3f527c9

Run `run-50fc0d07810d`: all five official gates pass. T=0.243353 s,
M=65,507,328 bytes, S=960, D=1, K=21.581336, **66.703917 points**.
The previous best was K=21.242087 / 66.359859 points: retain the small gain.
The 80-point target remains outstanding. Exact record:
`validation/trackb9-scatter-official-summary.json`.

A remains the exact restored best source (historical 76.408344 points); its
new repeat records 76.044238 points. C's independent a822664 source is unchanged
by this B commit; its higher 70.367154 record is rerun variation, not a B gain.
'''
for file in ['track-b/PERF.md', 'research/CONTINUATION9_TRACK_B.md']:
    path = ROOT / file
    if '## Official balanced-scatter result: 3f527c9' not in path.read_text():
        with path.open('a') as stream: stream.write(entry)
print('Recorded retained official B score 66.703917; target 80 remains outstanding.')
