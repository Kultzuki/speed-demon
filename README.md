# CodeScythe - Speed Demon 2026

Solo entrant: **Prashant Krishan Bharti**. C++20 implementations for **all four tracks**.

| Track | Approach |
|---|---|
| A Ingest | Fixed-layout timestamp parsing, endpoint/hour groups, exact percentile selection |
| B Index | Query-driven term index, sorted Boolean postings, exact positional phrase checks |
| C Join | Quote-aware CSV scanning, exact cents, direct region lookup, exact interned-name membership |
| D Traverse | Forward/reverse CSR, bidirectional Dijkstra, reusable search storage, six workers |

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
and percentile rank boundaries. `--full` checks the published full-size hashes.
Run it on Linux with Python 3.13 and the compiled binaries. `tools/prepare.py`
refreshes the four identical helper headers, Dockerfiles and track manifests.

## Evidence and limits

All four full public output hashes have passed locally. This is correctness
coverage for those inputs, not proof for every hidden seed. Local measurements
are made on an AMD Windows laptop through WSL2 and are not official scores.
Each track's PERF.md separates published reference numbers, local evidence and
board runs. No local timing is presented as a board run ID.

The public board is a practice score. Final scoring uses unseen data and adds
human judging. See the [frozen specs and harness](https://github.com/hackathon-raptors/speed-demon-2026)
and [competition rules](https://speeddemon.dev/#coefficient).

## License and assistance

MIT; see LICENSE. The retained Python references are the organizers' unmodified
MIT-licensed code and are not the runtime entrypoints. Codex assists with code,
validation and documentation. There is one human team member.
