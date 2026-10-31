"""Check the actual staged LF sources and unchanged B/C kernels before committing."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
lf = json.loads((ROOT / 'validation/rust8-lf-artifact-provenance.json').read_text())
result = {}
for track in 'ad':
    result[track] = {}
    for file in ['main.rs', 'common.rs']:
        path = f'track-{track}/{file}'
        data = subprocess.check_output(['git', 'show', ':' + path], cwd=ROOT)
        sha = hashlib.sha256(data).hexdigest()
        assert sha == lf[track]['sources'][file]['lf_sha256'], path
        result[track][file] = sha
subprocess.run(['git', 'diff', '--cached', '--exit-code', '--',
    'track-b/main.cpp', 'track-b/common.hpp', 'track-b/Dockerfile',
    'track-c/main.cpp', 'track-c/common.hpp', 'track-c/Dockerfile'], cwd=ROOT, check=True)
subprocess.run(['git', 'diff', '--cached', '--check', '--', 'track-a', 'track-d', 'tools'], cwd=ROOT, check=True)
with (ROOT / 'validation/rust8-staged-source-provenance.json').open('x') as stream:
    json.dump(result, stream, indent=2); stream.write('\n')
print('PASS actual staged Rust LF sources match validated executables; B/C kernels unchanged. Raw evidence logs retained verbatim.')
