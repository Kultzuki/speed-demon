"""Measure C++/header/Dockerfile code using the organizer-pinned tools."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/'build/static-tools'
report={}
for track in 'abcd':
    sources=[ROOT/f'research/prototypes/continuation5-start-{track}.cpp']
    sources+=sorted((ROOT/'research/prototypes').glob(f'{track}-*5.cpp'))
    report[track]={}
    for source in sources:
        with tempfile.TemporaryDirectory() as folder:
            temp=Path(folder)
            for name,path in [('main.cpp',source),('common.hpp',ROOT/f'track-{track}/common.hpp')]:
                raw=subprocess.check_output([str(TOOLS/'clang-format'),'--style=LLVM',f'--assume-filename={name}'],input=path.read_bytes())
                (temp/name).write_bytes(raw)
            (temp/'Dockerfile').write_bytes((ROOT/f'track-{track}/Dockerfile').read_bytes())
            flags=['--no-config','--no-gitignore','--no-ignore','--no-scc-ignore','--no-gitmodule','--no-cocomo','--no-size','--no-complexity','--by-file','--format','json']
            counted=json.loads(subprocess.check_output([str(TOOLS/'scc'),*flags,folder]))
            s=sum(language['Code'] for language in counted)
            report[track][source.stem]={'S':s,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'counts':counted}
            print(track,source.stem,s,flush=True)
(ROOT/'validation/continuation5-source-counts.json').write_text(json.dumps({'tools':{'scc':'4.1.0','clang-format':'23.1.3'},'scope':'Canonical C++ and header formatting plus Dockerfile; byte-identical organizer references excluded; D=1 unchanged','tracks':report},indent=2)+'\n')
