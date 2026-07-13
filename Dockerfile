# syntax=docker/dockerfile:1.6
#
# os-helper — reproducible container image.
#
# Image built on top of python:3.11-slim. Installs os-helper with the
# [cli] extra so both CLI twins are available. os-helper is a library
# plus two CLIs (argparse `os-helper`, click `os-helper-click`); there is
# no long-running server surface, so the container is meant for one-shot
# commands via `docker run`.
#
# Build:
#   docker build -t os-helper .
#
# Run CLI one-shot:
#   docker run --rm -v $PWD:/data os-helper \
#     os-helper hash file /data/pyproject.toml

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

# Copy the package first so pip picks up pyproject.toml before we
# invalidate the layer with source changes.
COPY --chown=app:app pyproject.toml README.md LICENSE ./
COPY --chown=app:app os_helper ./os_helper

# Install with the [cli] extra so both CLI twins are available. The
# argparse CLI (`os-helper`) works out of the box; the click twin
# (`os-helper-click`) needs the [cli] extra installed here.
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir '.[cli]'

USER app
ENV PYTHONUNBUFFERED=1

# tini reaps orphan children cleanly on SIGTERM.
ENTRYPOINT ["/usr/bin/tini", "--"]
# Default: print the argparse CLI help. Override for one-shot CLI usage.
CMD ["os-helper", "--help"]
