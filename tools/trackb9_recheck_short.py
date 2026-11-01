"""Record a rejected prototype's contract-boundary failure independently."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
expected = next(x['sha256'] for x in json.loads((ROOT / 'validation/trackb9-production-release.json').read_text())['results']
                if x['case'] == 'trackb9-keys-windows')
out = ROOT / '.out/trackb9-short-recheck'
out.mkdir(exist_ok=True)
subprocess.run(['docker', 'exec', 'codescythe-research', '/work/build/bench7/b9-short',
    '--data', '/work/data/b/trackb9-keys-windows', '--out', '/work/.out/trackb9-short-recheck'], check=True)
actual = hashlib.sha256((out / 'results.txt').read_bytes()).hexdigest()
result = {'scope': 'Rejected short-key research prototype, never submitted.',
    'source': 'research/prototypes/trackb9-short.cpp',
    'source_sha256': hashlib.sha256((ROOT / 'research/prototypes/trackb9-short.cpp').read_bytes()).hexdigest(),
    'binary_sha256': hashlib.sha256((ROOT / 'build/bench7/b9-short').read_bytes()).hexdigest(),
    'case': 'trackb9-keys-windows', 'expected': expected, 'actual': actual, 'matches': actual == expected,
    'inspection': 'The unclamped BZHI count len*8 becomes 256 for a valid 32-byte token. This prototype is not eligible.'}
assert actual != expected
(ROOT / 'validation/trackb9-rejected-short-boundary.json').write_text(json.dumps(result, indent=2) + '\n')
print('Confirmed rejected short-key prototype fails 32-byte boundary fixture; production SIMD keys remain validated.')
