"""Serialized local cgroup measurements on a Linux volume; never board scores."""
import hashlib
import json
from pathlib import Path
import statistics
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE='debian:13-slim@sha256:62bd423aeee912639ca8ee681c2b762cb3e25137e0a92b20be455898a9f034ad'
VOLUME='codescythe-bench-continuation5'
HELPER='codescythe-data-continuation5'

def call(args,**kwargs):return subprocess.run(args,check=True,**kwargs)

call(['docker','volume','create',VOLUME],stdout=subprocess.DEVNULL)
call(['docker','run','-d','--name',HELPER,'--network=none','--memory=1g','--memory-swap=1g',
      '--mount',f'type=volume,src={VOLUME},dst=/benchdata','--entrypoint','sleep',BASE,'infinity'],stdout=subprocess.DEVNULL)
try:
    producer=subprocess.Popen(['docker','exec','codescythe-research','tar','-C','/benchdata','-cf','-','.'],stdout=subprocess.PIPE)
    call(['docker','exec','-i',HELPER,'tar','-C','/benchdata','-xf','-'],stdin=producer.stdout)
    producer.stdout.close()
    assert producer.wait()==0
    print('Copied preserved public inputs into separate Linux benchmark volume.',flush=True)
    build=ROOT/'build/continuation5-cgroup';build.mkdir(exist_ok=True)
    common=['docker','exec','codescythe-research','g++','-std=c++20','-O3','-DNDEBUG','-pthread','-static','-s']
    call(common+['research/tests/cgroup-monitor5.cpp','-o','build/continuation5-cgroup/monitor'])
    sources={'b':{'baseline':'continuation5-start-b','csr':'b-csr5','twopass':'b-twopass5'},
             'c':{'baseline':'continuation5-start-c','prefetch':'c-prefetch5'},
             'd':{'baseline':'continuation5-start-d','escaped':'d-labelescape5'}}
    counts=json.loads((ROOT/'validation/continuation5-source-counts.json').read_text())['tracks']
    manifest=json.loads((ROOT/'.competition/SHA256SUMS.json').read_text())['tracks']
    report={'scope':'Local WSL2, fresh cgroups, Linux-local hot inputs, process fork/exec/exit timer, read-only root/data, 8g/no swap, 12 pinned logical CPUs. Monitor overhead and tmpfs output are included; not official scoring.', 'tracks':{}}
    for track,candidates in sources.items():
        entries={}
        for label,stem in candidates.items():
            flags=['-march=x86-64-v3'] if track=='b' and label!='baseline' else []
            name=f'{track}-{label}'
            call(common+flags+['-I',f'track-{track}',f'research/prototypes/{stem}.cpp','-o',f'build/continuation5-cgroup/{name}'])
            entries[label]={'source':stem,'S':counts[track][stem]['S'],'D':1,'runs':[]}
        for iteration in range(3):
            labels=list(candidates)
            if iteration%2:labels.reverse()
            for label in labels:
                command=['docker','run','--rm','--network=none','--read-only','--memory=8g','--memory-swap=8g',
                         '--cpuset-cpus=0-11','--cpuset-mems=0','--pids-limit=512','--cap-drop=ALL','--security-opt=no-new-privileges',
                         '--user=65534:65534','--tmpfs','/tmp:rw,size=1g,exec','--tmpfs','/out:rw,size=64m',
                         '--mount',f'type=volume,src={VOLUME},dst=/data,readonly',
                         '--mount',f'type=bind,src={build},dst=/candidates,readonly',
                         '-e',f'OUTPUT_FILE=/out/{manifest[track]["output"]}','--entrypoint','/candidates/monitor',BASE,
                         f'/candidates/{track}-{label}','--data',f'/data/{track}','--out','/out']
                run=call(command,capture_output=True,text=True)
                lines=run.stdout.strip().splitlines()
                metric=json.loads(next(x[7:] for x in lines if x.startswith('METRIC ')))
                digest=next(x.split()[0] for x in lines if x.endswith('/out/'+manifest[track]['output']))
                assert digest==manifest[track]['expected_output_sha256'][0]
                metric['sha256']=digest;entries[label]['runs'].append(metric)
                print(track,label,metric,flush=True)
        for label,result in entries.items():
            result['T_s']=statistics.median(x['T_s'] for x in result['runs'])
            result['M_bytes']=statistics.median(x['M_bytes'] for x in result['runs'])
        baseline=entries['baseline']
        for label,result in entries.items():
            # Source and dependency factors are below their caps for these C++
            # submissions. Reference memory is well above these measurements.
            result['local_K_ratio_to_baseline']=(baseline['T_s']/result['T_s'])**.5*(baseline['M_bytes']/result['M_bytes'])**.2*(baseline['S']/result['S'])**.15
            print('COMBINED',track,label,result['T_s'],result['M_bytes'],result['S'],result['local_K_ratio_to_baseline'],flush=True)
        report['tracks'][track]=entries
        (ROOT/'research/results/continuation5-cgroup-coefficient.json').write_text(json.dumps(report,indent=2)+'\n')
finally:
    call(['docker','stop',HELPER],stdout=subprocess.DEVNULL)
print('Helper stopped; benchmark volume retained for reproducible follow-ups.',flush=True)
