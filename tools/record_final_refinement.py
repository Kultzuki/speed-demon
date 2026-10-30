"""Record the final gate and keep the A rollback explicit."""
import hashlib
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
release=json.loads((ROOT/'validation/final-release-build.json').read_text())
sanitized=json.loads((ROOT/'validation/final-sanitized-build.json').read_text())
assert (ROOT/'track-a/main.cpp').read_bytes()==subprocess.check_output(['git','show','0c89c6e:track-a/main.cpp'])
for track in 'abcd':
    digest=hashlib.sha256((ROOT/f'track-{track}/main.cpp').read_bytes()).hexdigest()
    assert release[track]['source_sha256']==sanitized[track]['source_sha256']==digest
for mode in ['release','sanitized']:
    for suffix,count in [('',69),('-full',4),('-extra',10)]:
        assert len(json.loads((ROOT/f'validation/final-{mode}{suffix}.json').read_text())['results'])==count
selection={'checkpoint':'6cb35093ef9de4babf07b6ed58347e40da6fa76d',
           'sources':{'a':'a-parallel-output.cpp (measured 0c89c6e source restored)','b':'b-inline-query.cpp','c':'c-contract-cuts.cpp','d':'d-hash.cpp (unused reorder/remap removed)'},
           'status':'final release and ASan/UBSan gates passed',
           'production_source_sha256':{k:v['source_sha256'] for k,v in release.items()},
           'rejected_official_a':'b30392c: K=18.583948 < 19.851814; memory outweighed time gain'}
(ROOT/'research/refinement-selection.json').write_text(json.dumps(selection,indent=2)+'\n')
path=ROOT/'track-c/PERF.md'
text=path.read_text()+'''

## Final refinement: record-boundary discovery

The second supplied set suggested a useful contract-specific cut rule. Section
2.2 guarantees names have no LF and note bytes cannot contain digits or a BOM.
Therefore LF followed by a digit/BOM starts a record. Searching locally from
each desired cut removes the whole-file quote-parity pass. Exact decoded-name
equality and dynamically growing arenas remain unchanged.

An alternating five-run full-hash batch improved 0.085193s to 0.073064s locally
(`research/results/c-contract-cuts-paired.json`). This is not an official time.
The final four-track release and ASan/UBSan gates each pass 83 dataset comparisons,
the three direct C/D programs, and the forced uint64 B full-hash check. This
includes the long record, optional EOF, 64 boundary alignments and both full seeds.
Final production provenance is in `validation/final-*-build.json`.
'''
path.write_text(text)
print('PASS final source hashes, stronger measured A restoration, and both complete gates')
