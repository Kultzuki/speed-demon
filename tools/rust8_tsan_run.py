"""Run rebuilt-std TSan with process-local ASLR control; official sandbox stays separate."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
base = ROOT / 'build/rust8-tsan-target'
binary, = [p for p in (base / 'x86_64-unknown-linux-gnu/debug/deps').glob('publication-*') if not p.suffix]
command = ['docker', 'run', '--rm', '--network=none', '--read-only', '--memory=5g', '--memory-swap=5g',
    '--cpuset-cpus=0-11', '--cap-drop=ALL', '--security-opt=no-new-privileges',
    '--security-opt=seccomp=unconfined', '--tmpfs', '/tmp:rw,size=1g,exec',
    '--mount', f'type=bind,src={base},dst=/check,readonly', '-e', 'RUST_MIN_STACK=8388608',
    '--entrypoint', '/check/' + binary.relative_to(base).as_posix(), 'codescythe/rust8-tools:local',
    'exact_publication', '--exact', '--nocapture']
with (ROOT / 'validation/rust8-tsan-publication.txt').open('x') as log:
    proc = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
result = {'ok': proc.returncode == 0, 'exit_code': proc.returncode, 'command': command,
    'scope': 'Additional TSan race check only. Instrumented std/test. Per-process ASLR control permitted '
             'with seccomp unconfined; no global sysctl or official runtime sandbox change.'}
with (ROOT / 'validation/rust8-tsan-publication.json').open('x') as stream:
    json.dump(result, stream, indent=2); stream.write('\n')
print('TSAN publication', result['ok'], flush=True)
raise SystemExit(proc.returncode)
