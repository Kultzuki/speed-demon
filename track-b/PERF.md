# Track B: performance log

## Published reference

The organizers' scoring-box reference takes 56.35 seconds. This is
published calibration, not our own board run.

## First C++ implementation

Read all queries first and index only their terms. Corpus tokenization lowercases ASCII A-Z only; all other non-alphanumeric bytes are separators. Sorted document postings support strictly left-to-right Boolean set operations. For phrases, select the least frequent occurrence list as the anchor and compare exact adjacent token IDs. A boundary bit on every document's final token forbids cross-document matches. Full string equality resolves dictionary hash collisions; results are exact.

Local full public seed 1: output SHA-256 `f86973c210228141bcb6f1f1b10188ad2a9b65f71e7cd7cf4590b38de4e80927`.
The direct local process check took 14.6211 seconds on the
Windows/WSL2 laptop with input and output on a Windows bind mount. This single
run includes local process launch and file-sharing overhead and is not an
official timing. It is not comparable to the scoring-box reference.

## Board evidence

Initial C++ board measurement at commit `b5cbc28`.

| Run ID | T (s) | M (MB) | Formatted source lines | D | K | Machine points |
|---|---:|---:|---:|---:|---:|---:|
| `run-d2ad96a22ae8` | 5.822991 | 411.35 | 259 | 1 | 3.718642 | 28.519218 |

All correctness, timeout and sandbox gates passed. This is a single public-board
run on public seed 1, not a five-run holdout result. Full board evidence is in
`validation/board-baseline.json` at the repository root.

## Experiments and correctness

Differential cases include ASCII case conversion, UTF-8 separators, repeated phrase terms, sentence punctuation, absent terms, empty documents and mixed left-associative Boolean operators.

## Second implementation: local experiment

A contiguous exact dictionary replaces node-based probes. Six workers parse complete document-line blocks and merge ordered postings and translated token positions.

Five local full-seed-1 runs: 2.59227, 2.56169, 2.62141, 2.55414, 2.58628 seconds. The middle-three mean is 2.58008 seconds. Every output hash matched. These are Linux-filesystem WSL2 process timings, not board measurements. The previous local middle-three mean was 11.2331 seconds.

AddressSanitizer and UndefinedBehaviorSanitizer passed all 57 differential cases, including sample seeds 2 and 17. Sanitizer timings are not performance evidence. A new official board run is needed to price the speed gain against extra source and peak memory.

## Second official board run

Commit `9aad3f4`, run `run-3c8605ffbbe8`: T=2.301115s, M=642.91MB, S=355, D=1, K=5.160148, machine points=35.633107. All gates passed.

Parallel parsing and the flat dictionary improved board wall time from 5.822991s to 2.301115s; peak memory increased from 411.35MB to 642.91MB and formatted source grew from 259 to 355 lines. K still improved from 3.718642 to 5.160148. The coefficient prices the additional memory and code rather than treating this as a wall-time-only win.

## Third official board run

Commit `5dc9c4f`, run `run-72a424b92d56`: T=2.192134s, M=643.08MB, S=355, D=1, K=5.286576, machine points=36.158726. All gates passed.

Runtime implementation code was unchanged from the second board run; differences are not attributed to another optimization.
## Continuation from df84b71: remove global tokens and posting merges

Runtime samples choose phrase anchors; a complete exact pass builds selected
64-bit byte offsets and Boolean-only document postings. Phrases compare exact
ASCII tokens in mapped input, stopping at document boundaries. Workers retain
disjoint document blocks; left-fold Boolean results can be summarized per block
without building a duplicate global index. Frequent postings promote to dense
bitmaps during construction; rare terms retain sorted lists.

Five serialized Linux-local full public runs:

| Variant | Trimmed mean (s) | Approximate peak process RSS (MiB) |
|---|---:|---:|
| Published architecture, rerun | 2.23731 | 852.4 |
| Raw anchors and block-local sparse postings | 1.48281 | 416.4 |
| Raw anchors plus adaptive sparse/bitmap postings | 1.06426 | 385.3 |

Results are local AMD/WSL2 evidence, not official T/M. See corresponding
`research/results/b-baseline-confirm.json`, `b-raw-anchors.json`, `b-hybrid-6.json`.
Sampling only changes planning; it never substitutes estimated results.
Bitmap tail bits cannot be set by AND or binary NOT, and every OR operand
contains only actual document bits. Sparse cursors preserve document order.

Release and ASan/UBSan passed the expanded 69-case four-track suite and full
public hashes. B tests include exact 32-byte tokens, UTF-8 separators, repeated
terms, chunk boundaries, empty documents, and an empty left fold followed by OR.
Offline image and official sandbox/hash checks also passed.

