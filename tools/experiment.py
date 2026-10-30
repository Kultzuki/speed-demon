"""Compile and measure a candidate inside the Linux research container.

Inputs must already be verified and copied to /benchdata/<track>. This records
process wall time and RSS, not official cgroup memory or a board score.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("track", choices=list("abcd"))
    parser.add_argument("source", type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()
    source = args.source.read_text()
    if args.workers is not None:
        assert "std::min(6u," in source
        source = source.replace("std::min(6u,", f"std::min({args.workers}u,")
    manifest = json.loads((ROOT / ".competition/SHA256SUMS.json").read_text())["tracks"][args.track]
    data = Path("/benchdata") / args.track
    for name, expected in manifest["inputs_sha256"].items():
        with (data / name).open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == expected
    flags = ["-std=c++20", "-O3", "-DNDEBUG", "-pthread", "-static", "-s"]
    result = {"name": args.name, "track": args.track, "source": str(args.source),
              "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
              "workers": args.workers, "flags": flags, "walls_s": [], "rss_bytes": [],
              "environment": "Local WSL2, Linux-local public seed-1 inputs. RSS is not the official memory axis."}
    with tempfile.TemporaryDirectory(prefix="codescythe-experiment-") as temporary:
        temporary = Path(temporary)
        path = temporary / "main.cpp"
        path.write_text(source)
        binary = temporary / "candidate"
        subprocess.run(["g++", *flags, "-I", str(ROOT / f"track-{args.track}"), str(path), "-o", str(binary)], check=True)
        for run in range(args.runs):
            command = [str(binary), "--data", str(data), "--out", str(temporary)]
            start = time.perf_counter()
            pid = os.posix_spawn(command[0], command, os.environ)
            _, status, usage = os.wait4(pid, 0)
            elapsed = time.perf_counter() - start
            assert os.waitstatus_to_exitcode(status) == 0
            with (temporary / manifest["output"]).open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            assert digest == manifest["expected_output_sha256"][0]
            result["walls_s"].append(elapsed)
            result["rss_bytes"].append(usage.ru_maxrss * 1024)
            print(f"{args.name} run {run+1}: {elapsed:.5f}s RSS={usage.ru_maxrss/1024:.1f}MiB hash PASS", flush=True)
    result["sha256"] = digest
    ordered = sorted(result["walls_s"])
    result["trimmed_mean_s"] = statistics.mean(ordered[1:-1] if len(ordered) >= 3 else ordered)
    target = ROOT / "research/results" / (args.name + ".json")
    target.parent.mkdir(exist_ok=True, parents=True)
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(f"{args.name}: {result['trimmed_mean_s']:.5f}s trimmed mean", flush=True)


if __name__ == "__main__":
    main()
