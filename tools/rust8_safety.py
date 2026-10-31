"""Fail-closed ASan/checked builds and full differential gates; new evidence only."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
with (ROOT / 'validation/rust8-final-safety-gates.txt').open('x') as log:
    for mode in ['asan', 'checked']:
        name = f'rust8-final-{mode}'
        commands = [
            [sys.executable, ROOT / 'tools/rust8_build.py', '--name', 'rust8-final', '--mode', mode, '--tests'],
            ['docker', 'exec', '-e', 'RUST_MIN_STACK=8388608', 'codescythe-research',
             'python3', '/work/tools/rust8_checks.py', '--name', name, '--direct'],
            ['docker', 'exec', 'codescythe-research', 'python3', '/work/tools/rust8_extra.py', '--name', name],
        ]
        print('START', name, flush=True)
        for command in commands:
            subprocess.run([str(x) for x in command], check=True, stdout=log, stderr=subprocess.STDOUT)
            log.flush()
        count = len(json.loads((ROOT / f'validation/{name}-checks.json').read_text())['results'])
        extra = len(json.loads((ROOT / f'validation/{name}-extra-checks.json').read_text())['results'])
        assert count == 93 and extra == 4
        print('PASS', name, count + extra, 'comparisons plus direct checks', flush=True)
