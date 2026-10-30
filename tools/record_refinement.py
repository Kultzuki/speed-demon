"""Record completed local gates without attributing local results to the board."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/'validation'/name).read_text())
release=read('refined-release-build.json');sanitized=read('refined-sanitized-build.json')
for track in 'abcd':
    digest=hashlib.sha256((ROOT/f'track-{track}/main.cpp').read_bytes()).hexdigest()
    assert release[track]['source_sha256']==sanitized[track]['source_sha256']==digest
    assert release[track]['common_sha256']==sanitized[track]['common_sha256']
for mode in ['release','sanitized']:
    assert len(read(f'refined-{mode}.json')['results'])==69
    assert len(read(f'refined-{mode}-full.json')['results'])==4
    assert len(read(f'refined-{mode}-extra.json')['results'])==10
images=read('image-sizes-refined.json')
assert all(item['size_bytes']<2*1024**3 for item in images.values())
selection=json.loads((ROOT/'research/refinement-selection.json').read_text())
selection.update(status='release, ASan/UBSan, both full seeds and offline sandbox passed',
                 production_source_sha256={k:v['source_sha256'] for k,v in release.items()})
(ROOT/'research/refinement-selection.json').write_text(json.dumps(selection,indent=2)+'\n')
mechanisms={
'a':'''Twelve workers parse once into exact seven-byte latency/group records in
bounded pages, then count/prefix/scatter into one contiguous latency array.
An exact open-addressed endpoint map replaces per-row unordered-map lookup.
Nearest-rank selection and ordered per-hour formatting remain parallel.
The 1,842-endpoint, 72-hour and 3.1M-row specification proves the group and
cursor widths; latency retains its entire uint32 range.

Alternating full-hash-checked local runs: checkpoint 0.140581s versus selected
twelve-worker pages 0.105338s trimmed mean (`a-twelve-paired.json`). Local RSS
increased from approximately 271.9 to 281.5 MiB; only official cgroup memory can
settle the coefficient tradeoff.''',
'b':'''Sparse postings retain four uint16 block-local IDs inline, with exact dynamic
heap-list/bitmap promotion. Blocks beyond 65,536 documents use uint32 IDs.
Query lookup stores compact hash/ID slots and still checks exact token bytes.
Inline query plans respect the published 8-term phrase and 6-term boolean bounds.
Occurrence offsets are block-relative uint32 only after a span check; larger
blocks instantiate uint64 offsets. Strict boolean left folds are unchanged.

The paired compact-posting trial improved 1.147780s to 0.857186s locally. A later
batch compared 0.756912s for compact postings against 0.749726s with relative
occurrences/inline plans, at approximately 336 versus 322.7 MiB process RSS.
See `b-compact-paired.json` and `b-occurrences-paired.json`; batches must not be
combined into a precise speedup. The supplied Rust document-filter idea was
implemented with exact uncapped scanning but measured slower and was not selected.''',
'c':'''The exact decoded-name catalog now uses immutable stable nodes, acquire/release
publication, insertion locks only on misses, and atomic country-membership words
to elect exactly one distinct-count increment. Smaller arenas reduce slack.
Twelve parser workers use independently computed quote parities and a prefix
scan to find safe CSV boundaries. Escaped bytes, significant spaces, BOMs,
embedded LF and full integer-cent aggregates remain exact.

Alternating full-hash-checked local runs: checkpoint 0.210809s versus the selected
decoded-name twelve-worker candidate 0.101670s trimmed mean. RSS was approximately
207.8 versus 205.9 MiB. See `c-twelve-paired.json`. Borrowed mapped-name keys and
encoded-key variants were measured separately and did not beat this choice.''',
'd':'''Parallel two-pass CSR uses atomic degree/cursor updates and disjoint edge slots.
Node width is derived from n; compact edge words use an exact sorted overflow
entry for every weight at or beyond the inline sentinel. Bidirectional radix
Dijkstra expands the smaller frontier, preserving the frontier-minimum stopping
proof. Exact uint64 labels live in per-worker generation-tagged sparse hash
tables; wrap clears every tag. BFS ordering and its identity remap are removed.

Alternating full-hash-checked local runs: checkpoint 1.944286s versus the sparse
hash/compact-edge candidate 1.032172s trimmed mean; about 270.5 versus 152.9 MiB
RSS. See `d-hash-paired.json`. Mapped input is included in local RSS, so this is
not an official memory saving. D's high-weight reverse-frontier explosion was
also tested and addressed without narrowing weights or distances.'''
}
for track,details in mechanisms.items():
    path=ROOT/f'track-{track}/PERF.md'
    text=path.read_text()
    marker='## Refinement from 6cb3509: validated candidate'
    assert marker not in text
    text+='\n\n'+marker+'\n\n'+details+'''

Local correctness gates passed in both release and ASan/UBSan: 69 differential
cases, all four public full hashes, six added boundary/reproduction datasets,
and all four independently referenced full-seed-20261031 outputs. Three direct
C/D state/concurrency/boundary programs and the forced uint64 B offset build
also passed. Reports: `validation/refined-{release,sanitized}*.json`.
Actual production sources were compiled. Offline image rebuilds and every
full-hash read-only/no-network/unprivileged sandbox check passed, all under the
2 GB image cap. `validation/sandbox-refined.txt` and `image-sizes-refined.json`
record the image tests. No x86-64-v3 or native flag was promoted after local trials.

Official score/placement is recorded separately after the implementation push.
'''
    path.write_text(text)
print('PASS current-source provenance, all release/sanitizer reports and offline image sizes; PERF records written')
