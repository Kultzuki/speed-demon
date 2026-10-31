from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[1]
with (ROOT / 'validation/rust8-cargo-check.txt').open('x') as log:
    for track in 'ad':
        subprocess.run(['docker', 'exec', 'codescythe-rust8', 'cargo', 'check', '--offline', '--frozen',
            '--manifest-path', f'/work/track-{track}/Cargo.toml', '--target-dir', f'/work/build/rust8-cargo-check/{track}'],
            check=True, stdout=log, stderr=subprocess.STDOUT)
print('PASS A/D Cargo manifests and locks build offline.')
