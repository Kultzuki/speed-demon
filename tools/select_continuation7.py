"""Select only the documented finalists, after checking the archived input state."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
ARCHIVE = ROOT / '.out/continuation7-incoming'
selected = {'a': 'continuation7-incoming-a.cpp', 'b': 'continuation7-block16-b.cpp',
            'c': 'continuation7-incoming-exit-c.cpp', 'd': 'continuation7-compact-shards-d.cpp'}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


manifest = json.loads((ARCHIVE / 'manifest.json').read_text())
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == manifest['head']
for track in 'ac':
    current = ROOT / f'track-{track}/main.cpp'
    saved = ARCHIVE / 'files' / f'track-{track}/main.cpp'
    assert current.read_bytes() == saved.read_bytes(), track
for track in 'bd':
    submitted = subprocess.check_output(['git', 'show', f'HEAD:track-{track}/main.cpp'], cwd=ROOT).decode()
    assert (ROOT / f'track-{track}/main.cpp').read_text() == submitted, track
target = ROOT / 'research/HANDOVER_INCOMING_CONTINUATION7.md'
assert not target.exists()
shutil.copy2(ARCHIVE / 'files/HANDOVER_NEXT.md', target)
records = {}
for track, name in selected.items():
    source = PROTO / name
    target = ROOT / f'track-{track}/main.cpp'
    previous = target.read_bytes()
    target.write_bytes(source.read_bytes())
    records[track] = {'source': source.relative_to(ROOT).as_posix(),
        'incoming_sha256': digest(previous), 'selected_sha256': digest(target.read_bytes()),
        'S': {'a': 310, 'b': 922, 'c': 401, 'd': 450}[track], 'D': 1}
result = {'checkpoint': manifest['head'], 'archive': str(ARCHIVE), 'selected': records,
          'status': 'local selection only; full gates, rebuilt images and official K pending',
          'rejected': ['A parallel prefault and reserve', 'C split membership',
                       'D inline/spill graph', 'D packed radix entries',
                       'generator-only A/C PGO: no established gain over simpler finalists'],
          'unselected': ['B exclusive interior bitmap words and SIMD keys',
                         'D twelve-worker construction', 'generic early exit in A/B/D']}
(ROOT / 'research/continuation7-selection.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
