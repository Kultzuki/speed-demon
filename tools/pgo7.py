"""Local A/C PGO trial trained only by unmodified generator output."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/pgo7'
FLAGS = ['-std=c++20', '-O3', '-DNDEBUG', '-pthread', '-static', '-s']


def call(command):
    subprocess.run([str(x) for x in command], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', required=True, choices='ac')
    args = ap.parse_args()
    track = args.track
    work = BASE / track
    work.mkdir(parents=True, exist_ok=False)
    source = ROOT / f'research/prototypes/continuation7-incoming-{track}.cpp'
    generator = ROOT / f'.competition/official/generators/{"a_ingest" if track == "a" else "c_join"}.py'
    binary = work / 'solution'
    profiles = work / 'profiles'
    profiles.mkdir()
    common = ['g++', *FLAGS, '-I', ROOT / f'track-{track}', source, '-o', binary]
    call([*common, f'-fprofile-generate={profiles}', '-fprofile-update=atomic'])
    inputs = {}
    for seed in [197731, 806317]:
        data = work / f'seed{seed}'
        out = work / f'out{seed}'
        out.mkdir()
        call(['python3', generator, '--scale', 'sample', '--seed', seed, '--out', data])
        call([binary, '--data', data, '--out', out])
        inputs[str(seed)] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in data.iterdir() if p.is_file()}
    call([*common, f'-fprofile-use={profiles}', '-fprofile-correction'])
    bench = ROOT / f'build/bench7/pgo-{track}7'
    shutil.copy2(binary, bench)
    result = {'scope': 'Generator-only local PGO trial; no public/holdout input or cached answers in profiles.',
              'track': track, 'flags': FLAGS, 'seeds': [197731, 806317], 'scale': 'sample',
              'generator_sha256': hashlib.sha256(generator.read_bytes()).hexdigest(),
              'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'binary_sha256': hashlib.sha256(bench.read_bytes()).hexdigest(), 'inputs_sha256': inputs,
              'profiles_sha256': {p.relative_to(profiles).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in profiles.rglob('*.gcda')}}
    (ROOT / f'validation/pgo7-{track}-training.json').write_text(json.dumps(result, indent=2) + '\n')
    print('TRAINED', track, result['binary_sha256'], flush=True)


if __name__ == '__main__':
    main()
