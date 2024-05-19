FROM mcr.microsoft.com/devcontainers/python:1-3.12 AS base
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /workspace

RUN ["apt", "update"]

FROM base AS dive
WORKDIR /tmp

COPY install-dive.sh .
RUN ./install-dive.sh
