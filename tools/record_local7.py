"""Record only completed gates and exact selected-source local evidence."""
import hashlib
import json
import statistics
from pathlib import Path

from bench7 import source_size

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


public = {'a': ('a-pgo-confirm7', 'incoming-a7'), 'b': ('b-posting-blocks7', 'block16-b7'),
          'c': ('c-pgo-confirm7', 'incoming-exit-c7'), 'd': ('d-heap-layout7', 'compact-shards-d7')}
fresh = {'a': ('a-pgo-fresh7', 'incoming-a7'), 'b': ('b-block16-fresh7', 'block16-b7'),
         'c': ('c-ring-fresh7', 'incoming-exit-c7'), 'd': ('d-compact-fresh7', 'compact-shards-d7')}
notes = {
    'a': 'Retain the incoming first/last-eight-byte plus length hash, with complete endpoint equality. No prefault, reservation or PGO is selected.',
    'b': 'Increase lazy packed posting blocks from 4096 to 65536 entries. Exact term/phrase semantics, adaptive postings and both document/offset width fallbacks are unchanged.',
    'c': 'Use the incoming exact first/last-byte hash and four-record ring, and call _exit(0) only after write_output has checked and closed the output. Decoded scratch lifetimes, growing owned names and atomic membership remain exact.',
    'd': 'Parse graph text once, encode normal temporary edges in eight bytes, and index a growing exact per-worker stream for all wider weights. Bucket each direction into 64 node ranges whose owners count/prefix/scatter without shared atomic cursors. Final CSR, full uint64 labels and balanced bidirectional radix search are retained.'}
profiles = {'a': ('a-lifetime-prefault7', 'profile-a7'), 'b': ('b-index-keys7', 'profile-b7'),
            'c': ('c-lifetime-ring7', 'profile-c7'), 'd': ('d-lifetime-workers7', 'profile-d7')}

selection = read('research/continuation7-selection.json')
images = read('validation/image-sizes-continuation7.json')
provenance = {'scope': 'Selected actual sources; all local checks completed before official measurement.',
              'tracks': {}, 'gates': {}}
for mode in ['release', 'sanitized']:
    name = 'continuation7-' + mode
    counts = {suffix: len(read(f'validation/{name}{suffix}.json')['results'])
              for suffix in ['', '-full', '-extra', '-additional', '-new']}
    assert sum(counts.values()) == 93, counts
    provenance['gates'][mode] = counts
    builds = read(f'validation/{name}-build.json')
    for track in 'abcd':
        assert builds[track]['source_sha256'] == sha(f'track-{track}/main.cpp')
        assert builds[track]['binary_sha256'] == sha(f'build/{name}/track-{track}')
        if mode == 'release':
            assert images[track]['solution_sha256'] == builds[track]['binary_sha256'], track
            assert images[track]['size_bytes'] < 2 * 1024**3
            assert builds[track]['source_sha256'] == selection['selected'][track]['selected_sha256']
            size = source_size(track, f'track-{track}/main.cpp')
            assert size == selection['selected'][track]['S'], (track, size)
            provenance['tracks'][track] = {**builds[track], **images[track], 'S': size, 'D': 1,
                'Dockerfile_sha256': sha(f'track-{track}/Dockerfile'),
                'manifest_sha256': sha(f'track-{track}/.speed-demon.toml'),
                'source_lf_sha256': hashlib.sha256((ROOT / f'track-{track}/main.cpp').read_text().encode()).hexdigest()}
path = ROOT / 'validation/continuation7-artifact-provenance.json'
assert not path.exists()
path.write_text(json.dumps(provenance, indent=2) + '\n')

