"""Copy, never regenerate, the independently referenced full seed for benchmarking."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
HELPER = 'codescythe-fresh-continuation7'
VOLUME = 'codescythe-bench-continuation5'
BASE = 'debian:13-slim@sha256:62bd423aeee912639ca8ee681c2b762cb3e25137e0a92b20be455898a9f034ad'


def call(command, **kwargs):
    return subprocess.run(command, check=True, **kwargs)


call(['docker', 'run', '-d', '--name', HELPER, '--network=none',
      '--mount', f'type=volume,src={VOLUME},dst=/data', '--entrypoint', 'sleep', BASE, 'infinity'],
     stdout=subprocess.DEVNULL)
try:
    call(['docker', 'exec', HELPER, 'mkdir', '-p', '/data/fresh7'])
    read = subprocess.Popen(['docker', 'cp', 'codescythe-research:/benchfresh/seed20261031/.', '-'],
                            stdout=subprocess.PIPE)
    try:
        call(['docker', 'exec', '-i', HELPER, 'tar', '-xf', '-', '-C', '/data/fresh7'], stdin=read.stdout)
    finally:
        read.stdout.close()
    assert read.wait() == 0
    previous = json.loads((ROOT / 'validation/fresh-full-seed20261031.json').read_text())
    verified = {}
    for track, item in previous['provenance'].items():
        verified[track] = {}
        for name, expected in item['inputs_sha256'].items():
            output = subprocess.check_output(['docker', 'exec', HELPER, 'sha256sum',
                f'/data/fresh7/{track}/{name}'], text=True)
            actual = output.split()[0]
            assert actual == expected, (track, name, expected, actual)
            verified[track][name] = actual
    (ROOT / 'validation/continuation7-fresh-benchmark-data.json').write_text(json.dumps({
        'source': 'codescythe-research:/benchfresh/seed20261031', 'volume': VOLUME,
        'destination': '/data/fresh7', 'inputs_sha256': verified}, indent=2) + '\n')
    print('PASS copied all full-seed inputs without regeneration; every input hash agrees.')
finally:
    call(['docker', 'stop', HELPER], stdout=subprocess.DEVNULL)
