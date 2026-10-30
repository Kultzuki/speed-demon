"""Validate the optional streaming-phrase B variant against saved reference hashes."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import validate

ROOT = validate.ROOT
source = ROOT / "research/prototypes/b-stream.cpp"
cases = json.loads((ROOT / "validation/improved-release.json").read_text())["results"]
fresh = json.loads((ROOT / "validation/fresh-full-seed20261031.json").read_text())["results"]
manifest = json.loads((ROOT / ".competition/SHA256SUMS.json").read_text())["tracks"]["b"]
for sanitized in [False, True]:
    name = "stream-sanitized" if sanitized else "stream-release"
    destination = ROOT / "build" / name
    destination.mkdir(exist_ok=True)
    binary = destination / "track-b"
    flags = ["-std=c++20", "-pthread"] + (["-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
            if sanitized else ["-O3", "-DNDEBUG", "-static", "-s"])
    subprocess.run(["g++", *flags, "-I", str(ROOT / "track-b"), str(source), "-o", str(binary)], check=True)
    validate.BINARY_DIR = destination
    validate.REPORT.clear()
    for case in cases:
        if case["track"] == "b":
            validate.check("b", case["case"], ROOT / "data/b" / case["case"], case["sha256"])
    validate.check("b", "full-seed1", Path("/benchdata/b"), manifest["expected_output_sha256"][0])
    expected = next(c["sha256"] for c in fresh if c["track"] == "b")
    validate.check("b", "fresh-full-seed20261031", Path("/benchfresh/seed20261031/b"), expected)
    # A common-anchor pattern wraps the ring repeatedly, includes unknown tokens,
    # and must be counted once per document even when it occurs several times.
    data = ROOT / "data/b/stream-ring"
    data.mkdir(exist_ok=True)
    with (data / "docs.txt").open("w", newline="\n") as out:
        for i in range(1000):
            texts = ["a b c d e f g h " * 5, "a b c d unknown f g h", "f g h a b c d e", "a a a a a a a a a"]
            out.write(f"{i}\t{texts[i % 4]}\n")
    (data / "queries.txt").write_text('PHRASE "a b c d e f g h"\nPHRASE "a a a a a a a a"\nPHRASE "h a"\nPHRASE "d e f"\nPHRASE "e f g h a"\n', newline="\n")
    validate.check("b", "stream-ring", data)
    report = {"environment": "Local correctness validation; not official timing", "flags": flags,
              "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "binary_sha256": validate.digest(binary), "results": list(validate.REPORT)}
    (ROOT / "validation" / f"{name}.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS {name}: {len(validate.REPORT)} cases", flush=True)
