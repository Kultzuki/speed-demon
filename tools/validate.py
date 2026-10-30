"""Differential checks against the frozen references, plus official public hashes.

Run inside the compiler container with Python 3, after compiling build/track-*.
The report labels all timings as local and includes the exact dataset/hash.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = ROOT / ".competition/official"
MODULE = {"a": "a_ingest", "b": "b_index", "c": "c_join", "d": "d_traverse"}
OUTPUT = {"a": "summary.txt", "b": "results.txt", "c": "aggregates.txt", "d": "distances.txt"}
REPORT = []


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def check(track, label, data, expected=None):
    target = ROOT / ".out/validation" / track / label
    target.mkdir(parents=True, exist_ok=True)
    if expected is None:
        reference = target / "reference"
        reference.mkdir(exist_ok=True)
        subprocess.run([sys.executable, str(OFFICIAL / f"reference/{MODULE[track]}.py"),
                        "--data", str(data), "--out", str(reference)], check=True)
        expected = digest(reference / OUTPUT[track])
    started = time.perf_counter()
    subprocess.run([str(ROOT / f"build/track-{track}"), "--data", str(data),
                    "--out", str(target)], check=True, timeout=120)
    elapsed = time.perf_counter() - started
    actual = digest(target / OUTPUT[track])
    if actual != expected:
        raise AssertionError(f"{track}/{label}: {actual} != {expected}")
    entry = {"track": track, "case": label, "sha256": actual, "local_seconds": round(elapsed, 6)}
    REPORT.append(entry)
    print(f"PASS {track}/{label} {elapsed:.4f}s {actual}", flush=True)


def generated(tracks, scales):
    for scale, seed in scales:
        for track in tracks:
            data = ROOT / f"data/{track}/{scale}-seed{seed}"
            subprocess.run([sys.executable, str(OFFICIAL / f"generators/{MODULE[track]}.py"),
                            "--seed", str(seed), "--scale", scale, "--out", str(data)], check=True,
                           stdout=subprocess.DEVNULL)
            check(track, f"{scale}-seed{seed}", data)


def worked_examples():
    for track in "abcd":
        module = load(f"test_worked_{track}", OFFICIAL / f"tests/test_{MODULE[track]}.py")
        data = ROOT / f"data/{track}/worked-example"
        data.mkdir(parents=True, exist_ok=True)
        if track == "a":
            files = {"requests.log": module.WORKED_INPUT.encode()}
        elif track == "b":
            files = {"docs.txt": module.EXAMPLE_DOCS, "queries.txt": module.EXAMPLE_QUERIES}
        elif track == "c":
            files = {"records.csv": module.WORKED_RECORDS, "regions.csv": module.WORKED_REGIONS}
        else:
            files = {"graph.txt": module.EXAMPLE_GRAPH.encode(), "queries.txt": module.EXAMPLE_QUERIES.encode()}
        for name, contents in files.items():
            (data / name).write_bytes(contents)
        check(track, "worked-example", data)


def adversarial():
    rng = random.Random(90210)
    # Arbitrary directed multigraphs, not just the official road distribution.
    for seed in range(20):
        n = rng.randrange(2, 35)
        edges = [(rng.randrange(n), rng.randrange(n), rng.choice([0, 1, 3, 17, 2**32 - 1]))
                 for _ in range(rng.randrange(n, n * 7))]
        data = ROOT / f"data/d/fuzz{seed}"
        data.mkdir(parents=True, exist_ok=True)
        (data / "graph.txt").write_text(f"{n} {len(edges)}\n" + "".join(f"{u} {v} {w}\n" for u, v, w in edges))
        (data / "queries.txt").write_text("".join(f"{s} {t}\n" for s in range(n) for t in range(n)))
        check("d", f"fuzz{seed}", data)
    # Exact byte tokenization, repeated tokens, mixed operators and boundaries.
    words = ["a", "b", "c", "the", "and", "not", "007", "7", "Zürich", "İSTANBUL", "K", "ﬁ", "CAFÉ"]
    separators = [" ", "—", "'", "/", ". ", "\u00a0"]
    for seed in range(10):
        data = ROOT / f"data/b/fuzz{seed}"
        data.mkdir(parents=True, exist_ok=True)
        docs = [rng.choice(separators).join(rng.choices(words, k=rng.randrange(30))) for _ in range(70)]
        (data / "docs.txt").write_text("".join(f"{i}\t{text}\n" for i, text in enumerate(docs)), encoding="utf-8")
        queries = []
        for _ in range(300):
            terms = rng.choices(["a", "b", "c", "the", "and", "not", "007", "7", "z", "rich", "stanbul", "caf", "absent"], k=rng.randrange(2, 7))
            if rng.random() < 0.5:
                queries.append('PHRASE "' + " ".join(terms) + '"')
            else:
                q = terms[0]
                for term in terms[1:]:
                    q += " " + rng.choice(["AND", "OR", "NOT"]) + " " + term
                queries.append("BOOL " + q)
        (data / "queries.txt").write_text("\n".join(queries) + "\n")
        check("b", f"fuzz{seed}", data)
    # End-of-file CSV termination, escaped quotes, BOMs and significant spaces.
    data = ROOT / "data/c/final-no-newline"
    data.mkdir(parents=True, exist_ok=True)
    (data / "regions.csv").write_bytes(b"region_id,country\n1,AAA\n2,BBB\n3,CCC\n")
    (data / "records.csv").write_bytes(
        b'\xef\xbb\xbfid,name,note,region_id,amount\r\n'
        b'1,"Ann ""Annie"" Lee","""start\nend""",1,-0.01\n'
        b'\xef\xbb\xbf2,"Ann ""Annie"" Lee ","x,y",1,10.00\r\n'
        b'3,,,9999999,0.00\n4,"","",1,99999.99\r\n'
        b'5,"same","",2,-999.99\n6,"same ","",2,-0.99')
    check("c", "final-no-newline", data)
    data = ROOT / "data/a/empty"
    data.mkdir(parents=True, exist_ok=True)
    (data / "requests.log").write_bytes(b"")
    check("a", "empty", data)
    data = ROOT / "data/a/percentile-boundaries"
    data.mkdir(parents=True, exist_ok=True)
    lines = []
    for n in [1, 2, 3, 99, 100, 101, 128, 129, 257, 1001]:
        values = [rng.choice([0, 1, rng.randrange(2**32), 2**32 - 1]) for _ in range(n)]
        rng.shuffle(values)
        for i, value in enumerate(values):
            lines.append(f"2026-11-01T00:00:00.000000Z GET /n{n} {rng.choice([200, 499, 500, 599])} {value}\n")
    rng.shuffle(lines)
    (data / "requests.log").write_text("".join(lines))
    check("a", "percentile-boundaries", data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    if args.full:
        manifest = json.loads((ROOT / ".competition/SHA256SUMS.json").read_text(encoding="utf-8-sig"))
        for track, spec in manifest["tracks"].items():
            data = ROOT / f"data/{track}/full-seed1"
            for name, expected in spec["inputs_sha256"].items():
                assert digest(data / name) == expected, (track, name)
            check(track, "full-seed1", data, spec["expected_output_sha256"][0])
    else:
        worked_examples()
        generated("abcd", [("tiny", 1), ("tiny", 2), ("tiny", 17)])
        adversarial()
        if not args.quick:
            generated("abcd", [("sample", 2), ("sample", 17)])
    report = ROOT / (".competition/full-validation.json" if args.full else ".competition/validation.json")
    report.write_text(json.dumps({"environment": "local Linux container on Windows WSL2; not official board timings", "results": REPORT}, indent=2))
    print(f"PASS: {len(REPORT)} cases. Report: {report}", flush=True)


if __name__ == "__main__":
    main()
