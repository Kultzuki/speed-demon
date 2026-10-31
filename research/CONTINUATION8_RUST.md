# Continuation 8: Rust A and D - October 31, 2026

Continued the existing private CodeScythe entry and speed-demon branch from
e9deec07fa38f9abf0c167d6768c41c388e37ba5. No restart, registration, reset,
force-push or agent delegation. The complete incoming handover is preserved as
HANDOVER_INCOMING_RUST8.md. All 12 incoming dirty files were archived byte for
byte in .out/continuation8-rust-incoming; original user D and the interim tree
are also preserved in .out/continuation8-user-d-rust. Earlier evidence is retained.

The fresh starting feed is validation/leaderboard-rust8-start.json: aggregate
69.780860, rank 26, leader 81.805732. These are dated public practice results.
First place remains outstanding; no local timing is an official score.

## User-supplied Rust D

Read every file under track-d-rust/track-d. Original files are unchanged and
their hashes are checked in final provenance. The source accepts positional
paths instead of --data/--out, and its manifest says "your team name". Its
PERF notes describe a separate 2-core machine and have no official run IDs.
Those historical times are not independently verified here.

A CLI-only adapter is research/prototypes/d-user-cli8.rs. It matches the public
full hash. In an alternating local full comparison it takes 0.810449 s and
299,954,176 cgroup bytes (S=316), versus the established C++ entry's 0.762841 s,
123,367,424 bytes and S=385: local K ratio 0.836661. The radix heap was adapted
into the exact bidirectional port; BFS/forward search was not promoted.

## Frozen candidates and local measurements

A owns full endpoint bytes, uses persistent worker caches and small buffered
parallel reads, retains exact packed-record overflow and selects percentiles
in parallel. D preserves the established compact two-pass forward/reverse CSR
and bidirectional radix search while separating aligned full uint64 distances
from width-derived uint32 node/generation tags. Epoch wrap clears tags safely.
No distance narrowing, cached answers or hash-only equality is introduced.

The complete local coefficient uses fresh cgroups, exec-to-exit timing, 8 GB/no
swap, twelve pinned CPUs, read-only root/data, no network, measured memory.peak,
canonical rustfmt 1.10.0/scc 4.1.0 source counts and D=1. Alternating full runs
check every output hash. Results are noisy; the table does not establish a
stable gain on the official CPU. D's earlier local-to-official failure remains
the reason official measurement decides retention.

| Track | Full seed | C++ T s | Rust T s | Rust M bytes | Rust S | Local K ratio |
|---|---|---:|---:|---:|---:|---:|
| A | public | 0.068161 | 0.065565 | 24264704 | 449 | 1.004586 |
| A | fresh | 0.063933 | 0.055420 | 24121344 | 449 | 1.057827 |
| D | public | 0.944865 | 0.868140 | 105361408 | 485 | 1.037259 |
| D | fresh | 0.860158 | 0.813380 | 99201024 | 485 | 1.020718 |

Canonical selected S is A=449, D=485, with zero third-party runtime dependencies.
Selection: rust8-selection.json. Prior exact C++ sources are in baseline8/.
B/C submitted sources remain unchanged and their validated binaries are reused.

## Rejected or unselected work

All raw reports remain under results/ and exact sources under prototypes/.
Mapped Rust A, owned-key-only changes, simple early exit, the dedicated writer,
six/twelve-worker alternatives and SWAR decimal parsing did not provide a
consistent complete-coefficient advantage. The simpler buffered scalar version
was selected. The SWAR version remains validated research, not the submitted path.

D's full-width packed one-pass intermediate raises peak construction memory and
source cost without a stable K gain. Single-probe relaxation and six query
workers also lose the matched final comparison. The simpler two-pass, twelve-
query-worker sparse state wins locally on both full seeds. No rejected owner-
sharded builder, narrow label or 12-byte packed heap was repeated.

Initial monotonic instrumentation records A parsing near 30-35 ms, plus gather,
selection/formatting and serialized output. D spends roughly 120-135 ms counting,
45-55 ms prefixing/allocating, 245-295 ms scattering, and 400-485 ms searching.
These are separate instrumented WSL2 binaries and diagnostic phase intervals,
not deployable timing or source-size evidence. Final instrumented sources and
measurements are recorded separately when available.

