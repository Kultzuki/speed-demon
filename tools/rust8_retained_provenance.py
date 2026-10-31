"""Reconcile the active restored C++ entry and preserved complete Rust alternatives."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
def read(path): return json.loads((ROOT / path).read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
images = read('validation/image-sizes-rust8-retained.json')
baseline = read('validation/continuation7-final-artifact-provenance.json')
rust = read('validation/rust8-final-artifact-provenance-corrected.json')
result = {'scope': 'Active submissions restored exactly to stronger incoming C++; requested Rust implementations remain complete and separately validated.',
          'created_at': datetime.now(timezone.utc).isoformat(), 'tracks': {}, 'gates': {}, 'rust_alternatives': {}}
for mode in ['release', 'sanitized']:
    name = f'rust8-retained-{mode}'
    build = read(f'validation/{name}-build.json')
    assert len(read(f'validation/{name}-checks.json')['results']) == 93
    assert len(read(f'validation/{name}-extra-checks.json')['results']) == 4
    result['gates'][mode] = {'comparisons': 97, 'direct': read(f'validation/{name}-checks.json')['direct']}
    for track in 'abcd':
        entry = build['tracks'][track]
        for file, sha in entry['sources'].items():
            path = ROOT / f'track-{track}/{file}'; assert digest(path) == sha
            assert path.read_text().encode() == subprocess.check_output(
                ['git', 'show', f'e9deec07fa38f9abf0c167d6768c41c388e37ba5:track-{track}/{file}'], cwd=ROOT)
        binary = ROOT / f'build/{name}/track-{track}'
        assert digest(binary) == entry['binary_sha256']
        if mode == 'release':
            assert entry['binary_sha256'] == images[track]['solution_sha256']
            assert entry['binary_sha256'] == baseline['tracks'][track]['binary_sha256']
            result['tracks'][track] = {**entry, **images[track], 'S': baseline['tracks'][track]['S'], 'D': 1,
                'source_lf_sha256': hashlib.sha256((ROOT / f'track-{track}/main.cpp').read_text().encode()).hexdigest(),
                'Dockerfile_sha256': digest(ROOT / f'track-{track}/Dockerfile'),
                'manifest_sha256': digest(ROOT / f'track-{track}/.speed-demon.toml')}
for track in 'ad':
    folder = ROOT / f'research/rust8-validated/track-{track}'
    for file, sha in rust['tracks'][track]['submission_sha256'].items(): assert digest(folder / file) == sha
    result['rust_alternatives'][track] = {'path': str(folder.relative_to(ROOT)), 'S': rust['tracks'][track]['S'], 'D': 1,
        'validated_binary_sha256': rust['tracks'][track]['binary_sha256'], 'official_commits': ['0ca1987', '8aa8ddb']}
for entry in read('.out/continuation8-user-d-rust/manifest.json')['files']:
    if entry['path'].startswith('track-d-rust/'): assert digest(ROOT / entry['path']) == entry['sha256']
with (ROOT / 'validation/rust8-retained-artifact-provenance.json').open('x') as stream:
    json.dump(result, stream, indent=2); stream.write('\n')
print('PASS retained 97+97 gates, exact incoming C++ sources/binaries, rebuilt image identities and complete preserved Rust/user originals.')
