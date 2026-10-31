# Continuation 7 - October 31, 2026

Continued the same private repository, four entries and watched `speed-demon`
branch from `c503752efebdbebcd9c6de41a4485af8ef1776fd`. No restart, registration,
reset, force-push, App permission change or agent delegation was performed.

The incoming tree differed from the supplied handover: A already used an exact
first/last-byte hash and C used that hash plus a four-record prefetch ring.
Continuation-6 prototypes, benchmarks and release/sanitizer records were also
present. All 104 incoming changed/untracked files, status, patch and SHA-256
identities were archived byte for byte in ignored `.out/continuation7-incoming`.
The submitted baseline is recovered read-only with `git show`, never by reset.

The refreshed starting board snapshot is
`validation/leaderboard-continuation7-start.json`: CodeScythe 69.160567, rank 18;
Cause Of Death 80.244238. The watch still reads c503752, all four latest runs
pass, and nothing is queued. These are public practice results.

## Measurement setup

`tools/bench7.py` builds isolated sources under `build/bench7`, uses the exact
organizer-pinned clang-format 23.1.3/scc 4.1.0 source counters, and alternates
candidate order. Each run has a fresh cgroup, 12 pinned CPUs, read-only root and
data, no network, 8 GB/no swap, tmpfs output and a fork/exec/exit timer. Every
output hash is checked. Data stays on the existing Linux-local benchmark volume.
Memory includes the small common monitor/output overhead. CPU seconds are
diagnostic; neither these times nor local K ratios are official scores.

Instrumented phase sources are separate from deployable candidates. They use
the monotonic clock through `std::chrono::steady_clock` and print only to stderr.
Source-size counts for instrumented variants are not promotion evidence.

## Initial findings

- A: four alternating runs give baseline 0.077951 s / 30,447,616 bytes / S=290,
  incoming exact hash 0.067486 s / 30,304,256 bytes / S=310. Local K ratio 1.0650.
  `_exit` alone gives 1.0293; parallel `MADV_POPULATE_READ` loses at 0.9225 and
  per-hour reservation loses at 0.9685. Neither prefault nor reservation is
  selected. The parser takes about 26-31 ms and select/format/output 17-19 ms;
  process lifetime also includes teardown not covered by those phase intervals.
- D: initial instrumented runs spend 113-124 ms counting degrees, 31-43 ms in
  prefixes/allocation, 264-342 ms scattering, and 382-402 ms searching. `_exit`
  alone has only a noisy small local effect. Increasing build workers to twelve
  increases CPU work; the initial wall-time difference needs controlled evidence.
- D: one-pass inline adjacency with exact CSR spills is correct on the full
  public hash, but memory offsets most of its time gain. With capacity 3 and 4,
  local K ratios are only 1.0053 and 1.0068; twelve build workers give 0.9566.
  These layouts are not selected. See `research/results/d-inline-build7.json`.

Further isolated measurements and promotion decisions follow below. Current
production A/C are still the archived incoming experiments until a documented
selection is made; B/D are unchanged from the pushed checkpoint.


## Frozen finalists and repeated full-seed comparison

The selected A is the incoming exact partial-byte hash without PGO. B changes
only the lazy posting block capacity. C combines the incoming exact hash and
four-record ring with checked-close early exit. D selects compact owner-sharded
CSR construction; its heap and full-width sparse labels remain unchanged.

| Track | Full seed | Baseline T s | Candidate T s | Candidate cgroup M | S | Local K ratio |
|---|---|---:|---:|---:|---:|---:|
| A | public | 0.068653 | 0.064268 | 30720000 | 310 | 1.012863 |
| A | fresh | 0.078047 | 0.062025 | 30416896 | 310 | 1.105708 |
| B | public | 0.496101 | 0.424977 | 73129984 | 922 | 1.103667 |
| B | fresh | 0.514579 | 0.442578 | 72845312 | 922 | 1.102537 |
| C | public | 0.087715 | 0.082908 | 14884864 | 401 | 1.012654 |
| C | fresh | 0.105814 | 0.083047 | 14663680 | 401 | 1.116693 |
| D | public | 0.839969 | 0.613400 | 125763584 | 450 | 1.141378 |
| D | fresh | 0.850462 | 0.607711 | 125358080 | 450 | 1.135325 |

A/C effects vary across repeat batches; these rows do not establish a stable
gain of that size on the official machine. For example, A's first public batch
was 1.0650 while the later batch was 1.0129. C's incoming hash without exit lost
one public batch (0.9616), and the selected combination ranged from 1.0127 to
1.0511 in the two public batches. Official measurements decide retention.

The simpler 12-byte D heap entries lose, including with the new CSR. Separate
C membership storage also loses. Larger B blocks improve both full seeds;
65,536 entries beat 16,384 and 262,144 on the combined local coefficient.
SIMD B keys and exclusive bitmap words show only small gains and are unselected.

Generator-only PGO was actually tested for A and C using unmodified generators,
sample seeds 197731 and 806317, with no scoring-data training. It is not selected:
A's PGO is faster on the public seed but loses to the simpler hash on the fresh
full seed (0.069123 versus 0.062025 s), while C's additional gain is small and
unstable after build/source cost. Training hashes and binary provenance are in
validation/pgo7-{a,c}-training.json; no PGO generator/build step enters a track.

All selected sources pass 93 release and 93 ASan/UBSan comparisons: the previous
89 plus deliberate A/C partial-hash collisions and two >2 MB parallel D cases
with many wide weights, duplicate edges, zero edges and shard-boundary nodes.
An independent iostream-based test checks every forward/reverse CSR edge and
its multiplicity in both 200,000-edge cases. All prior direct tests and forced
uint64 B offsets also pass. Rebuilt offline sandbox images match validated
release executable hashes exactly. See validation/continuation7-artifact-provenance.json.

The same independently referenced full seed was copied, never regenerated,
into /data/fresh7 in the existing benchmark volume. Every copied input hash
matches its original. The new helper is stopped; no original dataset or volume
was deleted. Official measurement of this candidate bundle is the next step.
