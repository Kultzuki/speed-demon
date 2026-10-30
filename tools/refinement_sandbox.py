"""Rebuild all final images offline and verify the official starter sandbox."""
import json
import argparse
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--name',default='refined');args=parser.parse_args()
manifest=json.loads((ROOT/'.competition/SHA256SUMS.json').read_text(encoding='utf-8-sig'))['tracks']
# check.py recreates exactly these output folders. Resolve them before any delete.
for track in 'abcd':
    target=(ROOT/'.out'/f'track-{track}').resolve()
    assert target.is_relative_to(ROOT.resolve()) and target.parent==(ROOT/'.out').resolve()
    print(f'Verified sandbox output target: {target}',flush=True)
sizes={}
with (ROOT/f'validation/sandbox-{args.name}.txt').open('w') as log:
    for track in 'abcd':
        command=[sys.executable,str(ROOT/'check.py'),track,'--data',str(ROOT/f'data/{track}/full-seed1'),
                 '--expected',manifest[track]['expected_output_sha256'][0]]
        run=subprocess.run(command,capture_output=True,text=True)
        log.write(f'\nTRACK {track}\n{run.stdout}\n{run.stderr}\n');log.flush()
        print(run.stdout,flush=True)
        if run.returncode:
            print(run.stderr,flush=True)
            raise SystemExit(run.returncode)
        tag=f'speeddemon-check/track-{track}'
        info=json.loads(subprocess.check_output(['docker','image','inspect',tag],text=True))[0]
        digest=subprocess.check_output(['docker','run','--rm','--network=none','--read-only','--entrypoint','sha256sum',tag,'/app/solution'],text=True).split()[0]
        sizes[track]={'image_id':info['Id'],'size_bytes':info['Size'],'solution_sha256':digest}
(ROOT/f'validation/image-sizes-{args.name}.json').write_text(json.dumps(sizes,indent=2)+'\n')
print('PASS all rebuilt offline images, sandbox contracts, sizes and full hashes',flush=True)
