"""Serialized continuation experiments; do not run beside validation/build jobs."""
import subprocess
import sys

TRIALS = [
    ("a", "a-baseline.cpp", "a-baseline-confirm", None),
    ("a", "a-parallel-output.cpp", "a-parallel-output-6", 6),
    ("b", "b-baseline.cpp", "b-baseline-confirm", None),
    ("b", "b-hybrid.cpp", "b-hybrid-6", 6),
    ("c", "c-parallel.cpp", "c-parallel-3-confirm", 3),
    ("c", "c-parallel.cpp", "c-parallel-6-confirm", 6),
    ("d", "d-packed-bfs.cpp", "d-packed-bfs-4", 4),
    ("d", "d-packed-bfs.cpp", "d-packed-bfs-6-confirm", 6),
]
for track, source, name, workers in TRIALS:
    command = [sys.executable, "tools/experiment.py", track, "research/prototypes/" + source,
               "--name", name, "--runs", "5"]
    if workers is not None: command += ["--workers", str(workers)]
    subprocess.run(command, check=True)
