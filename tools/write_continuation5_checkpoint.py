"""Write this batch's pre-measurement checkpoint; never reuse an older writer."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TEXT='''# Speed Demon continuation checkpoint - October 31, 2026

Continue this existing entry. Do not restart, register, reset or force-push.
Use the same private repository and watched speed-demon branch.

## Incoming state and preservation

This continuation started at 12aa1a4b22c970d7ce41700594fb8561f981dccd.
The incoming working tree was intentionally dirty, including the unpushed mapped
C rollback and official records. Every incoming dirty file was saved byte for
byte in .out/continuation5-incoming. Its exact handover is also preserved as
research/HANDOVER_INCOMING_2026-10-31.md. Prior measured records were retained.
Read that archived handover for the complete earlier architecture and history.

User authorization covers implementation, tests, ordinary commits and pushes.
Do not request registration or App access again. No agents or new user-owned
chats were created. Solo entrant remains CodeScythe / Prashant Krishan Bharti.

## Current candidate and evidence

Selected sources: A unchanged; B checked query-aware CSR with pipelined lookups;
C restored mmap plus a safe exact-name prefetch ring; D sparse uint32 labels
with exact uint64 overflow storage. Runtime dependencies remain zero, D=1,
C++20. B targets x86-64-v3, compatible with the scoring CPU. There is no
approximate/hash-only identity, cached output or seed recognition.

Release and ASan/UBSan each pass 89 dataset comparisons, both full seeds,
four direct programs and the forced uint64 B-offset full public hash. All four
offline images pass the starter sandbox and match the release binary SHA-256.
C's stale buffered image and README have been reconciled.

- Builds/gates: validation/continuation5-{release,sanitized}*.json.
- Images: validation/image-sizes-continuation5.json and sandbox-continuation5.txt.
- Exact experiments and rejections: research/CONTINUATION5.md.
- Full local cgroup T/M/S/D: research/results/continuation5-cgroup-coefficient.json.
- Canonical source counts: validation/continuation5-source-counts.json.

Full local coefficient ratios versus incoming kernels are approximately
B=1.245876, C=1.016422, D=1.013712. These are local, not official gains. B's
two-pass alternative uses less memory but loses the combined local coefficient.
A's hashing/formatting and private-table trials were unselected. Wider SIMD CSV
parsing, decimal decoding, forward D search, a window queue, BFS/paged labels
and one-probe relaxation were also unselected or rejected.

## Supplied files

All four handover attachments were preserved under research/supplied-fifth
and compiled/tested/benchmarked in D/C/B/A order. The distinct four pasted
in this chat are research/supplied-sixth, compiled/tested in that order.
Original identity and path-only adapters are preserved separately.

Initial supplied review: 99/108 pass. Four more collision/width cases add one
pass and three failures. Pending C hangs at its fixed name-table limit; new C
fails both full hashes. Both original B versions fail a real wide worker domain
(one exits, one silently truncates). New A merges distinct endpoint keys; its
dual-CRC collision is reproduced. Production passes the corresponding cases.
Raw evidence: validation/supplied-continuation5-{provenance,review,additional}.json.

## Official measurement status

Before this batch, the refreshed board showed 67.167388, rank 20, leader
78.617098, in validation/leaderboard-continuation5-start.json. The older rank 12
and leader 75.793 snapshot is historical. Refresh before quoting standings.

This checkpoint is prepared for the next implementation commit and official
measurement. Do not claim local improvements as official. Wait for all four
tracks at the pushed SHA, compare K against the recorded best independently,
and restore any coefficient loser before the final handover is written. The
board retains historical bests independently of branch tip.

## Environment and next steps

codescythe-research is running: GCC 16, network none, 5g/no swap, CPUs 0-11,
workspace at /work. Original Linux-local data remain at /benchdata/{a,b,c,d}
and /benchfresh/seed20261031/{a,b,c,d}. A separate codescythe-bench-continuation5
Docker volume contains copied public inputs; its copy helper
codescythe-data-continuation5 is stopped. Keep these data.

Exact organizer-pinned scc/clang-format are in ignored build/static-tools;
downloaded checksums were verified. C++/header and Dockerfile counting reproduces
all four prior official S values exactly.

After the authorized push, wait with tools/board_status.py, capture a snapshot
with tools/refinement_snapshot.py, verify private watch access, and record run
IDs in PERF.md. Reject K regressions even if T improves. Do not overwrite this
handover with older writer scripts, including this pre-measurement writer.

Outstanding: B still spends most time indexing; D still spends about half its
time building CSR; C's faster fixed-table design needs a proven growing fallback
before consideration. PGO on generator output remains untested. First place
has not been reached.

Deadline: November 2, 2026 at 20:30 IST / 15:00 UTC. Runtime: six P-cores /
12 threads, turbo off, AVX2/no AVX-512, 8 GB/no swap, offline digest-pinned
allowlisted builds under 600s, image under 2 GB, read-only data/root, 1 GB scratch.
Keep all four tracks entered. Last captured live rule: one run per push, 300s
interval, one in-flight job. The private App access was already verified.
'''
(ROOT/'HANDOVER_NEXT.md').write_text(TEXT,encoding='utf-8',newline='\n')
