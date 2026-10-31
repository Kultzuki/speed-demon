"""Continuation 7: isolated binaries, alternating runs and complete local K."""
import argparse
import hashlib
import json
import os
import shutil
import statistics
from pathlib import Path
import subprocess
import tempfile

import bench6

ROOT = Path(__file__).resolve().parents[1]
bench6.BUILD = ROOT / 'build/bench7'


def source_size(track, source, dockerfile=None):
    if os.name == 'nt':
        code = "import sys;sys.path.insert(0,'/work/tools');from bench7 import source_size;print(source_size(sys.argv[1],sys.argv[2],sys.argv[3] or None))"
        return int(subprocess.check_output(['docker', 'exec', 'codescythe-research',
            'python3', '-c', code, track, source, dockerfile or ''], text=True))
    tools = ROOT / 'build/static-tools'
    with tempfile.TemporaryDirectory() as folder:
        dest = Path(folder)
        for name, path in [('main.cpp', ROOT / source), ('common.hpp', ROOT / f'track-{track}/common.hpp')]:
            formatted = subprocess.check_output([str(tools / 'clang-format'), '--style=LLVM',
                                                  f'--assume-filename={name}'], input=path.read_bytes())
            (dest / name).write_bytes(formatted)
        (dest / 'Dockerfile').write_bytes((ROOT / (dockerfile or f'track-{track}/Dockerfile')).read_bytes())
        flags = ['--no-config', '--no-gitignore', '--no-ignore', '--no-scc-ignore', '--no-gitmodule',
                 '--no-cocomo', '--no-size', '--no-complexity', '--by-file', '--format', 'json']
        counts = json.loads(subprocess.check_output([str(tools / 'scc'), *flags, folder]))
        return sum(item['Code'] for item in counts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', required=True, choices='abcd')
    ap.add_argument('--candidates', required=True, nargs='+', help='label=repo-relative-source.cpp')
    ap.add_argument('--name', required=True)
    ap.add_argument('--runs', type=int, default=5)
    ap.add_argument('--extra', default='')
    ap.add_argument('--data', default='')
    ap.add_argument('--reuse', action='store_true')
    ap.add_argument('--pgo', action='append', default=[], help='Label of a pgo7.py-trained binary')
    ap.add_argument('--pgo-dockerfile', default='')
    args = ap.parse_args()
    report_path = ROOT / f'research/results/{args.name}.json'
    if report_path.exists():
        raise FileExistsError(report_path)
    bench6.BUILD.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / 'build/bench6/monitor6', bench6.BUILD / 'monitor6')
    candidates = dict(item.split('=', 1) for item in args.candidates)
    flags = (['-march=x86-64-v3'] if args.track == 'b' else []) + args.extra.split()
    report = {'scope': 'Local WSL2; hot Linux-local data, fresh cgroups, read-only root/data, '
              '8g/no swap, CPUs 0-11, fork/exec/exit timer. Not an official score.',
              'track': args.track, 'data': args.data or f'/data/{args.track}', 'entries': {}}
    for label, source in candidates.items():
        binary = bench6.BUILD / label
        if not args.reuse or not binary.exists():
            subprocess.run(['docker', 'exec', 'codescythe-research', 'g++',
                *bench6.COMMON, *flags, '-I', f'/work/track-{args.track}',
                f'/work/{source}', '-o', f'/work/build/bench7/{label}'], check=True)
            print('BUILT', label, flush=True)
        report['entries'][label] = {'source': source, 'flags': bench6.COMMON + flags,
            'source_sha256': hashlib.sha256((ROOT / source).read_bytes()).hexdigest(),
            'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
            'S': source_size(args.track, source, args.pgo_dockerfile if label in args.pgo else None), 'D': 1, 'raw': []}
        if label in args.pgo:
            training_path = ROOT / f'validation/pgo7-{args.track}-training.json'
            training = json.loads(training_path.read_text())
            result = report['entries'][label]
            assert result['source_sha256'] == training['source_sha256']
            assert result['binary_sha256'] == training['binary_sha256']
            result['flags'] += [f'-fprofile-use=/work/build/pgo7/{args.track}/profiles', '-fprofile-correction']
            result['training_provenance'] = training_path.relative_to(ROOT).as_posix()
    manifest = json.loads((ROOT / '.competition/SHA256SUMS.json').read_text(encoding='utf-8-sig'))
    expected = manifest['tracks'][args.track]['expected_output_sha256'][0]
    if args.data:
        previous = json.loads((ROOT / 'validation/fresh-full-seed20261031.json').read_text())
        expected = next(r['sha256'] for r in previous['results'] if r['track'] == args.track)
    names = list(candidates)
    bench6.run(args.track, names[0], report['data'])
    for i in range(args.runs):
        for label in names if i % 2 == 0 else reversed(names):
            metric = bench6.run(args.track, label, report['data'])
            if metric['sha256'] != expected:
                raise AssertionError((label, expected, metric))
            report['entries'][label]['raw'].append(metric)
            print(label, json.dumps(metric), flush=True)
    baseline = report['entries'][names[0]]
    for result in report['entries'].values():
        for key in ['T_s', 'M_bytes', 'CPU_s']:
            result[key] = statistics.median(r.get(key, 0) for r in result['raw'])
    for label, result in report['entries'].items():
        result['local_K_ratio'] = ((baseline['T_s'] / result['T_s']) ** .5
            * (baseline['M_bytes'] / result['M_bytes']) ** .2
            * (baseline['S'] / result['S']) ** .15)
        print('SUMMARY', label, {k: result[k] for k in ['T_s', 'M_bytes', 'CPU_s', 'S', 'D', 'local_K_ratio']}, flush=True)
    report_path.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
