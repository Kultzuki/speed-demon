"""Keep immutable benchmark source/binary pairs when the active source changes."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
first = json.loads((ROOT / 'validation/trackb9-production-release.json').read_text())
source = ROOT / '.out/trackb9-scatter/prior-main.cpp'
binary = ROOT / 'build/bench7/b9-active'
assert hashlib.sha256(source.read_bytes()).hexdigest() == first['source_sha256']
assert hashlib.sha256(binary.read_bytes()).hexdigest() == first['binary_sha256']
shutil.copy2(source, ROOT / 'research/prototypes/trackb9-retained-c641273.cpp')
shutil.copy2(binary, ROOT / 'build/bench7/b9-c641')
print('Frozen c641273 source/binary pair; do not reuse b9-active against a changed source.')
