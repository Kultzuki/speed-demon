FROM gcc:16@sha256:43978d7710a803d1c3d32f4117c1528ec7285a4ce2c0a51e982ec1a6e3d87d95 AS build
WORKDIR /src
COPY main.cpp common.hpp a_ingest_generator.py ./
RUN mkdir -p /tmp/profile /tmp/train /tmp/output \
 && g++ -std=c++20 -O3 -DNDEBUG -pthread -static -s -fprofile-generate=/tmp/profile -fprofile-update=atomic main.cpp -o /solution \
 && python3 a_ingest_generator.py --seed 197731 --scale sample --out /tmp/train \
 && /solution --data /tmp/train --out /tmp/output \
 && python3 a_ingest_generator.py --seed 806317 --scale sample --out /tmp/train \
 && /solution --data /tmp/train --out /tmp/output \
 && g++ -std=c++20 -O3 -DNDEBUG -pthread -static -s -fprofile-use=/tmp/profile -fprofile-correction main.cpp -o /solution

FROM debian:13-slim@sha256:62bd423aeee912639ca8ee681c2b762cb3e25137e0a92b20be455898a9f034ad
COPY --from=build /solution /app/solution
ENTRYPOINT ["/app/solution"]
