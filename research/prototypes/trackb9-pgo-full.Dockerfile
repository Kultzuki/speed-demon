FROM python:3.13-slim@sha256:d98cc29d3266e535dd9da1099688d9cb3ca4753813571e071763d17725460962 AS training
WORKDIR /src
COPY b_index_generator.py ./
RUN python3 b_index_generator.py --seed 60773 --scale full --out /train/60773 \
 && python3 b_index_generator.py --seed 284911 --scale full --out /train/284911

FROM gcc:16@sha256:43978d7710a803d1c3d32f4117c1528ec7285a4ce2c0a51e982ec1a6e3d87d95 AS build
WORKDIR /src
COPY main.cpp common.hpp ./
COPY --from=training /train /train
RUN mkdir -p /tmp/profile /tmp/output \
 && g++ -std=c++20 -O3 -DNDEBUG -march=x86-64-v3 -pthread -static -s -fprofile-generate=/tmp/profile -fprofile-update=atomic main.cpp -o /solution \
 && /solution --data /train/60773 --out /tmp/output \
 && /solution --data /train/284911 --out /tmp/output \
 && g++ -std=c++20 -O3 -DNDEBUG -march=x86-64-v3 -pthread -static -s -fprofile-use=/tmp/profile -fprofile-correction -Werror=missing-profile main.cpp -o /solution

FROM debian:13-slim@sha256:62bd423aeee912639ca8ee681c2b762cb3e25137e0a92b20be455898a9f034ad
COPY --from=build /solution /app/solution
ENTRYPOINT ["/app/solution"]
