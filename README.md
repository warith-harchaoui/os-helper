# OS Helper

[🇫🇷](https://github.com/warith-harchaoui/os-helper/blob/main/LISEZMOI.md) · [🇬🇧](https://github.com/warith-harchaoui/os-helper/blob/main/README.md)

[![CI](https://github.com/warith-harchaoui/os-helper/actions/workflows/ci.yml/badge.svg)](https://github.com/warith-harchaoui/os-helper/actions/workflows/ci.yml) [![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](LICENSE) [![Python](https://img.shields.io/badge/python-3.10%E2%80%933.13-blue.svg)](#)

`OS Helper` belongs to a collection of libraries called `AI Helpers` developed for building Artificial Intelligence.

[🌍 AI Helpers](https://harchaoui.org/warith/ai-helpers)

[![logo](https://raw.githubusercontent.com/warith-harchaoui/os-helper/main/assets/logo.png)](https://harchaoui.org/warith/ai-helpers)

OS Helper is a Python library that provides utility functions for working with different operating systems. It offers a set of tools to simplify common system operations, file handling, and OS-specific tasks.

## Documentation

[💻 Documentation](https://harchaoui.org/warith/ai-helpers/docs/os-helper-doc/)

[📋 Examples](https://github.com/warith-harchaoui/os-helper/blob/main/EXAMPLES.md)

## Features

Everything is a thin, well-typed, well-documented wrapper — no heavy system
dependency, pure-Python across macOS / Linux / Windows.

- **OS detection** — `windows()`, `linux()`, `macos()`, `unix()`.
- **Process & command execution** — `system()` (shell-free `subprocess`, captured
  stdout/stderr, optional exit-code and expected-output checks), `openfile()`
  (open with the OS default app), `getpid()`, `get_nb_workers()` (scikit-learn
  `n_jobs` convention, `NB_WORKERS`-overridable).
- **Paths** — `join()`, `folder_name_ext()` (`.tar.gz`-aware split),
  `absolute2relative_path()`, `relative2absolute_path()`, `path_without_home()`,
  `recursive_glob()`.
- **Files & directories** — `file_exists()`, `dir_exists()` (with emptiness
  checks), `size_file()`, `checkfile()`, `copyfile()`, `make_directory()`,
  `remove_directory()`, `remove_files()` (best-effort batch).
- **Temporary resources** — `temporary_filename()` (context-managed, optional
  target directory), `temporary_folder()`, `make_temporary_directory()`
  (persistent, caller-owned cleanup), `temporary_remote_file()` (stage to
  S3/GCS/SFTP/anywhere with guaranteed remote cleanup).
- **Hashing** — `hash_string()`, `hashfile()`, `hashfolder()` (RIPEMD-160 when
  available, BLAKE2b fallback; stable 40-char hex digests cross-platform).
- **Configuration loading** — `get_config()` with a deterministic fallback order:
  JSON/YAML file (or folder) → `.env` files → process environment.
- **Strings** — `emptystring()` (None / empty / whitespace), `asciistring()`
  (accent-folding, filesystem-safe slugs).
- **Downloads & networking** — `download_file()` (streaming, flat memory,
  adaptive block size, progress bar, returns `{path, content_type, bytes}`),
  `progress_bar()` (shared byte-scaled `tqdm` factory, auto-quiet off-TTY),
  `is_working_url()`, `get_user_ip()`.
- **Folder reporting & archiving** — `folder_description()` (size map +
  Bootstrap `index.html` + `description.json`), `zip_folder()`.
- **Durations & timestamps** — `now_string()`, `format_size()`, `time2str()`,
  `str2time()`.
- **Timing & profiling** — `wall_timer()`, `cpu_timer()`, `gpu_timer()` (CUDA
  events / Apple-Silicon MPS, lazy `torch`), and MATLAB-style `tic()` / `toc()`.
- **Logging surface** — `init_logging()` (colored console + file, named-logger
  and live-stream modes), `verbosity()` (integer level get/set), and
  `debug()` / `info()` / `warning()` / `error()` / `critical()` / `check()`.
- **Three surfaces, one codebase** — importable library, an `os-helper` argparse
  CLI (always installed), and an `os-helper-click` twin (via the `[cli]` extra).

## Installation

**Prerequisites** — **Python 3.10–3.13** and **git**, cross-platform (os-helper needs no heavy system dependency):

- 🍎 **macOS** ([Homebrew](https://brew.sh)): `brew install python git`
- 🐧 **Ubuntu/Debian**: `sudo apt update && sudo apt install -y python3 python3-pip git`
- 🪟 **Windows** (PowerShell): `winget install Python.Python.3.12 Git.Git`

We recommend using Python environments. Check this link if you're unfamiliar with setting one up: [🥸 Tech tips](https://harchaoui.org/warith/4ml/#install).

### From PyPI (recommended)

```bash
# Core utilities (library + argparse CLI)
pip install os-helper

# Optional click-based CLI twin
pip install "os-helper[cli]"
```

### From source (no PyPI)

```bash
# Core utilities (library + argparse CLI)
pip install "git+https://github.com/warith-harchaoui/os-helper.git@v1.7.2"

# Optional click-based CLI twin
pip install "os-helper[cli] @ git+https://github.com/warith-harchaoui/os-helper.git@v1.7.2"
```

## Usage

Below are examples demonstrating how to use various features of the `os_helper` library. Make sure to import the library as `osh` before starting.

```python
import os_helper as osh
```

1. Set Verbosity and Check Operating System

```python
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
# Copy a file from source to destination
source_file = "source.txt"
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

# Zip a folder
folder_to_zip = "my_folder"
zip_output = "my_folder_backup.zip"
osh.zip_folder(folder_to_zip, zip_output)
osh.info(f"Folder {folder_to_zip} zipped into {zip_output}")
```

## Multi-surface exposure

`os-helper` is not just a library — the same functions are exposed as a
Python import, an argparse CLI, and a click CLI twin:

```bash
# Python library (default)
import os_helper as osh

# argparse-based CLI (installed automatically)
os-helper os system
os-helper path exists ~/.zshrc
os-helper hash string hello --size 8
os-helper misc format-size 12345678
os-helper misc now --fmt filename

# click-based CLI twin (needs the [cli] extra)
pip install "os-helper[cli]"
# or from source:
pip install "os-helper[cli] @ git+https://github.com/warith-harchaoui/os-helper.git@v1.7.2"
os-helper-click hash file ./pyproject.toml
```

An innovative GUI plan (Tree Radar treemap, Dedupe Lens, Config
Explorer) lives in [GUI.md](https://github.com/warith-harchaoui/os-helper/blob/main/GUI.md).

The competitive landscape (stdlib, pathlib, click, python-dotenv,
psutil, fsspec, …) is analysed in [LANDSCAPE.md](https://github.com/warith-harchaoui/os-helper/blob/main/LANDSCAPE.md).

## Author

 - [Warith HARCHAOUI](https://linkedin.com/in/warith-harchaoui)

## Acknowledgements

Special thanks to [Mohamed Chelali](https://mchelali.github.io) and [Bachir Zerroug](https://www.linkedin.com/in/bachirzerroug) for fruitful discussions.

## License

This project is licensed under the BSD-3-Clause License — see the [LICENSE](LICENSE) file for details.
