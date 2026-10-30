# Track B: performance log

## Published reference

The organizers' scoring-box reference takes 56.35 seconds. This is
published calibration, not our own board run.

## First C++ implementation

Read all queries first and index only their terms. Corpus tokenization lowercases ASCII A-Z only; all other non-alphanumeric bytes are separators. Sorted document postings support strictly left-to-right Boolean set operations. For phrases, select the least frequent occurrence list as the anchor and compare exact adjacent token IDs. A boundary bit on every document's final token forbids cross-document matches. Full string equality resolves dictionary hash collisions; results are exact.

Local full public seed 1: output SHA-256 `f86973c210228141bcb6f1f1b10188ad2a9b65f71e7cd7cf4590b38de4e80927`.
The direct local process check took 14.6211 seconds on the
Windows/WSL2 laptop with input and output on a Windows bind mount. This single
run includes local process launch and file-sharing overhead and is not an
official timing. It is not comparable to the scoring-box reference.

## Board evidence

No scored C++ board run has been recorded yet. The first implementation is
ready for its initial run; its measured run ID, time, memory, source size,
dependency weight and K will be recorded after the board publishes them.
No speedup is claimed from local timings alone.

## Experiments and correctness

Differential cases include ASCII case conversion, UTF-8 separators, repeated phrase terms, sentence punctuation, absent terms, empty documents and mixed left-associative Boolean operators.
