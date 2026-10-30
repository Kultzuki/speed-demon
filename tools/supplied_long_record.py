"""Confirm the supplied C parser's fixed-record-lookahead failure."""
import json
import os
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[1]
data=root/'data/c/supplied-long-name'
out=root/'.out/supplied-rust/c/long-name'
data.mkdir(parents=True,exist_ok=True)
out.mkdir(parents=True,exist_ok=True)
(data/'regions.csv').write_bytes(b'region_id,country\n1,AAA\n')
records=bytearray(b'\xef\xbb\xbfid,name,note,region_id,amount\r\n')
target=2*1024*1024-70000
count=0
while len(records)+2048<target:
    count+=1
    records.extend(f'{count},"A","",1,0.01\n'.encode())
ordinary=count
count+=1
empty=f'{count},"","",1,0.01\n'.encode()
filler=b'Z'+b' '*(target-len(records)-len(empty)-1)
records.extend(f'{count},"'.encode()+filler+b'","",1,0.01\n')
assert len(records)==target
count+=1
name=b'B'+b' '*99999
records.extend(f'{count},"'.encode()+name+b'","",1,0.01\r\n')
(data/'records.csv').write_bytes(records)
expected=f'AAA {count} {count*(count+1)//2} {count//100}.{count%100:02} 0.01 0.01 3 {ordinary+len(filler)+len(name)} 0\n'
entry={'track':'c','case':'unbounded-trailing-spaces','expected_text':expected,'maximum_name_bytes':100000,'last_record_offset':target}
try:
    run=subprocess.run([str(root/'build/supplied-rust/track-c.exe'),'--data',str(data),'--out',str(out)],
                       env=dict(os.environ,DATA_DIR=str(data),OUT_DIR=str(out)),capture_output=True,text=True,timeout=3)
    path=out/'aggregates.txt'
    actual=path.read_text() if path.is_file() else None
    entry.update(returncode=run.returncode,actual_text=actual,ok=run.returncode==0 and actual==expected,stderr=run.stderr)
except subprocess.TimeoutExpired:
    entry.update(ok=False,error='timeout: parser makes no progress on continuation of a long record')
report=root/'validation/supplied-rust-review.json'
saved=json.loads(report.read_text())
saved['checks']=[x for x in saved['checks'] if not (x['track']=='c' and x['case']==entry['case'])]+[entry]
report.write_text(json.dumps(saved,indent=2)+'\n')
print(json.dumps(entry,indent=2))
