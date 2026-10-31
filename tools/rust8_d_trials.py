"""Compare only exact full-u64 label layouts and query worker counts."""
from pathlib import Path
import subprocess
from rust8_build import FLAGS

ROOT = Path(__file__).resolve().parents[1]
for label, old, workers in [('d-simple8', True, 12), ('d-six8', False, 6)]:
    folder = ROOT / f'research/prototypes/{label}'
    folder.mkdir(exist_ok=False)
    text = (ROOT / ('research/prototypes/rust8-compact/d/main.rs' if old else 'track-d/main.rs')).read_text()
    if old:
        text = text.replace('    checked_close(file)\n}', '    checked_close(file)?;\n    unsafe extern "C" { fn _exit(code: i32) -> !; }\n    unsafe { _exit(0) }\n}')
    text = text.replace('workers(12)', f'workers({workers})')
    (folder / 'main.rs').write_text(text)
    (folder / 'common.rs').write_bytes((ROOT / 'track-d/common.rs').read_bytes())
    subprocess.run(['docker', 'exec', '-w', '/work/' + folder.relative_to(ROOT).as_posix(),
        'codescythe-rust8', 'rustc', *FLAGS, 'main.rs', '-o', f'/work/build/rust8-trial/{label}'], check=True)
