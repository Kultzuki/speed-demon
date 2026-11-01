"""Stage a B-only follow-up while preserving the previous measured selection."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument('--prototype', required=True)
ap.add_argument('--name', required=True)
args = ap.parse_args()
selection_path = ROOT / 'research/trackb9-selection.json'
previous = json.loads(selection_path.read_text())
active = ROOT / 'track-b/main.cpp'
assert hashlib.sha256(active.read_bytes()).hexdigest() == previous['selected_sha256']
archive = ROOT / '.out' / args.name
archive.mkdir(exist_ok=False)
(archive / 'prior-main.cpp').write_bytes(active.read_bytes())
(archive / 'prior-selection.json').write_bytes(selection_path.read_bytes())
source = (ROOT / args.prototype).read_text()
source = source.replace('// Two independent multiplies; almost every token fits in the first two words.',
    '// Hardware CRC32C fingerprints a key; complete byte equality resolves collisions.')
source = source.replace('// text 8 bytes at a time:', '// text 32 bytes at a time:')
source = source.replace('''// An append-only list of 24-bit entries kept in blocks mapped straight from
// the kernel (pages count only once written). drain() unmaps each block as soon
// as it has been read, so the memory really goes back; malloc would keep it.''',
    '''// Lossless term/document-gap words with an explicit absolute-document
// escape. The checked wide-document path stores full 32-bit offsets.
// Anonymous blocks return their physical pages as they drain.''')
source = source.replace('// The scan files each posting under a bucket of 512 consecutive term ids, as\n// the term\'s offset in the bucket (9 bits) above the doc\'s offset in the',
    '// The scan files postings in buckets of consecutive term ids, with the\n// term offset above the document offset in the logical replay value. The')
active.write_text(source, newline='\n')
selection = dict(previous)
selection.update({'phase': args.name, 'prior_selection': str((archive / 'prior-selection.json').relative_to(ROOT)),
    'selected_prototype': args.prototype,
    'selected_sha256': hashlib.sha256(active.read_bytes()).hexdigest(),
    'official_status': 'Follow-up staged; exact local production gates and official measurement pending.'})
selection_path.write_text(json.dumps(selection, indent=2) + '\n')
print('Staged B follow-up only:', args.name)
