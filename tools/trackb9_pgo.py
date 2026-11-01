"""Build an isolated, generator-only PGO image; never train on scoring data."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument('--source', default='track-b/main.cpp')
ap.add_argument('--label', required=True)
ap.add_argument('--scale', choices=['sample', 'full'], default='full')
ap.add_argument('--tune', default='')
args = ap.parse_args()
assert all(c.isalnum() or c in '-_' for c in args.label)
assert args.tune in ['', 'alderlake']
ctx = ROOT / 'build' / args.label
ctx.mkdir(parents=True, exist_ok=False)
shutil.copy2(ROOT / args.source, ctx / 'main.cpp')
shutil.copy2(ROOT / 'track-b/common.hpp', ctx / 'common.hpp')
generator = subprocess.check_output(['git', '-C', str(ROOT / '.competition/official'),
    'show', 'HEAD:generators/b_index.py'])
(ctx / 'b_index_generator.py').write_bytes(generator)
flags = '-std=c++20 -O3 -DNDEBUG -march=x86-64-v3 -pthread -static -s'
if args.tune:
    flags += ' -mtune=' + args.tune
dockerfile = f'''FROM python:3.13-slim@sha256:d98cc29d3266e535dd9da1099688d9cb3ca4753813571e071763d17725460962 AS training
WORKDIR /src
COPY b_index_generator.py ./
RUN python3 b_index_generator.py --seed 60773 --scale {args.scale} --out /train/60773 \\
 && python3 b_index_generator.py --seed 284911 --scale {args.scale} --out /train/284911

FROM gcc:16@sha256:43978d7710a803d1c3d32f4117c1528ec7285a4ce2c0a51e982ec1a6e3d87d95 AS build
WORKDIR /src
COPY main.cpp common.hpp ./
COPY --from=training /train /train
RUN mkdir -p /tmp/profile /tmp/output \\
 && g++ {flags} -fprofile-generate=/tmp/profile -fprofile-update=atomic main.cpp -o /solution \\
 && /solution --data /train/60773 --out /tmp/output \\
 && /solution --data /train/284911 --out /tmp/output \\
 && g++ {flags} -fprofile-use=/tmp/profile -fprofile-correction -Werror=missing-profile main.cpp -o /solution

FROM debian:13-slim@sha256:62bd423aeee912639ca8ee681c2b762cb3e25137e0a92b20be455898a9f034ad
COPY --from=build /solution /app/solution
ENTRYPOINT ["/app/solution"]
'''
(ctx / 'Dockerfile').write_text(dockerfile, newline='\n')
(ROOT / f'research/prototypes/{args.label}.Dockerfile').write_text(dockerfile, newline='\n')
tag = 'codescythe-trackb9/' + args.label
log_path = ROOT / f'validation/{args.label}-build.log'
started = time.monotonic()
with log_path.open('x') as log:
    subprocess.run(['docker', 'build', '--network=none', '-t', tag, str(ctx)],
        check=True, stdout=log, stderr=subprocess.STDOUT, timeout=590)
elapsed = time.monotonic() - started
binary = subprocess.check_output(['docker', 'run', '--rm', '--network=none', '--read-only',
    '--entrypoint', 'cat', tag, '/app/solution'])
output = ROOT / f'build/bench7/{args.label}'
output.write_bytes(binary)
report = {'scope': 'Isolated offline image; profiles generated only from unmodified organizer generator output.',
    'seeds': [60773, 284911], 'scale': args.scale, 'flags': flags,
    'source': args.source, 'source_sha256': hashlib.sha256((ctx / 'main.cpp').read_bytes()).hexdigest(),
    'common_sha256': hashlib.sha256((ctx / 'common.hpp').read_bytes()).hexdigest(),
    'generator_sha256': hashlib.sha256(generator).hexdigest(), 'generator_from': 'official Git blob HEAD:generators/b_index.py',
    'dockerfile_sha256': hashlib.sha256((ctx / 'Dockerfile').read_bytes()).hexdigest(),
    'image': tag, 'binary_sha256': hashlib.sha256(binary).hexdigest(), 'offline_build_seconds': elapsed}
(ROOT / f'validation/{args.label}-training.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2), flush=True)
