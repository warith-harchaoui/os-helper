# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.0] - 2026-10-21

### Added

- **The Tree Radar GUI speaks French and English.** Every string it shows now
  comes from `os_helper/locales/i18n.yaml` through `Locales` — the loader this
  package itself provides (`CODING.md` 21.3) — instead of being written into
  the markup. `GET /gui?lang=fr|en` picks the language; anything the file does
  not carry, including a mistyped code and the empty default, falls back to the
  declared default locale, so a bad `?lang=` returns a page rather than a 500.
  A flag in the header toggles between the two.

  The foundation now eats its own cooking: os-helper offers the suite a locale
  loader and reads its own strings through the same door, which is the only
  honest way to find out what the loader is missing.

  The template is tokenised (`{{TOKEN}}` in HTML, a `T` object for the
  script), so one piece of markup serves both languages and a translator never
  opens a Python file. The script's strings are injected as JSON rather than
  substituted as text: it is the encoding an apostrophe cannot break out of,
  and French copy is full of them. Two strings carry named fields
  (`{root}`, `{count}`, `{when}`) rather than being glued together in
  JavaScript, so a translator can reorder the sentence.

  The hover tooltip's type family is translated too — the server keeps sending
  the machine name (`code`, `data`, …) and the page maps it through the locale
  file, so the tooltip reads as a word rather than as an enum. Dates in it now
  follow the page's language instead of the browser's default.

### Changed

- **The launch root is injected through a template token.** It was patched in
  by replacing the literal `window.__OSH_ROOT__ || ""` inside the page — a
  string match against markup, which breaks the day the markup is reformatted.
  It is now a `{{ROOT_JSON}}` token, still a `json.dumps` literal so a Windows
  path's backslashes cannot break the script, with a test that holds it.

### Notes

- The locale file lives **inside** the package, is declared in `package-data`,
  and is carved out of this repository's blanket `*.yaml` ignore rule. Three
  tests hold those three properties, because the suite has now shipped this
  bug twice by two different routes: best-engine-ai-helper published wheels
  with no data at all until 1.6.1 (data beside the package, patterns matching
  nothing), and youtube-helper's `.gitignore` would have kept its catalogue
  out of git — therefore out of the sdist, therefore out of the wheel. Both
  are invisible locally, where the file sits on disk either way. Verified the
  way the defect was: the built wheel and sdist were opened and the file
  found in both.

## [2.4.0] - 2026-10-20

### Added

- **`Locales`: the suite's shared loader for `locales/i18n.yaml`.** Two
  members had already adopted the file described in `CODING.md` section 21.3
  and each had answered it alone — one with a 133-line private module, one
  with ad-hoc reads — while nine others ship a GUI with its strings written
  into the source. The loader belongs here, in the package all of them
  already depend on.

  It resolves deterministically (section 21.3.4): a key missing in the asked
  locale falls back to the declared default and says so in a warning, and a
  key missing there too raises rather than handing a developer's identifier
  to a user. `render()` fills `{placeholder}` fields by formatting and never
  by evaluating (section 21.3.5), and checks the field names first, so a
  caller learns what it forgot instead of shipping a sentence with a hole in
  it. `problems()` returns every fault at once rather than raising on the
  first — a translator fixing a file wants the whole list in one pass — and
  is what a CI job asserts on (section 21.3.7).

  **Sections are named by the caller and carry no meaning here.** The loader
  parses, resolves and validates; it never knows what any one section is for.
  That is what lets a single implementation serve packages whose files hold
  very different things, and it is why this module can live in os-helper at
  all.

  `meta.unlocalized_sections` declares the sections that are deliberately
  single-language, whose sub-keys are therefore not locale codes but roles or
  variants. Without it, validating such a section reports a wall of missing
  translations that were never meant to exist — observed against a real file
  in the suite, which went from 38 findings to none once declared. `raw()`
  reaches those entries, since no locale can resolve them.

## [2.3.5] - 2026-10-19

### Fixed

- **`string_utils.asciistring(s, replacement_char="")` raised
  `re.PatternError`.** The run-collapsing step builds
  `f"{re.escape(replacement_char)}+"`; with an empty replacement that is the
  pattern `"+"`, which `re` rejects outright as "nothing to repeat".

  Asking for unwanted characters to be *dropped* rather than substituted is the
  obvious second thing to want from this function, the signature advertises a
  plain `str` with no stated constraint, and no docstring forbade it. The caller
  got a regex error, raised from inside `re`, for a call containing no regex and
  naming neither `asciistring` nor the argument responsible.

  Both the collapse and the trim are now skipped when there is no replacement
  character — with none, there are no runs to collapse and no edges to strip, so
  the joined result is already the answer. `lower` and `allow_digits` still
  apply on that path.

### Changed

