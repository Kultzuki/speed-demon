"""Validate the exact staged Track B source and retain complete gate logs."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument('--name', default='trackb9-production')
ap.add_argument('--doc-bits', type=int, choices=[15, 16], default=15)
args = ap.parse_args()
source = ROOT / 'track-b/main.cpp'
selection = json.loads((ROOT / 'research/trackb9-selection.json').read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest() == selection['selected_sha256']
log_path = ROOT / f'validation/{args.name}-gates.log'
units = {}
with log_path.open('x') as log:
    for mode in ['release', 'sanitized']:
        print('START Track B production', mode, flush=True)
        extra = ['--sanitized'] if mode == 'sanitized' else []
        subprocess.run([sys.executable, ROOT / 'tools/trackb9_gate.py', '--name', args.name, *extra],
            check=True, stdout=log, stderr=subprocess.STDOUT)
        log.flush()
        out = ROOT / f'build/{args.name}-{mode}/b-token-window9'
        flags = ['-std=c++20', '-pthread', '-march=x86-64-v3', '-Wno-subobject-linkage', '-Wno-return-type', f'-DPACKED_DOC_BITS={args.doc_bits}']
        flags += ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer'] if mode == 'sanitized' else ['-O2', '-DNDEBUG']
        subprocess.run(['g++', *flags, f'-DCANDIDATE_SOURCE="{source}"', '-I', str(ROOT / 'track-b'),
            str(ROOT / 'research/tests/b-token-window9.cpp'), '-o', str(out)], check=True,
            stdout=log, stderr=subprocess.STDOUT)
        result = subprocess.run([str(out)], check=True, capture_output=True, text=True)
        log.write(result.stdout + result.stderr); log.flush()
        units[mode] = {'flags': flags, 'binary_sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
            'test_source_sha256': hashlib.sha256((ROOT / 'research/tests/b-token-window9.cpp').read_bytes()).hexdigest(),
            'stdout': result.stdout, 'stderr': result.stderr}
        comparisons = len(json.loads((ROOT / f'validation/{args.name}-{mode}.json').read_text())['results'])
        print('PASS Track B production', mode, comparisons, 'datasets, full seeds, forced wide offsets, 4096 direct alignments, CRC collisions and posting escapes', flush=True)
assert hashlib.sha256(source.read_bytes()).hexdigest() == selection['selected_sha256']
(ROOT / f'validation/{args.name}-direct.json').write_text(json.dumps(units, indent=2) + '\n')
print('PASS exact frozen Track B production gates', flush=True)
