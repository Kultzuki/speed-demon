"""Download official public inputs, verifying every file before using it."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://s3.amazonaws.com/raptors.dev/speeddemon.dev/2026/data/"


def request(url):
    return urllib.request.urlopen(urllib.request.Request(
        url, headers={"User-Agent": "CodeScythe-validation/1.0"}), timeout=120)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    with request(BASE + "SHA256SUMS.json") as response:
        manifest = json.load(response)
    (ROOT / ".competition").mkdir(exist_ok=True)
    (ROOT / ".competition/SHA256SUMS.json").write_text(json.dumps(manifest, indent=2))
    for track, spec in manifest["tracks"].items():
        folder = ROOT / "data" / track / "full-seed1"
        folder.mkdir(parents=True, exist_ok=True)
        for name, expected in spec["inputs_sha256"].items():
            path = folder / name
            if path.exists() and digest(path) == expected:
                print(f"cached {track}/{name}", flush=True)
                continue
            partial = path.with_suffix(path.suffix + ".partial")
            with request(BASE + f"track-{track}/full-seed1/{name}") as response:
                with partial.open("wb") as output:
                    while chunk := response.read(1 << 20):
                        output.write(chunk)
            if digest(partial) != expected:
                raise RuntimeError(f"Input hash mismatch: {track}/{name}")
            partial.replace(path)
            print(f"verified {track}/{name}: {path.stat().st_size} bytes", flush=True)


if __name__ == "__main__":
    main()
