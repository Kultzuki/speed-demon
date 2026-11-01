"""Compare immutable, hash-verified B binaries, including an offline PGO image."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics

import bench6
import bench7

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument('--name', required=True)
ap.add_argument('--candidates', nargs='+', default=['scatter', 'pgo', 'buffers'])
ap.add_argument('--runs', type=int, default=5)
ap.add_argument('--data', choices=['public', 'fresh'], default='public')
args = ap.parse_args()
output = ROOT / f'research/results/{args.name}.json'
if output.exists(): raise FileExistsError(output)
bench6.BUILD = ROOT / 'build/bench7'
plain = json.loads((ROOT / 'validation/trackb9-scatter-release.json').read_text())
frozen = ROOT / 'research/prototypes/trackb9-retained-3f527c9.cpp'
if not frozen.exists(): frozen.write_bytes((ROOT / 'track-b/main.cpp').read_bytes())
assert hashlib.sha256(frozen.read_bytes()).hexdigest() == plain['source_sha256']
shutil.copy2(ROOT / 'build/trackb9-scatter-release/track-b', bench6.BUILD / 'b9-scatter')
training = json.loads((ROOT / 'validation/trackb9-pgo-full-training.json').read_text())
entries = {
    'scatter': {'binary': 'b9-scatter', 'source': frozen.relative_to(ROOT).as_posix(), 'flags': plain['flags'],
                'expected_binary': plain['binary_sha256']},
    'pgo': {'binary': 'trackb9-pgo-full', 'source': 'build/trackb9-pgo-full/main.cpp',
            'flags': training['flags'].split() + ['-fprofile-use=/tmp/profile', '-fprofile-correction', '-Werror=missing-profile'],
            'dockerfile': 'research/prototypes/trackb9-pgo-full.Dockerfile',
            'expected_binary': training['binary_sha256'], 'training': training},
    'buffers': {'binary': 'b9-qbuffers', 'source': 'research/prototypes/trackb9-query-buffers.cpp',
                'flags': bench6.COMMON + ['-march=x86-64-v3']},
    'profile': {'binary': 'b9-qprofile', 'source': 'research/prototypes/trackb9-query-profile.cpp',
                'flags': bench6.COMMON + ['-march=x86-64-v3'], 'diagnostic_only': True},
}
manifest = json.loads((ROOT / '.competition/SHA256SUMS.json').read_text())['tracks']['b']
if args.data == 'fresh':
    data = '/data/fresh7/b'
    expected = next(x['sha256'] for x in json.loads((ROOT / 'validation/fresh-full-seed20261031.json').read_text())['results'] if x['track'] == 'b')
else:
    data = '/data/b'; expected = manifest['expected_output_sha256'][0]
report = {'scope': 'Local WSL2, immutable prebuilt binaries; fresh pinned offline/read-only/no-network cgroups; not official scores.',
          'data': data, 'entries': {}}
for label in args.candidates:
    entry = dict(entries[label])
    source = ROOT / entry['source']
    binary = bench6.BUILD / entry['binary']
    entry['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    entry['common_sha256'] = hashlib.sha256((ROOT / 'track-b/common.hpp').read_bytes()).hexdigest()
    entry['binary_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
    assert entry['common_sha256'] == plain['common_sha256']
    if 'expected_binary' in entry: assert entry['binary_sha256'] == entry['expected_binary']
    if label == 'pgo': assert entry['source_sha256'] == training['source_sha256']
    entry.update({'S': bench7.source_size('b', entry['source'], entry.get('dockerfile')), 'D': 1, 'raw': []})
    report['entries'][label] = entry
bench6.run('b', report['entries'][args.candidates[0]]['binary'], data)
for run in range(args.runs):
    for label in args.candidates if run % 2 == 0 else list(reversed(args.candidates)):
        entry = report['entries'][label]
        metric = bench6.run('b', entry['binary'], data)
        assert metric['sha256'] == expected, (label, metric)
        entry['raw'].append(metric)
        print(label, json.dumps(metric), flush=True)
for entry in report['entries'].values():
    for key in ['T_s', 'M_bytes', 'CPU_s']:
        entry[key] = statistics.median(x[key] for x in entry['raw'])
baseline = report['entries'][args.candidates[0]]
for label, entry in report['entries'].items():
    entry['local_K_ratio'] = (baseline['T_s']/entry['T_s'])**.5 * (baseline['M_bytes']/entry['M_bytes'])**.2 * (baseline['S']/entry['S'])**.15
    print('SUMMARY', label, {k: entry[k] for k in ['T_s', 'M_bytes', 'CPU_s', 'S', 'local_K_ratio']}, flush=True)
output.write_text(json.dumps(report, indent=2) + '\n')
