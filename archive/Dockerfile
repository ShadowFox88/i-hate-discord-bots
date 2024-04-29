# TODO: Add dive to devcontainer
FROM debian:bookworm-slim AS dive

RUN apt-get update && \
    apt-get install -y curl

COPY install-dive.sh .

RUN /bin/bash install-dive.sh
