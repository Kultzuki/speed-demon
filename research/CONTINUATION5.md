# Continuation 5 - October 31, 2026

Continued local HEAD 12aa1a4 on the same private speed-demon branch. No reset,
force push, registration, App change or agent delegation was performed. The
incoming dirty files were saved byte for byte under .out/continuation5-incoming;
the complete incoming handover is also archived here. Prior official records,
including the rejected buffered C measurement, are preserved.

The refreshed starting feed at 2026-10-31T04:59:05.828427+00:00 gives CodeScythe
67.167388, rank 20, leader 78.617098.
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
| a-hash-private5-paired | baseline | 0.058450 |
| a-hash-private5-paired | crc | 0.057207 |
| a-hash-private5-paired | private | 0.062031 |
| a-hash-private5-paired | supplied | 0.065680 |
| a-format5-paired | baseline | 0.059890 |
| a-format5-paired | formatted | 0.059126 |
| b-csr5-paired | baseline | 0.573644 |
| b-csr5-paired | csr | 0.340117 |
| b-twopass5-paired | baseline | 0.562003 |
| b-twopass5-paired | csr | 0.351006 |
| b-twopass5-paired | twopass | 0.419227 |
| c-prefetch5-paired | baseline | 0.066148 |
| c-prefetch5-paired | prefetch | 0.060806 |
| c-structure5-paired | baseline | 0.065984 |
| c-structure5-paired | structure | 0.070890 |
| c-structure5-paired | piped | 0.067375 |
| c-decimal5-paired | baseline | 0.071031 |
| c-decimal5-paired | decimal | 0.082574 |
| c-decimal5-paired | combined | 0.068151 |
| d-window5-paired | baseline | 0.662389 |
| d-window5-paired | window | 0.683962 |
| d-forward5-paired | baseline | 0.679986 |
| d-forward5-paired | forward | 0.976041 |
| d-forward5-paired | window | 0.970440 |
| d-locality5-paired | baseline | 0.679291 |
| d-locality5-paired | locality | 0.788086 |
| d-relax-label5-paired | baseline | 0.641530 |
| d-relax-label5-paired | relax | 0.643613 |
| d-relax-label5-paired | escaped | 0.632144 |
| d-supplied-fifth5-paired | baseline | 0.645519 |
| d-supplied-fifth5-paired | supplied | 3.499546 |
| c-supplied-fifth5-paired | baseline | 0.068711 |
| c-supplied-fifth5-paired | supplied | 0.053038 |

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


## Full local coefficient comparison

Local WSL2, fresh cgroups, Linux-local hot inputs, process fork/exec/exit timer, read-only root/data, 8g/no swap, 12 pinned logical CPUs. Monitor overhead and tmpfs output are included; not official scoring.

| Track | Candidate | Median T s | Median cgroup peak bytes | S | Local K ratio |
|---|---|---:|---:|---:|---:|
| b | baseline | 0.618436 | 102862848 | 583 | 1.000000 |
| b | csr | 0.382275 | 80887808 | 922 | 1.245876 |
| b | twopass | 0.463169 | 56963072 | 914 | 1.215679 |
| c | baseline | 0.075807 | 14761984 | 349 | 1.000000 |
| c | prefetch | 0.071347 | 14884864 | 379 | 1.016422 |
| d | baseline | 0.720036 | 124403712 | 385 | 1.000000 |
| d | escaped | 0.726307 | 112410624 | 391 | 1.013712 |

The one-pass B layout wins the full local comparison despite the two-pass layouts lower memory. C and D gains are modest and need official confirmation. The extra helper is stopped; the separate codescythe-bench-continuation5 volume remains. Existing /benchdata and /benchfresh were not changed.


## Official result at 160e4dd

Exact pushed commit: 160e4dd03a5210afd31ba01af791c03d1907da7b. Captured at 2026-10-31T05:38:46.223220+00:00.
Best-three aggregate **69.077744**, rank **16**;
leader **79.190878**. This remains public practice.

| Track | T seconds | M bytes | S | K | Points | Official run | Decision |
|---|---:|---:|---:|---:|---:|---|---|
| A | 0.052783 | 29478912 | 290 | 28.986473 | 73.109768 | run-258ef14a9368 | unchanged A kernel; retain source and historical best |
| B | 0.31168 | 79962112 | 922 | 18.435477 | 63.282719 | run-c3af4a46878b | retain |
| C | 0.06621 | 13393920 | 379 | 23.727679 | 68.762763 | run-6c8aae8ae5d2 | retain |
| D | 0.391017 | 107118592 | 391 | 14.963401 | 58.751516 | run-12519a0ceed8 | reject and restore incoming source |

A has no new runtime change. Each other decision compares the full official coefficient with the starting historical best, not the most recent losing rerun. Rejected candidates must be restored and changed images rebuilt before closing the handover.


D is restored locally to the incoming full-uint64 source after its official K regression. B/C are retained. Final mixed-source release/sanitizer gates and a rebuilt D image precede the next push.