table = []
for track in 'abcd':
    local = []
    for label, mapping in [('public', public), ('fresh', fresh)]:
        report, candidate = mapping[track]
        result = read(f'research/results/{report}.json')
        base = next(iter(result['entries'].values()))
        chosen = result['entries'][candidate]
        local.append(f'{label}: T={base["T_s"]:.6f}->{chosen["T_s"]:.6f}s, '
                     f'M={int(base["M_bytes"])}->{int(chosen["M_bytes"])} bytes, '
                     f'S={base["S"]}->{chosen["S"]}, D=1; local K ratio {chosen["local_K_ratio"]:.6f} '
                     f'(`research/results/{report}.json`).')
        table.append(f'| {track.upper()} | {label} | {base["T_s"]:.6f} | {chosen["T_s"]:.6f} | '
                     f'{int(chosen["M_bytes"])} | {chosen["S"]} | {chosen["local_K_ratio"]:.6f} |')
    perf = ROOT / f'track-{track}/PERF.md'
    text = perf.read_text()
    marker = '## Continuation 7: selected local candidate'
    assert marker not in text
    text += '\n\n' + marker + '\n\n' + notes[track] + '\n\n' + '\n\n'.join(local) + '\n\n'
    profile_report, profile_label = profiles[track]
    phases = {}
    for run in read(f'research/results/{profile_report}.json')['entries'][profile_label]['raw']:
        for line in run['stderr'].splitlines():
            if line.startswith('PHASE '):
                _, phase, value = line.split()
                phases.setdefault(phase, []).append(float(value))
    text += ('Checkpoint phase medians from the separate instrumented source: '
             + ', '.join(f'{phase}={statistics.median(values)*1000:.3f} ms' for phase, values in phases.items())
             + f'. Raw stderr is in research/results/{profile_report}.json. '
               'These diagnostic intervals omit parts of process startup/cleanup and must not be added to invent an official time.\n\n')
    text += ('These are alternating hot-data local WSL2 measurements with fresh cgroups, including process exit; '
             'they are not official scores. Short A/C repeats vary materially, and the gain is not a stable '
             'percentage across every batch. Every measured output hash matches.\n\n'
             'The frozen combination passes 93 release and 93 ASan/UBSan dataset comparisons, both full seeds, '
             'the existing direct guard/publication/boundary/membership/state checks, and two new independent '
             'checks of all 200,000 forward/reverse CSR edges. Forced uint64 B offsets pass the full hash. '
             'All four rebuilt offline images pass the unprivileged read-only/no-network starter sandbox '
             'and their executables match the validated release binaries exactly. Exact source/common/compiler/'
             'binary/image identities are in validation/continuation7-artifact-provenance.json. '
             'Official retention remains pending.\n')
    perf.write_text(text)

report = ROOT / 'research/CONTINUATION7.md'
text = report.read_text()
text += '''

## Frozen finalists and repeated full-seed comparison

The selected A is the incoming exact partial-byte hash without PGO. B changes
only the lazy posting block capacity. C combines the incoming exact hash and
four-record ring with checked-close early exit. D selects compact owner-sharded
CSR construction; its heap and full-width sparse labels remain unchanged.

| Track | Full seed | Baseline T s | Candidate T s | Candidate cgroup M | S | Local K ratio |
|---|---|---:|---:|---:|---:|---:|
''' + '\n'.join(table) + '''

A/C effects vary across repeat batches; these rows do not establish a stable
gain of that size on the official machine. For example, A's first public batch
was 1.0650 while the later batch was 1.0129. C's incoming hash without exit lost
one public batch (0.9616), and the selected combination ranged from 1.0127 to
1.0511 in the two public batches. Official measurements decide retention.

The simpler 12-byte D heap entries lose, including with the new CSR. Separate
C membership storage also loses. Larger B blocks improve both full seeds;
65,536 entries beat 16,384 and 262,144 on the combined local coefficient.
SIMD B keys and exclusive bitmap words show only small gains and are unselected.

Generator-only PGO was actually tested for A and C using unmodified generators,
sample seeds 197731 and 806317, with no scoring-data training. It is not selected:
A's PGO is faster on the public seed but loses to the simpler hash on the fresh
full seed (0.069123 versus 0.062025 s), while C's additional gain is small and
unstable after build/source cost. Training hashes and binary provenance are in
validation/pgo7-{a,c}-training.json; no PGO generator/build step enters a track.

All selected sources pass 93 release and 93 ASan/UBSan comparisons: the previous
89 plus deliberate A/C partial-hash collisions and two >2 MB parallel D cases
with many wide weights, duplicate edges, zero edges and shard-boundary nodes.
An independent iostream-based test checks every forward/reverse CSR edge and
its multiplicity in both 200,000-edge cases. All prior direct tests and forced
uint64 B offsets also pass. Rebuilt offline sandbox images match validated
release executable hashes exactly. See validation/continuation7-artifact-provenance.json.

The same independently referenced full seed was copied, never regenerated,
into /data/fresh7 in the existing benchmark volume. Every copied input hash
matches its original. The new helper is stopped; no original dataset or volume
was deleted. Official measurement of this candidate bundle is the next step.
'''
report.write_text(text)
print('PASS exact sources, 93+93 gates, canonical source counts, image/binary agreement and local evidence.')
