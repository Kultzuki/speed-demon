"""Preserve source baselines and prepare an isolated comparison of the user's D."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
dest = ROOT / 'research/baseline8'
dest.mkdir(exist_ok=False)
records = {}
for track in 'ad':
    for file in ['main.cpp', 'common.hpp', 'Dockerfile', '.speed-demon.toml']:
        path = ROOT / f'track-{track}' / file
        target = dest / f'track-{track}' / file
        target.parent.mkdir(exist_ok=True)
        shutil.copy2(path, target)
        records[f'track-{track}/{file}'] = hashlib.sha256(path.read_bytes()).hexdigest()
user = ROOT / 'track-d-rust/track-d/src/main.rs'
text = user.read_text()
text = text.replace('let data = args.get(1).map_or("/data", |s| s.as_str());',
                    'let data = args.windows(2).find(|a| a[0] == "--data").map_or("/data", |a| a[1].as_str());')
text = text.replace('let out = args.get(2).map_or("/out", |s| s.as_str());',
                    'let out = args.windows(2).find(|a| a[0] == "--out").map_or("/out", |a| a[1].as_str());')
with (ROOT / 'research/prototypes/d-user-cli8.rs').open('x') as stream:
    stream.write(text)
records['user_d_sha256'] = hashlib.sha256(user.read_bytes()).hexdigest()
with (ROOT / 'validation/rust8-incoming-sources.json').open('x') as stream:
    json.dump(records, stream, indent=2)
    stream.write('\n')
print('Preserved established A/D C++ and original user Rust D; CLI-only D trial prepared.')
