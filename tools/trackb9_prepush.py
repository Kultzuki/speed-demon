"""Record exact image provenance and the user-requested best-A restoration."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
best = '6b71e02218f87a492f41aad0b6ea304c0e6cb172'
trial = 'a7136fd8da9cf8ecebba731b664fdd279bbc734a'
source = ROOT / 'track-b/main.cpp'
release = json.loads((ROOT / 'validation/trackb9-production-release.json').read_text())
sanitized = json.loads((ROOT / 'validation/trackb9-production-sanitized.json').read_text())
image = json.loads((ROOT / 'validation/image-sizes-trackb9-production.json').read_text())['b']
assert release['binary_sha256'] == image['solution_sha256']
assert release['source_sha256'] == sanitized['source_sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
saved = ROOT / '.out/trackb9-incoming/track-a-trial-a7136fd'
saved.mkdir(exist_ok=True)
a = {}
for name in ['main.cpp', 'common.hpp', 'Dockerfile', '.speed-demon.toml']:
    path = ROOT / 'track-a' / name
    expected = subprocess.check_output(['git', 'show', f'{best}:track-a/{name}'], cwd=ROOT)
    assert path.read_text() == expected.decode(), f'A does not match best: {name}'
    old = subprocess.check_output(['git', 'show', f'{trial}:track-a/{name}'], cwd=ROOT)
    (saved / name).write_bytes(old)
    a[name] = {'best_git_blob_sha256': hashlib.sha256(expected).hexdigest(),
               'restored_worktree_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
selection = json.loads((ROOT / 'research/trackb9-selection.json').read_text())
selection['user_steering'] = 'Push validated small gains; restore Track A to its best officially measured source.'
selection['track_a_restoration'] = {'best_commit': best, 'best_K': 33.741694,
    'rejected_trial_commit': trial, 'rejected_trial_K': 32.046061,
    'note': 'The shared checkout already staged the exact best source. Preserve the trial in history and the ignored archive.', 'files': a}
selection['official_status'] = 'All local B release, sanitizer, direct and offline image gates pass; ready for ordinary push.'
(ROOT / 'research/trackb9-selection.json').write_text(json.dumps(selection, indent=2) + '\n')
provenance = {'source_sha256': release['source_sha256'], 'common_sha256': release['common_sha256'],
    'release': release['binary_sha256'], 'sanitized': sanitized['binary_sha256'],
    'image': image, 'track_a_restoration': selection['track_a_restoration']}
(ROOT / 'validation/trackb9-prepush-provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
print('PASS exact B image/release provenance; A matches official best, trial preserved.')
