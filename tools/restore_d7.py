"""Reject the officially losing D build while retaining successful A/B/C."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
trial = json.loads((ROOT / 'research/continuation7-selection.json').read_text())
official = json.loads((ROOT / 'validation/continuation7-official-summary.json').read_text())
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == official['commit']
assert official['latest']['d']['K'] < 15.399979
current = ROOT / 'track-d/main.cpp'
assert hashlib.sha256(current.read_bytes()).hexdigest() == trial['selected']['d']['selected_sha256']
source = ROOT / 'research/prototypes/continuation7-base-d.cpp'
published = subprocess.check_output(['git', 'show', trial['checkpoint'] + ':track-d/main.cpp']).decode()
assert source.read_text() == published
assert hashlib.sha256(source.read_bytes()).hexdigest() == trial['selected']['d']['incoming_sha256']
current.write_bytes(source.read_bytes())
readme = subprocess.check_output(['git', 'show', trial['checkpoint'] + ':track-d/README.md'])
(ROOT / 'track-d/README.md').write_bytes(readme)
final = {'checkpoint': official['commit'], 'selected': dict(trial['selected']),
         'status': 'D restored after official coefficient regression; final mixed gates/images pending'}
final['selected']['d'] = {'source': 'research/prototypes/continuation7-base-d.cpp',
    'selected_sha256': hashlib.sha256(current.read_bytes()).hexdigest(), 'S': 385, 'D': 1}
(ROOT / 'research/continuation7-final-selection.json').write_text(json.dumps(final, indent=2) + '\n')
text = ('''\n\nD's owner-sharded candidate is rejected after the official run: K=14.710088,
versus the historical 15.399979 and unchanged incoming rerun 15.015017. Its
0.366347 s does not reproduce the 14-17% local coefficient gain; the incoming
kernel's latest official time was 0.368451 s at similar memory, while source
size rose from 385 to 450. The exact incoming full-uint64 kernel is restored.
A/B/C retain their officially improved implementations. Final mixed-source
gates, rebuilt D image and another exact-commit official run follow.
''')
for rel in ['research/CONTINUATION7.md', 'track-d/PERF.md']:
    path = ROOT / rel
    path.write_text(path.read_text() + text)
print('RESTORED exact incoming D source; retained officially improved A/B/C; no reset or force push.')
