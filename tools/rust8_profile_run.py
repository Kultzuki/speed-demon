import json
import argparse
from pathlib import Path
import bench6

ROOT = Path(__file__).resolve().parents[1]
bench6.BUILD = ROOT / 'build/rust8-bench'
report = {}
ap = argparse.ArgumentParser(); ap.add_argument('--name', default='profile8'); ap.add_argument('--report', default='rust8-initial-phases'); args = ap.parse_args()
for track in 'ad':
    report[track] = []
    for _ in range(3):
        metric = bench6.run(track, f'{track}-{args.name}', f'/data/{track}')
        print(track, json.dumps(metric), flush=True)
        report[track].append(metric)
with (ROOT / f'research/results/{args.report}.json').open('x') as stream:
    json.dump(report, stream, indent=2); stream.write('\n')
