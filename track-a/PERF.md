# Track A: performance log

## Published reference

The organizers' scoring-box reference takes 32.05 seconds. This is
published calibration, not our own board run.

## First C++ implementation

Parse only the fixed UTC hour, endpoint, error-status digit and integer latency. Ignore method and sub-hour timestamp fields. Intern endpoints and keep 72 groups per endpoint; the complete span is fixed by the spec. Sort small groups and select the three nearest ranks in large groups, preserving previously selected ranks. Sort output endpoint keys lexicographically for each hour. All percentile and error-ppm arithmetic uses integers.

Local full public seed 1: output SHA-256 `495ca09682b9673ef836a506496177680bb4a3af54255174befddb1f83481cd3`.
The direct local process check took 2.4244 seconds on the
Windows/WSL2 laptop with input and output on a Windows bind mount. This single
run includes local process launch and file-sharing overhead and is not an
official timing. It is not comparable to the scoring-box reference.

## Board evidence

No scored C++ board run has been recorded yet. The first implementation is
ready for its initial run; its measured run ID, time, memory, source size,
dependency weight and K will be recorded after the board publishes them.
No speedup is claimed from local timings alone.

## Experiments and correctness

Full-scale checking found a partition-selection bug: a later nth_element could move a previously selected percentile. Starting each later partition after the selected rank fixes it. A dedicated test covers group sizes 1, 2, 3, 99, 100, 101, 128, 129, 257 and 1001, including duplicate and extreme uint32 latencies. This correction was made before the first push.
