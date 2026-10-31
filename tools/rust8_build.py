"""Build isolated Rust A/D and retain the validated unchanged C++ B/C binaries."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FLAGS = ['--edition=2021', '-C', 'opt-level=3', '-C', 'lto=fat', '-C', 'codegen-units=1',
         '-C', 'panic=abort', '-C', 'strip=symbols', '-C', 'target-feature=+crt-static',
         '-C', 'target-cpu=x86-64-v3']

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['release', 'asan', 'checked'], default='release')
    ap.add_argument('--name', default='rust8')
    ap.add_argument('--tests', action='store_true')
    args = ap.parse_args()
    folder = ROOT / f'build/{args.name}-{args.mode}'
    folder.mkdir(exist_ok=False)
    report = {'mode': args.mode, 'tracks': {}, 'compiler': subprocess.check_output(
        ['docker', 'exec', 'codescythe-rust8', 'rustc', '-vV'], text=True)}
    flags = FLAGS if args.mode == 'release' else ['--edition=2021', '-C', 'opt-level=1', '-C', 'debuginfo=2',
        '-C', 'debug-assertions=yes', '-C', 'overflow-checks=yes', '-C', 'force-frame-pointers=yes',
        '-C', 'target-cpu=x86-64-v3']
    if args.mode == 'asan':
        flags += ['-Z', 'sanitizer=address']
    for track in 'ad':
        command = ['docker', 'exec', '-e', 'RUSTC_BOOTSTRAP=1', '-w', f'/work/track-{track}',
            'codescythe-rust8', 'rustc', *flags, 'main.rs', '-o', f'/work/build/{folder.name}/track-{track}']
        subprocess.run(command, check=True)
        report['tracks'][track] = {'flags': flags, 'binary_sha256': digest(folder / f'track-{track}'),
            'sources': {f: digest(ROOT / f'track-{track}/{f}') for f in ['main.rs', 'common.rs']}}
        if args.tests:
            testflags = ['--test', '--edition=2021', '-C', 'opt-level=2', '-C', 'debuginfo=2',
                '-C', 'debug-assertions=yes', '-C', 'overflow-checks=yes', '-C', 'force-frame-pointers=yes',
                '-C', 'target-cpu=x86-64-v3']
            if args.mode == 'asan': testflags += ['-Z', 'sanitizer=address']
            test = f'/work/research/tests/{track}-rust8.rs'
            binary = folder / f'{track}-rust8-tests'
            subprocess.run(['docker', 'exec', '-e', 'RUSTC_BOOTSTRAP=1', '-e', 'SPEED_DEMON_ROOT=/work',
                'codescythe-rust8', 'rustc', *testflags, test,
                '-o', f'/work/build/{folder.name}/{binary.name}'], check=True)
            report['tracks'][track]['direct_test'] = {'binary_sha256': digest(binary), 'flags': testflags,
                'source_sha256': digest(ROOT / f'research/tests/{track}-rust8.rs')}
    mode = 'release' if args.mode == 'release' else 'sanitized'
    for track in 'bc':
        src = ROOT / f'build/continuation7-final-{mode}/track-{track}'
        shutil.copy2(src, folder / src.name)
        report['tracks'][track] = {'binary_sha256': digest(src), 'origin': str(src.relative_to(ROOT))}
    path = ROOT / f'validation/{folder.name}-build.json'
    with path.open('x') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    print('Built', folder.name, flush=True)

if __name__ == '__main__':
    main()