The additional streaming-phrase experiment was not promoted: its five-run local
trimmed mean was 1.71814s at about 387.4 MiB RSS, with no useful memory reduction.
It passed 22 release/sanitizer B checks, including both full seeds and a ring-wrap
fixture. Late repeats showed substantial timing drift: hybrid 1.85900s versus
unchanged baseline 3.27725s, compared with the earlier 1.06426s/2.23731s.
Streaming's time comparison is therefore inconclusive, not a proven 61% regression.
Retain the simpler hybrid until a repeatable additional benefit is established.
See `b-stream-6.json`, `b-hybrid-confirm-final.json` and `b-baseline-final.json`.

The promoted version also matches its independently generated full-seed-20261031
reference output; input and binary hashes are in
validation/fresh-full-seed20261031.json. This is a local correctness check, not
a hidden-seed or official timing result.

## Fourth official board run: all-track architecture update

Commit `0c89c6e71d502e9edee2b646072b86f9b48c082a`, run `run-326b4e6b2559`:
T=0.859651s, M=153538560 bytes, S=500, D=1,
K=10.679361, machine points=51.427263. All check/build/correctness/
timeout/sandbox gates passed. This is one official public-seed run, not final
holdout scoring. Exact evidence is in `validation/board-fourth.json`.


## Refinement from 6cb3509: validated candidate

Sparse postings retain four uint16 block-local IDs inline, with exact dynamic
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
implemented with exact uncapped scanning but measured slower and was not selected.

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


## Official b30392c measurement and promotion decision

Commit `b30392c91f458577a4678b3d9bec4c892a3a964c`, run `run-a58493d74b1a`: T=0.734635s, M=87310336 bytes, S=570, D=1, K=12.681341, points=55.158259. All official gates passed.

This improves the previous best coefficient and is retained. Exact board/team data is in `validation/leaderboard-refinement-b30392c.json`.


## Final official measurement at 154e195

Run `run-5dbacdad7818`: T=0.703434s, M=86552576 bytes, S=570, D=1, K=12.982145, points=55.667322. All official gates passed.

Runtime source is unchanged from b30392c; this rerun improved its recorded best, without another B/D kernel change.

Best-three aggregate is 63.343397; captured rank 19. Exact data: `validation/leaderboard-refinement-final.json`. Public practice scoring remains separate from final holdouts and judging.


## Continuation from d069bfd: selected local refinement

Twelve block workers, an exact-safe negative dictionary filter, and duplicate-write suppression for dense postings are selected. Every possible filter hit still goes through exact byte equality. Query folds, phrase verification, uint16/uint32 document fallback and uint32/uint64 relative-offset fallback remain.

Five alternating full-hash-checked Linux-local runs of the actual selected source: checkpoint 0.775465s, selected 0.549416s trimmed mean. See `research/results/continuation3-paired-b.json`. These are AMD/WSL2 timings; RSS includes mapped input and is not official cgroup memory.

Both release and ASan/UBSan pass 83 dataset comparisons, four direct A/C/D boundary/concurrency/state programs, and a forced uint64-offset B full-hash build. A also passes 1,750 guard-page parses and twelve-way endpoint publication. Provenance is in `validation/continuation3-*-build.json`. Offline rebuilt images pass all four public full hashes in the read-only/no-network/unprivileged sandbox; see `validation/sandbox-continuation3.txt` and `image-sizes-continuation3.json`. Official promotion is decided separately from these local measurements.


## Official continuation measurement at 7321615

Run `run-210e7863db85`: T=0.551677s, M=102199296 bytes, S=583, D=1, K=14.132306, points=57.510652. All official gates passed.

Compared with the refreshed starting best K=12.982145: **retained**. This is one public-practice run; local paired gains and unchanged-code rerun variation are separate from hidden-seed/final judging results.


## Official packed-A follow-up at 12aa1a4

Run `run-dc6e65a747ff`: T=0.549548s, M=102383616 bytes, S=583, D=1, K=14.154553, points=57.544808. All official gates passed.

Runtime source is unchanged from 7321615. Any change in this rerun is measurement variation, not another kernel optimization.


## Continuation 5 local validation

See research/CONTINUATION5.md and the exact paired reports. Current production
sources pass 89 release and 89 ASan/UBSan dataset comparisons, both full seeds,
four direct programs and the forced uint64 B-offset full hash. Rebuilt offline
images pass the starter sandbox and match the release binary hashes. These are
local checks, not official coefficient gains. Official run IDs are pending.


## Official continuation measurement 160e4dd

Run `run-c3af4a46878b` at `160e4dd03a5210afd31ba01af791c03d1907da7b`: gates=True,
T=0.31168s, M=79962112 bytes, S=922,
D=1, K=18.435477, points=63.282719.
Previous recorded best K=14.154553. Decision: **retain**.

Captured best-three aggregate 69.077744, rank 16; leader 79.190878. Snapshot: validation/leaderboard-continuation5-official.json. Public practice, not final judging.
