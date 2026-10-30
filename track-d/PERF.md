# Track D: performance log

## Published reference

The organizers' scoring-box reference takes 72.69 seconds. This is
published calibration, not our own board run.

## First C++ implementation

Read graph bytes into forward and reverse compressed sparse row arrays with two parsing passes. Each query runs bidirectional Dijkstra on the directed graph, with 64-bit distances, zero weights and parallel edges preserved. Stop when the frontier lower bound reaches the best complete path. Generation stamps avoid clearing every node per query. Six workers own independent search storage; results are written in input order after joining.

Local full public seed 1: output SHA-256 `a23dbdf0a3e49cc8901310a9ee1dc6a9a569a85297b6da75c2a7002cb2ed277e`.
The direct local process check took 4.7394 seconds on the
Windows/WSL2 laptop with input and output on a Windows bind mount. This single
run includes local process launch and file-sharing overhead and is not an
official timing. It is not comparable to the scoring-box reference.

## Board evidence

No scored C++ board run has been recorded yet. The first implementation is
ready for its initial run; its measured run ID, time, memory, source size,
dependency weight and K will be recorded after the board publishes them.
No speedup is claimed from local timings alone.

## Experiments and correctness

Differential checks include all pairs on 20 random directed multigraphs with zero weights and uint32-max weights, plus the official injected cases. Query parallelism preserves only output order, not execution order.
