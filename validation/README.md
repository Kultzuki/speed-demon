# Validation evidence

These files distinguish local tests, local experiments and official public-board
measurements. None is a final hidden-seed result or a claim of winning the event.

- `board-fourth.json`: all four official runs at `0c89c6e`, every gate passed,
  every track improved, best-three aggregate 58.007574. A/B/C count.
- `leaderboard-continuation.json`: dated 18:35:36 UTC October 30 public-feed
  comparison, including the leader and a C++ team in fourth place. Rankings can
  change; this snapshot is not a final result.

- `board-baseline.json`: first official four-track runs at `b5cbc28`; all gates
  passed. The exact run IDs, wall times, kernel memory measurements, formatted
  source sizes and coefficient values come from the organizers' public feed.
- `board-second.json`: official runs at `9aad3f4`; parallel indexing and radix
  heaps improved B and D. A and C implementation code was unchanged.
- `full-validation.json`: initial direct-process full public checks, against all
  four published SHA-256 values. Timings include the local process launch.
- `validation.json`: initial 57 differential cases: worked examples, tiny seeds
  1/2/17, sample seeds 2/17 and adversarial cases.
- `sanitizers.json`: the 57-case suite under AddressSanitizer and
  UndefinedBehaviorSanitizer, after the B and D changes.
- `sanitizers-c-compact.json`: the revised C code under both sanitizers, including
  full public data and a 135,000-name case forcing both dictionary and string
  arena growth. Repeated earlier names test that growth preserves equality.
- `benchmark-baseline.json`, `benchmark-optimized.json` and
  `benchmark-c-compact.json`: five local runs with inputs copied onto the Linux
  filesystem. These isolate Windows file sharing from the timed process but
  still use a different CPU and operating environment from the scoring box.
  Per-process peak RSS differs from the official kernel cgroup memory axis.

`tools/validate.py` now has 61 differential cases, or 69 with `--fresh` (tiny and
sample seed 20261031). Earlier reports retain their original case sets rather
than claiming that old measurements included newer tests.

Continuation evidence:

- `candidate-release*.json` / `candidate-sanitized*.json`: checkpoint A/C/D
  prototypes plus the first raw-anchor B implementation. Release includes 69
  differential cases; sanitizer includes 61; each also has four full public hashes.
- `improved-release*.json` / `improved-sanitized*.json`: A parallel output, B
  sparse/bitmap postings, C shared exact-name shards, D packed state/BFS. Each
  configuration passed 69 differential cases and four full public hashes. Build
  records contain source/binary hashes and exact compiler flags.
- `research/tests/c-boundaries.cpp`: 64 alignments across 1-12 workers, checked
  against independently constructed record boundaries under release/sanitizers.
- `research/tests/d-state.cpp`: forced generation wrap with poisoned old state,
  a full-scale 53-bit distance-budget check, and known wide-distance answers.
- New serialized performance trials are under `research/results/`; they retain
  all five samples and local RSS and do not claim official kernel memory.

The generator-based full-seed checks in `tools/fresh_full.py` record both input
and binary SHA-256 values. Their elapsed times are correctness-run diagnostics,
not serialized performance comparisons.

`fresh-full-seed20261031.json` records all four passing fresh full reference
comparisons. `sandbox-continuation.txt` retains the official checker output for
all four rebuilt runtime images. `stream-release.json` and `stream-sanitized.json`
each contain 22 passing B cases for the rejected streaming-phrase experiment;
it provided no memory benefit, and local drift made its timing comparison
inconclusive, so it was not promoted.

Experiment source hashes normalize text line endings. Build source hashes
record the actual local bytes before Git's normal CRLF/LF conversion.

Input files, generated datasets, compiled binaries and reference outputs are
ignored by Git and never copied into the runtime images. Each Dockerfile copies
only its C++ source/header to the compiler stage and the resulting executable to
the final runtime stage.
