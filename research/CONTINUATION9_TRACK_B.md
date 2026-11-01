# Continuation 9: Track B only, November 1, 2026

The user's current scope is Track B only, with a target of 80 displayed practice
points. A/C/D remain entered and their runtime files are preserved. No agents,
registration changes, resets or force pushes are used. Incoming dirty work and
the exact B baseline are archived in `.out/trackb9-incoming`; the incoming commit
is `6b71e02218f87a492f41aad0b6ea304c0e6cb172`.

The refreshed starting feed, `validation/leaderboard-trackb9-start.json`, records
B=64.360736 points, K=19.373796, T=0.295209 s, M=71,454,720 bytes, S=922,
run `run-55ec3a94a1e5`. The displayed overall leader has B=78.547989 points,
but the highest individual B score in that feed is another ello at 81.049387.
These are time-specific practice results. Eighty points requires K >=
10**1.6 = 39.810717; no local measurement establishes that score.

## Selected implementation and why

Keep the query-aware exact hybrid index. A 64-byte ASCII classification window
now produces separate token-start and token-end masks; consume paired set bits
instead of rebuilding the remaining-token mask for every token. Construct each
padded lowercase key with one masked AVX2 load. Hardware CRC32C fingerprints the
key, while every potential match still compares all four 64-bit key words.
CRC collisions are never term identity.

Compress each worker's temporary posting bucket using a 16-bit word: 9 bits for
the term's bucket offset and 7 bits for the increase in its local document id.
The reserved delta 127 introduces an explicit absolute-document word. Repeated
document ids have delta zero. Decoder state carries across allocation boundaries.
Use 262,144-word lazy anonymous blocks and return each consumed block to Linux.
The established checked uint32 document-stream/posting fallback and uint64 text
offset fallback remain. Query folds and exact phrase verification are unchanged.

The independent full-seed comparison in
`research/results/trackb9-finalist-fresh.json` uses five alternating runs:

| Candidate | Median T s | cgroup M bytes | Canonical S | Local K ratio |
|---|---:|---:|---:|---:|
| Incoming B | 0.406856677 | 73,007,104 | 922 | 1.000000 |
| Tokenizer/CRC only | 0.355475487 | 73,003,008 | 921 | 1.070019 |
| Selected compressed stream | 0.361628282 | 64,532,480 | 944 | 1.083355 |

These are AMD Ryzen/WSL2 local results with fresh cgroups, 12 pinned CPUs,
read-only data/root, no network, 8 GB/no swap, process startup/exit included and
every output hash checked. They are not official scores. Local wall times vary
substantially. The earlier public gap batch overlapped a correctness/compiler
job and is diagnostic only; the clean fresh comparison supports the selection.

## Rejected or unselected work

The `trackb9-*` prototypes and JSON reports preserve all trials. Direct per-term
growing arrays increased allocations and memory. Inline/slab-linked lists also
lost. Exact worker lookup caches, pointer-key pipelines, inline dictionaries,
negative filters, denser bitmap thresholds, vector bitmap totals, distributed
Boolean conjunctions and anchor-only phrase scans gave no convincing full
coefficient improvement over the selected combination. Simpler rare-anchor
phrase checking increased text rescans; full candidate intersection is retained.

A complete query-activated streaming design was implemented and full-hash
checked. It uses an epoch-tagged term bitmap per 64-document block, provably
complete Boolean clause anchors and exact phrase checks. It reduced memory to
about 44 MB but activated roughly 21 million queries per full corpus and lost
on time. Adaptive 256/512/1024-document variants also lost. These remain research,
not submitted kernels. Do not promote their low memory in isolation.

Term-major segment metadata, empty-worker masks, exclusive interior bitmap
words and query-use-aware density were measured but unselected. The later
output-owner scatter experiments are isolated prototypes, pending measurement;
no such change is active in the submitted source at this checkpoint.

## Exactness and production validation

The exact staged source is identified by `research/trackb9-selection.json`.
Both release and ASan/UBSan gates pass 33 Track B dataset comparisons, including
both full referenced seeds, all available tiny/sample fixtures, UTF-8 byte
tokenization, 32-byte terms, long unknown tokens, empty/no-query input, and the
skewed 70,001-document fixture that actually dispatches to full-width postings.
The forced uint64-offset build also passes the public full hash in both modes.

`research/tests/b-token-window9.cpp` additionally checks 4,096 token/window
alignments, finds and distinguishes a real CRC collision, forces dictionary
growth and renumbering, puts an escape marker at the final word of an allocation
with its absolute document in the next allocation, and exercises uint32_max
posting ids. Both release and sanitizer direct programs pass.

Evidence: `validation/trackb9-production-{release,sanitized}.json`,
`validation/trackb9-production-direct.json`, and
`validation/trackb9-production-gates.log`. Offline image/sandbox and official
measurement are recorded below when complete. Eighty points is not achieved
at this checkpoint; retain only a measured official coefficient improvement.

## User steering: push small gains and restore best A

The user additionally authorized pushing validated small improvements and
restoring A to its best source. A separate concurrent chat had committed
`a7136fd8da9cf8ecebba731b664fdd279bbc734a`; its official A run
`run-ec6d5385ecb1` passed but scored K=32.046061 / 75.288733 points, below the
6b71e02 best K=33.741694 / 76.408344 points. The staged A main/common already
match 6b71e02 exactly. Include that restoration with the B submission, while
preserving the rejected A trial in Git and `.out/trackb9-incoming`.

The exact production B image passes the offline official sandbox and matches
the validated release executable byte for byte (SHA-256
`703ea3259bbb210ec266445081ad8d61153758e1c0d1ccb34b08e7f6c7106e70`).
Only B was rebuilt. The later isolated public five-run comparison is
`research/results/trackb9-production-public.json`: median T=0.372092851 to
0.364772902 s, M=72,699,904 to 64,434,176 bytes, local K ratio 1.031007.
This smaller repeat confirms why local timing variation must not be promoted
as an assured official gain.
