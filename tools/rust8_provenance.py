"""Verify source, validated executable and rebuilt image identities."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.competition/official/harness'))
import static_axes

def read(path): return json.loads((ROOT / path).read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

selection = read('research/rust8-selection.json')
images = read('validation/image-sizes-rust8-final.json')
static = read('validation/rust8-final-static.json')
old = read('validation/continuation7-final-artifact-provenance.json')
result = {'scope': 'Frozen Rust A/D and byte-identical validated C++ B/C; no unvalidated trial binary.',
          'compiler': read('validation/rust8-final-release-build.json')['compiler'], 'tracks': {}, 'gates': {}}
for mode in ['release', 'asan', 'checked']:
    name = f'rust8-final-{mode}'
    checks = read(f'validation/{name}-checks.json')
    extras = read(f'validation/{name}-extra-checks.json')
    assert len(checks['results']) == 93 and len(extras['results']) == 4
    assert set(checks['direct']) == {'a-rust8-tests', 'd-rust8-tests'}
    result['gates'][mode] = {'comparisons': 97, 'direct': checks['direct']}
    build = read(f'validation/{name}-build.json')
    for track in 'abcd':
        entry = build['tracks'][track]
        binary = ROOT / f'build/{name}/track-{track}'
        assert digest(binary) == entry['binary_sha256']
        if track in 'ad':
            assert entry['sources'] == selection['selected'][track]['sources']
            for file, sha in entry['sources'].items(): assert digest(ROOT / f'track-{track}/{file}') == sha
        else:
            normalized = (ROOT / f'track-{track}/main.cpp').read_text().encode()
            assert hashlib.sha256(normalized).hexdigest() == old['tracks'][track]['source_lf_sha256']
            assert digest(ROOT / f'track-{track}/common.hpp') == old['tracks'][track]['common_sha256']
        if mode == 'release':
            assert entry['binary_sha256'] == images[track]['solution_sha256'], (track, entry, images[track])
            files = ['main.rs', 'common.rs', 'Cargo.toml', 'Cargo.lock'] if track in 'ad' else ['main.cpp', 'common.hpp']
            files += ['Dockerfile', '.speed-demon.toml']
            result['tracks'][track] = {**entry, **images[track],
                'submission_sha256': {f: digest(ROOT / f'track-{track}/{f}') for f in files},
                'S': static[track]['S'] if track in 'ad' else old['tracks'][track]['S'], 'D': 1}
for track in 'ad':
    assert static[track]['S'] == selection['selected'][track]['S']
    assert static_axes.dependency_axis(str(ROOT / f'track-{track}'))['D'] == 1
    reference = 'a_ingest.py' if track == 'a' else 'd_traverse.py'
    assert reference in static_axes.published_copies(str(ROOT / f'track-{track}'))
    assert not (ROOT / f'track-{track}/main.cpp').exists()
for entry in read('.out/continuation8-user-d-rust/manifest.json')['files']:
    if entry['path'].startswith('track-d-rust/'):
        assert digest(ROOT / entry['path']) == entry['sha256']
with (ROOT / 'validation/rust8-final-artifact-provenance.json').open('x') as stream:
    json.dump(result, stream, indent=2); stream.write('\n')
print('PASS all source/mode/binary/image identities, published-reference exemptions, zero dependencies and original user D preservation.')
