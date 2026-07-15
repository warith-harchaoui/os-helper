# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.5.2] - 2026-07-15

### Documentation

- Harmonize README/LISEZMOI to the AI Helpers common structure (single
  H1, PyPI + source install paths, refreshed pins to v1.5.2); no code
  changes.

## [1.5.1] - 2026-07-14

### Maintenance

- Apply the project coding standards across `os_helper/` and `tests/`:
  Numpy-style docstrings on every function/class (including private and
  nested helpers), full type annotations with `from __future__ import
  annotations`, and comment density raised above the floor in every
  module. The argparse CLI's bare `print(...)` calls are routed through
  thin `_emit`/`_emit_err` stdout/stderr helpers (byte-for-byte
  identical output) to keep the data channel separate from the logging
  surface. No public API or behavior changes.
- Refresh the project logo asset.

## [1.5.0] - 2026-07-13

### Removed

- **BREAKING:** drop the FastAPI HTTP surface (`os_helper.api`) and the
  MCP server (`os_helper.mcp`). os-helper is a low-level OS/path/string/
  hash utility library; service surfaces belong on the domain helpers,
  not here. Anyone importing `os_helper.api` / `os_helper.mcp`, running
  `uvicorn os_helper.api:app`, or using the `os-helper-mcp` console
  script must migrate — the library, the argparse CLI (`os-helper`) and
  the click CLI (`os-helper-click`) are unchanged.
- Drop the `[api]` and `[mcp]` optional-dependency extras and their
  `fastapi` / `uvicorn` / `python-multipart` / `fastapi-mcp` deps. The
  `dev` extra is trimmed to `pytest` + `click`.

## [1.4.2] - 2026-07-08

### Documentation

- Cross-platform Install prerequisites (macOS / Ubuntu / Windows).

## [1.4.1] - 2026-07-07

### Documentation

- Establish suite-wide Python coding-style mandate in `CONTRIBUTING.md`:
  numpy-style docstrings on every function and class, module-level
  docstring header (with usage example + author), full type annotations,
  generous explanatory comments.
- `EXAMPLES.md` cookbook present at the repo root and linked from
  README + LISEZMOI.
- `print(...)` in docs (EXAMPLES.md / README / LISEZMOI) is followed by
  a `#`-comment showing the expected output (doctest / REPL style);
  library `.py` code uses `osh.info` / `osh.warning` / `osh.error`
  instead of bare `print`.
- Every `brew install <pkg>` mention is paired with a brew.sh hint when
  not already obvious from context.
- `.gitignore` updated to drop accidental `*config.json` commits while
  keeping `*config.json.example` templates tracked.

### Changed

- Convert `pyproject.toml` from `[tool.poetry]` to PEP 621 `[project]`;
  switch build-backend to `setuptools`.
- Drop `requirements.txt`, `environment.yml`, `poetry.lock` (sole source
  of truth is `pyproject.toml`).
- Add full PyPI metadata: `license = BSD-3-Clause`, classifiers,
  keywords, project URLs, `[project.optional-dependencies] dev`.
- Add GitHub Actions CI: cross-OS matrix
  (`ubuntu-latest` × `macos-latest` × `windows-latest`) × Python 3.10–3.13.
  os-helper is the most OS-sensitive helper of the suite, so all three
  major operating systems are exercised on every push.
- Drop the stale `tests.yml` workflow (referenced the now-deleted
  `requirements.txt`).
- Ruff lint baseline applied: modernize type annotations to PEP 604
  (`X | None`, `X | Y`) and PEP 585 (`list[X]`, `dict[K, V]`), drop
  unused imports, fix percent-formatting → f-strings, clean trailing
  whitespace. No behavior change; tests pass identically.
- Add `CHANGELOG.md`, `CONTRIBUTING.md` (SemVer policy), `LISEZMOI.md`
  (French mirror of README), and CI / license / Python badges.

## [1.3.0] - 2026-06-28

### Added

- `profile_utils` module: `wall_timer`, `cpu_timer`, `gpu_timer`
  context managers (Apple Silicon MPS + NVIDIA CUDA support) plus
  the lightweight `tic` / `toc` companions.

### Changed

- `verbosity()` doubles as both getter and setter (idempotent when
  called with the same arg twice).

## [1.2.0] - 2026-06-28

### Added

- Revive `folder_description` as a working function.
- `temporary_remote_file` context manager (HTTP fetch into a temp file,
  cleanup on exit).

### Changed

- Replace `not s` / `s == ""` style checks across the codebase with
  `emptystring(s)` (consistent semantics for None / empty / whitespace).
- File and directory operations now propagate OS exceptions instead of
  silencing them via `SystemExit`.
- `split_path` correctly handles multi-part file extensions (e.g. `.tar.gz`).

## [1.1.0] - 2026-05-10

### Added

- `verbosity()` helper for runtime log-level adjustment.

### Removed

- Stale `__all__` entries (`os_path_constructor`, `folder_description`).

## [1.0.0] - 2025-02-11

First tagged release.
