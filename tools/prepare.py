"""Keep each independently built track self-contained."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = """FROM gcc:16@sha256:43978d7710a803d1c3d32f4117c1528ec7285a4ce2c0a51e982ec1a6e3d87d95 AS build
WORKDIR /src
COPY main.cpp common.hpp ./
RUN g++ -std=c++20 -O3 -DNDEBUG -pthread -static -s main.cpp -o /solution

FROM debian:13-slim@sha256:62bd423aeee912639ca8ee681c2b762cb3e25137e0a92b20be455898a9f034ad
COPY --from=build /solution /app/solution
ENTRYPOINT ["/app/solution"]
"""

for track in "abcd":
    folder = ROOT / f"track-{track}"
    shutil.copyfile(ROOT / "tools/common.hpp", folder / "common.hpp")
    (folder / "Dockerfile").write_text(DOCKERFILE, encoding="utf-8", newline="\n")
    (folder / ".speed-demon.toml").write_text(
        f'track = "{track}"\nteam = "CodeScythe"\nlanguage = "C++"\ndependency_count = 0\n',
        encoding="utf-8", newline="\n")
