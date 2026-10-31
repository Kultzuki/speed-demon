"""Prove Git's LF-normalized Rust sources produce the validated executable."""
import hashlib
import json
from pathlib import Path
import subprocess
from rust8_build import FLAGS

ROOT = Path(__file__).resolve().parents[1]
report = {}
for track in 'ad':
    folder = ROOT / f'build/rust8-lf-{track}'
    folder.mkdir(exist_ok=False)
    sources = {}
    for file in ['main.rs', 'common.rs']:
        path = ROOT / f'track-{track}/{file}'
        raw = path.read_bytes(); normalized = path.read_text().encode()
        (folder / file).write_bytes(normalized)
        sources[file] = {'raw_sha256': hashlib.sha256(raw).hexdigest(),
                         'lf_sha256': hashlib.sha256(normalized).hexdigest()}
    target = folder / 'solution'
    subprocess.run(['docker', 'exec', '-w', '/work/' + folder.relative_to(ROOT).as_posix(),
        'codescythe-rust8', 'rustc', *FLAGS, 'main.rs', '-o', '/work/' + target.relative_to(ROOT).as_posix()], check=True)
    actual = hashlib.sha256(target.read_bytes()).hexdigest()
    expected = hashlib.sha256((ROOT / f'build/rust8-final-release/track-{track}').read_bytes()).hexdigest()
    assert actual == expected, (track, actual, expected)
    report[track] = {'sources': sources, 'lf_binary_sha256': actual, 'validated_binary_sha256': expected}
with (ROOT / 'validation/rust8-lf-artifact-provenance.json').open('x') as stream:
    json.dump(report, stream, indent=2); stream.write('\n')
print('PASS LF-normalized A/D executables exactly match validated release and offline images.')