- **The three `*_gb` functions in `hardware_utils` now name their unit.**
  `ram_gb` and `available_ram_gb` divide by `1024**3` (GiB); `disk_usage_gb`
  divides by `1e9` (decimal GB). All three docstrings previously said only
  "in GB", so anyone comparing free RAM against free disk — or summing them —
  was off by 7 % with nothing to warn them.

  **No number changed.** The units are each conventionally correct: RAM is sold
  and reported binary, drives are sold decimal. Moving either would be the wrong
  fix, and moving `ram_gb` would silently shift every downstream memory
  comparison, including `best-engine-ai-helper`'s model-fits-in-RAM decision.
  What was missing was only that nothing said so; each docstring now states its
  unit and points at the others.

## [2.3.4] - 2026-09-03

### Fixed

- **`path_utils.path_without_home` matched the home directory as a bare
  string prefix**, so a sibling directory that merely shared the same
  characters (e.g. home `/home/bob` against a path under `/home/bobby/`)
  was wrongly collapsed into a bogus `~by/...` path instead of being left
  unchanged. Now requires a real path-segment boundary (`home + os.sep`,
  or an exact match) before collapsing to `~`. Regression tests added.

## [2.3.3] - 2026-08-24

### Fixed

- **`hash_utils.hashfolder` was not deterministic across directory-entry
  order.** It hashed each file's bytes in whatever order `os.walk`/
  `os.scandir` happened to return — filesystem directory-entry order, not
  alphabetical order — contradicting the module's own documented promise
  ("the same input always produces the same fingerprint", "have these two
  folders diverged"). Now sorts `dirs` (steering `os.walk`'s traversal) and
  iterates `sorted(files)` per directory, so two folders with identical
  content built in a different write sequence hash the same. Regression
  test: `test_hashfolder_is_independent_of_directory_entry_order`.
- **`misc_utils.folder_description`'s `description.json` had the same
  non-determinism**: written via plain `json.dump(result, ...)` with no
  `sort_keys=True`, so re-running it on an unchanged folder could produce a
  byte-different file (key order only) — undermining using it to diff a
  folder snapshot over time. The HTML index right below it already sorted
  for the same reason; the JSON output now does too.

### Added

- **Git pre-push hook** (`.githooks/pre-push`): blocks the push outright if
  `ruff check`, `ruff format --check`, or the full `pytest -q -m ""` sweep
  fails, so a red local state never even reaches CI. Documented in
  `CONTRIBUTING.md`.

## [2.3.2] - 2026-08-17

### Added

- **Usage Example sections for seven module docstrings**
  (`config_utils`, `hash_utils`, `misc_utils`, `path_utils`, `string_utils`,
  `system_utils`, `temp_utils`) that were bare feature lists with no
  runnable example, unlike the rest of the package — `CONTRIBUTING.md`
  mandates one on every module. Each now opens with an intuition-first
  framing (why the module exists, what problem it solves) plus a verified
  example.
- **Test coverage for `cpu_count_physical()`**: public and documented, but
  had zero test coverage until now.

### Fixed

- **Two RST list-indentation bugs** in `get_config()`'s and `gui.py`'s module
  docstrings: a list started immediately after a paragraph with no blank
  line, which docutils misparses as `"Unexpected indentation"` and breaks
  the rendered Sphinx docs page.
- **README.md/LISEZMOI.md's Features list mischaracterized
  `folder_name_ext()`** as `".tar.gz-aware"`, which reads as "treats
  `.tar.gz` as one unit." The function's own docstring and behavior are the
  opposite: it splits on the last dot only, so `archive.tar.gz` decomposes
  to `archive.tar` + `gz`, deliberately not collapsed.
- **`string_utils.py`'s module docstring claimed it handles string↔time
  conversion**; that functionality (`time2str`/`str2time`) actually lives
  in `misc_utils.py`.

## [2.3.1] - 2026-08-15

### Security

- **`POST /config` no longer resolves a key from the server's ambient
  process environment.** Previously, a network caller could name any
  environment-variable key and get its live value back whenever no
  `path`/`env_files` resolved it first — a credential-exposure shape
  (mitigated only by the default loopback-only bind). `get_config()` gained
  an `allow_ambient_env` keyword (default `True`, so CLI/library behavior is
  unchanged); the API now calls it with `allow_ambient_env=False`, so a key
  can only resolve from `path` or the requested `env_files`' own contents.

### Fixed

- **`get_config()` crashed on a syntactically valid but non-mapping config
  file.** A YAML/JSON document whose top-level value is a bare scalar (e.g.
  a lone `42`) made `all(key in config for key in keys)` raise
  `TypeError: argument of type 'int' is not iterable` instead of being
  treated as an invalid config file and falling through to the next source,
  as every other malformed-input case already does.
- **Both CLI twins printed a raw Python traceback on an ordinary library
  error** (e.g. `get_config`'s documented `RuntimeError` when no source
  resolves the requested keys) instead of a clean one-line message. Both
  `os-helper` and `os-helper-click` now print `Error: ...` to stderr and
  exit 1; `os-helper-click`'s console-script entry point now points at a new
  `cli_click.main()` wrapper (was the bare `cli` group).
- **The HTTP API collapsed every library exception into a generic 500.**
  `POST /config` failing to resolve its requested keys — an ordinary
  client-input outcome, not a server bug — now returns 400 with the
  library's own message instead of an opaque 500.
- **`requirements.txt` was missing `psutil`.** `pyproject.toml`'s core
  `dependencies` gained `psutil>=5.9,<8` with the 2.2.0 hardware-inspection
  work, but `requirements.txt` (the plain `pip install -r requirements.txt`
  path) was never updated to match — `import os_helper` installed that way
  would break the moment `cpu_count_physical()` / `ram_gb()` /
  `hardware_info()` were called. Added the missing pin; the two files'
  dependency lists are now programmatically identical.

## [2.3.0] - 2026-08-09

### Added

- **Live hardware metrics** (`hardware_utils.py`): `cpu_percent()`,
  `available_ram_gb()`, `disk_usage_gb()`, `gpu_utilization_percent()`
  (Apple Silicon via IOKit's `ioreg` — no `sudo`/`powermetrics` needed;
  NVIDIA via `nvidia-smi`; AMD via `rocm-smi`). These are live figures
  sampled at call time, distinct from the static facts `hardware_info()`
  already reported; `hardware_info()` now folds them in (`cpu.percent`,
  `available_ram_gb`, `disk`, `gpu_utilization_percent`), so the CLI/API/MCP
  `hardware info` snapshot picks them up automatically.

### Fixed

- **`system()` mangled Windows paths.** `shlex.split()`'s default POSIX mode
  treats backslash as an escape character wherever it appears, including
  inside a quoted argument; on Windows every path (`sys.executable`, a temp
  file embedded in an inline `-c` script, ...) is full of backslashes, so a
  POSIX split corrupted them (`C:\Python\python.exe` -> `C:Pythonpython.exe`,
  `FileNotFoundError: [WinError 2]`, caught by CI on `windows-latest`). On
  Windows, `system()` now splits with `posix=False` (no backslash processing
  at all -- Windows command lines have no such escape convention) and strips
  the grouping quote characters itself instead.
- **`tests/test_system_utils.py::test_system_expected_output_check`** spliced
  a raw `tmp_path` straight into an inline Python `-c` string; on Windows
  that path's backslashes could form an accidental escape sequence (e.g.
  `\U` reads as the 8-hex-digit Unicode escape) and fail with a `SyntaxError`
  in the spawned interpreter regardless of the fix above. Now embeds the
  path via `repr()`, which escapes it correctly for re-parsing on any OS.

