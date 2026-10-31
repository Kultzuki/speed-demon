"""Run both complete gates and the new construction/identity regressions."""
import hashlib
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--name', default='continuation7')
parser.add_argument('--selection', default='research/continuation7-selection.json')
args = parser.parse_args()
selection = json.loads((ROOT / args.selection).read_text())


def verify_sources():
    for track, entry in selection['selected'].items():
        actual = hashlib.sha256((ROOT / f'track-{track}/main.cpp').read_bytes()).hexdigest()
        assert actual == entry['selected_sha256'], track


with (ROOT / f'validation/{args.name}-gates.txt').open('x') as log:
    for mode in ['release', 'sanitized']:
        name = f'{args.name}-{mode}'
        print('START', name, flush=True)
        verify_sources()
        extra = ['--sanitized'] if mode == 'sanitized' else []
        commands = [
            [sys.executable, ROOT / 'tools/refinement_checks.py', '--name', name, '--packed-a', *extra],
            [sys.executable, ROOT / 'tools/continuation5_extra.py', '--name', name],
        ]
        flags = ['-std=c++20', '-pthread']
        flags += (['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer']
                  if mode == 'sanitized' else ['-O3', '-DNDEBUG', '-static', '-s'])
        commands += [
            ['g++', *flags, f'-DCANDIDATE_SOURCE="{ROOT / "track-d/main.cpp"}"',
             '-I', ROOT / 'track-d', ROOT / 'research/tests/d-csr-contents7.cpp',
             '-o', ROOT / f'build/{name}/d-csr-contents7'],
            [sys.executable, ROOT / 'tools/continuation7_extra.py', '--name', name],
        ]
        for command in commands:
            subprocess.run([str(x) for x in command], check=True, stdout=log, stderr=subprocess.STDOUT)
            log.flush()
        counts = {suffix: len(json.loads((ROOT / f'validation/{name}{suffix}.json').read_text())['results'])
                  for suffix in ['', '-full', '-extra', '-additional', '-new']}
        assert counts == {'': 69, '-full': 4, '-extra': 12, '-additional': 4, '-new': 4}, counts
        print('PASS', name, sum(counts.values()), 'dataset comparisons plus direct checks', flush=True)
    verify_sources()
print('PASS frozen finalists, 93 release and 93 sanitized comparisons, direct checks and full seeds.', flush=True)
