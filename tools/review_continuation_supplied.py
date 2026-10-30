"""Preserve and review the two new pasted sets; adapters only change paths."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from review_supplied_second import ADAPTER

FOURTH={'a':'0b541605-153c-426a-92d0-a0a832d5858f',
        'c':'9a382e36-dc26-458e-81b5-a1466ab6fb0d',
        'd':'cedf40f1-142e-4aac-baa7-64ad53c74bdf'}

def prepare():
    directory=ROOT/'research/supplied-fourth';directory.mkdir(exist_ok=True)
    for track,attachment in FOURTH.items():
        (directory/f'track-{track}.c').write_bytes((Path.home()/'.codex/attachments'/attachment/'Pasted text.txt').read_bytes())
    for batch,tracks in [('third','ac'),('fourth','acd')]:
        for track in tracks:
            source=(ROOT/f'research/supplied-{batch}/track-{track}.c').read_text(encoding='utf-8-sig')
            source=source.replace('int main(void) {',ADAPTER+'\nint main(int argc,char** argv) {\n  review_paths(argc,argv);')
            source=re.sub(r'"/data/([^"\n]+)"',r'review_location("\1",0)',source)
            source=re.sub(r'"/out/([^"\n]+)"',r'review_location("\1",1)',source)
            (ROOT/f'research/prototypes/supplied-{batch}-{track}.c').write_text(source)
    print('Preserved fourth originals and path-only adapters for both new sets')

def check():
    import validate
    manifest=json.loads((ROOT/'.competition/SHA256SUMS.json').read_text())['tracks']
    fresh=json.loads((ROOT/'validation/fresh-full-seed20261031.json').read_text())
    flags=['-std=gnu11','-O3','-DNDEBUG','-mavx2','-mpopcnt','-pthread','-static','-s']
    folder=ROOT/'build/supplied-continuation';folder.mkdir(exist_ok=True)
    report={'flags':flags,'scope':'Exact pasted originals with input/output path adapters only; Linux local checks, not official scores.',
            'unchanged':{'third-b':'Byte-identical to second B; previous full-seed/boundary review applies.',
                         'third-c-duplicate':'Byte-identical to third C.'},'builds':{},'checks':[]}
    extras={'a':['empty','percentile-boundaries','parallel-boundaries'],
            'c':['final-no-newline','name-table-growth','parallel-hostile','supplied-long-name','second-suffix-arena'],
            'd':['worked-example','fuzz0','fuzz1','fuzz2','fuzz3','fuzz4']}
    for batch,tracks in [('third','ac'),('fourth','acd')]:
        for track in tracks:
            label=f'{batch}-{track}'
            source=ROOT/f'research/prototypes/supplied-{label}.c'
            binary=folder/label
            run=subprocess.run(['gcc',*flags,str(source),'-o',str(binary)],capture_output=True,text=True)
            report['builds'][label]={'ok':run.returncode==0,'stderr':run.stderr,
                'original_sha256':validate.digest(ROOT/f'research/supplied-{batch}/track-{track}.c'),
                'adapter_sha256':validate.digest(source)}
            print('BUILD',label,run.returncode,flush=True)
            if run.returncode:continue
            cases=[('public-full',Path(f'/benchdata/{track}'),manifest[track]['expected_output_sha256'][0]),
                   ('fresh-full',Path(f'/benchfresh/seed20261031/{track}'),next(x['sha256'] for x in fresh['results'] if x['track']==track))]
            for case in extras[track]:
                data=ROOT/f'data/{track}/{case}'
                expected=ROOT/f'.out/validation/{track}/{case}/reference'/validate.OUTPUT[track]
                if not expected.is_file():
                    expected.parent.mkdir(parents=True,exist_ok=True)
                    subprocess.run([sys.executable,str(validate.OFFICIAL/f'reference/{validate.MODULE[track]}.py'),'--data',str(data),'--out',str(expected.parent)],check=True)
                cases.append((case,data,validate.digest(expected)))
            for case,data,expected in cases:
                target=ROOT/f'.out/supplied-continuation/{label}/{case}';target.mkdir(parents=True,exist_ok=True)
                start=time.perf_counter()
                try:
                    run=subprocess.run([str(binary),'--data',str(data),'--out',str(target)],capture_output=True,text=True,timeout=15)
                    output=target/validate.OUTPUT[track]
                    actual=validate.digest(output) if output.is_file() else None
                    entry={'label':label,'case':case,'ok':run.returncode==0 and actual==expected,'returncode':run.returncode,
                           'sha256':actual,'expected_sha256':expected,'stderr':run.stderr[:3000]}
                except subprocess.TimeoutExpired:
                    entry={'label':label,'case':case,'ok':False,'error':'15-second timeout'}
                entry['local_seconds']=time.perf_counter()-start
                report['checks'].append(entry);print(json.dumps(entry),flush=True)
                (ROOT/'validation/supplied-continuation-review.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
    prepare() if args.prepare else check()
