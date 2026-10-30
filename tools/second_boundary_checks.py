"""Reproduce the second set's unsafe load and fixed-name-arena defects."""
import json
from pathlib import Path
import subprocess
import sys
import validate

ROOT=validate.ROOT
folder=ROOT/'build/supplied-second'
unit=folder/'a-guard.c'
unit.write_text(r'''
#define main supplied_main
#include "/work/research/prototypes/supplied-second-a.c"
#undef main
int main(void) {
  char* p=mmap(NULL,8192,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
  if(p==MAP_FAILED || mprotect(p,4096,PROT_READ|PROT_WRITE))return 2;
  memcpy(p+4096-8,"/ 200 0\n",8);
  return next_space(p+4096-8)==p+4096-7?0:3;
}
''')
subprocess.run(['gcc','-std=gnu11','-O3','-mavx2','-pthread',str(unit),'-o',str(folder/'a-guard')],check=True)
guard=subprocess.run([str(folder/'a-guard')],capture_output=True,text=True)
data=ROOT/'data/c/second-suffix-arena'
out=ROOT/'.out/supplied-second/c/suffix-arena'
data.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
(data/'regions.csv').write_bytes(b'region_id,country\n1,AAA\n')
with (data/'records.csv').open('w') as stream:
    stream.write('id,name,note,region_id,amount\n')
    for i in range(100):
        name='Name'+chr(65+i//26)+chr(65+i%26)+' '*6000
        stream.write(f'{i+1},"{name}","",1,0.01\n')
binary=folder/'c-sanitized'
subprocess.run(['gcc','-std=gnu11','-O1','-g','-mavx2','-pthread','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'research/prototypes/supplied-second-c.c'),'-o',str(binary)],check=True)
run=subprocess.run([str(binary),'--data',str(data),'--out',str(out)],capture_output=True,text=True,timeout=20)
ref=out/'reference';ref.mkdir(exist_ok=True)
subprocess.run([sys.executable,str(validate.OFFICIAL/'reference/c_join.py'),'--data',str(data),'--out',str(ref)],check=True)
report={'a_guard_page':{'returncode':guard.returncode,'expected':0,'stderr':guard.stderr},
        'c_suffix_arena':{'returncode':run.returncode,'stderr':run.stderr,'reference_sha256':validate.digest(ref/'aggregates.txt')}}
(ROOT/'validation/supplied-second-boundaries.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'a_guard_returncode':guard.returncode,'c_suffix_returncode':run.returncode,'c_sanitizer':run.stderr[:2200]},indent=2))
