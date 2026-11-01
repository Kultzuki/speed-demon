"""Stage the exact, already gated six-builder source without touching other tracks."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
subprocess.run(['python', str(ROOT / 'tools/trackb9_record_scatter.py')], check=True)
active = ROOT / 'track-b/main.cpp'
selection_path = ROOT / 'research/trackb9-selection.json'
selection = json.loads(selection_path.read_text())
assert hashlib.sha256(active.read_bytes()).hexdigest() == selection['selected_sha256']
archive = ROOT / '.out/trackb9-sixbuilders-submit'
archive.mkdir(exist_ok=False)
(archive / 'prior-main.cpp').write_bytes(active.read_bytes())
(archive / 'prior-selection.json').write_bytes(selection_path.read_bytes())
source = (ROOT / 'build/trackb9-pgo-six/main.cpp').read_bytes()
source_hash = hashlib.sha256(source).hexdigest()
for mode in ['release', 'sanitized']:
    gate = json.loads((ROOT / f'validation/trackb9-sixbuilders-{mode}.json').read_text())
    assert gate['source_sha256'] == source_hash
    assert len(gate['results']) == 36
assert source_hash == '3f46f14d979cbefbe87442da5834be325bb654526503d0078f0d220cb42f3a6b'
active.write_bytes(source)
selection.update({'phase': 'trackb9-sixbuilders', 'selected_prototype': 'research/prototypes/trackb9-doc16-6-hybrid-owner2.cpp',
    'selected_sha256': source_hash, 'prior_selection': archive.relative_to(ROOT).as_posix() + '/prior-selection.json',
    'official_status': '36 release and 36 ASan/UBSan comparisons passed; offline image and official measurement pending.'})
selection_path.write_text(json.dumps(selection, indent=2) + '\n')
readme = ROOT / 'track-b/README.md'
text = readme.read_text().replace('with up to twelve workers.', 'with up to six index builders and twelve query workers.')
text = text.replace('A checked 15-bit local stream', 'A checked 16-bit local stream').replace('32,768 documents.', '65,536 documents.')
text = text.replace('Profile on the scoring CPU, test full 16-bit local domains with fewer builders,\nand train compiler profiles only on organizer-generator output.',
    'Profile on the scoring CPU and train compiler profiles only on\norganizer-generator output. Continue measuring exact phrase verification.')
readme.write_text(text)
entry = '''

## Six-builder trial: full uint16 document domains

The next candidate uses six index builders and twelve query workers. Its
logical replay packet uses all sixteen local-document bits; worker domains
larger than 65,536 documents still dispatch to the exact uint32 path. The
12-bit term / 4-bit gap physical stream and balanced scatter remain unchanged.
Six builders lower CPU work on local AMD tests, but wall-time gains are not
consistent. The official CPU has six physical cores: this is an architecture
hypothesis pending official measurement, not an assured gain.

Exact source SHA-256: 3f46f14d979cbefbe87442da5834be325bb654526503d0078f0d220cb42f3a6b.
Release and ASan/UBSan each pass all 36 comparisons, both full seeds, the
65,536/65,537-worker-domain fixtures and forced uint64 text offsets. Both direct
programs pass 4,096 token alignments, real CRC collision identity, dictionary
growth, cross-block escapes and uint32_max replay. Evidence:
validation/trackb9-sixbuilders-{release,sanitized,direct}.json.
The promotion baseline is official K=21.581336 / 66.703917 points at 3f527c9.
'''
for name in ['track-b/PERF.md', 'research/CONTINUATION9_TRACK_B.md']:
    path = ROOT / name
    assert '## Six-builder trial: full uint16 document domains' not in path.read_text()
    with path.open('a') as stream: stream.write(entry)
print('Staged exact gated source', source_hash)
