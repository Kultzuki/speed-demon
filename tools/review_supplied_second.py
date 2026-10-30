"""Compile and differentially check the second supplied A/B/C/D set as C11."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
ATTACHMENTS={'a':'5e8094d3-be04-468e-b01c-1b2617cb9ff6','b':'b4393cf1-3fa0-45f3-91df-bfcdac3d070c',
             'c':'5ee8a328-e243-4f3a-a47c-8c5d9c70e026','d':'d3fba53d-cf99-4cee-b909-198eeaf284cf'}
ADAPTER=r'''
static const char* review_data="/data";
static const char* review_out="/out";
static char review_path[4096];
static void review_paths(int argc,char** argv) {
  for(int i=1;i+1<argc;i+=2) {
    if(!strcmp(argv[i],"--data")) review_data=argv[i+1];
    if(!strcmp(argv[i],"--out")) review_out=argv[i+1];
  }
}
static const char* review_location(const char* name,int output) {
  snprintf(review_path,sizeof(review_path),"%s/%s",output?review_out:review_data,name);
  return review_path;
}
'''

def prepare():
    folder=ROOT/'research/supplied-second';folder.mkdir(exist_ok=True)
    for track,attachment in ATTACHMENTS.items():
        path=folder/f'track-{track}.c'
        data=(Path.home()/'.codex/attachments'/attachment/'Pasted text.txt').read_bytes()
        path.write_bytes(data)
        source=data.decode('utf-8-sig')
        source=source.replace('int main(void) {',ADAPTER+'\nint main(int argc,char** argv) {\n  review_paths(argc,argv);')
        import re
        source=re.sub(r'"/data/([^"\n]+)"',r'review_location("\1",0)',source)
        source=re.sub(r'"/out/([^"\n]+)"',r'review_location("\1",1)',source)
        (ROOT/f'research/prototypes/supplied-second-{track}.c').write_text(source)
    print('Preserved exact originals and path-only test adapters')

def check():
    sys.path.insert(0,str(ROOT/'tools'))
    import validate
    flags=['-std=gnu11','-O3','-DNDEBUG','-mavx2','-mpopcnt','-pthread','-static','-s']
    out=ROOT/'build/supplied-second';out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/'.competition/SHA256SUMS.json').read_text())['tracks']
    report={'environment':'Linux research container; originals with only input/output path argument adapter','flags':flags,'builds':{},'checks':[]}
    for track in 'abcd':
        source=ROOT/f'research/prototypes/supplied-second-{track}.c'
        binary=out/f'track-{track}'
        run=subprocess.run(['gcc',*flags,str(source),'-o',str(binary)],capture_output=True,text=True)
        report['builds'][track]={'original_sha256':validate.digest(ROOT/f'research/supplied-second/track-{track}.c'),
                                 'adapter_sha256':validate.digest(source),'ok':run.returncode==0,'stderr':run.stderr}
        print(f'BUILD {track}: {run.returncode}',run.stderr,flush=True)
        if run.returncode:continue
        cases=[('public-full',Path(f'/benchdata/{track}'),manifest[track]['expected_output_sha256'][0])]
        previous=json.loads((ROOT/'validation/fresh-full-seed20261031.json').read_text())
        cases.append(('fresh-full',Path(f'/benchfresh/seed20261031/{track}'),next(x['sha256'] for x in previous['results'] if x['track']==track)))
        extra={'a':['empty','percentile-boundaries','parallel-boundaries'],
               'b':['supplied-phrase-1024','token-and-block-boundaries'],
               'c':['final-no-newline','name-table-growth','parallel-hostile','supplied-long-name'],
               'd':['worked-example','fuzz0','fuzz1','fuzz2','fuzz3','fuzz4']}
        for label in extra[track]:
            data=ROOT/f'data/{track}/{label}'
            expected_dir=ROOT/f'.out/validation/{track}/{label}/reference'
            expected=expected_dir/validate.OUTPUT[track]
            if not expected.is_file():
                expected_dir.mkdir(parents=True,exist_ok=True)
                subprocess.run([sys.executable,str(validate.OFFICIAL/f'reference/{validate.MODULE[track]}.py'),'--data',str(data),'--out',str(expected_dir)],check=True)
            cases.append((label,data,validate.digest(expected)))
        for label,data,expected in cases:
            target=ROOT/f'.out/supplied-second/{track}/{label}';target.mkdir(parents=True,exist_ok=True)
            started=time.perf_counter()
            try:
                run=subprocess.run([str(binary),'--data',str(data),'--out',str(target)],capture_output=True,text=True,timeout=30)
                output=target/validate.OUTPUT[track]
                actual=validate.digest(output) if output.is_file() else None
                entry={'track':track,'case':label,'ok':run.returncode==0 and actual==expected,'returncode':run.returncode,
                       'sha256':actual,'expected_sha256':expected,'stderr':run.stderr}
            except subprocess.TimeoutExpired:
                entry={'track':track,'case':label,'ok':False,'error':'timeout'}
            entry['local_seconds']=time.perf_counter()-started
            report['checks'].append(entry);print(json.dumps(entry),flush=True)
        (ROOT/'validation/supplied-second-review.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Review saved',flush=True)

if __name__=='__main__':
    prepare() if '--prepare' in sys.argv else check()
