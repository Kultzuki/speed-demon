"""Reproduce the supplied hash collision and stream-width limits separately."""
import json
from pathlib import Path
import subprocess

import validate

ROOT=validate.ROOT
folder=ROOT/'build/supplied-continuation5'
binary=folder/'a-crc-collision'
subprocess.run(['g++','-std=c++20','-O3','-pthread','-static','-s','-march=x86-64-v3',str(ROOT/'research/tests/a-supplied-crc-collision5.cpp'),'-o',str(binary)],check=True)
run=subprocess.run([str(binary)],capture_output=True,text=True,check=True)
print(run.stdout,flush=True)
keys=run.stdout.strip().split()[-2:]
data=ROOT/'data/a/continuation5-crc-collision';data.mkdir(parents=True,exist_ok=True)
(data/'requests.log').write_text(''.join(f'2026-10-30T18:00:00.000000Z GET {key} 200 {i+1}\n' for i,key in enumerate(keys)))
report={'collision_tool_stdout':run.stdout,'checks':[]}
for track,case in [('a','continuation5-crc-collision'),('b','continuation5-wide-domain')]:
    data=ROOT/f'data/{track}/{case}'
    ref=ROOT/f'.out/validation/{track}/{case}/reference';ref.mkdir(parents=True,exist_ok=True)
    if not (ref/validate.OUTPUT[track]).is_file():
        subprocess.run(['python3',str(validate.OFFICIAL/f'reference/{validate.MODULE[track]}.py'),'--data',str(data),'--out',str(ref)],check=True)
    expected=validate.digest(ref/validate.OUTPUT[track])
    for batch in ['fifth','sixth']:
        target=ROOT/f'.out/supplied-continuation5/{batch}-{track}/{case}';target.mkdir(parents=True,exist_ok=True)
        run=subprocess.run([str(folder/f'{batch}-{track}'),'--data',str(data),'--out',str(target)],capture_output=True,text=True,timeout=20)
        output=target/validate.OUTPUT[track]
        actual=validate.digest(output) if output.is_file() else None
        entry={'label':f'{batch}-{track}','case':case,'returncode':run.returncode,'ok':run.returncode==0 and actual==expected,'sha256':actual,'expected_sha256':expected,'stderr':run.stderr}
        report['checks'].append(entry)
        print(entry,flush=True)
(ROOT/'validation/supplied-continuation5-additional.json').write_text(json.dumps(report,indent=2)+'\n')
