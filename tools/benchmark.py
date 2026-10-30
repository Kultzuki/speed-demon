"""Local repeatable process timings on Linux files, not official board scores.

Copying the input from the Windows bind mount is deliberately outside the
process timer. This isolates algorithm work from Windows file sharing latency.
RSS is per-process getrusage, not the official cgroup memory measurement.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / ".competition/SHA256SUMS.json").read_text(encoding="utf-8-sig"))
results = []
with tempfile.TemporaryDirectory(prefix="codescythe-bench-") as temp:
    for track, spec in manifest["tracks"].items():
        data = Path(temp) / track
        shutil.copytree(ROOT / f"data/{track}/full-seed1", data)
        output = Path(temp) / (track + "-out")
        output.mkdir()
        walls, rss = [], []
        for run in range(5):
            command = [str(ROOT / f"build/track-{track}"), "--data", str(data), "--out", str(output)]
            started = time.perf_counter()
            pid = os.posix_spawn(command[0], command, os.environ)
            _, status, usage = os.wait4(pid, 0)
            walls.append(time.perf_counter() - started)
            rss.append(usage.ru_maxrss * 1024)
            assert os.waitstatus_to_exitcode(status) == 0
            with (output / spec["output"]).open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            assert actual == spec["expected_output_sha256"][0]
            print(f"{track} run {run + 1}: {walls[-1]:.5f}s RSS={rss[-1]/1e6:.1f}MB", flush=True)
        result = {"track": track, "walls_s": walls, "middle_three_mean_s": statistics.mean(sorted(walls)[1:-1]),
                  "rss_bytes": rss, "sha256": actual}
        results.append(result)
report = {"environment": "Local WSL2 Linux container, inputs copied to Linux filesystem, startup included; RSS is not cgroup memory; not official scores", "results": results}
(ROOT / ".competition/benchmark.json").write_text(json.dumps(report, indent=2))
