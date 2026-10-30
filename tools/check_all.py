"""Run the official starter sandbox checker against each full public hash."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / ".competition/SHA256SUMS.json").read_text(encoding="utf-8-sig"))
for track, spec in manifest["tracks"].items():
    subprocess.run([sys.executable, str(ROOT / "check.py"), track, "--skip-build",
                    "--data", str(ROOT / f"data/{track}/full-seed1"),
                    "--expected", spec["expected_output_sha256"][0]], check=True)
