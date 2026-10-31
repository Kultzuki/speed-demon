"""Preserve raw reports and add the official TOML-exempt canonical S calculation."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.competition/official/harness'))
import static_axes

def read(path): return json.loads(path.read_text())
def write(path, data):
    with path.open('x') as stream: json.dump(data, stream, indent=2); stream.write('\n')

correction = {'captured_at': datetime.now(timezone.utc).isoformat(),
    'reason': 'The original local counter summed TOML manifests. Official static_axes.NOT_CODE exempts TOML/data. '
              'No executable, timing, memory observation or original report was changed.', 'reports': {}}
for path in sorted((ROOT / 'validation').glob('rust8-*-static.json')):
    original = read(path)
    rows = {}
    for track, entry in original.items():
        counts = entry['canonical_counts']
        actual = sum(g['Code'] for g in counts if g['Name'] not in static_axes.NOT_CODE)
        rows[track] = {'original_S': entry['S'], 'canonical_S': actual,
                       'excluded_data': {g['Name']: g['Code'] for g in counts if g['Name'] in static_axes.NOT_CODE}}
    correction['reports'][path.name] = rows
write(ROOT / 'validation/rust8-canonical-source-correction.json', correction)

final = read(ROOT / 'validation/rust8-final-static.json')
for track, entry in final.items():
    entry['initial_counter_S_including_TOML'] = entry['S']
    entry['S'] = correction['reports']['rust8-final-static.json'][track]['canonical_S']
    entry['correction'] = 'rust8-canonical-source-correction.json'
write(ROOT / 'validation/rust8-final-static-corrected.json', final)
provenance = read(ROOT / 'validation/rust8-final-artifact-provenance.json')
for track in 'ad':
    provenance['tracks'][track]['initial_counter_S_including_TOML'] = provenance['tracks'][track]['S']
    provenance['tracks'][track]['S'] = final[track]['S']
provenance['source_counter_correction'] = 'validation/rust8-canonical-source-correction.json'
write(ROOT / 'validation/rust8-final-artifact-provenance-corrected.json', provenance)

comparisons = {}
for track, stem, label in [('a', 'a-rust8-scalar', 'a-rust8-scalar-release'),
                           ('d', 'd-rust8-finalist', 'd-simple8')]:
    for seed in ['public', 'fresh']:
        name = f'{stem}-{seed}'
        report = deepcopy(read(ROOT / f'research/results/{name}.json'))
        base = report['entries'][f'{track}-cpp8']
        trial = report['entries'][label]
        original_s = trial['S']; trial['S'] = final[track]['S']
        trial['initial_counter_S_including_TOML'] = original_s
        ratio = ((base['T_s'] / trial['T_s']) ** .5 * (base['M_bytes'] / trial['M_bytes']) ** .2
                 * (base['S'] / trial['S']) ** .15)
        trial['initial_local_K_ratio'] = trial['local_K_ratio']; trial['local_K_ratio'] = ratio
        comparisons[name] = {'track': track, 'seed': seed, 'source_report': f'research/results/{name}.json',
            'candidate': label, 'T_s': trial['T_s'], 'M_bytes': trial['M_bytes'], 'S': trial['S'], 'D': 1,
            'baseline': {k: base[k] for k in ['T_s', 'M_bytes', 'S', 'D']}, 'local_K_ratio': ratio,
            'initial_local_K_ratio': trial['initial_local_K_ratio']}
write(ROOT / 'research/results/rust8-corrected-selected-coefficients.json', comparisons)

path = ROOT / 'research/rust8-selection.json'
selection = read(path)
for track in 'ad':
    selection['selected'][track]['initial_counter_S_including_TOML'] = selection['selected'][track]['S']
    selection['selected'][track]['S'] = final[track]['S']
selection['history'].append({'at': correction['captured_at'], 'status': 'Source counter corrected to exclude TOML; kernels unchanged; official build in progress'})
selection['source_counter_correction'] = 'validation/rust8-canonical-source-correction.json'
path.write_text(json.dumps(selection, indent=2) + '\n')

report = ROOT / 'research/CONTINUATION8_RUST.md'
report.write_text(report.read_text() + '''

## Canonical source-counter correction during official build

The initial local Rust counter mistakenly included TOML manifest code lines.
The organizer's static_axes.NOT_CODE excludes TOML/data. The actual canonical
totals are **A=437, D=473**, both D=1, rather than the conservative 449/485
shown in the original pre-push reports. Those raw reports, timings, memory and
source hashes are retained verbatim. Only the coefficient calculation changes.
Corrected evidence: validation/rust8-canonical-source-correction.json,
validation/rust8-final-static-corrected.json and
validation/rust8-final-artifact-provenance-corrected.json. No kernel or binary
changed. Corrected selected local coefficients are
research/results/rust8-corrected-selected-coefficients.json.
''')
for key, row in comparisons.items(): print(key, row['S'], row['local_K_ratio'])
