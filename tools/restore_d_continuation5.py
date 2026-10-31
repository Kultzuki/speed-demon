"""Reject D's official coefficient regression without resetting other work."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
summary=json.loads((ROOT/'validation/continuation5-official-summary.json').read_text())
assert summary['decisions']['d']['decision']=='reject and restore incoming source'
assert summary['decisions']['b']['decision']==summary['decisions']['c']['decision']=='retain'
shutil.copyfile(ROOT/'research/prototypes/continuation5-start-d.cpp',ROOT/'track-d/main.cpp')
(ROOT/'track-d/README.md').write_bytes(subprocess.check_output(['git','show','12aa1a4:track-d/README.md'],cwd=ROOT))
path=ROOT/'research/continuation5-selection.json';selection=json.loads(path.read_text())
selection['sources']['d']={'prototype':'continuation5-start-d.cpp','sha256':hashlib.sha256((ROOT/'track-d/main.cpp').read_bytes()).hexdigest(),'decision':'Restored: 160e4dd trial K=14.963401 regresses from best K=15.399979'}
selection['official_implementation']='160e4dd03a5210afd31ba01af791c03d1907da7b'
selection['status']='B/C retained officially; D restored to full uint64 labels; pending final rebuilt gates and push'
path.write_text(json.dumps(selection,indent=2)+'\n')
path=ROOT/'HANDOVER_NEXT.md';text=path.read_text()
text=text.replace('C restored mmap plus a safe exact-name prefetch ring; D sparse uint32 labels\nwith exact uint64 overflow storage.', 'C restored mmap plus a safe exact-name prefetch ring; D restored full uint64\nsparse labels after rejecting the overflow-label coefficient regression.')
text=text.replace('This checkpoint is prepared for the next implementation commit and official\nmeasurement. Do not claim local improvements as official. Wait for all four\ntracks at the pushed SHA, compare K against the recorded best independently,\nand restore any coefficient loser before the final handover is written. The\nboard retains historical bests independently of branch tip.', '''Commit 160e4dd03a5210afd31ba01af791c03d1907da7b passed all official gates.
B improved K=14.154553 to 18.435477 and C=22.257059 to 23.727679; both stay.
D regressed from 15.399979 to 14.963401 despite lower memory, so the stronger
incoming full-uint64 D source is restored. A is unchanged. Best-three public
aggregate is 69.077744, captured rank 16, leader 79.190878, in
validation/leaderboard-continuation5-official.json. Final restored-D release,
sanitizer and rebuilt image checks and a normal follow-up push are pending.
The board retains historical bests independently of branch tip.''')
path.write_text(text,encoding='utf-8',newline='\n')
path=ROOT/'research/CONTINUATION5.md'
path.write_text(path.read_text()+'\n\nD is restored locally to the incoming full-uint64 source after its official K regression. B/C are retained. Final mixed-source release/sanitizer gates and a rebuilt D image precede the next push.\n')
print('Restored only D main/README; all other implementations and official records preserved.')
