"""Select paired-tested continuation candidates; keep originals and rejected trials."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
selected={'a':'a-simd3.cpp','b':'b-bloom3.cpp','c':'c-compactbyte3.cpp','d':'d-wide3-twelve.cpp'}
report={}
for track,name in selected.items():
    source=ROOT/'research/prototypes'/name
    data=source.read_bytes()
    (ROOT/f'track-{track}/main.cpp').write_bytes(data)
    report[track]={'source':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(data).hexdigest()}
(ROOT/'validation/continuation3-selection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
