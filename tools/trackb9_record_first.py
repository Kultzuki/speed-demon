from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
snapshot = json.loads((ROOT / 'validation/leaderboard-trackb9-c641273-official.json').read_text())
team = snapshot['codescythe']
record = {
    'submitted_commit': 'c6412734cf45da31b5b841fdc5f6b8071d7f9327',
    'run_id': 'run-66176fc80d33', 'T_s': .262099, 'M_bytes': 62586880,
    'S': 944, 'D': 1, 'K': 21.038763, 'points': 66.151010,
    'starting_best_K': 19.373796, 'decision': 'retain',
    'gates': {'check': True, 'build': True, 'correctness': True, 'timeout': True, 'sandbox': True},
    'latest_same_source_b': team['tracks']['b']['best'],
    'note': 'A/C/D official repeats vary. A remains exact best source; C was independently changed by another chat.'}
same_commit = record['latest_same_source_b']['commit']
diff = subprocess.check_output(['git', 'diff', '--name-only', record['submitted_commit'], same_commit,
    '--', 'track-b/main.cpp', 'track-b/common.hpp', 'track-b/Dockerfile'], cwd=ROOT, text=True)
assert not diff
(ROOT / 'validation/trackb9-first-official-summary.json').write_text(json.dumps(record, indent=2) + '\n')
text = '''

## Official first Track B gain: c641273

Run `run-66176fc80d33` at `c6412734cf45da31b5b841fdc5f6b8071d7f9327`:
all five gates pass; T=0.262099 s, M=62,586,880 bytes, S=944, D=1,
K=21.038763, **66.151010 points**. Starting best K=19.373796 / 64.360736
points: retain the improvement.

The same commit restores A exactly to the 6b71e02 best source. Its new run is
K=31.030844 / 74.589680 points, below that source's historical 76.408344 best;
the byte-identical source is restored, and timing/memory variation is recorded
without claiming a new A algorithm gain.

A subsequent independent C commit, a822664, leaves B runtime files unchanged
and records B K=21.242087 / 66.359859 points (run `run-bcdf6cd41a3c`). That is
unchanged-source rerun variation. Snapshot and source comparison:
`validation/leaderboard-trackb9-c641273-official.json` and
`validation/trackb9-first-official-summary.json`. The 80-point B target remains.
'''
for file in ['track-b/PERF.md', 'research/CONTINUATION9_TRACK_B.md']:
    p = ROOT / file
    if '## Official first Track B gain: c641273' not in p.read_text():
        with p.open('a') as stream: stream.write(text)
print('Recorded retained official B improvement and separate unchanged-source rerun.')
