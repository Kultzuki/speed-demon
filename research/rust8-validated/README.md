# Validated Rust alternatives for Tracks A and D

These are the complete requested Rust implementations, preserved independently
of the active submitted C++ kernels. The user's original D package remains
unchanged at repository-root `track-d-rust/track-d`.

Both Rust packages pass all five official gates at `0ca1987` and `8aa8ddb`, all
97 local comparisons in release/ASan/checked modes, both full seeds, and direct
correctness checks. A's exact endpoint publication also passes an instrumented-
standard-library TSan test. They have zero third-party runtime dependencies and
build offline from allowlisted digest-pinned Dockerfiles.

| Package | Canonical S | Best measured official K | Established best K |
|---|---:|---:|---:|
| track-a | 437 | 31.161629 | 33.234541 |
| track-d | 473 | 14.542976 | 15.399979 |

Neither port beat the established coefficient, so the stronger C++ submissions
were restored under the user's regression rule. These Rust sources remain
available for further work; passing correctness is not a speed-gain claim.

From the repository root, build either package independently:

```powershell
docker build --network=none -t codescythe-rust-a research/rust8-validated/track-a
docker build --network=none -t codescythe-rust-d research/rust8-validated/track-d
```

The entrypoint defaults to `/data` and `/out`, or accepts `--data` and `--out`.
Use the same read-only/no-network/unprivileged sandbox as the competition.
Validated Rust executable directories are `build/rust8-final-{release,asan,checked}`;
the current submitted C++ mix uses `build/rust8-retained-{release,sanitized}`.
Do not interchange their provenance.

See `../CONTINUATION8_RUST.md`, `../RUST8_CORRECTNESS.md`, the two official
summaries, and `../../validation/rust8-final-artifact-provenance-corrected.json`.
The original local counter included TOML lines; its explicit correction and all
raw timing reports are retained rather than silently replaced.
