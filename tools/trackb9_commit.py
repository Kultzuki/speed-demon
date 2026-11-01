"""Commit only authorized B work and the exact best-A restoration."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
selection = json.loads((ROOT / 'research/trackb9-selection.json').read_text())
assert hashlib.sha256((ROOT / 'track-b/main.cpp').read_bytes()).hexdigest() == selection['selected_sha256']
for name in ['main.cpp', 'common.hpp', 'Dockerfile', '.speed-demon.toml']:
    expected = subprocess.check_output(['git', 'show', f'6b71e02:track-a/{name}'], cwd=ROOT).decode()
    assert (ROOT / 'track-a' / name).read_text() == expected
paths = [ROOT / p for p in ['track-a/main.cpp', 'track-a/common.hpp',
    'track-b/main.cpp', 'track-b/README.md', 'track-b/PERF.md',
    'research/CONTINUATION9_TRACK_B.md', 'research/trackb9-selection.json',
    'research/tests/b-token-window9.cpp']]
for folder, pattern in [('research/prototypes', 'trackb9-*.cpp'),
    ('research/results', 'trackb9-*.json'), ('tools', 'trackb9_*.py'),
    ('validation', 'trackb9-*'), ('validation', '*trackb9*')]:
    paths.extend(p for p in (ROOT / folder).glob(pattern) if p.is_file())
relative = sorted({p.relative_to(ROOT).as_posix() for p in paths})
subprocess.run(['git', 'diff', '--check', '--', *relative], cwd=ROOT, check=True)
subprocess.run(['git', 'add', '--', *relative], cwd=ROOT, check=True)
subprocess.run(['git', 'commit', '--only', '-m',
    'Optimize exact Track B scanning and posting gaps; restore best A', '--', *relative], cwd=ROOT, check=True)
sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
changed = subprocess.check_output(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', sha], cwd=ROOT, text=True).splitlines()
assert all(p in relative for p in changed), changed
assert subprocess.check_output(['git', 'show', f'{sha}:track-b/main.cpp'], cwd=ROOT) == (ROOT / 'track-b/main.cpp').read_bytes()
print('COMMIT', sha, 'FILES', len(changed), flush=True)
