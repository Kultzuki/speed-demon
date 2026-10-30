"""Compile actual production sources and run the complete refinement gate."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import validate

ROOT=validate.ROOT

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--sanitized',action='store_true')
    parser.add_argument('--extra-only',action='store_true')
    args=parser.parse_args()
    name='refined-sanitized' if args.sanitized else 'refined-release'
    output=ROOT/'build'/name
    output.mkdir(parents=True,exist_ok=True)
    provenance={}
    base=['-std=c++20','-pthread']
    base+=['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'] if args.sanitized else ['-O3','-DNDEBUG','-static','-s']
    flags_by_track={}
    for track in 'abcd':
        source=ROOT/f'track-{track}/main.cpp'
        flags=base+(['-march=x86-64-v3'] if '-march=x86-64-v3' in (ROOT/f'track-{track}/Dockerfile').read_text() else [])
        flags_by_track[track]=flags
        binary=output/f'track-{track}'
        subprocess.run(['g++',*flags,'-I',str(source.parent),str(source),'-o',str(binary)],check=True)
        provenance[track]={'source_sha256':validate.digest(source),'common_sha256':validate.digest(source.parent/'common.hpp'),
                           'binary_sha256':validate.digest(binary),'flags':flags}
    (ROOT/f'validation/{name}-build.json').write_text(json.dumps(provenance,indent=2)+'\n')
    command=[sys.executable,str(ROOT/'tools/validate.py'),'--binary-dir',str(output),'--reuse-generated','--fresh']
    if not args.extra_only:
        subprocess.run(command+['--report',str(ROOT/f'validation/{name}.json')],check=True)
        subprocess.run(command+['--full','--report',str(ROOT/f'validation/{name}-full.json')],check=True)
    units=[] if args.extra_only else [('c','c-boundaries.cpp'),('c','c-concurrent-names.cpp'),('d','d-sparse-state.cpp')]
    for track,file in units:
        binary=output/file.removesuffix('.cpp')
        flags=flags_by_track[track]
        source=ROOT/f'research/tests/{file}'
        subprocess.run(['g++',*flags,f'-DCANDIDATE_SOURCE="{ROOT/f"track-{track}/main.cpp"}"','-I',str(ROOT/f'track-{track}'),str(source),'-o',str(binary)],check=True)
        subprocess.run([str(binary)]+([str(ROOT/'data/d/worked-example/graph.txt')] if track=='d' else []),check=True)
    validate.BINARY_DIR=output
    for track,label in [('b','supplied-phrase-1024'),('c','supplied-long-name')]:
        validate.check(track,label,ROOT/f'data/{track}/{label}')
    for n in [1003,65536,65537,70000]:
        data=ROOT/f'data/b/refined-block-{n}'
        data.mkdir(parents=True,exist_ok=True)
        with (data/'docs.txt').open('w') as stream:
            for i in range(n):
                words=['common']
                if i<4:words.append('four')
                if i<5:words.append('five')
                if i<(n+15)//16:words.append('promoted')
                if i in [0,65535,65536,n-1]:words+=['boundary','phrase']
                stream.write(f'{i}\t'+ ' '.join(words)+'\n')
        (data/'queries.txt').write_text('BOOL four OR five\nBOOL common NOT four OR five\nBOOL promoted AND boundary\nBOOL absent AND four OR boundary\nPHRASE "boundary phrase"\nBOOL boundary\n')
        validate.check('b',f'refined-block-{n}',data)
    # Exercise the uint64 offset instantiation even on modest physical fixtures.
    with tempfile.TemporaryDirectory() as directory:
        temp=Path(directory);source=temp/'wide.cpp';binary=temp/'wide'
        source.write_text((ROOT/'track-b/main.cpp').read_text().replace('solve<uint16_t,uint32_t>(paths)','solve<uint16_t,uint64_t>(paths)'))
        subprocess.run(['g++',*flags_by_track['b'],'-I',str(ROOT/'track-b'),str(source),'-o',str(binary)],check=True)
        target=temp/'output';target.mkdir()
        subprocess.run([str(binary),'--data','/benchdata/b','--out',str(target)],check=True)
        spec=json.loads((ROOT/'.competition/SHA256SUMS.json').read_text())['tracks']['b']
        assert validate.digest(target/'results.txt')==spec['expected_output_sha256'][0]
        print('PASS B forced uint64 offset instantiation, full public hash',flush=True)
    previous=json.loads((ROOT/'validation/fresh-full-seed20261031.json').read_text())
    for track in 'abcd':
        data=Path(f'/benchfresh/seed20261031/{track}')
        expected=next(x['sha256'] for x in previous['results'] if x['track']==track)
        for file,digest in previous['provenance'][track]['inputs_sha256'].items():
            assert validate.digest(data/file)==digest
        validate.check(track,'fresh-full-seed20261031',data,expected)
    (ROOT/f'validation/{name}-extra.json').write_text(json.dumps({'provenance':provenance,'results':validate.REPORT},indent=2)+'\n')
    print(f'PASS refinement gate {name}',flush=True)

if __name__=='__main__':
    main()
