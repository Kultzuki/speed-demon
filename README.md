# CodeScythe - Speed Demon 2026

Solo entrant: **Prashant Krishan Bharti**. C++20 implementations for all four tracks.

| Track | Approach |
|---|---|
| [A Ingest](track-a/README.md) | Parallel parsing, packed hour records and exact percentile selection |
| [B Index](track-b/README.md) | Query-driven indexing, packed postings and exact phrase verification |
| [C Join](track-c/README.md) | Parallel CSV parsing, exact cents and sharded membership |
| [D Traverse](track-d/README.md) | Compact forward/reverse CSR and bidirectional radix Dijkstra with uint64 distances |

Each track builds independently from its own Dockerfile and includes its manifest,
source, README and PERF.md optimisation log. There are no third-party runtime
dependencies. Builds use digest-pinned images and statically linked executables.

## Run and check

Install Docker and Python 3.13. Obtain or generate input data using the
[organizers' generators and frozen specifications](https://github.com/hackathon-raptors/speed-demon-2026).
With the input files in a local directory, run:

```sh
python check.py a --data /path/to/a-input --expected 495ca09682b9673ef836a506496177680bb4a3af54255174befddb1f83481cd3
```

The example hash is for the full public seed-1 Track A dataset. Use `b`, `c` or
`d` and the corresponding expected hash for the other tracks. `check.py` builds
with networking disabled, runs with the competition sandbox settings, and checks
the output filename and SHA-256. Required base images must be available locally.

## Measurements and history

Each track's PERF.md retains its optimisation history and official board run IDs.
Local measurements are distinguished from official results. Saved validation
records remain in [validation/](validation/). Historical references to removed
research files and development scripts can be resolved at commit `8d9ca80`, before
the repository cleanup. The four submission implementations are unchanged by cleanup.

## License and assistance

MIT; see [LICENSE](LICENSE). See [AUTHORS.md](AUTHORS.md) for authorship and AI
assistance. Retained organizer references and generators keep their existing notices.
