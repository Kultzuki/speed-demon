"""Canonical rustfmt 1.10.0 and organizer scc 4.1.0; no submission mutation."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.competition/official/harness'))
import static_axes

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True)
    args = ap.parse_args()
    stage = ROOT / f'build/{args.name}-static'
    stage.mkdir(exist_ok=False)
    results = {}
    for track in 'adu':
        dest = stage / track
        dest.mkdir()
        if track == 'u':
            shutil.copy2(ROOT / 'research/prototypes/d-user-cli8.rs', dest / 'main.rs')
            shutil.copy2(ROOT / 'track-d-rust/track-d/Dockerfile', dest / 'Dockerfile')
            shutil.copy2(ROOT / 'track-d-rust/track-d/Cargo.toml', dest / 'Cargo.toml')
        else:
            for file in ['main.rs', 'common.rs']:
                shutil.copy2(ROOT / f'track-{track}/{file}', dest / file)
            shutil.copy2(ROOT / 'research/prototypes/rust8.Dockerfile', dest / 'Dockerfile')
            (dest / 'Cargo.toml').write_text('[package]\nname = "solution"\nversion = "0.1.0"\nedition = "2021"\n\n[[bin]]\nname = "solution"\npath = "main.rs"\n\n[dependencies]\n')
        (dest / '.speed-demon.toml').write_text(f'track = "{"d" if track == "u" else track}"\nteam = "CodeScythe"\nlanguage = "Rust"\ndependency_count = 0\n')
        original = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.iterdir()}
        (dest / 'neutral.toml').write_text('# canonical rustfmt defaults\n')
        subprocess.run(['docker', 'run', '--rm', '--network=none', '--mount',
            f'type=bind,src={dest},dst=/src', '-w', '/src', '--entrypoint', 'rustfmt',
            'codescythe/rust8-tools:local', '--edition', '2021', '--config-path', '/src/neutral.toml', 'main.rs'], check=True)
        linux = '/work/' + dest.relative_to(ROOT).as_posix()
        counts = json.loads(subprocess.check_output(['docker', 'exec', 'codescythe-research',
            '/work/build/static-tools/scc', '--no-config', '--no-gitignore', '--no-ignore', '--no-scc-ignore',
            '--no-gitmodule', '--no-cocomo', '--no-size', '--no-complexity', '--by-file', '--format', 'json', linux], text=True))
        result = {'S': sum(c['Code'] for c in counts if c['Name'] not in static_axes.NOT_CODE), 'D': static_axes.dependency_axis(str(dest))['D'],
                  'original_sha256': original, 'canonical_counts': counts,
                  'formatters': {'rustfmt': '1.10.0-stable (58cf8f9c35 2026-10-13)', 'scc': '4.1.0'},
                  'note': 'Stage has exactly candidate Rust/common/Dockerfile and zero-dependency manifests. '
                          'The preserved organizer Python reference is exempt and old C++ is outside the candidate.'}
        assert result['D'] == 1
        results[track] = result
        print(track, 'S=', result['S'], 'D=', result['D'], flush=True)
    with (ROOT / f'validation/{args.name}-static.json').open('x') as stream:
        json.dump(results, stream, indent=2); stream.write('\n')

if __name__ == '__main__': main()
