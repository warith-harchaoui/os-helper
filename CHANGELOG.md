# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.7.2] - 2026-07-20

### Documentation

- **Rewrite the README / LISEZMOI "Features" sections** to be exhaustive and
  accurate. The old list over-promised ("system information retrieval (CPU,
  memory, disk usage)", file "move") for capabilities the library never had, and
  omitted whole areas that do exist: configuration loading, temporary
  files/dirs (context-managed and persistent), the logging surface, timing /
  profiling (`wall_timer` / `cpu_timer` / `gpu_timer` / `tic` / `toc`), streaming
  downloads with a shared progress bar, duration parse/format, URL liveness
  checks, public-IP lookup, and the three exposure surfaces (library + argparse +
  click CLIs).
- **Backfill the changelog.** Entries for `1.6.0`, `1.7.0` and `1.7.1` were
  missing even though the features shipped; reconstruct them from the code and
  git history below. Also correct the mis-dated `1.5.3` entry.
- Refresh stale `@v1.5.2` source-install pins in README / LISEZMOI to the current
  release, and point `EXAMPLES.md` setup at `pip install os-helper` (it read
  `pip install -r requirements.txt`, the wrong entry point for a published
  package). Add short `EXAMPLES.md` recipes for `make_temporary_directory`,
  `temporary_filename(directory=...)`, the `download_file` metadata return, and
  `init_logging`.
- Fix `CONTRIBUTING.md`: it referenced a `pytest.mark.integration` marker and an
  `addopts = -m 'not integration'` setting that do not exist in this repo.

### Maintenance

- Add `.ruff_cache/` and `.deepeval/` to `.gitignore`; drop a stray empty
  `.deepeval/` directory and stale `dist/` 1.5.2 build artifacts. No code changes.

## [1.7.1] - 2026-07-20

### Fixed

- The convenience log functions (`debug` / `info` / `warning` / `error` /
  `critical` / `check`) now log through a dedicated **named** `"os_helper"`
  logger instead of the module-level `logging.info` / `logging.warning` / …
  helpers. The module-level helpers implicitly call `logging.basicConfig()` when
  the root has no handler — a library anti-pattern that attaches a stray root
  handler and double-prints records from any other named logger that propagates
  to root. The named logger avoids both; `init_logging` still catches these
  records via propagation when it configures the root.

## [1.7.0] - 2026-07-20

### Added

- **`download_file` now returns lightweight metadata** —
  `{"path", "content_type", "bytes"}` — so a caller can pick a file extension
  from the server's MIME type without a second request. Historically it returned
  `None`; callers that ignore the return value are unaffected (additive change).
- **`download_file(..., check_url=True)`** — new keyword to skip the pre-flight
  `HEAD` liveness check (some servers/CDNs reject `HEAD` with 405/403 even though
  `GET` succeeds); the `GET`'s `raise_for_status` remains the backstop.
- **`temporary_filename(..., directory=...)`** — place the temp file inside a
  chosen directory (e.g. next to sibling inputs a tool resolves relative paths
  against) instead of the system temp dir.
- **`make_temporary_directory(prefix, directory)`** — the non-context-manager
  companion to `temporary_folder`: creates a directory that **outlives** a `with`
  block and hands the caller responsibility for cleanup (the suite's `mkdtemp`).

## [1.6.0] - 2026-07-20

### Added

- **Named-logger mode for `init_logging(name=...)`** — configure a single
  logger tree (e.g. `"mytool"`) instead of the root. The reset step only removes
  handlers this function installed (so a host's / pytest's handlers survive),
  repeated calls are idempotent (no stacked duplicate console handler), and
  `propagate=True` keeps records reaching a host's / pytest's root handlers
  (`caplog`). This is the CLI-friendly configuration path.
- **`init_logging(live_stream=True)`** — the console handler re-resolves
  `sys.stdout` / `sys.stderr` on every emit instead of binding the stream once,
  so output survives pytest's `capsys` (which swaps the streams per test) and any
  post-configuration stream redirection.

## [1.5.3] - 2026-07-13

### Changed

- **`download_file` now streams with a progress bar.** It previously loaded the
  entire response into memory (`resp.content`) before writing — fine for a small
  file, fatal for a multi-hundred-MB archive. It now streams block-by-block
  (flat memory footprint) and shows a `tqdm` progress bar on an interactive
  terminal (auto-suppressed on a non-TTY, e.g. CI). New optional keyword args
  `chunk_size` and `progress`; the positional signature is unchanged, so callers
  need no edits. Adds a `(connect, read)` timeout so a stalled server can't hang
  the download forever.
- **Adaptive block size.** `chunk_size` defaults to `None` = *auto*: the block
  size is derived from the download's `Content-Length` (already read for the
  progress total, so no extra request) to target ~512 chunks, clamped to
  `[64 KiB, 4 MiB]`, with a 1 MiB fallback when the size is unknown. This keeps
  progress-bar redraws and per-iteration overhead sensible from a 2 KB config to
  a multi-GB model. Pass an explicit `chunk_size` to override.

### Added

- **`progress_bar(total, desc, disable, unit)`** — a shared, byte-scaled `tqdm`
  factory with the suite convention baked in (KiB/MiB/GiB units, ETA from a known
  total, and auto-suppression when `stderr` is not a TTY). Every helper that
  moves bytes wraps its transfer library's progress hook around one of these, so
  HTTP download, S3 up/download and SFTP put/get all show identical progress.
  `download_file` is refactored to use it.
- `tqdm>=4.66,<5` dependency (the progress bar for `download_file` / `progress_bar`).

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
