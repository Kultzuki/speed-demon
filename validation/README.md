# Validation evidence

These files distinguish local tests, local experiments and official public-board
measurements. None is a final hidden-seed result or a claim of winning the event.

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

`tools/validate.py` now includes the name-growth case, making its complete
differential suite 58 cases. Baseline and sanitizer reports retain their original
case sets rather than claiming that an older report included the later test.

Input files, generated datasets, compiled binaries and reference outputs are
ignored by Git and never copied into the runtime images. Each Dockerfile copies
only its C++ source/header to the compiler stage and the resulting executable to
the final runtime stage.
