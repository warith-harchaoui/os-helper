# syntax=docker/dockerfile:1.6
#
# os-helper — reproducible container image.
#
# Image built on top of python:3.11-slim. os-helper is a library: it ships no
# command line and no server in the core install, so this image is a *base
# layer* — the slim, reproducible Python + os-helper that downstream suite
# images build on, and a way to run a one-shot snippet against a mounted tree.
#
# Build:
#   docker build -t os-helper .
#
# Run a one-shot snippet:
#   docker run --rm -v $PWD:/data os-helper python -c \
#     'import os_helper as osh; print(osh.hashfile("/data/pyproject.toml"))'

FROM python:3.11-slim AS base

# System deps: tini for signal handling. os-helper itself has no C-ext
# runtime deps; we keep the image slim. Add `curl` / `unzip` here if a
# downstream image needs them.
RUN apt-get update && apt-get install --no-install-recommends -y \
        tini \
    && rm -rf /var/lib/apt/lists/*

# Non-root runtime user; the app never needs root at runtime.
RUN useradd --create-home --shell /bin/bash app
WORKDIR /app

# requirements.txt first (core deps only) so this layer caches independently
# of source changes; the package itself is installed once the source is in
# place, right below.
COPY --chown=app:app requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app pyproject.toml README.md LICENSE ./
COPY --chown=app:app os_helper ./os_helper

# Core install only. The api / mcp / gui surfaces are extras on purpose: nine
# suite packages import this library and must not pay for FastAPI.
RUN pip install --no-cache-dir .

USER app
ENV PYTHONUNBUFFERED=1

# tini reaps orphan children cleanly on SIGTERM.
ENTRYPOINT ["/usr/bin/tini", "--"]
# Default: report the installed version and exit 0 — the honest default for a
# library image. Override it to run anything else.
CMD ["python", "-c", "import importlib.metadata as m; print('os-helper', m.version('os-helper'))"]
