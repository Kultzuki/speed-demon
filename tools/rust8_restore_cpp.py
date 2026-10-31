"""Reject officially lower Rust coefficients and restore exact established C++ sources."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
selection_path = ROOT / 'research/rust8-selection.json'
selection = json.loads(selection_path.read_text())
assert not selection.get('retained'), 'One-shot restoration already recorded'
summaries = [json.loads((ROOT / f'validation/rust8-{name}-official-summary.json').read_text()) for name in ['candidate', 'repeat']]
assert all(all(r['ok'] and all(r['gates'].values()) for r in s['latest'].values()) for s in summaries)
retained = {}
for track in 'ad':
    runs = [s['latest'][track] for s in summaries]
    assert max(r['K'] for r in runs) < runs[0]['historical_best_K_at_start']
    folder = ROOT / f'track-{track}'; rust = ROOT / f'research/rust8-validated/track-{track}'
    for file in ['main.rs', 'common.rs', 'Cargo.toml', 'Cargo.lock']:
        assert digest(folder / file) == digest(rust / file), (track, file)
        (folder / file).unlink()
    for file in ['main.cpp', 'common.hpp', 'Dockerfile', '.speed-demon.toml']:
        shutil.copy2(ROOT / f'research/baseline8/track-{track}/{file}', folder / file)
        assert (folder / file).read_text().encode() == subprocess.check_output(
            ['git', 'show', f'e9deec07fa38f9abf0c167d6768c41c388e37ba5:track-{track}/{file}'], cwd=ROOT)
    old_readme = subprocess.check_output(['git', 'show', f'e9deec07fa38f9abf0c167d6768c41c388e37ba5:track-{track}/README.md'], cwd=ROOT)
    (folder / 'README.md').write_bytes(old_readme + b'\n\nThe validated continuation-8 Rust version is preserved independently in\n'
        + f'../research/rust8-validated/track-{track}/. Both official Rust runs pass every gate,\n'.encode()
        + b'but neither exceeds the established best coefficient, so the stronger C++\nentry is retained. See ../research/CONTINUATION8_RUST.md for complete evidence.\n')
    retained[track] = {'language': 'C++', 'sources': {f: digest(folder / f) for f in ['main.cpp', 'common.hpp']},
        'S': {'a': 310, 'd': 385}[track], 'D': 1, 'restored_from': 'e9deec07fa38f9abf0c167d6768c41c388e37ba5',
        'rust_best_K': max(r['K'] for r in runs), 'established_best_K': runs[0]['historical_best_K_at_start'],
        'rust_archive': f'research/rust8-validated/track-{track}'}
    path = folder / 'PERF.md'
    path.write_text(path.read_text() + f'\n\n## Rust continuation 8 retention decision\n\n'
        f'Both Rust official runs pass every gate. Best Rust K={retained[track]["rust_best_K"]:.6f} '
        f'does not exceed the established {retained[track]["established_best_K"]:.6f}. '
        'The exact stronger incoming C++ kernel is restored, following the coefficient-regression rule. '
        'The requested complete Rust implementation, Cargo/Docker builds, validation, corrected source counts '
        'and both official records remain in research/rust8-validated and validation/. '
        'No reset, force-push, registration change or evidence deletion was used.\n')
selection['retained'] = retained
selection['status'] = 'Rust A/D officially validated but not promoted; exact stronger C++ A/D restored; final mixed gates and official run pending'
selection['history'].append({'at': datetime.now(timezone.utc).isoformat(), 'status': selection['status']})
selection_path.write_text(json.dumps(selection, indent=2) + '\n')
path = ROOT / 'README.md'; text = path.read_text()
text = text.replace('Rust implementations for **A/D** and C++20 for **B/C**.', 'C++20 implementations for **all four submitted tracks**. Validated Rust A/D alternatives are preserved under `research/rust8-validated/`.')
text = text.replace('Buffered parallel reads, owned exact endpoint registry, packed hour records', 'Exact shared endpoint registry, packed hour records')
text = text.replace('separate uint64 distances and width-derived node/generation tags', 'generation-tagged sparse uint64 distances')
path.write_text(text)
path = ROOT / 'research/CONTINUATION8_RUST.md'
path.write_text(path.read_text() + '''

## Official retention decision

Both full Rust implementations pass all five official gates at 0ca1987 and the
source-identical 8aa8ddb. Best Rust A K=31.161629 is below the established
33.234541; best Rust D K=14.542976 is below 15.399979, and its unchanged rerun
falls to 12.536262. Local coefficient gains did not establish an official best.
Under the explicit regression rule, both submitted A/D kernels are restored
exactly to the incoming C++ sources. No rollback/reset/force-push is used.

The requested Rust work is complete and retained as independently buildable
packages in research/rust8-validated/track-{a,d}, with all release/ASan/checked
artifacts, original user work, source-counter erratum and official evidence.
Those are research alternatives, not the active submitted entry after restoration.

C's new best K=24.531325 and aggregate 69.811783 at 8aa8ddb come from unchanged
C++ source; they are rerun variation, not a Rust or C algorithm improvement.
Final restored-source gates, offline identities and official reconciliation follow.
''')
print('Restored exact stronger C++ A/D. Full validated Rust packages and all evidence remain intact.')
