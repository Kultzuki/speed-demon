"""Reproduce release/sanitizer checks for the selected checkpoint candidates."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {"a": "a-parallel.cpp", "b": "b-raw-anchors.cpp",
           "c": "c-parallel.cpp", "d": "d-packed-bfs.cpp"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sanitized", action="store_true")
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--improved", action="store_true")
    args = parser.parse_args()
    name = "candidate-sanitized" if args.sanitized else "candidate-release"
    sources = dict(SOURCES)
    if args.improved:
        sources.update(a="a-parallel-output.cpp", b="b-hybrid.cpp", c="c-shared.cpp")
        name = name.replace("candidate", "improved")
    output = ROOT / "build" / name
    output.mkdir(parents=True, exist_ok=True)
    flags = ["-std=c++20", "-pthread"]
    flags += (["-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
              if args.sanitized else ["-O3", "-DNDEBUG", "-static", "-s"])
    provenance = {}
    for track, source in sources.items():
        subprocess.run(["g++", *flags, "-I", str(ROOT / f"track-{track}"),
                        str(ROOT / "research/prototypes" / source), "-o", str(output / f"track-{track}")], check=True)
        provenance[track] = {"source": source,
                             "source_sha256": hashlib.sha256((ROOT / "research/prototypes" / source).read_bytes()).hexdigest(),
                             "binary_sha256": hashlib.sha256((output / f"track-{track}").read_bytes()).hexdigest()}
    (ROOT / "validation" / f"{name}-build.json").write_text(json.dumps({"flags": flags, "tracks": provenance}, indent=2) + "\n")
    for track, source in [("c", "c-boundaries.cpp"), ("d", "d-state.cpp")]:
        binary = output / source.removesuffix(".cpp")
        candidate = ROOT / "research/prototypes" / sources[track]
        subprocess.run(["g++", *flags, f'-DCANDIDATE_SOURCE="{candidate}"', "-I", str(ROOT / f"track-{track}"),
                        str(ROOT / "research/tests" / source), "-o", str(binary)], check=True)
        command = [str(binary)]
        if track == "d": command.append(str(ROOT / "data/d/worked-example/graph.txt"))
        subprocess.run(command, check=True)
    base = [sys.executable, str(ROOT / "tools/validate.py"), "--binary-dir", str(output), "--reuse-generated"]
    subprocess.run(base + ["--report", str(ROOT / "validation" / f"{name}.json")]
                   + (["--fresh"] if args.fresh else []), check=True)
    subprocess.run(base + ["--full", "--report", str(ROOT / "validation" / f"{name}-full.json")], check=True)


if __name__ == "__main__":
    main()
