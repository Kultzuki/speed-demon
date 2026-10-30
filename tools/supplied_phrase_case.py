"""Reproduce the supplied B token-cap defect with strict LF input bytes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[1]
data=root/'data/b/supplied-phrase-1024'
out=root/'.out/supplied-rust/b/phrase-after-token1024'
data.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
(data/'docs.txt').write_bytes(('0\t'+'writ of habeas corpus '*256+'bail bond\n').encode('ascii'))
(data/'queries.txt').write_bytes(b'PHRASE "bail bond"\nBOOL bail AND bond\n')
run=subprocess.run([str(root/'build/supplied-rust/track-b.exe'),'--data',str(data),'--out',str(out)],
                   env=dict(os.environ,DATA_DIR=str(data),OUT_DIR=str(out)),capture_output=True,text=True,check=True)
actual=(out/'results.txt').read_bytes()
entry={'track':'b','case':'phrase-after-token1024','returncode':0,'sha256':hashlib.sha256(actual).hexdigest(),
       'actual_text':actual.decode(),'expected_text':'1 0 0\n1 0 0\n','ok':actual==b'1 0 0\n1 0 0\n','strict_lf_inputs':True}
path=root/'validation/supplied-rust-review.json'
report=json.loads(path.read_text())
report['checks']=[x for x in report['checks'] if not (x['track']=='b' and x['case']==entry['case'])]+[entry]
path.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(entry,indent=2))
