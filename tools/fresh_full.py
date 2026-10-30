"""Generate a fresh full seed on Linux-local storage and compare exact outputs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import validate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261031)
    parser.add_argument("--binary-dir", type=Path, required=True)
    args = parser.parse_args()
    validate.BINARY_DIR = args.binary_dir.resolve()
    provenance = {}
    for track in "abcd":
        data = Path(f"/benchfresh/seed{args.seed}/{track}")
        subprocess.run([sys.executable, str(validate.OFFICIAL / f"generators/{validate.MODULE[track]}.py"),
                        "--seed", str(args.seed), "--scale", "full", "--out", str(data)], check=True)
        inputs = {p.name: validate.digest(p) for p in sorted(data.iterdir()) if p.is_file()}
        binary_hash = validate.digest(validate.BINARY_DIR / f"track-{track}")
        validate.check(track, f"fresh-full-seed{args.seed}", data)
        provenance[track] = {"inputs_sha256": inputs, "binary_sha256": binary_hash}
    report = {"environment": "Local Linux/WSL2; correctness only, not a performance comparison",
              "seed": args.seed, "provenance": provenance, "results": validate.REPORT}
    path = validate.ROOT / f"validation/fresh-full-seed{args.seed}.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS fresh full seed for all tracks: {path}", flush=True)


if __name__ == "__main__":
    main()
