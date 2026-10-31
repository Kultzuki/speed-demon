# Rust A/D invariants and evidence

These arguments describe the frozen sources at `0ca1987` and the identical
submitted sources at `8aa8ddb`. They complement executed tests; they do not turn
public-seed measurements into final holdout results.

## A: complete buffered records

The binding maximum line length is
`27 + 1 + 7 + 1 + 125 + 1 + 3 + 1 + 10 + 1 = 177` bytes. For an interior byte
offset x, `align_line` finds the first LF at or after x-1 and returns the byte
after it. The probe needs at most 177 bytes. An existing record boundary remains
unchanged. Alignment is monotone and maps file endpoints to themselves.

Adjacent raw ranges share exactly the same aligned boundary. Their aligned
ranges therefore partition the entire file, with no missing or duplicate record.
Each buffered read parses only through its last LF. The next read starts at the
first unparsed byte; rereading the incomplete suffix does not count it twice.
Every full buffer contains an LF because 256 KiB exceeds the maximum line length.
Every final range ends at LF. Empty input skips reading and creates empty output.

The guard-page suite covers every endpoint length 1..125, all seven methods and
latency sentinel/extreme values. Direct alignment tests check every byte of a
fixture and partitions with 1..19 ranges. A fresh independent reference fixture
also crosses actual 256 KiB buffers and parallel range boundaries.

## A: exact identity and publication

A registry slot moves only `0 -> reserved -> id+1`. The successful CAS elects one
writer; the atomic ID counter gives that writer a distinct name cell. The writer
copies all endpoint bytes and its length before release-publishing the ID.
Readers acquire the published ID before reading that immutable cell. A local
cache receives an ID only after publication. Cells never change or retire.
Main-thread sorting happens after all parser joins.

Thus the `UnsafeCell` sharing protocol never exposes a partially initialized or
mutated name. Full byte equality resolves every partial-hash collision. The
binding catalogue has 1,842 endpoints of at most 125 bytes, covered by the 2,048
IDs and 125-byte owned cells. The fixed capacities are contract bounds, not a
replacement for exact equality. Concurrent publication passes ASan, checked
arithmetic and a TSan test with the standard library rebuilt for the same ABI.

## A: lossless statistics

Bits 12..31 store `min(latency, 2^20-1)`; bits 1..11 store the endpoint ID; bit 0
stores the error flag. The fields are disjoint. Every sentinel record appends its
original uint32 latency to that bucket's overflow stream in the same order.
Persistent parser state preserves that relationship across buffer reads.
Gathering consumes one overflow value per sentinel, retaining all 32 bits.

Counts and group positions are bounded by 3,100,000. Error-ppm multiplication is
uint64 and fits below 3.1e12. For a nonempty group, each rank
`ceil(p*n/100)-1` is in range. Successive nth selections touch only the suffix
after earlier selected ranks; repeated ranks are already selected and skipped.
Duplicates are retained. Sorting full endpoint bytes and streaming ready hours
produces the same total output order for every scheduling/ID assignment.

## D: complete compact CSR

Atomic degree counts and prefix sums establish every node's exact CSR interval.
A cursor fetch-add claims one distinct position for each input edge, separately
in each direction. Both construction passes use the same complete-line cuts.
Joining parsers freezes the arrays before search. An independent text parser
compares every forward/reverse edge and duplicate multiplicity in two parallel
200,000-edge fixtures, including many wide weights.

Let b be the node bits derived from n and s=32-b. A word stores the node in its
upper b bits and small weights below the s-bit sentinel. A weight at or above
the sentinel has a separately indexed exact uint32 value. No wide value is
truncated; sentinel positions are unique and sorted before lookup.

## D: full-width sparse state and safe wrap

Distances occupy a separate aligned uint64 vector. Tags are uint32 values
`(epoch << b) | node`. Since node < 2^b, a node cannot alter generation bits.
Epoch 0 is inactive; search clears state before its first lookup. Active epochs
range from 1 through `UINT32_MAX >> b`. On exhaustion, every tag is cleared before
epoch 1 is reused. An old epoch-1 key therefore cannot survive the wrap.

Linear probing inserts at the first inactive-generation slot. The load factor
stays below one half, so an inactive slot exists. Rehash copies every active key
and its full distance to equal-length power-of-two vectors. No distance or heap
key is packed into a narrow integer. Direct tests force growth and wrap at
multiple node-width boundaries, including the single-generation-bit case.

## D: exact search and arithmetic

Each side independently extracts its smallest non-stale tentative distance.
Nonnegative weights make radix keys monotone; zero weights and duplicate keys
remain valid. Candidate `best` is the length of an actual forward/reverse joined
walk and hence an upper bound. Once the sum of cleaned frontier minima reaches
that bound, no shorter unfinished path remains. Choosing the smaller frontier
affects work only; it does not change either side's minimum extraction rule.

The supported compact node width has b < 32. Consequently n <= 2^31 and a shortest
simple path costs at most `(n-1)*(2^32-1) < INT64_MAX`. Relaxed labels and sums with
the inactive sentinel fit uint64. Arrays retain those full values. Isolated,
zero-distance, same-node, parallel-edge, wide-distance and unreachable cases are
checked independently against the frozen reference, including all-pairs random
multigraph fixtures and both full seeds.

## Artifacts and limits

The 97-comparison release, ASan and checked-arithmetic mixes, direct tests and
offline sandbox images agree. Image executables and Git-normalized LF source
builds match exact validated release hashes. Unchanged B/C provenance is retained.
Corrected canonical S is A=437 and D=473; TOML/data is excluded by the organizer's
counter. Original erroneous local totals remain preserved with an explicit
correction rather than replacing raw timing evidence.

Official scores are recorded separately by commit/run ID. The first Rust run
passes all five gates but does not exceed the historical A/D best coefficients.
No invariant above proves a speed gain or a first-place result.
