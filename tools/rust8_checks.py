"""Replay all 93 independent reference comparisons into new, isolated outputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = {'a': 'summary.txt', 'b': 'results.txt', 'c': 'aggregates.txt', 'd': 'distances.txt'}

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True)
    ap.add_argument('--tracks', default='abcd')
    ap.add_argument('--direct', action='store_true')
    args = ap.parse_args()
    binary_dir = ROOT / f'build/{args.name}'
    build = json.loads((ROOT / f'validation/{args.name}-build.json').read_text())
    for track in 'ad':
        for file, sha in build['tracks'][track]['sources'].items():
            assert digest(ROOT / f'track-{track}/{file}') == sha
    reports = [ROOT / f'validation/continuation7-final-release{s}.json'
               for s in ['', '-full', '-extra', '-additional', '-new']]
    fixtures = [(file.name, entry) for file in reports for entry in json.loads(file.read_text())['results']]
    assert len(fixtures) == 93
    results = []
    for origin, entry in fixtures:
        track, case = entry['track'], entry['case']
        if track not in args.tracks: continue
        data = (Path(f'/benchfresh/seed20261031/{track}') if case == 'fresh-full-seed20261031'
                else Path(f'/benchdata/{track}') if case == 'full-seed1' else ROOT / f'data/{track}/{case}')
        assert data.is_dir(), data
        target = ROOT / f'.out/{args.name}/{track}/{case}'
        target.mkdir(parents=True, exist_ok=False)
        start = time.monotonic()
        proc = subprocess.run([str(binary_dir / f'track-{track}'), '--data', str(data), '--out', str(target)],
                              check=True, capture_output=True, timeout=180)
        assert not proc.stdout, (track, case, proc.stdout)
        assert sorted(p.name for p in target.iterdir()) == [OUTPUT[track]]
        actual = digest(target / OUTPUT[track])
        assert actual == entry['sha256'], (track, case, actual, entry['sha256'])
        results.append({'track': track, 'case': case, 'sha256': actual, 'reference_report': origin,
                        'local_seconds': time.monotonic() - start,
                        'inputs_sha256': {p.name: digest(p) for p in sorted(data.iterdir()) if p.is_file()}})
        print('PASS', track, case, flush=True)
    direct = []
    if args.direct:
        for track in 'ad':
            path = binary_dir / f'{track}-rust8-tests'
            subprocess.run([str(path), '--test-threads=1', '--nocapture'], check=True)
            direct.append(path.name)
    result = {'scope': 'Local differential/reference hashes including both full seeds; no official timing claims.',
              'build': build, 'results': results, 'direct': direct}
    with (ROOT / f'validation/{args.name}-checks.json').open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print('PASS', args.name, len(results), 'comparisons', direct, flush=True)

if __name__ == '__main__':
    main()
