"""Fresh independent parser boundary and degenerate-graph reference checks."""
import argparse
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
def digest(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()

ap = argparse.ArgumentParser(); ap.add_argument('--name', required=True); args = ap.parse_args()
cases = []
data = ROOT / 'data/a/rust8-buffer-boundaries'
if not data.exists():
    data.mkdir()
    base = datetime(2026, 10, 30, 18)
    methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']
    values = [0, 9, 10, 99, 100, 9999, 9999999, 100000000, 1000000000, 4294967295]
    with (data / 'requests.log').open('w') as stream:
        for i in range(100000):
            hour = (i * 19) % 72
            stamp = (base + timedelta(hours=hour)).strftime('%Y-%m-%dT%H:00:00.000000Z')
            endpoint = '/' + 'x' * ((i * 67) % 125)
            stream.write(f'{stamp} {methods[i % 7]} {endpoint} {[100,499,500,599][i % 4]} {values[i % 10]}\n')
cases.append(('a', data))
for label, graph, queries in [
    ('rust8-one-node', '1 3\n0 0 0\n0 0 4294967295\n0 0 1\n', '0 0\n' * 125),
    ('rust8-empty-graph', '17 0\n', ''.join(f'{s} {t}\n' for s in range(17) for t in range(17))),
    ('rust8-empty-queries', '2 1\n0 1 4294967295\n', '')]:
    data = ROOT / f'data/d/{label}'
    if not data.exists():
        data.mkdir(); (data / 'graph.txt').write_text(graph); (data / 'queries.txt').write_text(queries)
    cases.append(('d', data))
results = []
for track, data in cases:
    target = ROOT / f'.out/{args.name}-extra/{track}/{data.name}'
    target.mkdir(parents=True, exist_ok=False)
    reference = target / 'reference'; reference.mkdir()
    module, output = ('a_ingest', 'summary.txt') if track == 'a' else ('d_traverse', 'distances.txt')
    subprocess.run([sys.executable, ROOT / f'.competition/official/reference/{module}.py', '--data', data, '--out', reference], check=True)
    subprocess.run([ROOT / f'build/{args.name}/track-{track}', '--data', data, '--out', target], check=True)
    actual = digest(target / output); assert actual == digest(reference / output)
    results.append({'track': track, 'case': data.name, 'sha256': actual,
        'inputs_sha256': {p.name: digest(p) for p in data.iterdir()}})
    print('PASS new', track, data.name, flush=True)
with (ROOT / f'validation/{args.name}-extra-checks.json').open('x') as stream:
    json.dump({'results': results}, stream, indent=2); stream.write('\n')
