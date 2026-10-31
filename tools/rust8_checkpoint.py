"""Write the reviewable, locally validated checkpoint before its first push."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
archive = ROOT / 'research/rust8-validated'
archive.mkdir(exist_ok=False)
for track in 'ad':
    dest = archive / f'track-{track}'; dest.mkdir()
    for file in ['main.rs', 'common.rs', 'Dockerfile', '.speed-demon.toml', 'Cargo.toml', 'Cargo.lock', 'README.md']:
        shutil.copy2(ROOT / f'track-{track}/{file}', dest / file)
selection_path = ROOT / 'research/rust8-selection.json'
selection = json.loads(selection_path.read_text())
selection['history'] = [{'at': selection['created_at'], 'status': selection['status']}]
selection['status'] = 'All local gates, exact offline/LF artifacts and TSan publication pass; first official Rust push pending'
selection['history'].append({'at': datetime.now(timezone.utc).isoformat(), 'status': selection['status']})
selection_path.write_text(json.dumps(selection, indent=2) + '\n')
report = ROOT / 'research/CONTINUATION8_RUST.md'
report.write_text(report.read_text() + '''

## Final phase and packaging evidence

results/rust8-final-phases.json records the separate final monotonic profile.
The first A run is cold (303 ms in parsing/reads); later warm runs parse in
30.94-32.65 ms and reach checked output closure in 46.90-48.01 ms. Their worker
read intervals are about 4.7-6.0 ms; sampled exact hash/lookup timing includes
clock overhead and is diagnostic only. Gather, selection, formatting and output
intervals are reported per worker. D's later runs count in 83.64-137.39 ms,
prefix/allocate in 41.84-42.60 ms, scatter in 248.15-253.12 ms and search in
388.77-393.17 ms. The first D run is slower too. No cold run is silently removed
from the raw report, and these instrumented values do not replace uninstrumented K.

Both Cargo manifests/locks check offline. LF-normalized Rust sources compile to
the exact validated release and image executables:
validation/rust8-lf-artifact-provenance.json. Complete source/configuration copies
are retained in rust8-validated/ even if official measurements reject a port.
''')
(ROOT / 'HANDOVER_NEXT.md').write_text('''# Speed Demon handover - Rust continuation 8, October 31, 2026

Continue the existing private entry. Do not restart, reset, force-push or
re-register. No agent delegation is authorized.

## Checkpoint

Workspace C:/Users/kultzuki/Coding/Speed-demon. Origin
https://github.com/Kultzuki/speed-demon.git, watched branch speed-demon.
Last submitted/officially validated HEAD is
e9deec07fa38f9abf0c167d6768c41c388e37ba5. The current working Rust A/D bundle is
fully locally validated and ready for its first commit/push; it has not yet been
officially measured. Record the new exact commit and wait for all four tracks.

Read research/CONTINUATION8_RUST.md and research/rust8-selection.json completely.
The full incoming handover is research/HANDOVER_INCOMING_RUST8.md, and the earlier
continuation-7 evidence and snapshots are preserved. Fresh pre-push feed:
validation/leaderboard-rust8-prepush.json, 69.780860 / rank 28, leader 81.805732.
These are dated public practice results; refresh before quoting current standings.
First place remains outstanding.

## Current kernels

- A is Rust: eight buffered pread workers, reusable 256 KiB buffers, proven
  177-byte complete-line alignment, exact owned endpoint keys, persistent local
  caches, packed hour records with full uint32 latency overflow, exact parallel
  percentile selection and ordered checked-close output. Full endpoint equality
  remains; S=449, D=1. SIMD loads remain bounded. Small inputs use one worker.
- D is Rust: established six-worker two-pass forward/reverse compact CSR,
  exact full uint32 wide weights, twelve bidirectional radix query workers,
  separate aligned full uint64 distances and width-derived uint32 node/generation
  tags with complete safe wrap clearing. No sharded build, BFS remap, narrow
  labels or packed heap entries. S=485, D=1.
- B/C submitted sources are unchanged. Their validated continuation-7 release
  and ASan/UBSan executables are copied exactly into the new mixed gates.

The user's entire original track-d-rust/track-d is unchanged and hashed. Its
radix heap informs the port; its positional CLI, placeholder team manifest,
BFS/forward-search memory cost and unverified historical notes are documented.
The CLI-only comparison and every trial are preserved. Complete current Rust
sources/configurations are also in research/rust8-validated/; established C++
sources/configurations are in research/baseline8/.

## Validated artifacts

Use build/rust8-final-{release,asan,checked}/track-*. Every mix passes 97 dataset
comparisons (prior 93 plus four fresh references), both full seeds, and direct
A guard/publication/alignment/decimal/percentile plus D rehash/wrap/full-width/
complete-CSR checks. Rust uses ASan and checked arithmetic; B/C retain ASan/UBSan.
TSan publication passes with std/test rebuilt under the same ABI. Only that
dedicated race-test container permits process-local ASLR control; no host ASLR
or official sandbox setting was changed.

All four rebuilt offline images pass official starter sandbox/full hashes,
remain about 119 MB, and exactly match the validated release binaries.
Git-normalized LF Rust sources also produce those exact executable hashes.
Provenance: validation/rust8-final-artifact-provenance.json,
validation/rust8-lf-artifact-provenance.json and
validation/image-sizes-rust8-final.json. Do not use earlier trial binaries.
The unchanged B forced-uint64-offset and C direct evidence remains valid with
their exact continuation-7 source/binary provenance.

## Measurement and next step

Local complete K ratios against matched C++: A 1.0046 public / 1.0578 fresh;
D 1.0373 / 1.0207. WSL2 timing varies materially; no stable percentage or official
gain is claimed. All alternating trials check full output hashes and include
fresh cgroup memory, canonical source size and zero dependency cost.

Mapped Rust A, dedicated output writer, SWAR decimal parsing, D packed one-pass
intermediate, fused sparse relaxation and six query workers are unselected.
Read the research notes before revisiting them. D's earlier owner-sharded official
regression remains rejected. Preserve exact equality and all width/epoch fallbacks.

First commit/push the frozen bundle, wait for every official gate and measurement,
then reject actual coefficient regressions. B/C source-unchanged differences are
rerun variation. Existing authorization covers ordinary commits/pushes and tests.
No registration or App permission change is needed. Do not blindly run any old
selector, prepare.py, restore script or handover writer.

Original benchmark data, volumes and all evidence remain. codescythe-research
and the new pinned offline codescythe-rust8 compiler container use /work with
twelve pinned CPUs and 5g/no swap. Data is still at /benchdata and
/benchfresh/seed20261031 in the original container, plus /data/fresh7 in the
existing benchmark volume. No original data or container was deleted.

Deadline remains November 2, 2026, 20:30 IST / 15:00 UTC. Target: i5-13500,
six P-cores/twelve threads, turbo off, AVX2/no AVX-512, exec-to-exit time and
cgroup memory.peak. One run per push, 300-second interval, one in flight.
''')
print('Prepared current handover, measured notes and immutable Rust source archive.')
