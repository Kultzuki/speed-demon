# Evaluation of the three external research reports

Continuation of `df84b71`, October 30, 2026. The attachments are research input,
not authority to change the frozen semantics or to contact organizers. All four
tracks remain entered. Experiments are independent original C++ implementations;
no third-party runtime source or dependency was added.

## Assessment

1. **Closing the Gap with Architectural Overhauls: An Action Plan for Speed
   Demon 2026** has useful broad themes, but several concrete claims are wrong.
   643 MB does not exceed 8 GB; B was dropped because its points were lowest,
   not because it failed a memory gate. Board memory does not reveal a leader's
   algorithm. A already uses partitioned `nth_element` and counts errors while
   parsing; latencies alone cannot reconstruct error counts. Heap fallback does
   not establish worst-case linear selection. C already uses a direct region
   lookup, and partitioning by region does not make country/name groups disjoint.
   Name membership still needs an exact merge. Library/header-only claims do not
   waive the actual dependency/source rules. Reordering and packed state need
   correctness tests; they are not risk-free.

2. **Speed Demon 2026 - Concrete, implementation-ready recommendations and
   experiment plan for CodeScythe** contains useful contiguous aggregation and
   adaptive-posting ideas, but repeatedly attributes our implementation details
   to specs that do not prescribe those implementations. Several recommendations
   (buffered output, small-sort/large-selection, compact name arena) are already
   implemented. A uint16 group length can overflow. A 16-bit token ID needs a
   proven dictionary bound, not an assumed small vocabulary. A serialized index
   with disk spill/virtual iterators adds unnecessary work for this one-run task.
   No organizer message or library installation is needed for the selected work.

3. **Recommendation: Prioritize architecture** is the strongest fit. It admits
   the unavailable repository evidence, separates ideas from measurements, and
   correctly prioritizes the existing A/C/D candidates plus B's token-array
   removal. Its point-delta model is useful only with the actual caps and the
   organizer's memory/source figures. Its 15-minute queue uncertainty is now
   resolved by the live feed: `min_interval_s=300`, `runs_per_push=1`.

## Decisions implemented or tested

| Track | Decision | Why |
|---|---|---|
| A | Validate six line-aligned parser workers; separately try parallel per-hour selection/formatting | Existing full-hash gain; substantial output and independent groups |
| B | New raw-anchor prototype, then adaptive sparse/bitmap postings | Removes global token IDs and global posting merges; only selected phrase anchors retain 64-bit byte offsets |
| C | Validate quote-parity partitioning; replace replicated catalogs with one exact table across 256 locked shards | Private 3/6-worker variants were measured; the shared version was both faster and smaller locally |
| D | Validate packed state and BFS relabeling, including forced wrap | Existing measured locality gain; exact weighted search remains unchanged |

B samples runtime corpus bytes only to choose an anchor. Every selected anchor
is indexed over the entire input, and each phrase is verified by exact ASCII
token comparison without crossing TAB/LF. Sampling cannot change the answer.
Boolean sets are evaluated independently in disjoint document blocks, retaining
the specified left fold; counts/sums add and first IDs combine in block order.
The hybrid trial promotes a frequent document list to a bitmap during parsing,
avoiding a complete duplicate representation at finalization.

C's shared-table trial preserves the compact arena/table layout. Choosing a shard
from high hash bits leaves low bits available for the shard's table probing.
Each shard lock covers allocation, equality and country membership together, so
distinct counts can be safely accumulated in ordinary per-worker aggregates.

Deferred: A's packed record/count/scatter layout until the cheaper parallel
output trial is measured; general compressed-index libraries; full SSSP/CH
rewrites; C radix join; unconditional Rust migration. These are not required to
validate the present hypotheses, and no claimed leader implementation is known.

## Verified evidence boundaries

- All of `HANDOVER_ASTRA.md` was read; initial HEAD was the clean `df84b71`.
- Frozen specs and reference programs are in `.competition/official` at
  `adb931623de2bcd3e12ab696f392a281783a3b43`.
- The runner prewarms input **outside** the run's cgroup, then measures cgroup
  `memory.peak`. Mapped input contributes to local process RSS but usually has
  already been charged outside that fresh cgroup. RSS must not substitute for M.
- The public board's current rules specify one public run per push, a 300-second
  team interval, and a 600-second build cap. Final five-run holdout scoring is a
  separate measurement. The feed was checked October 30 around 18:00 UTC.
- That board snapshot's top five teams all report Rust. It is observational
  evidence, not a controlled C++/Rust comparison. No language rewrite has been
  benchmarked. The C++ prototypes themselves demonstrate architectural gains.
- Sanitizers, generated/adversarial differential tests, full hashes, offline
  image builds and the sandbox checker precede a production push. Actual board
  run IDs and any regressions belong in the per-track PERF logs.

## Primary-source mechanisms checked again

- [Original C 1BRC progression](https://www.dannyvankooten.com/blog/2024/1brc/):
  independent chunks, mapped input, custom parsing and exact merging. Its
  workload/CPU/timing do not predict our percentile task.
- [Original SIMD CSV explanation](https://nullprogram.com/blog/2021/12/04/):
  quote parity and doubled-quote handling support safe record boundary scans;
  parity alone is not the semantic CSV parser.
- [Competition site](https://speeddemon.dev/): score caps, dependency treatment,
  hardware and public competition context. The checked-out executable harness
  and live rules feed resolve operational details.
- [Public board feed](https://s3.amazonaws.com/raptors.dev/speeddemon.dev/2026/board/board.json):
  actual rules, per-track measurements and language metadata; positions can
  change after the snapshot.

Additional paper/engineering references already assessed at the checkpoint are
retained in `RESEARCH.md`. No new theoretical result is treated as a measured
speedup on this task.

## Completed validation and rejected streaming trial

The selected A/B/C/D versions passed 69 differential cases in both release and
ASan/UBSan builds, all four public full hashes, offline builds, sandbox checks,
and all four freshly generated full datasets at seed 20261031. The latter report
records input and binary hashes in `validation/fresh-full-seed20261031.json`.

The extra `b-stream.cpp` experiment matches common-anchor phrases using an
eight-token per-document ring and retains offsets only for other phrases. It
passed all 22 B checks, including both full seeds and a dedicated wrap/dedup case,
in release and sanitizers. Five local runs averaged 1.71814s trimmed mean at
about 387.4 MiB RSS. Late repeats exposed timing drift: the selected hybrid moved
from 1.06426s to 1.85900s and the unchanged baseline from 2.23731s to 3.27725s.
Thus streaming's time comparison is inconclusive; comparing it only against the
earlier 1.06426s would overstate a regression. It has no memory advantage and no
established repeatable benefit, so it remains unpromoted. The original hybrid
still improved on the baseline in the late comparison. All raw runs are retained.
