"""Isolated worker-count candidates; preserve the exact sources and compiler flags."""
from pathlib import Path
import subprocess
from rust8_build import FLAGS

ROOT = Path(__file__).resolve().parents[1]
for workers in [6, 8]:
    folder = ROOT / f'research/prototypes/rust8-a{workers}'
    folder.mkdir(exist_ok=False)
    (folder / 'common.rs').write_bytes((ROOT / 'track-a/common.rs').read_bytes())
    (folder / 'main.rs').write_text((ROOT / 'track-a/main.rs').read_text().replace('workers(12)', f'workers({workers})'))
    subprocess.run(['docker', 'exec', '-w', '/work/' + folder.relative_to(ROOT).as_posix(),
        'codescythe-rust8', 'rustc', *FLAGS, 'main.rs', '-o', f'/work/build/rust8-trial/a{workers}'], check=True)
