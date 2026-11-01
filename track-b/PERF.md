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


## Official continuation measurement c503752

Run `run-23826c7d60fc` at `c503752efebdbebcd9c6de41a4485af8ef1776fd`: gates=True,
T=0.30495s, M=80130048 bytes, S=922,
D=1, K=18.629977, points=63.510615.
Previous recorded best K=14.154553. Decision: **unchanged retained 160e4dd kernel; rerun variation**.

Captured best-three aggregate 69.160567, rank 16; leader 79.338836. Snapshot: validation/leaderboard-continuation5-final.json. Public practice, not final judging.


## Continuation 7: selected local candidate

Increase lazy packed posting blocks from 4096 to 65536 entries. Exact term/phrase semantics, adaptive postings and both document/offset width fallbacks are unchanged.

public: T=0.496101->0.424977s, M=81334272->73129984 bytes, S=922->922, D=1; local K ratio 1.103667 (`research/results/b-posting-blocks7.json`).

fresh: T=0.514579->0.442578s, M=81416192->72845312 bytes, S=922->922, D=1; local K ratio 1.102537 (`research/results/b-block16-fresh7.json`).

Checkpoint phase medians from the separate instrumented source: map-check-widths=1.333 ms, queries=25.084 ms, index-scan=214.394 ms, scatter=87.222 ms, index-finish=2.153 ms, evaluate=74.114 ms, format-output=2.559 ms, cleanup=9.398 ms. Raw stderr is in research/results/b-index-keys7.json. These diagnostic intervals omit parts of process startup/cleanup and must not be added to invent an official time.

These are alternating hot-data local WSL2 measurements with fresh cgroups, including process exit; they are not official scores. Short A/C repeats vary materially, and the gain is not a stable percentage across every batch. Every measured output hash matches.

The frozen combination passes 93 release and 93 ASan/UBSan dataset comparisons, both full seeds, the existing direct guard/publication/boundary/membership/state checks, and two new independent checks of all 200,000 forward/reverse CSR edges. Forced uint64 B offsets pass the full hash. All four rebuilt offline images pass the unprivileged read-only/no-network starter sandbox and their executables match the validated release binaries exactly. Exact source/common/compiler/binary/image identities are in validation/continuation7-artifact-provenance.json. Official retention remains pending.


## Official continuation 7 at f992539

Run `run-55ec3a94a1e5` at `f99253995d7fa9f97f825c9c8b37c4ec705d3e66`: T=0.295209s, M=71454720 bytes, S=922, D=1, K=19.373796, points=64.360736. All five official gates passed. Starting historical best K=18.629977: **candidate exceeds the starting recorded best**.

Captured practice aggregate 69.780860, rank 17; leader 80.244238. This is public practice, not final holdout or human judging. Full record: validation/leaderboard-continuation7-official.json.


## Final continuation 7 local reconciliation

A/B/C retain their improved f992539 sources. D is restored exactly to the
stronger incoming source after its official coefficient regression. The final
mix passes 93 release and 93 ASan/UBSan comparisons, both full seeds, the direct
programs including both complete 200,000-edge CSR checks, and forced uint64 B
offsets. All final image executables match build/continuation7-final-release.
A/B/C images originate in sandbox-continuation7.txt; restored D was rebuilt
in sandbox-continuation7-final-d.txt. Complete final provenance is
validation/continuation7-final-artifact-provenance.json. The earlier
continuation7 builds contain the rejected D trial and remain historical only.


## Official continuation 7 at e9deec0

Run `run-6d82f9e889d8` at `e9deec07fa38f9abf0c167d6768c41c388e37ba5`: T=0.299818s, M=71102464 bytes, S=922, D=1, K=19.243317, points=64.213996. All five official gates passed. Starting historical best K=18.629977: **unchanged retained f992539 kernel; this measurement is rerun variation**.

Captured practice aggregate 69.780860, rank 17; leader 80.253740. This is public practice, not final holdout or human judging. Full record: validation/leaderboard-continuation7-final.json.


## Official Rust continuation at 0ca1987

Run `run-bfdb1fa492e6` at `0ca1987477223527268d60911e073ff334feb8bd`: T=0.346143s, M=71774208, S=922, D=1, K=17.875749. All five official gates pass. Incoming exact-head K=19.243317; historical best K=19.373796. Unchanged B/C source; timing/coefficient differences are rerun variation.

Captured practice aggregate 69.780860, rank 28; leader 81.805732. Full snapshot: validation/leaderboard-rust8-candidate.json.


## Official Rust continuation at 8aa8ddb

Run `run-a27adb1e3656` at `8aa8ddb8f8aeba7d5d9b2b7c32745a26e5683d6e`: T=0.318701s, M=71217152, S=922, D=1, K=18.658515. All five official gates pass. Incoming exact-head K=19.243317; historical best K=19.373796. Unchanged submitted source; this run measures rerun variation. Unchanged B/C source; timing/coefficient differences are rerun variation.

Captured practice aggregate 69.811783, rank 28; leader 81.805732. Full snapshot: validation/leaderboard-rust8-repeat.json.


## Final restored continuation 8 at 6b71e02

Run `run-5ddd9b5cb8dd`: T=0.306344s, M=70959104, S=922, D=1, K=19.044931. All five official gates pass. Exact incoming C++ source is retained; differences are rerun variation. Captured practice aggregate 69.934612, rank 28, leader 81.805732. Full record: validation/leaderboard-rust8-retained.json.

## Continuation 9: Track B-only tokenizer and compressed temporary postings

Pair all token starts/ends in each 64-byte ASCII classification window, build
exact padded keys with masked AVX2 loads, and use CRC32C fingerprints followed
by full equality. Compress the narrow temporary posting stream to 16-bit
term/document-gap words with explicit absolute-id escapes. Preserve both width
fallbacks and all Boolean/phrase semantics. Use 262,144-word lazy blocks.

Five alternating runs on the independent full seed: incoming 0.406856677 s /
73,007,104 cgroup bytes / S=922; selected 0.361628282 s / 64,532,480 bytes /
S=944, D=1. Local K ratio 1.083355. These are local WSL2 measurements, not an
official score. Every measured output hash matches. Exact report:
`research/results/trackb9-finalist-fresh.json`; approach and rejected experiments:
`research/CONTINUATION9_TRACK_B.md`.

The frozen production source passes 33 release and 33 ASan/UBSan dataset
comparisons, both full seeds, actual full-width document dispatch, forced uint64
offsets, 4,096 direct tokenizer alignments, a real CRC collision, dictionary
growth/renumbering, cross-allocation escape decoding and uint32_max postings.
Evidence is in `validation/trackb9-production-*`. Official run ID and retention
decision follow after the validated image is measured. The 80-point target
remains outstanding at this local-validation checkpoint.
