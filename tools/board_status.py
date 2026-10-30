"""Read the public board; optionally wait for a specific pushed commit."""
import argparse
import json
from pathlib import Path
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
URL = "https://s3.amazonaws.com/raptors.dev/speeddemon.dev/2026/board/board.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", default="")
    parser.add_argument("--wait", type=int, default=0)
    args = parser.parse_args()
    deadline = time.monotonic() + args.wait
    previous = None
    while True:
        request = urllib.request.Request(URL, headers={"User-Agent": "CodeScythe-board-status/1.0"})
        with urllib.request.urlopen(request, timeout=25) as response:
            board = json.load(response)
        team = next((t for t in board["teams"] if t.get("team", "").lower() == "codescythe"), None)
        if team is None:
            print("CodeScythe is not in the current public feed", flush=True)
            return 2
        latest = {track: item.get("latest") or {} for track, item in team["tracks"].items()}
        watch = team.get("watch") or {}
        queue = team.get("queue") or {}
        summary = {"watch": {key: watch.get(key) for key in ["ok", "error", "head"]},
                   "queue": {key: ({k: value.get(k) for k in ["state", "commit", "builder"]} if isinstance(value, dict) else value)
                             for key, value in queue.items()},
                   "tracks": {t: {key: run.get(key) for key in
                                    ["run_id", "commit", "stage", "ok", "T_s", "M_bytes", "S", "D", "K", "points", "failure"]}
                              for t, run in latest.items()}}
        text = json.dumps(summary, sort_keys=True)
        if text != previous:
            print(json.dumps(summary, indent=2), flush=True)
            previous = text
            (ROOT / ".competition/board-team.json").write_text(json.dumps(team, indent=2))
        matching = len(latest) == 4 and all(run.get("commit", "").startswith(args.commit) for run in latest.values())
        if matching and all(run.get("ended_at") is not None for run in latest.values()):
            return 0 if all(run.get("ok") for run in latest.values()) else 2
        if args.wait == 0 or time.monotonic() >= deadline:
            return 0
        time.sleep(min(20, max(0, deadline - time.monotonic())))


if __name__ == "__main__":
    raise SystemExit(main())
