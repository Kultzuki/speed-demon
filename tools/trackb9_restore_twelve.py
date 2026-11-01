"""Record the rejected six-core hypothesis and restore the retained B runtime."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
snapshot = json.loads((ROOT / 'validation/leaderboard-trackb9-six-check1.json').read_text())
track = snapshot['codescythe']['tracks']['b']
trial = track['latest']
assert trial['commit'] == 'f8b4589c1d2e0fbd84add980ecd0f6f63115a913' and all(trial['gates'].values())
assert trial['K'] < track['best']['K']
summary = {'decision': 'restore exact twelve-builder source', 'trial': trial, 'retained_best': track['best'],
    'note': 'The best source is byte-identical to 3f527c9; the later score is unchanged-source rerun variation.'}
(ROOT / 'validation/trackb9-sixbuilders-official-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
source = subprocess.check_output(['git', 'show', '3f527c9:track-b/main.cpp'], cwd=ROOT)
assert hashlib.sha256(source).hexdigest() == '8041f7d8a1dc5e8ce8d05b242347637c6833dffc563166494bb344a0e15d67ce'
(ROOT / 'track-b/main.cpp').write_bytes(source)
(ROOT / 'track-b/README.md').write_bytes(subprocess.check_output(['git', 'show', '3f527c9:track-b/README.md'], cwd=ROOT))
selection_path = ROOT / 'research/trackb9-selection.json'
selection = json.loads(selection_path.read_text())
selection.update({'phase': 'trackb9-restored-twelve', 'selected_prototype': 'research/prototypes/trackb9-retained-3f527c9.cpp',
    'selected_sha256': hashlib.sha256(source).hexdigest(), 'official_record': track['best'],
    'official_status': 'Retain exact twelve-builder kernel; six builders regressed official K and are restored.'})
selection_path.write_text(json.dumps(selection, indent=2) + '\n')
entry = '''

## Reject six builders and restore the measured twelve-builder kernel

At f8b4589, run run-d0fec9934adb passes every official gate but records
T=0.283163 s, M=62,459,904 bytes, S=962, D=1, K=20.192057 / 65.259028 points.
Six physical cores did not make six index builders faster. Restore the exact
3f527c9 runtime source and Dockerfile; keep the trial and all receipts in Git.
The latest unchanged-source twelve-builder best at 9ae6c5d is K=21.659658 /
66.782580 points, T=0.242057 s, M=65,196,032 bytes, S=960. This increment over
66.703917 is rerun variation. A's unchanged restored source similarly records
a new best of 76.418537 points at 9ae6c5d.

The conservative phrase-prefix filter passed both full hashes. It gained local
K on public data (1.118287) but lost slightly on the fresh seed (0.994885), so
it is unselected. Word comparisons plus that filter also lack a repeatable
second-seed gain. These reports are comparative local evidence, not board scores.
'''
for name in ['track-b/PERF.md', 'research/CONTINUATION9_TRACK_B.md']:
    with (ROOT / name).open('a') as stream: stream.write(entry)
print('Restored exact retained B source; six-builder regression recorded.')
