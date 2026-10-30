# CodeScythe - Speed Demon 2026

Solo entrant: **Prashant Krishan Bharti**. C++20 implementations for **all four tracks**.

| Track | Approach |
|---|---|
| A Ingest | Parallel line parsing, exact group merge, parallel percentile selection and ordered formatting |
| B Index | Query-only dictionary, adaptive sparse/bitmap postings, exact mapped-text phrase verification |
| C Join | Quote-safe parallel parsing, exact cents, shared sharded name membership |
| D Traverse | Forward/reverse CSR, BFS locality relabeling, bidirectional radix Dijkstra, packed search state |

No third-party runtime dependencies. Every track builds independently, offline,
from allowlisted digest-pinned images. The runtime executable is statically linked.
The helper header is copied into each track and counts toward that track's source size.

## Run

With Docker running and Python 3.13 available:

```sh
git clone https://github.com/hackathon-raptors/speed-demon-2026 .competition/official
python tools/fetch_data.py
python check.py a --data data/a/full-seed1 --expected 495ca09682b9673ef836a506496177680bb4a3af54255174befddb1f83481cd3
```

Repeat for b, c and d using `.competition/SHA256SUMS.json`. `check.py` builds each
track with `--network=none` and runs it under the supplied sandbox settings.
It verifies exactly one correctly named output file. Root data and build folders
are ignored by Git and do not enter any track image.

`tools/validate.py` compares compiled `build/track-*` binaries against the frozen
references using worked examples, three tiny seeds, two unseen sample seeds,
random directed multigraphs, random mixed Boolean/phrase queries, CSV edge cases
and percentile rank boundaries. The suite now has 61 cases, or 69 with `--fresh`
(tiny and sample seed 20261031). Both release and AddressSanitizer/UndefinedBehaviorSanitizer
builds pass those 69 cases and the four public full hashes. Reports and build
hashes are in validation/. `--full` checks the published full-size hashes.
All four selected implementations also match reference outputs on a freshly
generated full-scale seed 20261031, with input/binary hashes saved in validation/.
Run it on Linux with Python 3.13 and the compiled binaries. `tools/prepare.py`
refreshes the four identical helper headers, Dockerfiles and track manifests.

## Evidence and limits

The all-track architecture update at **0c89c6e** passed every official gate and
improved each track. Its best-three public machine aggregate is **58.008**, up
from **47.178**; A/B/C count and D is dropped. Exact run IDs and measurements are
in `validation/board-fourth.json` and the per-track PERF.md files. This is one
public-seed measurement, not final holdout scoring. For continuing work, start
with [HANDOVER_NEXT.md](HANDOVER_NEXT.md).

All four full public output hashes have passed locally and all four tracks passed their first official board runs at commit b5cbc28. This is correctness
coverage for those inputs, not proof for every hidden seed. Local measurements
are made on an AMD Windows laptop through WSL2 and are not official scores.
Each track's PERF.md separates published reference numbers, local evidence and
board runs. No local timing is presented as a board run ID.

The continuation from checkpoint `df84b71` evaluates all three external reports
in [research/EXTERNAL_REVIEW.md](research/EXTERNAL_REVIEW.md). Reproducible candidate
checks are in `tools/research_checks.py`; `tools/fresh_full.py` generates and
differentially checks another full-scale seed. Experiments and rejected variants
remain under research/, outside the isolated track builds.

The public board is a practice score. Final scoring uses unseen data and adds
human judging. See the [frozen specs and harness](https://github.com/hackathon-raptors/speed-demon-2026)
and [competition rules](https://speeddemon.dev/#coefficient).

## License and assistance

MIT; see LICENSE. The retained Python references are the organizers' unmodified
MIT-licensed code and are not the runtime entrypoints. Codex assists with code,
validation and documentation. There is one human team member.
