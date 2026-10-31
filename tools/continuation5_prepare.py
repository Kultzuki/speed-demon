"""Preserve the incoming dirty checkpoint and both new attachment sets once."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from review_supplied_second import ADAPTER

ROOT = Path(__file__).resolve().parents[1]
SETS = {
    'fifth': dict(zip('dcba', [
        '3543610f-a653-4ba5-870c-978d30c55934',
        '916ef1a4-a4a6-4d13-a763-80ccf556e9d7',
        '02d67f4b-96eb-4da7-91a4-7002a227365f',
        '393af749-cc45-4619-88b5-7977f2babdde'])),
    'sixth': dict(zip('dcba', [
        '35f01562-8642-4d6a-b5b9-1cf35c437a60',
        'dc1b6a70-1705-47d2-b5a5-2c2b69ddef5b',
        'b8d6a87c-1204-4240-82dd-0fdcad3d4c39',
        'c6ddf466-67b1-4f75-9996-d3e6799f56fd'])),
}

def main():
    backup = ROOT / '.out/continuation5-incoming'
    backup.mkdir(parents=True, exist_ok=False)
    status = subprocess.check_output(['git', 'status', '--porcelain=v1', '-z'], cwd=ROOT)
    (backup / 'status.z').write_bytes(status)
    (backup / 'diff.patch').write_bytes(subprocess.check_output(['git', 'diff', '--binary'], cwd=ROOT))
    saved = {}
    for item in status.decode().split('\0'):
        if not item:
            continue
        rel = item[3:]
        path = ROOT / rel
        if not path.is_file():
            continue
        dest = backup / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        saved[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    (backup / 'sha256.json').write_text(json.dumps(saved, indent=2) + '\n')
    records = {}
    for batch, entries in SETS.items():
        folder = ROOT / f'research/supplied-{batch}'
        folder.mkdir(exist_ok=False)
        for track, attachment in entries.items():
            ext = 'c' if (batch, track) == ('sixth', 'd') else 'cpp'
            original = Path.home() / '.codex/attachments' / attachment / 'Pasted text.txt'
            raw = original.read_bytes()
            (folder / f'track-{track}.{ext}').write_bytes(raw)
            source = raw.decode('utf-8-sig')
            # Add only command-line data/output path selection for research.
            pattern = r'int main\((?:void)?\)\s*\{'
            assert len(re.findall(pattern, source)) == 1, (batch, track)
            source = re.sub(pattern, lambda _: ADAPTER + '\nint main(int argc,char** argv) {\n review_paths(argc,argv);', source)
            source = re.sub(r'"/data/([^"\n]+)"', r'review_location("\1",0)', source)
            source = re.sub(r'"/out/([^"\n]+)"', r'review_location("\1",1)', source)
            adapted = ROOT / f'research/prototypes/supplied-{batch}-{track}.{ext}'
            adapted.write_text(source, encoding='utf-8', newline='\n')
            records[f'{batch}-{track}'] = {'attachment': str(original), 'original_sha256': hashlib.sha256(raw).hexdigest(),
                                          'adapter_sha256': hashlib.sha256(adapted.read_bytes()).hexdigest()}
    (ROOT / 'validation/supplied-continuation5-provenance.json').write_text(json.dumps(records, indent=2) + '\n')
    for track in 'abcd':
        shutil.copyfile(ROOT / f'track-{track}/main.cpp', ROOT / f'research/prototypes/continuation5-start-{track}.cpp')
    print('Saved incoming dirty files byte-for-byte; preserved both attachment sets in D/C/B/A order.')

if __name__ == '__main__':
    main()
