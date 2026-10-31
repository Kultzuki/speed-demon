FROM rust:1-trixie@sha256:931c2c0531a8b143e044f0f3914dfe802f15bb3d1955f0b657e9359327ac2ffc AS build
WORKDIR /src
COPY main.rs common.rs ./
RUN rustc --edition=2021 -C opt-level=3 -C lto=fat -C codegen-units=1 -C panic=abort -C strip=symbols -C target-feature=+crt-static -C target-cpu=x86-64-v3 main.rs -o /solution

FROM debian:13-slim@sha256:62bd423aeee912639ca8ee681c2b762cb3e25137e0a92b20be455898a9f034ad
COPY --from=build /solution /app/solution
ENTRYPOINT ["/app/solution"]
