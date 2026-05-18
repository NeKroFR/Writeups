FROM docker.io/library/ubuntu:26.04 AS builder

RUN apt-get update && \
    apt install -y python3 python3-pip cargo

COPY --chmod=0755 5z3k-dist/ /app/
COPY --chmod=0755 5z3k-dist/verifier.py /app/run
COPY --chmod=0755 response.txt /app/response.txt
COPY --chmod=0644 flag.txt /app/flag.txt
RUN cd /app/galois_ring && cargo build -r && cp target/release/lib_galois_ring.so /app/_galois_ring.so && rm -rf target
RUN chmod -R 0755 /app

FROM pwn.red/jail@sha256:ee52ad5fd6cfed7fd8ea30b09792a6656045dd015f9bef4edbbfa2c6e672c28c

COPY --from=builder / /srv

ENV JAIL_TIME=600
ENV JAIL_MEM=400MB
ENV JAIL_POW=45000