## [2.2.0] - 2026-08-06

### Added

- **Hardware inspection** (`hardware_utils.py`): `hardware_info()` one-call
  snapshot, plus `cpu_count_logical()`, `cpu_count_physical()`, `cpu_model()`,
  `ram_gb()`, `gpu_vendor()` (`apple`/`nvidia`/`amd`/`intel`/`cpu`), `gpus()`
  (name + VRAM per NVIDIA/AMD GPU), `apple_chip_name()` /
  `apple_unified_memory_gb()`, and `platform_name()`. Consumer repos (e.g.
  `best-engine-ai-helper`) that need AI-inference-specific derivations
  (memory-bandwidth tables, decode-throughput estimates) build those on top
  of these raw facts rather than duplicating the subprocess probing.
  CLI: `os-helper hardware info` (argparse) and `os-helper-click hardware
  info` (click) print the same snapshot as JSON. `psutil>=5.9,<8` is now a
  core runtime dependency (RAM + physical-core detection).
- **HTTP API** (`os_helper.api`, `[api]` extra, entry point `os-helper-api`):
  the safe, side-effect-free subset of the library over FastAPI — hardware
  info, hashing, ASCII normalization, size/time formatting, URL reachability,
  config loading. Deliberately excludes any filesystem-mutation endpoint
  (`mkdir`/`rm`/`cp`/`download` stay library/CLI-only) — see the module
  docstring for the reasoning.
- **MCP surface** (`os_helper.mcp`, `[mcp]` extra, entry point
  `os-helper-mcp`): exposes the same FastAPI app as MCP tools via
  `fastapi-mcp`, mirroring the pattern already shipped in `standpoint` /
  `vocal-helper` / `md2star`. Closes the CLI/API/MCP surface gap for
  os-helper flagged in `ai-helpers/.private/do.md` §7 (previously the only
  member with neither a generic HTTP API nor MCP).

