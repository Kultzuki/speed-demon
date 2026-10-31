"""Publish reproducible local evidence and an honest pre-measurement checkpoint."""
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
backup=ROOT/'.out/continuation5-incoming/HANDOVER_NEXT.md'
archived=ROOT/'research/HANDOVER_INCOMING_2026-10-31.md'
if not archived.exists():shutil.copyfile(backup,archived)
snapshot=json.loads((ROOT/'validation/leaderboard-continuation5-start.json').read_text())
own=next(t for t in snapshot['ranking'] if t['team']=='CodeScythe')
leader=snapshot['ranking'][0]
reports=['a-hash-private5-paired','a-format5-paired','b-csr5-paired','b-twopass5-paired','c-prefetch5-paired','c-structure5-paired','c-decimal5-paired','d-window5-paired','d-forward5-paired','d-locality5-paired','d-relax-label5-paired','d-supplied-fifth5-paired','c-supplied-fifth5-paired']
rows=[]
for name in reports:
    data=json.loads((ROOT/f'research/results/{name}.json').read_text())
    for label,result in data['results'].items():rows.append(f"| {name} | {label} | {result['trimmed_mean_s']:.6f} |")
text=f'''# Continuation 5 - October 31, 2026

Continued local HEAD 12aa1a4 on the same private speed-demon branch. No reset,
force push, registration, App change or agent delegation was performed. The
incoming dirty files were saved byte for byte under .out/continuation5-incoming;
the complete incoming handover is also archived here. Prior official records,
including the rejected buffered C measurement, are preserved.

The refreshed starting feed at {snapshot['fetched_at']} gives CodeScythe
{own['aggregate']:.6f}, rank {own['rank']}, leader {leader['aggregate']:.6f}.
This is public practice scoring, not final judging or hidden-seed evidence.

## Supplied code

The handover's pending four files were preserved under supplied-fifth and
evaluated in D/C/B/A order. The four distinct attachments pasted in this chat
are supplied-sixth, also evaluated in D/C/B/A order. SHA-256 identities and
path-only adapters are recorded in validation/supplied-continuation5-provenance.json.

Both sets compile. The first 108 comparisons give 99 passes and 9 failures;
the four further collision/width comparisons add one pass and three failures.
These raw review counts are not production gate counts.

- Pending D passes both full hashes and 20 arbitrary directed multigraphs. Its
  twelve-worker count/cursor matrices and paged labels cost far more time and
  memory locally. It is rejected as a replacement.
- Pending C passes both full hashes and the long-name/EOF cases, but its fixed
  131,072-slot name table hangs on the 135,000-name growth case. There is also
  an unchecked fixed suffix arena. The parser/prefetch ideas were tested
  independently against the growing owned-name implementation.
- Pending B passes both full hashes, Unicode token separators, phrase and left
  fold cases. It exits on the real 70,001-document worker domain instead of
  widening its 15-bit stream. The derived candidate checks real ranges first,
  instantiates uint32 documents/64-bit packed entries when needed, and keeps
  checked uint64 file offsets. Complete key and phrase equality remain exact.
- Pending A passes both full hashes and tested boundaries. Its private endpoint
  tables and arenas lose paired local timings; it was not promoted wholesale.
- New D passes both full hashes and 20 arbitrary directed multigraphs. Its
  BFS/Dial/direct-array architecture remains research input, not our submission.
- New C fails both full hashes and all eight tested cases. The code stores
  signed SIMD movemasks directly in uint64, allowing sign extension in combined
  masks. This explanation is code inspection; the incorrect hashes and crashes
  themselves are reproduced. Its fixed table and arena also remain concerns.
- New B passes both full hashes, but silently truncates document offsets on the
  new skewed-width case. Its repaired two-pass layout was measured separately.
- New A passes both full hashes but merges distinct valid endpoint bytes using
  hash-only equality. A deterministic birthday search reproduced the collision:
  /crc/rpbryafunzmzlnqvybmf and /crc/hakugyqfbnehjdgljotv. The pending A and retained
  production A keep them distinct. Raw evidence is in the additional review JSON.

## Profiles and independent trials

Profiles use the actual incoming kernels and Linux-local full public input.
D spends roughly 0.29-0.33s building CSR and 0.34s searching. C spends about
0.05s parsing/interning, versus 0.005s in its region lookup. B spends about
0.37-0.51s indexing, 0.07-0.08s evaluating, and 0.04-0.05s reading/planning
queries. A is around 0.02s parsing and 0.02s selecting/formatting with occasional
large local outliers. Instrumented phases are diagnostic, not official scores.

Exact-source alternating runs below include process startup and hash verification.
Each batch is local WSL2; batches must not be mixed into an official score.
Process RSS in these files includes mapped data and is not the memory axis.

| Paired batch | Candidate | Trimmed mean seconds |
|---|---|---:|
'''+ '\n'.join(rows)+'''

The organizer-pinned scc 4.1.0 and clang-format 23.1.3 reproduce the baseline
source counts exactly: A=290, B=583, C=349, D=385. Selected trial counts are
B=922, C=379, D=391. The size tools were downloaded with the exact checksums
from the organizer Dockerfile and remain in ignored build/static-tools.

No standalone A hashing, private tables or line formatting trial justified a
promotion. Bitmap summaries, structural CSV scanning, decimal decoding, forward
D search, a window queue, BFS/paged labels and one-probe relaxation were rejected
or left unselected after their independent comparisons. A is unchanged.

## Selected candidates and gates

- B: query-only CSR, lagged exact token lookups, packed streams, adaptive exact
  list/bitmap algebra, uncapped mapped phrase verification and checked widths.
- C: restore mapped C from the stronger checkpoint and prefetch exact owned-name
  lookups in a sixteen-record pipeline. Escaped-name scratch survives retirement.
- D: retain bidirectional radix search and compact edges; represent common sparse
  labels in uint32 and use a full uint64 overflow map for the sentinel and every
  wider value. Rehash and safe epoch wrap remain exact; there is no restart.

Release and ASan/UBSan each pass 89 dataset comparisons: the previous 85 plus
real B wide-domain dispatch, D sentinel/wide distances, C escaped ring reuse and
A's hash-collision endpoints. Four direct programs cover 4,375 A guarded parses
and publication, C's 64 boundary alignments/1-12 workers and concurrent membership,
and D rehash/wrap/overflow/searches. Forced uint64 B offsets pass the full public
hash. Both full seeds are checked against independently referenced outputs.

All four current images were rebuilt offline, pass the starter sandbox, match
the exact release executable hashes and are about 119 MB. C's old buffered image
is reconciled. Compiler/source/common/binary hashes are saved in the build JSON;
image IDs and binary hashes are saved in image-sizes-continuation5.json.

Official K decides retention; local speed or RSS alone never establishes a gain.
The next section will record full local cgroup tradeoffs and official run IDs.
'''
(ROOT/'research/CONTINUATION5.md').write_text(text,encoding='utf-8',newline='\n')
for track in 'abcd':
    path=ROOT/f'track-{track}/PERF.md';prior=path.read_text();marker='## Continuation 5 local validation'
    assert marker not in prior
    prior+=f'''\n\n{marker}

See research/CONTINUATION5.md and the exact paired reports. Current production
sources pass 89 release and 89 ASan/UBSan dataset comparisons, both full seeds,
four direct programs and the forced uint64 B-offset full hash. Rebuilt offline
images pass the starter sandbox and match the release binary hashes. These are
local checks, not official coefficient gains. Official run IDs are pending.
'''
    path.write_text(prior,encoding='utf-8',newline='\n')
path=ROOT/'research/CONTINUATION3.md'
text=path.read_text().replace('Current C uses private 64 KiB pread buffers','The rejected 12aa1a4 C trial used private 64 KiB pread buffers').replace('Current A/C plus unchanged B/D pass both 85-comparison gates','That A/C trial plus unchanged B/D passed both 85-comparison gates')
path.write_text(text,encoding='utf-8',newline='\n')
print('Preserved incoming handover and prior official records; wrote measured local continuation evidence.')
