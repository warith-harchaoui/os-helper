# OS Helper

[🇫🇷](https://github.com/warith-harchaoui/os-helper/blob/main/LISEZMOI.md) · [🇬🇧](https://github.com/warith-harchaoui/os-helper/blob/main/README.md)

[![CI](https://github.com/warith-harchaoui/os-helper/actions/workflows/ci.yml/badge.svg)](https://github.com/warith-harchaoui/os-helper/actions/workflows/ci.yml) [![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://github.com/warith-harchaoui/os-helper/blob/main/LICENSE) [![Python](https://img.shields.io/badge/python-3.10%E2%80%933.13-blue.svg)](#) [![Local-first](https://img.shields.io/badge/privacy-local--first-2f6f5e.svg)](#the-promise)

`OS Helper` belongs to a collection of libraries called `AI Helpers` developed for building Artificial Intelligence.

[🌍 AI Helpers](https://deraison.ai/ai-helpers)

[![logo](https://raw.githubusercontent.com/warith-harchaoui/os-helper/main/assets/logo.png)](https://deraison.ai/ai-helpers)

OS Helper is a Python library that provides utility functions for working with different operating systems. It offers a set of tools to simplify common system operations, file handling, and OS-specific tasks.

## The Promise

os-helper is part of a local-first, sovereignty-minded suite. Rather than
market that, here is the honest, case-by-case reality:

1. **Guaranteed local.** os-helper is a pure local filesystem / utility
   toolbox. Nothing is uploaded, there is no telemetry, and there is no
   account. The optional Tree Radar GUI reads your disk and renders the
   treemap locally in your browser (the server binds to `127.0.0.1` only);
   your paths, sizes, and content hashes never leave the machine.

2. **Not possible to be local: the caveats.** Two helpers make outbound
   HTTP *by design*, because fetching something is their whole purpose:
   `download_file()` (it downloads a URL you hand it) and the URL-liveness
   checks (`is_working_url()` / `check_url`). `get_user_ip()` also calls a
   public echo service on purpose. These are the only network calls in the
   library, and you only trigger them by explicitly calling them.

3. **Your decision.** Nothing here forces the cloud. `temporary_remote_file()`
   can stage to S3/GCS/SFTP, but only when *you* wire it to a remote. If you
   build network behavior on top of os-helper, that is your choice, never a
   default.

## Documentation

[💻 Documentation](https://deraison.ai/ai-helpers/docs/os-helper-doc/)

[🗺️ Landscape](https://github.com/warith-harchaoui/os-helper/blob/main/LANDSCAPE.md)

[📋 Examples](https://github.com/warith-harchaoui/os-helper/blob/main/EXAMPLES.md)

[🔐 Credentials Management](https://github.com/warith-harchaoui/os-helper/blob/main/CREDENTIALS_MANAGEMENT.md)

## Features

Everything is a thin, well-typed, well-documented wrapper: no heavy system
dependency, pure-Python across macOS / Linux / Windows.

- **OS detection**: `windows()`, `linux()`, `macos()`, `unix()`.
- **Hardware inspection**: `hardware_info()` (one-call snapshot), plus its
  building blocks: `cpu_count_logical()`, `cpu_count_physical()`, `cpu_model()`,
  `ram_gb()`, `gpu_vendor()` (`apple`/`nvidia`/`amd`/`intel`/`cpu`), `gpus()`
  (name + VRAM per discrete GPU), `apple_chip_name()` /
  `apple_unified_memory_gb()` for Apple Silicon's shared memory pool. Live
  figures too: `cpu_percent()`, `available_ram_gb()`, `disk_usage_gb()`,
  `gpu_utilization_percent()` (Apple via IOKit, no `sudo`/`powermetrics`
  needed; NVIDIA via `nvidia-smi`; AMD via `rocm-smi`).
- **Process and command execution**: `system()` (shell-free `subprocess`, captured
  stdout/stderr, optional exit-code and expected-output checks), `openfile()`
  (open with the OS default app), `getpid()`, `get_nb_workers()` (scikit-learn
  `n_jobs` convention, `NB_WORKERS`-overridable).
- **Paths**: `join()`, `folder_name_ext()` (splits on the last dot only, so
  `archive.tar.gz` decomposes as `archive.tar` + `gz`, never collapsed to one
  multi-part extension), `absolute2relative_path()`, `relative2absolute_path()`,
  `path_without_home()`, `recursive_glob()`.
- **Files and directories**: `file_exists()`, `dir_exists()` (with emptiness
  checks), `size_file()`, `checkfile()`, `copyfile()`, `make_directory()`,
  `remove_directory()`, `remove_files()` (best-effort batch).
- **Temporary resources**: `temporary_filename()` (context-managed, optional
  target directory), `temporary_folder()`, `make_temporary_directory()`
  (persistent, caller-owned cleanup), `temporary_remote_file()` (stage to
  S3/GCS/SFTP/anywhere with guaranteed remote cleanup).
- **Hashing**: `hash_string()`, `hashfile()`, `hashfolder()` (RIPEMD-160 when
  available, BLAKE2b fallback; stable 40-char hex digests cross-platform).
- **Configuration loading**: `get_config()` with a deterministic fallback order,
  JSON/YAML file (or folder), then `.env` files, then process environment.
- **Localization**: two mechanisms, one per shape of problem.
  `Catalog.from_package()` reads `gettext` `.po`/`.mo` catalogues keyed on the
  English source string — what the suite's GUIs use — and
  `Catalog.problems(used=...)` reports a source the code asks for that no
  catalogue carries, which is what keeps a reworded sentence from silently
  half-reverting to English. `compile_catalogs()` writes the `.mo` itself, so
  GNU `msgfmt` is never a build dependency. Alongside it,
  `Locales.from_path()` reads a `locales/i18n.yaml` holding
  every human-readable string in one place, resolves a key for a locale with a
  deterministic fallback to the declared default, fills `{placeholder}` fields
  safely with `render()`, and reports every missing translation or mismatched
  placeholder at once with `problems()` — the check a CI job asserts on.
  Sections are named by the caller and mean nothing here, so one loader serves
  whatever each package keeps in its file.
- **Strings**: `emptystring()` (None / empty / whitespace), `asciistring()`
  (accent-folding, filesystem-safe slugs).
- **Downloads and networking**: `download_file()` (streaming, flat memory,
  adaptive block size, progress bar, returns `{path, content_type, bytes}`),
  `progress_bar()` (shared byte-scaled `tqdm` factory, auto-quiet off-TTY),
  `is_working_url()`, `get_user_ip()`.
- **Folder reporting and archiving**: `folder_description()` (size map,
  Bootstrap `index.html`, and `description.json`), `zip_folder()`.
- **Durations and timestamps**: `now_string()`, `format_size()`, `time2str()`,
  `str2time()`.
- **Timing and profiling**: `wall_timer()`, `cpu_timer()`, `gpu_timer()` (CUDA
  events / Apple-Silicon MPS, lazy `torch`), and MATLAB-style `tic()` / `toc()`.
- **Logging surface**: `init_logging()` (colored console + file, named-logger
  and live-stream modes), `verbosity()` (integer level get/set), and
  `debug()` / `info()` / `warning()` / `error()` / `critical()` / `check()`.
- **Multiple surfaces, one codebase**: importable library, an HTTP API
  (`os-helper-api`, via `[api]`), MCP tools (`os-helper-mcp`, via `[mcp]`) and
  the Tree Radar GUI (`os-helper-gui`, via `[gui]`). The API/MCP surfaces expose
  only the safe, side-effect-free subset (hardware info, hashing, ASCII,
  formatting, URL check, config loading; no filesystem mutation). There is
  deliberately **no command line**: os-helper is the suite's foundation, and
  every one of the sixteen other members reaches it by `import os_helper as osh`.

## How it works

![How os-helper works: the same call, whatever machine it lands on](https://raw.githubusercontent.com/warith-harchaoui/os-helper/main/assets/diagrams/how-it-works.png)

## Installation

**Prerequisites**: **Python 3.10–3.13** and **git**, cross-platform (os-helper needs no heavy system dependency):

- 🍎 **macOS** ([Homebrew](https://brew.sh)): `brew install python git`
- 🐧 **Ubuntu/Debian**: `sudo apt update && sudo apt install -y python3 python3-pip git`
- 🪟 **Windows** (PowerShell): `winget install Python.Python.3.12 Git.Git`

We recommend using Python environments. Check this link if you're unfamiliar with setting one up: [🥸 Tech tips](https://deraison.ai/4ml/#install).

### From PyPI (recommended)

```bash
pip install os-helper
```

### From source (no PyPI)

```bash
git clone https://github.com/warith-harchaoui/os-helper.git
cd os-helper

pip install -e .
```

## Quick start

Below are examples demonstrating how to use various features of the `os_helper` library. Make sure to import the library as `osh` before starting.

```python
import os_helper as osh
```

1. Set Verbosity and Check Operating System

```python
# Attach a console handler first: verbosity() only sets the *level*, so
# without init_logging() the info() calls below are filtered out silently.
osh.init_logging()

# Set verbosity level to display debugging messages
osh.verbosity(3)

# Check if the system is Unix-based (Linux or macOS)
if osh.unix():
    osh.info("You are running on a Unix-based system.")
else:
    osh.info("You are not running on a Unix-based system.")
```

2. Timestamp and File Existence Check
```python
# Generate a formatted timestamp for logging
timestamp = osh.now_string("log")
osh.info(f"Current timestamp (log format): {timestamp}")

# Check if a file exists and is not empty
test_file = "example.txt"
if osh.file_exists(test_file, check_empty=True):
    osh.info(f"File {test_file} exists and is not empty.")
else:
    osh.error(f"File {test_file} does not exist or is empty.")
```

3. Directory Creation and File Search
```python
# Create a directory
test_dir = "test_directory"
osh.make_directory(test_dir)
osh.info(f"Directory {test_dir} created.")

# Perform recursive search for '.txt' files in the directory
matching_files = osh.recursive_glob(test_dir, "*.txt")
osh.info(f"Matching files: {matching_files}")
```

4. Copy and Remove Files
```python
# Copy a file from source to destination (the source has to exist first)
source_file = "source.txt"
with open(source_file, "w") as handle:
    handle.write("some content worth backing up")

destination_file = "backup_source.txt"
osh.copyfile(source_file, destination_file)
osh.info(f"File {source_file} copied to {destination_file}")

# Remove the copied file (each removal is logged at INFO level)
osh.remove_files([destination_file])
```

5. Decompose a Path and Temporary File Creation
```python
# Decompose a file path into folder, basename, and extension
folder, basename, ext = osh.folder_name_ext("/path/to/myfile.tar.gz")
osh.info(f"Folder: {folder}, Basename: {basename}, Extension: {ext}")

# Create and write to a temporary file
with osh.temporary_filename(suffix=".log") as temp_log:
    osh.info(f"Temporary file created at: {temp_log}")
    with open(temp_log, "w") as log_file:
        log_file.write("This is a temporary log entry.")
```

6. Running System Commands
```python
# Execute a system command and capture its output
cmd_output = osh.system("echo 'Hello, World!'")
osh.info(f"Command output: {cmd_output['out']}")
```

7. Hashing Files and Strings
```python
# Hash the contents of a file
file_to_hash = "testfile.txt"
if osh.file_exists(file_to_hash):
    file_hash = osh.hashfile(file_to_hash)
    osh.info(f"Hash of {file_to_hash}: {file_hash}")

# Hash a string with a specific length
hashed_string = osh.hash_string("MyTestString", size=8)
osh.info(f"Hashed string: {hashed_string}")
```

8. ASCII String Conversion and Process ID
```python
# Convert a string into a safe ASCII format
safe_string = osh.asciistring("Café-Con-Leche!", replacement_char="_")
osh.info(f"Safe ASCII string: {safe_string}")

# Get the current process ID
pid = osh.getpid()
osh.info(f"Current Process ID: {pid}")
```

9. Check URL Validity and Zip Folder
```python
# Check if a URL is valid and reachable
url = "https://www.example.com"
if osh.is_working_url(url):
    osh.info(f"The URL {url} is valid and reachable.")
else:
    osh.error(f"The URL {url} is not reachable.")

# Zip a folder (reusing the one created in step 3)
folder_to_zip = test_dir
zip_output = "test_directory_backup.zip"
osh.zip_folder(folder_to_zip, zip_output)
osh.info(f"Folder {folder_to_zip} zipped into {zip_output}")
```

## Multi-surface exposure

`os-helper` is a library first. The same safe operations are also reachable
over HTTP, as MCP tools, and through the Tree Radar GUI:

```python
# Python library — the way every other suite member uses it
import os_helper as osh
```

There is **no command line**, on purpose: a shell wrapper around
`path exists` or `str ascii` duplicated the shell's own vocabulary without
adding anything, and the sixteen suite packages that `import os_helper` never
called it.

### HTTP API + MCP

The library's safe, side-effect-free operations (hardware info, hashing,
ASCII normalization, size/time formatting, URL reachability, config loading;
deliberately no filesystem-mutation endpoint) are also reachable over HTTP,
and as MCP tools for any MCP-aware agent host:

```bash
pip install "os-helper[api]"
os-helper-api                    # -> http://127.0.0.1:8010 (docs at /docs)
curl http://127.0.0.1:8010/hardware

pip install "os-helper[mcp]"
os-helper-mcp                    # same app + an /mcp endpoint (fastapi-mcp)
```

### Optional Tree Radar GUI

A first, real slice of the [GUI.md](https://github.com/warith-harchaoui/os-helper/blob/main/GUI.md)
plan ships as an **optional** surface: **Tree Radar**, a local disk-usage
**treemap** dashboard. Each rectangle is a file or folder (area = size),
colored by **age**, **hash-dedupe** status, or **type family**. It reads
your disk and renders it in your browser; nothing is uploaded.

The GUI's web stack lives behind the `[gui]` extra so the core
`import os_helper` stays lean (no FastAPI in the default install):

```bash
pip install "os-helper[gui]"

# Launch the local dashboard (loopback only), then open http://127.0.0.1:8017/gui
os-helper-gui --root ~/Downloads
```

The page speaks **French and English**. `?lang=fr` / `?lang=en` picks one, a
flag in the header toggles between them, and a code no catalogue carries falls
back to the default rather than failing. The English is the source, written in
the markup itself; the French lives in
[`os_helper/locales/fr/LC_MESSAGES/os_helper.po`](https://github.com/warith-harchaoui/os-helper/blob/main/os_helper/locales/fr/LC_MESSAGES/os_helper.po),
a standard `gettext` catalogue read through `os_helper.Catalog` — the same
loader the rest of the suite uses, so a translator works in the format every
translation tool already speaks:

```bash
open http://127.0.0.1:8017/gui?lang=en
```

The remaining GUI milestones (Dedupe Lens actions, Config Explorer) stay
described in [GUI.md](https://github.com/warith-harchaoui/os-helper/blob/main/GUI.md).

### Use it as an agent skill

`skills/os-helper/` packages os-helper as a **Claude Skill** *and* an **OpenCode
skill**, so an agent can reach for it on your behalf. See
[`skills/README.md`](https://github.com/warith-harchaoui/os-helper/blob/main/skills/README.md) to install it (symlink into
`~/.claude/skills/` and `~/.opencode/skills/`), and
[`TRIGGERS.md`](https://github.com/warith-harchaoui/os-helper/blob/main/TRIGGERS.md) for the exhaustive trigger catalogue —
`scripts/check_triggers.py` keeps the skill's description in sync with it, and
the test suite fails if a capability stops being named.

## Author

 - [Warith HARCHAOUI](https://linkedin.com/in/warith-harchaoui)

## Acknowledgements

Special thanks to [Mohamed Chelali](https://mchelali.github.io) and [Bachir Zerroug](https://www.linkedin.com/in/bachirzerroug) for fruitful discussions.

## License

This project is licensed under the BSD-3-Clause License; see the [LICENSE](https://github.com/warith-harchaoui/os-helper/blob/main/LICENSE) file for details.
