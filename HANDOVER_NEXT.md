# Speed Demon handover - Rust continuation 8, October 31, 2026

Continue the existing private entry. Do not restart, reset, force-push or
re-register. No agent delegation is authorized.

## Checkpoint

Workspace C:/Users/kultzuki/Coding/Speed-demon. Origin
https://github.com/Kultzuki/speed-demon.git, watched branch speed-demon.
The latest source-changing, pushed and officially scored checkpoint is
0ca1987477223527268d60911e073ff334feb8bd. All five gates passed on all four tracks.
The next commit records official evidence and fixes the local source-counter
bookkeeping only; submitted kernels are unchanged. Wait for its official rerun
before another kernel change, then record the exact final checkpoint.

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
  remains; S=437, D=1. SIMD loads remain bounded. Small inputs use one worker.
- D is Rust: established six-worker two-pass forward/reverse compact CSR,
  exact full uint32 wide weights, twelve bidirectional radix query workers,
  separate aligned full uint64 distances and width-derived uint32 node/generation
  tags with complete safe wrap clearing. No sharded build, BFS remap, narrow
  labels or packed heap entries. S=473, D=1.
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
Provenance: validation/rust8-final-artifact-provenance-corrected.json,
validation/rust8-lf-artifact-provenance.json and
validation/image-sizes-rust8-final.json. Do not use earlier trial binaries.
The unchanged B forced-uint64-offset and C direct evidence remains valid with
their exact continuation-7 source/binary provenance.

## Measurement and next step

Corrected local complete K ratios against matched C++: A 1.0087 public / 1.0621 fresh;
D 1.0412 / 1.0246. The original counter included 12 TOML data lines per track;
validation/rust8-canonical-source-correction.json preserves that correction. WSL2 timing varies materially; no stable percentage or official
gain is claimed. All alternating trials check full output hashes and include
fresh cgroup memory, canonical source size and zero dependency cost.

Mapped Rust A, dedicated output writer, SWAR decimal parsing, D packed one-pass
intermediate, fused sparse relaxation and six query workers are unselected.
Read the research notes before revisiting them. D's earlier owner-sharded official
regression remains rejected. Preserve exact equality and all width/epoch fallbacks.

First official Rust: A K=30.827569, D K=14.542976. Both exceed the incoming
e9deec0 latest rerun (29.654383/14.469309) but do not beat historical bests
(33.234541/15.399979). validation/rust8-candidate-official-summary.json and
validation/leaderboard-rust8-candidate.json retain every gate and run ID.
One unchanged-source rerun accompanies the genuine source-counter correction
and official-evidence commit. Compare it before final retention; do not claim
a stable performance gain from these first measurements. B/C source-unchanged differences are
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
