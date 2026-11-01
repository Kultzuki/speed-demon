"""Stage only the measured Track B candidate, preserving all incoming work."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
prototype = ROOT / 'research/prototypes/trackb9-gapstream18.cpp'
source = prototype.read_text()
source = source.replace('// Two independent multiplies; almost every token fits in the first two words.',
    '// Hardware CRC32C fingerprints the complete padded key; equality still\n// compares all 32 bytes, including keys with identical CRC fingerprints.')
source = source.replace('''// An append-only list of 24-bit entries kept in blocks mapped straight from
// the kernel (pages count only once written). drain() unmaps each block as soon
// as it has been read, so the memory really goes back; malloc would keep it.''',
    '''// An append-only stream of (9-bit term, document) pairs. The narrow path
// stores a 7-bit document delta beside the term in 16 bits, escaping larger
// gaps with an absolute document word. The wide path keeps full 32-bit ids.
// Anonymous blocks are released as they drain, returning their real pages.''')
source = source.replace('''// text 8 bytes at a time: token bytes are all [A-Za-z0-9], so OR-ing 0x20
// lowercases letters and leaves digits alone.''',
    '''// text 32 bytes at a time: token bytes are all [A-Za-z0-9], so OR-ing 0x20
// lowercases letters and leaves digits alone.''')
(ROOT / 'track-b/main.cpp').write_text(source, newline='\n')
selection = {'scope': 'Track B only; local measurements are not official scores.',
    'incoming_commit': '6b71e02218f87a492f41aad0b6ea304c0e6cb172',
    'selected_prototype': prototype.relative_to(ROOT).as_posix(),
    'selected_sha256': hashlib.sha256((ROOT / 'track-b/main.cpp').read_bytes()).hexdigest(),
    'incoming_b_source_sha256': hashlib.sha256((ROOT / '.out/trackb9-incoming/baseline-b/main.cpp').read_bytes()).hexdigest(),
    'other_runtime_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for track in 'acd' for p in (ROOT / f'track-{track}').iterdir() if p.name in
        ['main.cpp', 'common.hpp', 'Dockerfile', '.speed-demon.toml']},
    'evidence': ['research/results/trackb9-finalist-public.json',
                 'research/results/trackb9-gap-fourteenth.json',
                 'research/results/trackb9-finalist-fresh.json'],
    'hypothesis': 'AVX2 paired token boundaries and masked keys reduce scanning work; lossless 16-bit gap streams reduce temporary memory. Preserve exact equality and both width dispatches.',
    'official_status': 'Not submitted; production release/sanitizer/sandbox gates pending.'}
(ROOT / 'research/trackb9-selection.json').write_text(json.dumps(selection, indent=2) + '\n')
print('Staged Track B only; all other runtime files hash-recorded and preserved.')
