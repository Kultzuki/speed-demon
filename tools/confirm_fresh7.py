"""Compare finalists on a second independently referenced full seed, serially."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
jobs = [
    ('a', 'a-pgo-fresh7', [
        'base-a7=research/prototypes/continuation7-base-a.cpp',
        'incoming-a7=research/prototypes/continuation7-incoming-a.cpp',
        'pgo-a7=research/prototypes/continuation7-incoming-a.cpp'],
     ['--pgo', 'pgo-a7', '--pgo-dockerfile', 'research/prototypes/continuation7-pgo-a.Dockerfile']),
    ('b', 'b-block16-fresh7', [
        'base-b7=research/prototypes/continuation7-base-b.cpp',
        'block16-b7=research/prototypes/continuation7-block16-b.cpp'], []),
    ('c', 'c-ring-fresh7', [
        'base-c7=research/prototypes/continuation7-base-c.cpp',
        'incoming-c7=research/prototypes/continuation7-incoming-c.cpp',
        'incoming-exit-c7=research/prototypes/continuation7-incoming-exit-c.cpp'], []),
    ('d', 'd-compact-fresh7', [
        'base-d7=research/prototypes/continuation7-base-d.cpp',
        'compact-shards-d7=research/prototypes/continuation7-compact-shards-d.cpp'], []),
]
with (ROOT / 'validation/continuation7-fresh-bench.txt').open('x') as log:
    for track, name, candidates, extra in jobs:
        print('START', name, flush=True)
        subprocess.run([sys.executable, str(ROOT / 'tools/bench7.py'), '--track', track, '--name', name,
            '--runs', '4', '--reuse', '--data', f'/data/fresh7/{track}', *extra,
            '--candidates', *candidates], stdout=log, stderr=subprocess.STDOUT, check=True)
        log.flush()
        report = json.loads((ROOT / f'research/results/{name}.json').read_text())
        for label, result in report['entries'].items():
            print(name, label, {k: result[k] for k in ['T_s', 'M_bytes', 'CPU_s', 'S', 'local_K_ratio']}, flush=True)
