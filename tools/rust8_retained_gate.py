"""Replay both complete gates against exact restored C++ executables."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
with (ROOT / 'validation/rust8-retained-gates.txt').open('x') as log:
    for mode in ['release', 'sanitized']:
        name = f'rust8-retained-{mode}'; dest = ROOT / f'build/{name}'
        dest.mkdir(exist_ok=False)
        source = ROOT / f'build/continuation7-final-{mode}'
        old = json.loads((ROOT / f'validation/continuation7-final-{mode}-build.json').read_text())
        build = {'mode': mode, 'scope': 'Exact restored established C++ sources; same validated executables as continuation 7.', 'tracks': {}}
        for track in 'abcd':
            binary = source / f'track-{track}'
            assert digest(binary) == old[track]['binary_sha256']
            shutil.copy2(binary, dest / binary.name)
            build['tracks'][track] = {**old[track], 'language': 'C++',
                'sources': {f: digest(ROOT / f'track-{track}/{f}') for f in ['main.cpp', 'common.hpp']}}
        units = [('a-publication-guard', []), ('c-boundaries', []), ('c-concurrent-names', []),
                 ('d-sparse-state', ['/work/data/d/worked-example/graph.txt']),
                 ('d-csr-contents7', ['/work/data/d/continuation7-parallel-wide-2/graph.txt']),
                 ('d-csr-contents7', ['/work/data/d/continuation7-parallel-wide-65537/graph.txt'])]
        for file, _ in units:
            if not (dest / file).exists(): shutil.copy2(source / file, dest / file)
        build['direct_binaries'] = [{'binary': file, 'args': args} for file, args in units]
        with (ROOT / f'validation/{name}-build.json').open('x') as stream:
            json.dump(build, stream, indent=2); stream.write('\n')
        for script, extra in [('rust8_checks.py', ['--direct']), ('rust8_extra.py', [])]:
            subprocess.run(['docker', 'exec', 'codescythe-research', 'python3', f'/work/tools/{script}', '--name', name, *extra],
                           check=True, stdout=log, stderr=subprocess.STDOUT)
            log.flush()
        count = sum(len(json.loads((ROOT / f'validation/{name}{suffix}.json').read_text())['results'])
                    for suffix in ['-checks', '-extra-checks'])
        assert count == 97
        print('PASS restored', mode, count, 'comparisons plus complete direct gates', flush=True)
