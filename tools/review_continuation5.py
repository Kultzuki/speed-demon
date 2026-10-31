"""Compile path-only adapters, then test the supplied sets in D/C/B/A order."""
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time

import validate

ROOT = validate.ROOT
EXTRAS = {
    'd': ['worked-example', *[f'fuzz{i}' for i in range(20)]],
    'c': ['worked-example', 'final-no-newline', 'parallel-hostile', 'name-table-growth', 'supplied-long-name', 'second-suffix-arena'],
    'b': ['worked-example', *[f'fuzz{i}' for i in range(10)], 'token-and-block-boundaries', 'supplied-phrase-1024', 'refined-block-65537', 'refined-block-70000'],
    'a': ['worked-example', 'empty', 'percentile-boundaries', 'parallel-boundaries', 'packed-sentinel', 'packed-overflow'],
}

def main():
    folder = ROOT / 'build/supplied-continuation5'
    folder.mkdir(parents=True, exist_ok=True)
    report = {'scope': 'Linux local; supplied originals with path adapters only, never official scores', 'builds': {}, 'checks': []}
    manifest = json.loads((ROOT / '.competition/SHA256SUMS.json').read_text())['tracks']
    fresh = json.loads((ROOT / 'validation/fresh-full-seed20261031.json').read_text())
    for batch in ['fifth', 'sixth']:
        for track in 'dcba':
            label = f'{batch}-{track}'
            ext = 'c' if (batch, track) == ('sixth', 'd') else 'cpp'
            source = ROOT / f'research/prototypes/supplied-{label}.{ext}'
            binary = folder / label
            flags = ['-std=gnu11' if ext == 'c' else '-std=c++20', '-O3', '-DNDEBUG', '-pthread', '-static', '-s', '-march=x86-64-v3', '-mpclmul']
            built = subprocess.run(['gcc' if ext == 'c' else 'g++', *flags, str(source), '-o', str(binary)], capture_output=True, text=True)
            report['builds'][label] = {'ok': built.returncode == 0, 'flags': flags, 'stderr': built.stderr,
                                       'source_sha256': validate.digest(source)}
            print('BUILD', label, built.returncode, built.stderr[:1000], flush=True)
            if built.returncode:
                continue
            cases = [('public-full', Path(f'/benchdata/{track}'), manifest[track]['expected_output_sha256'][0]),
                     ('fresh-full', Path(f'/benchfresh/seed20261031/{track}'), next(x['sha256'] for x in fresh['results'] if x['track'] == track))]
            for case in EXTRAS[track]:
                data = ROOT / f'data/{track}/{case}'
                if not data.is_dir():
                    continue
                reference = ROOT / f'.out/validation/{track}/{case}/reference'
                expected = reference / validate.OUTPUT[track]
                if not expected.is_file():
                    reference.mkdir(parents=True, exist_ok=True)
                    subprocess.run([sys.executable, str(validate.OFFICIAL / f'reference/{validate.MODULE[track]}.py'), '--data', str(data), '--out', str(reference)], check=True)
                cases.append((case, data, validate.digest(expected)))
            for case, data, expected in cases:
                target = ROOT / f'.out/supplied-continuation5/{label}/{case}'
                target.mkdir(parents=True, exist_ok=True)
                started = time.perf_counter()
                try:
                    run = subprocess.run([str(binary), '--data', str(data), '--out', str(target)], capture_output=True, text=True, timeout=20)
                    output = target / validate.OUTPUT[track]
                    actual = validate.digest(output) if output.is_file() else None
                    entry = {'label': label, 'case': case, 'ok': run.returncode == 0 and actual == expected,
                             'returncode': run.returncode, 'sha256': actual, 'expected_sha256': expected, 'stderr': run.stderr[:2000]}
                except subprocess.TimeoutExpired:
                    entry = {'label': label, 'case': case, 'ok': False, 'error': '20-second timeout'}
                entry['local_seconds'] = time.perf_counter() - started
                report['checks'].append(entry)
                print(label, case, 'PASS' if entry['ok'] else 'FAIL', f"{entry['local_seconds']:.6f}s", entry.get('returncode'), entry.get('stderr', '')[:200], flush=True)
                (ROOT / 'validation/supplied-continuation5-review.json').write_text(json.dumps(report, indent=2) + '\n')
    print('RESULT', sum(x['ok'] for x in report['checks']), '/', len(report['checks']), flush=True)

if __name__ == '__main__':
    main()
