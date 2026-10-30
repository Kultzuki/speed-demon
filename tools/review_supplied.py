"""Preserve and validate the four supplied Rust candidates without promoting."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
ATTACHMENTS={
    'b':'cfccd0d3-db62-4d89-96ed-7902b0dc24dc',
    'a':'3558bfa3-a036-4f68-ba60-5217c17461b3',
    'c':'523ae1f8-50da-416d-bac3-b3d31473ec97',
    'd':'d90b52e8-5682-4db9-a85a-1ba6e1b6d8f0',
}

def main():
    sources=ROOT/'research/supplied'
    binaries=ROOT/'build/supplied-rust'
    sources.mkdir(exist_ok=True)
    binaries.mkdir(parents=True,exist_ok=True)
    report={'environment':'Windows native Rust; correctness only, timings not comparable to Linux C++ trials','builds':{},'checks':[]}
    report['compiler']=subprocess.check_output(['rustc','--version'],text=True).strip()
    for track,attachment in ATTACHMENTS.items():
        data=(Path.home()/'.codex/attachments'/attachment/'Pasted text.txt').read_bytes()
        source=sources/f'track-{track}.rs'
        source.write_bytes(data)
        binary=binaries/f'track-{track}.exe'
        completed=subprocess.run(['rustc','--edition=2021','-C','opt-level=3',str(source),'-o',str(binary)],capture_output=True,text=True)
        report['builds'][track]={'source_sha256':hashlib.sha256(data).hexdigest(),'ok':completed.returncode==0,'stderr':completed.stderr}
        print(f'BUILD {track}: {completed.returncode}\n{completed.stderr}',flush=True)
    manifest=json.loads((ROOT/'.competition/SHA256SUMS.json').read_text(encoding='utf-8-sig'))['tracks']
    def check(track,label,data,expected_hash=None,expected_text=None):
        out=ROOT/'.out/supplied-rust'/track/label
        out.mkdir(parents=True,exist_ok=True)
        env=dict(os.environ,DATA_DIR=str(data),OUT_DIR=str(out))
        start=time.perf_counter()
        try:
            completed=subprocess.run([str(binaries/f'track-{track}.exe'),'--data',str(data),'--out',str(out)],env=env,capture_output=True,text=True,timeout=100)
            output=out/manifest[track]['output']
            actual=hashlib.sha256(output.read_bytes()).hexdigest() if output.is_file() else None
            text=output.read_text() if output.is_file() and expected_text is not None else None
            entry={'track':track,'case':label,'returncode':completed.returncode,'sha256':actual,'expected_sha256':expected_hash,
                   'ok':completed.returncode==0 and (actual==expected_hash if expected_hash else text==expected_text),'stderr':completed.stderr}
            if expected_text is not None:entry.update(actual_text=text,expected_text=expected_text)
        except subprocess.TimeoutExpired:
            entry={'track':track,'case':label,'ok':False,'error':'timeout'}
        entry['wall_s']=time.perf_counter()-start
        report['checks'].append(entry)
        print(json.dumps(entry),flush=True)
    data=ROOT/'data/b/supplied-phrase-1024'
    data.mkdir(parents=True,exist_ok=True)
    (data/'docs.txt').write_bytes(('0\t'+'writ of habeas corpus '*256+'bail bond\n').encode('ascii'))
    (data/'queries.txt').write_bytes(b'PHRASE "bail bond"\nBOOL bail AND bond\n')
    check('b','phrase-after-token1024',data,expected_text='1 0 0\n1 0 0\n')
    for track in 'abcd':
        if report['builds'][track]['ok']:
            check(track,'full-seed1',ROOT/f'data/{track}/full-seed1',expected_hash=manifest[track]['expected_output_sha256'][0])
    target=ROOT/'validation/supplied-rust-review.json'
    target.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Report: {target}',flush=True)

if __name__=='__main__':
    main()
