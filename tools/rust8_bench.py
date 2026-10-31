"""Alternating complete-process measurements; fresh cgroup on every run."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics

import bench6

ROOT = Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', choices='ad', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--build', default='rust8-initial-release')
    ap.add_argument('--static', default='rust8-initial')
    ap.add_argument('--fresh', action='store_true')
    ap.add_argument('--user', action='store_true')
    ap.add_argument('--runs', type=int, default=5)
    ap.add_argument('--candidate', action='append', default=[], help='label=relative-binary:S')
    args = ap.parse_args()
    bench6.BUILD = ROOT / 'build/rust8-bench'
    bench6.BUILD.mkdir(exist_ok=True)
    shutil.copy2(ROOT / 'build/bench6/monitor6', bench6.BUILD / 'monitor6')
    static = json.loads((ROOT / f'validation/{args.static}-static.json').read_text())
    track = args.track
    binaries = {f'{track}-cpp8': (ROOT / f'build/continuation7-final-release/track-{track}', 310 if track == 'a' else 385),
                f'{track}-{args.build}': (ROOT / f'build/{args.build}/track-{track}', static[track]['S'])}
    if args.user:
        binaries['d-user-cli8'] = (ROOT / 'build/rust8-trial/d-user-cli8', static['u']['S'])
    for extra in args.candidate:
        label, spec = extra.split('=', 1)
        binary, size = spec.rsplit(':', 1)
        binaries[label] = (ROOT / binary, int(size))
    data = f'/data/fresh7/{track}' if args.fresh else f'/data/{track}'
    if args.fresh:
        previous = json.loads((ROOT / 'validation/fresh-full-seed20261031.json').read_text())
        expected = next(r['sha256'] for r in previous['results'] if r['track'] == track)
    else:
        expected = json.loads((ROOT / '.competition/SHA256SUMS.json').read_text(encoding='utf-8-sig'))['tracks'][track]['expected_output_sha256'][0]
    report = {'scope': 'Local WSL2. exec-to-exit, fresh cgroups, pinned 12 CPUs, 8g/no swap, read-only root/data, '
                        'network none. Complete K ratio includes measured cgroup memory, canonical S and D=1. Not official.',
              'track': track, 'data': data, 'entries': {}}
    for label, (binary, s) in binaries.items():
        target = bench6.BUILD / label
        shutil.copy2(binary, target)
        report['entries'][label] = {'binary_sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'S': s, 'D': 1, 'raw': []}
    names = list(binaries)
    bench6.run(track, names[0], data)
    for i in range(args.runs):
        for label in names if i % 2 == 0 else reversed(names):
            metric = bench6.run(track, label, data)
            assert metric['sha256'] == expected, (label, metric)
            report['entries'][label]['raw'].append(metric)
            print(label, json.dumps(metric), flush=True)
    for result in report['entries'].values():
        for key in ['T_s', 'M_bytes', 'CPU_s']:
            result[key] = statistics.median(r.get(key, 0) for r in result['raw'])
    base = report['entries'][names[0]]
    for label, result in report['entries'].items():
        result['local_K_ratio'] = ((base['T_s'] / result['T_s']) ** .5 *
                                   (base['M_bytes'] / result['M_bytes']) ** .2 * (base['S'] / result['S']) ** .15)
        print('SUMMARY', label, {k: result[k] for k in ['T_s', 'M_bytes', 'S', 'local_K_ratio']}, flush=True)
    with (ROOT / f'research/results/{args.name}.json').open('x') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')

if __name__ == '__main__': main()