## Validation and offline artifacts

build/rust8-final-{release,asan,checked}/track-* each pass all previous 93
comparisons plus four fresh reference cases (97 total), including both full seeds.
Rust direct tests cover 4,375 guard-page parses, concurrent exact endpoint
publication, every byte of an alignment fixture, decimal widths, duplicate
percentile ranks, sparse growth/epoch wrap, full-width weights/distances and
complete forward/reverse CSR multiplicities on both 200,000-edge fixtures.

Rust A/D use AddressSanitizer and a separate checked-arithmetic build; unchanged
C++ B/C use their validated ASan/UBSan executables. No Rust UBSan claim is made.
The extra TSan publication test rebuilt std/test with the same sanitizer ABI.
The default container blocked TSan's process-local ASLR control; the dedicated
race-test container permits it, with network none and a read-only binary mount.
That check passes. No global ASLR or official sandbox setting was changed.

All four offline images pass the official starter sandbox and public hashes.
Every image executable exactly matches its validated release binary. Provenance:
validation/rust8-final-artifact-provenance.json, validation/image-sizes-rust8-final.json,
validation/rust8-final-safety-gates.txt and validation/rust8-tsan-publication.json.
The existing B forced-uint64-offset and C direct checks retain their unchanged
source/binary provenance from continuation 7.

Official submission and retention decisions follow below. No first-place claim.


## Final phase and packaging evidence

results/rust8-final-phases.json records the separate final monotonic profile.
The first A run is cold (303 ms in parsing/reads); later warm runs parse in
30.94-32.65 ms and reach checked output closure in 46.90-48.01 ms. Their worker
read intervals are about 4.7-6.0 ms; sampled exact hash/lookup timing includes
clock overhead and is diagnostic only. Gather, selection, formatting and output
intervals are reported per worker. D's later runs count in 83.64-137.39 ms,
prefix/allocate in 41.84-42.60 ms, scatter in 248.15-253.12 ms and search in
388.77-393.17 ms. The first D run is slower too. No cold run is silently removed
from the raw report, and these instrumented values do not replace uninstrumented K.

Both Cargo manifests/locks check offline. LF-normalized Rust sources compile to
the exact validated release and image executables:
validation/rust8-lf-artifact-provenance.json. Complete source/configuration copies
are retained in rust8-validated/ even if official measurements reject a port.


## Canonical source-counter correction during official build

The initial local Rust counter mistakenly included TOML manifest code lines.
The organizer's static_axes.NOT_CODE excludes TOML/data. The actual canonical
totals are **A=437, D=473**, both D=1, rather than the conservative 449/485
shown in the original pre-push reports. Those raw reports, timings, memory and
source hashes are retained verbatim. Only the coefficient calculation changes.
Corrected evidence: validation/rust8-canonical-source-correction.json,
validation/rust8-final-static-corrected.json and
validation/rust8-final-artifact-provenance-corrected.json. No kernel or binary
changed. Corrected selected local coefficients are
research/results/rust8-corrected-selected-coefficients.json.


## Official result at 0ca1987

All five gates pass on every track at 0ca1987477223527268d60911e073ff334feb8bd. Captured 2026-10-31T15:58:55.698572+00:00: aggregate 69.780860, rank 28, leader 81.805732. Unchanged-source rerun: False.

| Track | T s | M bytes | S | K | Incoming exact-head K | Historical best K | Run |
|---|---:|---:|---:|---:|---:|---:|---|
| A | 0.045110 | 23592960 | 437 | 30.827569 | 29.654383 | 33.234541 | run-672e375ec819 |
| B | 0.346143 | 71774208 | 922 | 17.875749 | 19.243317 | 19.373796 | run-bfdb1fa492e6 |
| C | 0.061315 | 13463552 | 401 | 24.423479 | 24.343070 | 24.427280 | run-026c3a6758fb |
| D | 0.397762 | 102604800 | 473 | 14.542976 | 14.469309 | 15.399979 | run-5ccc134f1b0c |

B/C sources are unchanged. A/D historical records are not improved by the first Rust run; first place remains outstanding. Public practice is separate from final holdouts and judging.
