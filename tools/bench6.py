"""Continuation-6 local benchmark harness.

Fresh cgroups, process fork/exec/exit timer, read-only data, 8g/no swap,
12 pinned CPUs. Local evidence only; never an official board score.
"""
import argparse
import hashlib
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build' / 'bench6'
BASE = 'debian:13-slim@sha256:62bd423aeee912639ca8ee681c2b762cb3e25137e0a92b20be455898a9f034ad'
VOLUME = 'codescythe-bench-continuation5'
OUTPUT = {'a': 'summary.txt', 'b': 'results.txt', 'c': 'aggregates.txt', 'd': 'distances.txt'}
DATA = {'a': '/data/a', 'b': '/data/b', 'c': '/data/c', 'd': '/data/d'}
COMMON = ['-std=c++20', '-O3', '-DNDEBUG', '-pthread', '-static', '-s']


def call(args, **kw):
    return subprocess.run(args, check=True, **kw)


def build(track, source, name, extra):
    BUILD.mkdir(parents=True, exist_ok=True)
    cmd = ['docker', 'exec', 'codescythe-research', 'g++'] + COMMON + extra + [
        '-I', f'/work/track-{track}', f'/work/{source}', '-o', f'/work/build/bench6/{name}']
    call(cmd)
    digest = hashlib.sha256((BUILD / name).read_bytes()).hexdigest()
    print(f'BUILT {name} {digest}', flush=True)
    return digest


def run(track, name, data, keep_output=False):
    out = ROOT / '.out' / 'bench6'
    out.mkdir(parents=True, exist_ok=True)
    cmd = ['docker', 'run', '--rm', '--network=none', '--read-only', '--memory=8g', '--memory-swap=8g',
           '--cpuset-cpus=0-11', '--cpuset-mems=0', '--pids-limit=512', '--cap-drop=ALL',
           '--security-opt=no-new-privileges', '--user=65534:65534',
           '--tmpfs', '/tmp:rw,size=1g,exec', '--tmpfs', '/out:rw,size=64m',
           '--mount', f'type=volume,src={VOLUME},dst=/data,readonly',
           '--mount', f'type=bind,src={BUILD},dst=/candidates,readonly',
           '-e', f'OUTPUT_FILE=/out/{OUTPUT[track]}', '--entrypoint', '/candidates/monitor6', BASE,
           f'/candidates/{name}', '--data', data, '--out', '/out']
    r = call(cmd, capture_output=True, text=True)
    lines = r.stdout.strip().splitlines()
    metric = json.loads(next(x[7:] for x in lines if x.startswith('METRIC ')))
    digest = next(x.split()[0] for x in lines if x.endswith('/out/' + OUTPUT[track]))
    metric['sha256'] = digest
    metric['stderr'] = r.stderr[-4000:]
    return metric


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=['build', 'run', 'compare'])
    ap.add_argument('--track', required=True, choices='abcd')
    ap.add_argument('--source', default='')
    ap.add_argument('--name', default='')
    ap.add_argument('--names', default='')
    ap.add_argument('--extra', default='')
    ap.add_argument('--runs', type=int, default=3)
    ap.add_argument('--warmup', type=int, default=1)
    ap.add_argument('--data', default='')
    ap.add_argument('--expected', default='')
    ap.add_argument('--json', default='')
    args = ap.parse_args()
    if args.action == 'build':
        build(args.track, args.source, args.name, args.extra.split())
        return
    if args.action == 'run':
        m = run(args.track, args.name, args.data or DATA[args.track])
        print(json.dumps(m, indent=1))
        return
    names = [n for n in args.names.split(',') if n]
    data = args.data or DATA[args.track]
    for _ in range(args.warmup):
        run(args.track, names[0], data)
    entries = {n: [] for n in names}
    for i in range(args.runs):
        order = names if i % 2 == 0 else list(reversed(names))
        for n in order:
            m = run(args.track, n, data)
            entries[n].append(m)
            print(f'{args.track} {n} T={m["T_s"]:.6f} CPU={m.get("CPU_s", 0):.6f} M={m["M_bytes"]} sha={m["sha256"][:12]}', flush=True)
    report = {'track': args.track, 'data': data, 'runs': args.runs, 'entries': {}}
    for n, ms in entries.items():
        t = statistics.median(x['T_s'] for x in ms)
        mem = statistics.median(x['M_bytes'] for x in ms)
        cpu = statistics.median(x.get('CPU_s', 0) for x in ms)
        tmin = min(x['T_s'] for x in ms)
        cpumin = min(x.get('CPU_s', 0) for x in ms)
        report['entries'][n] = {'T_s': t, 'M_bytes': mem, 'CPU_s': cpu, 'T_min': tmin, 'CPU_min': cpumin,
                                'sha256': sorted({x['sha256'] for x in ms}), 'raw': ms}
        print(f'MEDIAN {args.track} {n} T={t:.6f} Tmin={tmin:.6f} CPU={cpu:.6f} CPUmin={cpumin:.6f} M={mem}', flush=True)
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2) + '\n')
        print('WROTE', args.json)


if __name__ == '__main__':
    main()
