"""Rebuild std and test with TSan; never suppress the compiler ABI check."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
image = 'codescythe/rust8-tools:local'
commands = [
    ['docker', 'run', '-d', '--name', 'codescythe-rust8-tsan', '--memory=5g', '--memory-swap=5g',
     '--cpuset-cpus=0-11', '--mount', f'type=bind,src={ROOT},dst=/work', '-w', '/work', image, 'sleep', 'infinity'],
    ['docker', 'exec', 'codescythe-rust8-tsan', 'rustup', 'component', 'add', 'rust-src'],
    ['docker', 'exec', '-e', 'RUSTC_BOOTSTRAP=1', '-e', 'SPEED_DEMON_ROOT=/work',
     '-e', 'RUSTFLAGS=-Zsanitizer=thread -C target-cpu=x86-64-v3',
     '-e', 'RUST_MIN_STACK=8388608', 'codescythe-rust8-tsan', 'cargo', 'test',
     '--target', 'x86_64-unknown-linux-gnu', '-Zbuild-std=std,test',
     '--manifest-path', '/work/research/tsan8/Cargo.toml', '--target-dir', '/work/build/rust8-tsan-target',
     '--test', 'publication', 'exact_publication', '--', '--exact', '--nocapture'],
]
result = {'initial_attempt': 'rustc -Zsanitizer=thread with prebuilt std refused due sanitizer ABI mismatch.',
          'approach': 'Rebuild std/test with the same TSan flag; no unsafe ABI override.', 'commands': commands}
with (ROOT / 'validation/rust8-tsan.txt').open('x') as log:
    for command in commands:
        proc = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        log.flush()
        if proc.returncode:
            result.update(ok=False, failed_command=command, exit_code=proc.returncode)
            break
    else: result['ok'] = True
with (ROOT / 'validation/rust8-tsan.json').open('x') as stream:
    json.dump(result, stream, indent=2); stream.write('\n')
print('TSAN', result['ok'], flush=True)
raise SystemExit(0 if result['ok'] else 1)
