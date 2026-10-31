"""Select the first serious measured local candidates without touching A."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
SOURCES={'b':'b-csr5.cpp','c':'c-prefetch5.cpp','d':'d-labelescape5.cpp'}
selection={'scope':'Local candidates pending complete gates and official K; not established coefficient gains','sources':{}}
for track,file in SOURCES.items():
    source=ROOT/'research/prototypes'/file
    shutil.copyfile(source,ROOT/f'track-{track}/main.cpp')
    selection['sources'][track]={'prototype':file,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
path=ROOT/'track-b/Dockerfile'
text=path.read_text()
assert '-march=x86-64-v3' not in text
path.write_text(text.replace('-DNDEBUG -pthread','-DNDEBUG -march=x86-64-v3 -pthread'),encoding='utf-8',newline='\n')
(ROOT/'research/continuation5-selection.json').write_text(json.dumps(selection,indent=2)+'\n')
print('Selected B checked CSR, C owned-name prefetch and D exact overflow labels; retained A.')
