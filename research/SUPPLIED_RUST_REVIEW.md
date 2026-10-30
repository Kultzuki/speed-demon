# Review of the four supplied Rust implementations

The attachments were read completely in the supplied order B, A, C, D. Exact
copies are retained under `research/supplied/track-*.rs`; their source hashes,
compiler version and executed checks are in `validation/supplied-rust-review.json`.
They are research candidates, not instructions to replace the measured entry.

All four compile with the installed native Windows Rust compiler and match their
published full seed-1 output hashes. These checks establish that seed only.
Windows runtimes are not compared with the Linux C++ experiments.

| Track | Finding | Decision |
|---|---|---|
| B | `check_phrase_in_doc` truncates at 1,024 tokens. A document containing 256 copies of `writ of habeas corpus` followed by `bail bond` returns no phrase match, while the boolean query finds the same document. | Cannot promote unchanged. |
| A | Exact uint32 latencies, nearest-rank percentiles, runtime endpoint discovery and fixed timestamp span are appropriate. The global registry and local snapshots add locks and endpoint copying; per-group vectors and serial percentile/output work remain. | Viable candidate, but no measured evidence of an advantage over the new C++ architecture. |
| C | Distinct names are represented only by two hashes, without retaining or comparing the name. This is probabilistic identity and does not satisfy exact distinct counting. The streaming parser also assumes 64 KiB lookahead covers a whole record. | Cannot promote unchanged. A 100,000-byte name aligned across the 2 MiB read boundary makes the supplied implementation stop making progress. |
| D | Forward Dijkstra preserves zero weights and uint64 distances, and removing nonnegative self-loops is safe. Binary heaps, full per-worker distance/epoch arrays and static query batches remain; it does not implement bidirectional radix search. | Reasonable correctness baseline, not evidence of a first-place improvement. |

The C long-name fixture uses fewer than 131,072 bytes per field and is also
checked against the frozen Python CSV reference. Names have no fixed trailing
space bound in the published contract. A timed-out process is terminated by the
test runner. The comment claiming peak RSS below 50 MB has no measurement in the
attachment and ignores potentially millions of country/name hash entries.

The B idea of intersecting term postings before scanning candidate documents was
implemented separately as `b-docfilter.cpp`, using streaming exact phrase matching
without a fixed token-count cap. It passes the full public hash, but the paired
five-run experiment was slower: 1.05193s versus 0.86284s for the compact-posting
candidate in that batch. It saved only a few MiB of local process RSS and was not
selected. Those are local measurements, not official score/memory claims.

Useful retained direction: indexing only query terms, exact ASCII tokenization,
bounded-width IDs backed by a proof or checked fallback, CSR, parallel parsing,
and exact integer formatting. Several are already in the measured C++ entry.
No runtime library or language migration was introduced on the strength of these
attachments.