## [2.0.1] - 2026-08-02

Documentation-only follow-up to the stable foundation. The install commands now
point at PyPI (`pip install os-helper`) instead of a pinned git tag, so the
rendered PyPI project page never drifts to an old version, and the remaining
relative links (LICENSE, GUI.md) are now absolute GitHub URLs that resolve
off-repo.

### Fixed

- README / LISEZMOI install commands no longer self-pin to a git tag; they use
  `pip install os-helper` (and `"os-helper[cli]"`), which always resolves to the
  latest published release.
- Absolutized the remaining relative Markdown links (LICENSE badge, GUI.md) so
  they resolve on the PyPI page.

### Added

- `tests/test_readme_install_pin.py` guards against the stale git self-pin ever
  returning to any Markdown file.

### Changed

- Normalized formatting on four modules (`gui`, `logging_utils`, `misc_utils`,
  `temp_utils`) so `ruff format --check` is clean; no behaviour change.

## [2.0.0] - 2026-08-02

This release marks os-helper as the stable foundation the whole AI Helpers suite
pins for three things: logging (`osh.info` / `osh.warning` / `osh.error`), file
management, and now smart downloads. The download primitive gained resume,
retries, atomic finalize and integrity checks, so every helper that fetches
bytes (model mirrors, media, templates, catalogs) can route through one place.

### Added

- `download_file` is now a full transfer primitive, keeping the existing
  streamed, adaptive-chunk behaviour and adding:
  - **Resume** (`resume=True`, default): bytes accumulate in a `<file>.part`
    sidecar and an interrupted transfer continues with an HTTP `Range` request
    instead of restarting. If the server ignores `Range` (answers `200` rather
    than `206`), the sidecar restarts from zero automatically.
  - **Retries** (`retries=3`, default): transient network errors are retried
    with exponential backoff, each retry resuming from the current sidecar size.
  - **Integrity check** (`sha256=...`): the finished file's digest is verified
    and a mismatch raises `ValueError`, discarding the bad sidecar.
  - **Idempotence** (`overwrite=False`, default): an existing complete
    destination is reused without re-downloading (its digest re-checked when
    `sha256` is given), so callers can invoke it unconditionally.
- Internal `_sha256_file` streams a file through SHA-256 with a flat memory
  footprint, reused by the download verifier.

### Changed

- **Breaking-ish behaviour**: `download_file` now writes atomically (bytes land
  in `<file>.part` and are `os.replace`-d onto the destination in one step), so
  the final path only ever exists as a *complete* download; a crash leaves a
  `.part`, never a truncated final file. By default it also **skips an existing
  complete destination** unless `overwrite=True`. The return dict gains
  `"sha256"` and `"resumed"` keys (additive over `path` / `content_type` /
  `bytes`; callers reading only the old keys are unaffected).
- CI `ruff` lint is now **blocking** (was `continue-on-error` + `|| true`), so a
  style regression fails the build.

## [1.8.0] - 2026-07-24

### Added

- **Optional "Tree Radar" treemap GUI** (`os_helper.gui`). A local-first,
  disk-usage treemap disk dashboard: each rectangle is a file/folder
  (area = size), colored by **age** (mtime), **hash-dedupe** status
  (content hash via `hashfile`), or **type family** (code/data/media/
  archive/other). Served locally by FastAPI:
  - `GET /gui` — a self-contained HTML+JS page (vanilla JS, D3 treemap via
    CDN, no build step).
  - `GET /api/tree?root=...&depth=...&dedupe=0|1` — the directory tree as
    JSON, reusing the `os.walk`-style size collection, `format_size`, and
    `hashfile` from the core library (no reinvention).
  - Launchers: an `os-helper gui` subcommand and a dedicated
    `os-helper-gui` console script; both bind to `127.0.0.1` by default.
- **New optional extra `gui`** (`pip install "os-helper[gui]"`) carrying
  `fastapi` / `uvicorn` / `httpx`. The core `import os_helper` stays
  **FastAPI-free**: all web imports are guarded and load only when the GUI
  is actually created or run, preserving the deliberate lean-toolbox design
  the rest of the suite depends on.
- **"The Promise" / "La promesse"** sections and a `local-first` badge in
  `README.md` / `LISEZMOI.md`: a brutally honest, case-by-case statement of
  what is guaranteed local, what makes outbound HTTP by design
  (`download_file`, URL checks), and what is left to the user's choice.

### Tests

- `tests/test_gui.py` covers the `GET /gui` HTML route, the `/api/tree`
  JSON endpoint (including size roll-up, dedupe cluster detection, and the
  400-on-non-directory path). It `pytest.importorskip`s FastAPI so it skips
  cleanly when the `gui` extra is absent; CI installs `.[dev]` (which now
  includes the gui stack) so the tests actually run in CI.

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
