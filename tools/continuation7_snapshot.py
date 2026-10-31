"""Archive the incoming dirty checkout without changing it."""
import hashlib
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / '.out/continuation7-incoming'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    DEST.mkdir(parents=True, exist_ok=False)
    status = git('status', '--short', '--branch')
    (DEST / 'status.txt').write_bytes(status)
    (DEST / 'diff.patch').write_bytes(git('diff', '--binary'))
    names = git('ls-files', '--modified', '--others', '--exclude-standard', '-z')
    records = []
    for raw in names.split(b'\0'):
        if not raw:
            continue
        name = raw.decode('utf-8')
        source = ROOT / name
        if not source.is_file():
            records.append({'path': name, 'missing': True})
            continue
        data = source.read_bytes()
        target = DEST / 'files' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        records.append({'path': name, 'bytes': len(data),
                        'sha256': hashlib.sha256(data).hexdigest()})
    summary = {'captured_at': datetime.now(timezone.utc).isoformat(),
               'head': git('rev-parse', 'HEAD').decode().strip(),
               'branch': git('branch', '--show-current').decode().strip(),
               'files': records}
    (DEST / 'manifest.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'archive': str(DEST), 'head': summary['head'],
                      'file_count': len(records)}, indent=2))


if __name__ == '__main__':
    main()
