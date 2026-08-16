# OS Helper Examples

This document provides detailed examples for using the `OS Helper` module to simplify common programming tasks.

---

## Table of Contents

1. [Setup and Configuration](#setup-and-configuration)
2. [System Information](#system-information)
   - [Worker Count Resolution](#worker-count-resolution)
3. [Hardware Inspection](#hardware-inspection)
   - [One-Call Snapshot](#one-call-snapshot)
   - [Individual Probes](#individual-probes)
   - [Live Metrics](#live-metrics)
4. [Configuration Loading](#configuration-loading)
5. [File and Directory Utilities](#file-and-directory-utilities)
   - [Check File or Directory Existence](#check-file-or-directory-existence)
   - [Manage Directories](#manage-directories)
   - [File Size and Path Operations](#file-size-and-path-operations)
   - [Copy, Remove, and Locate Files](#copy-remove-and-locate-files)
   - [Describe Folder Contents](#describe-folder-contents)
   - [Decompose File/Folder Path](#decompose-filefolder-path)
   - [Compress a Folder into a ZIP File](#compress-a-folder-into-a-zip-file)
6. [String Utilities](#string-utilities)
   - [Check for Blank Strings](#check-for-blank-strings)
   - [ASCII String Conversion](#ascii-string-conversion)
7. [Temporary Resources](#temporary-resources)
   - [Create a Temporary File](#create-a-temporary-file)
   - [Create a Temporary Folder](#create-a-temporary-folder)
   - [Create a Persistent Temporary Directory](#create-a-persistent-temporary-directory-caller-owned-cleanup)
   - [Stage a File on a Remote Backend](#stage-a-file-on-a-remote-backend)
8. [System Commands](#system-commands)
   - [Run a System Command](#run-a-system-command)
9. [Networking](#networking)
   - [Check if a URL is Valid and Reachable](#check-if-a-url-is-valid-and-reachable)
   - [Retrieve Public IP Addresses](#retrieve-public-ip-addresses)
10. [Hashing](#hashing)
    - [Generate a Hash for a String](#generate-a-hash-for-a-string)
    - [Hash a File](#hash-a-file)
    - [Hash a Folder](#hash-a-folder)
11. [Duration Helpers](#duration-helpers)
    - [Format Durations into Readable Strings](#format-durations-into-readable-strings)
    - [Parse Strings into Durations](#parse-strings-into-durations)
12. [Miscellaneous Utilities](#miscellaneous-utilities)
    - [Verbosity and Logging](#verbosity-and-logging)
    - [Timestamps and Byte Sizes](#timestamps-and-byte-sizes)
    - [Download Files](#download-files)
    - [Progress Bars for Custom Transfers](#progress-bars-for-custom-transfers)
    - [Open Files with Default Applications](#open-files-with-default-applications)
13. [Profiling Helpers](#profiling-helpers)
    - [Wall-Clock Timer](#wall-clock-timer)
    - [CPU Timer](#cpu-timer)
    - [GPU Timer](#gpu-timer)
    - [MATLAB-style tic / toc](#matlab-style-tic--toc)

---


## Setup and Configuration

Install the package from PyPI (or directly from GitHub; see the README):

```bash
# Core utilities (library + argparse CLI)
pip install os-helper

# Optional click-based CLI twin
pip install "os-helper[cli]"
```

Then import the library; examples below use the conventional `osh` alias:

```python
import os_helper as osh
```

## System Information

Use the following functions to determine the platform your script is running on. These are especially useful for writing cross-platform scripts.

```python
from os_helper import windows, linux, macos, unix

# Check if the system is Windows
if windows():
    print("Running on Windows!")

# Check if the system is Linux
if linux():
    print("Running on Linux!")

# Check if the system is macOS
if macos():
    print("Running on macOS!")

# Check if the system is Unix-based
if unix():
    print("Running on a Unix-based system!")
```

### Worker Count Resolution

`get_nb_workers` follows scikit-learn's `n_jobs` convention (`0` = whole
pool, positive = exact count, negative = `pool_size + n + 1`), overridable
process-wide via the `NB_WORKERS` environment variable, handy in containers
where the visible CPU count lies about the real quota.

```python
from os_helper import get_nb_workers, getpid

print(get_nb_workers())      # -1 (default): all available CPU cores
print(get_nb_workers(-2))    # all cores but one
print(get_nb_workers(4))     # positive: taken literally
print(get_nb_workers(0))     # 0: the full pool size

print(getpid())              # current process ID, as a string
```

## Hardware Inspection

Cross-platform hardware facts and live metrics: no heavy system dependency
beyond `psutil` (core) and the platform's own tools (`system_profiler` /
`nvidia-smi` / `rocm-smi` / `ioreg`, shelled out to only when relevant).

### One-Call Snapshot

`hardware_info()` aggregates every probe below into a single JSON-ready
dict, the same payload the `hardware info` CLI/API/MCP surfaces return.

```python
from os_helper import hardware_info

info = hardware_info()
print(info)
# {
#     'platform': 'darwin',
#     'cpu': {'physical_cores': 12, 'logical_cores': 12,
#             'model': 'Apple M2 Max', 'percent': 8.3},
#     'ram_gb': 96.0, 'available_ram_gb': 61.2,
#     'disk': {'free_gb': 512.3, 'used_gb': 487.7,
#              'total_gb': 1000.0, 'percent_used': 48.8},
#     'gpu_vendor': 'apple', 'gpus': [],
#     'gpu_utilization_percent': 14.0,
#     'apple_chip': 'Apple M2 Max', 'apple_unified_gb': 96.0,
# }
```

### Individual Probes

Each field of the snapshot above is also its own function, for callers who
only need one fact (e.g. picking a batch size from `ram_gb()` without paying
for a GPU probe).

```python
from os_helper import (
    platform_name, cpu_count_logical, cpu_count_physical, cpu_model,
    ram_gb, gpu_vendor, gpus, apple_chip_name, apple_unified_memory_gb,
)

print(platform_name())         # 'darwin' / 'linux' / 'windows'
print(cpu_count_logical())     # 12 (includes hyperthreads/SMT)
print(cpu_count_physical())    # 12, or None if psutil can't tell
print(cpu_model())             # 'Apple M2 Max' or None

print(ram_gb())                # 96.0 (total installed RAM)
print(gpu_vendor())            # 'apple' / 'nvidia' / 'amd' / 'intel' / 'cpu'
print(gpus())                  # [] on Apple (unified memory, no discrete VRAM
                                #  list); [{'vendor': 'nvidia', 'name': ...,
                                #  'vram_gb': ...}, ...] on NVIDIA/AMD boxes

# Apple Silicon's memory pool is unified (shared with the GPU), so it is
# reported separately rather than folded into `gpus()`'s VRAM list.
if gpu_vendor() == "apple":
    print(apple_chip_name())          # 'Apple M2 Max'
    print(apple_unified_memory_gb())  # 96.0
```

### Live Metrics

Distinct from the static facts above: these are sampled fresh on every call
(fine for a one-shot diagnostic report or a CLI print; not for a hot loop).
`hardware_info()` already folds them in; reach for these directly only when
you want a single figure without paying for a whole snapshot.

```python
from os_helper import cpu_percent, available_ram_gb, disk_usage_gb, gpu_utilization_percent

print(cpu_percent())            # 8.3  (instantaneous CPU load, 0-100)
print(available_ram_gb())       # 61.2 (RAM free right now, <= ram_gb())

usage = disk_usage_gb()         # defaults to the home directory's filesystem
print(usage)                    # {'free_gb': 512.3, 'used_gb': 487.7,
                                 #  'total_gb': 1000.0, 'percent_used': 48.8}
print(disk_usage_gb("/tmp"))    # or check any specific path's filesystem

# Apple via IOKit (no sudo/powermetrics needed), NVIDIA via nvidia-smi,
# AMD via rocm-smi. None when unavailable (wrong vendor, tool not on PATH).
print(gpu_utilization_percent())  # 14.0, or None
```

## Configuration Loading

`get_config` resolves settings through a fixed fallback order: an explicit
JSON/YAML file (or the first matching file in a folder), then `.env` files
merged into `os.environ`, then the process environment. It raises a clear
`RuntimeError` only if none of the sources satisfy every required key.

```python
from os_helper import get_config

# 1) A config file (or a folder containing one) wins first, if it has every key.
config = get_config(
    keys=["host", "port"],
    config_type="database",
    path="config.yaml",  # or a folder: the first *.json/*.yaml/*.yml with
                          # all the required keys is picked, sorted by name
)
print(config)  # {'host': 'localhost', 'port': 5432}

# 2) No path (or the file is missing a key): falls through to .env files,
#    merged into os.environ (default: [".env"] in the current directory).
config = get_config(keys=["api_key"], config_type="API", env_files=[".env.local"])

# 3) Then plain environment variables, tried as UPPER_CASE first
#    (the conventional spelling), then the exact key as given.
import os
os.environ["API_KEY"] = "sk-example"
config = get_config(keys=["api_key"], config_type="API", path=None, env_files=[])
print(config)  # {'api_key': 'sk-example'}
```

> Loading real secrets (API keys, DB credentials) this way? See
> [CREDENTIALS_MANAGEMENT.md](CREDENTIALS_MANAGEMENT.md) for the security
> caveats and how to layer a vault (HashiCorp Vault, AWS/GCP/Azure secret
> managers) on top of `get_config`.

## File and Directory Utilities

The following utilities help you work with files and directories efficiently, including checking their existence, managing paths, and performing operations like zipping folders or describing contents.

### Check File or Directory Existence


```python
from os_helper import file_exists, dir_exists

# Check if a file exists
print(file_exists("example.txt"))  # True if the file exists, False otherwise

# Check if a directory exists and is non-empty
print(dir_exists("/path/to/folder", check_empty=True))  # True if non-empty, False otherwise
```

### Manage Directories

```python
from os_helper import make_directory, remove_directory

# Create a directory
make_directory("/path/to/new_folder")
print("Directory created!")

# Remove a directory (and its contents, if it exists)
remove_directory("/path/to/new_folder")
print("Directory removed!")
```

### File Size and Path Operations

```python
from os_helper import size_file, absolute2relative_path, relative2absolute_path

# Get the size of a file in bytes
print(size_file("example.txt"))  # Output: 1024 (if the file size is 1 KB)

# Convert an absolute path to a relative path
relative_path = absolute2relative_path("/home/user/project/file.txt", "/home/user")
print(relative_path)  # Output: 'project/file.txt'

# Convert a relative path to an absolute path
absolute_path = relative2absolute_path("relative/path/to/file")
print(absolute_path)  # Output: '/home/user/relative/path/to/file'
```

### Copy, Remove, and Locate Files

```python
from os_helper import checkfile, copyfile, remove_files, join, recursive_glob, path_without_home

# Assert a file exists (and optionally isn't empty), raising with a clear
# message otherwise; handy as a precondition at the top of a function.
checkfile("example.txt", "Expected input file is missing", check_empty=True)

# Copy a file, creating any missing destination directories along the way.
copyfile("example.txt", "backups/example.txt")

# Best-effort batch removal: each deletion is logged, missing files are
# skipped rather than raising.
remove_files(["backups/example.txt", "does-not-exist.txt"])

# join() is os.path.join with normalization, so callers get a consistent
# separator regardless of how the pieces were passed in.
config_path = join("configs", "prod", "app.yaml")
print(config_path)  # 'configs/prod/app.yaml'

# Recursively find every match for a glob pattern under a root directory.
python_files = recursive_glob("src", "*.py")
print(python_files)  # ['src/main.py', 'src/utils/helpers.py', ...]

# Render a path relative to the home directory, for user-facing log lines
# that shouldn't leak the full absolute path.
print(path_without_home("/Users/alice/projects/app/config.yaml"))
# '~/projects/app/config.yaml'
```

### Describe Folder Contents

`folder_description` walks a folder, returns a `{relative_path: size_in_bytes}`
mapping, and optionally writes a Bootstrap-styled `index.html` and a
`description.json` companion file next to it.

```python
from os_helper import folder_description

description = folder_description(
    "/path/to/folder",
    recursive=True,         # descend into subdirectories
    index_html=True,        # write /path/to/folder/index.html
    with_size=True,         # include a size column in the HTML index
    description_json=True,  # write /path/to/folder/description.json
)

print(description)
# {
#     'file1.txt': 1024,
#     'subfolder/file2.txt': 2097152,
# }
```

### Decompose File/Folder Path

`folder_name_ext` splits on the **last** dot, so multi-part suffixes such as
`.tar.gz` are not collapsed into one extension. Recover the original
file name with `"basename.extension"`.

```python
from os_helper import folder_name_ext

# Decompose a file path into folder, base name, and extension
folder, name, ext = folder_name_ext("/path/to/file.tar.gz")
print(folder, name, ext)  # Output: '/path/to', 'file.tar', 'gz'

# Handle folders
folder, name, ext = folder_name_ext("/path/to/folder")
print(folder, name, ext)  # Output: '/path/to', 'folder', ''

# Handle files without extensions
folder, name, ext = folder_name_ext("/path/to/file")
print(folder, name, ext)  # Output: '/path/to', 'file', ''

```

### Compress a Folder into a ZIP File

```python
from os_helper import zip_folder

# Create a ZIP archive of a folder and its contents
zip_folder("/path/to/folder", "/path/to/folder_archive.zip")
print("Folder successfully compressed into a ZIP archive!")
```

## String Utilities

String utilities simplify common string manipulation tasks, such as ensuring ASCII compatibility and cleaning up strings for safe usage in filenames or URLs.



### Check for Blank Strings

`emptystring` catches `None`, `""`, and whitespace-only strings in one call:
use it instead of `not s` or `s == ""`, which both miss `"   "`.

```python
from os_helper import emptystring

print(emptystring(None))     # True
print(emptystring(""))       # True
print(emptystring("   "))    # True  (whitespace-only)
print(emptystring("hello"))  # False
```

### ASCII String Conversion

```python
from os_helper import asciistring

# Convert a string to a safe ASCII representation
safe_string = asciistring("Café-Con-Leche!", replacement_char="_")
print(safe_string)  # Output: 'cafe_con_leche'

# Allow digits and preserve capitalization
safe_string = asciistring("Special#File$2024", lower=False)
print(safe_string)  # Output: 'Special-File-2024'

# Ensure the result is suitable for filenames or URLs
safe_string = asciistring("Café@2024.txt")
print(safe_string)  # Output: 'cafe-2024-txt'
```

## Temporary Resources

Temporary resource utilities allow the creation of temporary files or directories for testing or intermediate data storage. These resources are automatically cleaned up when the context ends.


### Create a Temporary File

```python
from os_helper import temporary_filename

# Create a temporary file
with temporary_filename(suffix=".txt") as temp_file:
    print(f"Temporary file created: {temp_file}")
    # Perform operations on the temporary file
    with open(temp_file, "wt") as f:
        f.write("Temporary content")
# The file is removed automatically after the context ends
```

### Create a Temporary Folder

```python
from os_helper import temporary_folder

# Create a temporary folder
with temporary_folder(prefix="tempdir") as temp_dir:
    print(f"Temporary folder created: {temp_dir}")
    # Perform operations inside the temporary folder
    with open(f"{temp_dir}/tempfile.txt", "wt") as f:
        f.write("Temporary content")
# The folder and its contents are removed automatically after the context ends
```

### Create a Persistent Temporary Directory (caller-owned cleanup)

`make_temporary_directory` is the non-context-manager companion to
`temporary_folder`: use it when the directory must **outlive** a `with` block
(a request handler that cleans up after streaming a response, a
process-lifetime scratch dir, …). You own the cleanup.

```python
from os_helper import make_temporary_directory, remove_directory

work = make_temporary_directory(prefix="myjob-")
try:
    # ... write intermediate artifacts into `work`, hand the path around ...
    pass
finally:
    remove_directory(work)  # you decide when it dies
```

You can also pin a `temporary_filename` inside a chosen directory (e.g. so a
tool that resolves paths relative to the file still finds its siblings):

```python
from os_helper import temporary_filename

with temporary_filename(suffix=".wav", directory=work) as tmp:
    # `tmp` sits inside `work`, next to any sibling inputs
    ...
```

### Stage a File on a Remote Backend

`temporary_remote_file` uploads a local file to wherever you point it (S3,
GCS, SFTP, an HTTP endpoint, an in-memory dict…) and guarantees the remote
artifact is deleted when the `with` block exits, even if the body raises.

Provide two callables for your backend: `upload(local_path) -> remote_id`
and `delete(remote_id) -> None`. Optionally pass `checkfile_function` to
validate the upload, or `from_local_file=<path>` to upload an existing file
instead of creating a new one.

```python
from os_helper import temporary_remote_file

storage = {}

def upload(local_path):
    with open(local_path, "rb") as f:
        storage[local_path] = f.read()
    return local_path  # use the local path as the "remote" handle

def delete(remote_path):
    storage.pop(remote_path, None)

with temporary_remote_file(
    upload, delete,
    prefix="run", suffix=".bin",
    initial_content=b"hello world",
) as remote:
    assert storage[remote] == b"hello world"
# remote artifact is gone after the block
```

## System Commands

The `system` utility function allows you to run system commands and capture their output and error messages. It provides robust error handling and optional checks for expected output files or directories.



### Run a System Command

```python
from os_helper import system

# Run a system command
output = system("echo 'Hello, World!'")
print(output["out"])  # Command output: "Hello, World!"
print(output["err"])  # Command error (if any)

# Run a command and check for expected output
output = system("touch example.txt", expected_output="example.txt")
assert output["out"] == ""  # No stdout output for the 'touch' command
assert output["err"] == ""  # No stderr output for the 'touch' command
```


## Networking

The `Networking` utilities provide simple ways to check URLs and retrieve public IP addresses.



### Check if a URL is Valid and Reachable

```python
from os_helper import is_working_url

# Check if a URL is valid and reachable
url = "https://www.google.com"
if is_working_url(url):
    print(f"The URL {url} is reachable.")
else:
    print(f"The URL {url} is not reachable.")
```

### Retrieve Public IP Addresses

```python
from os_helper import get_user_ip

# Get public IP addresses
ip_info = get_user_ip()
print(f"IPv4 Address: {ip_info['ipv4']}")
print(f"IPv6 Address: {ip_info['ipv6']}")
```

## Hashing

The `Hashing` utilities allow you to generate hashes for strings, files, and folders, including support for various content and configuration options.


### Generate a Hash for a String

```python
from os_helper import hash_string

# Generate a hash for a string
input_string = "example"
hash_result = hash_string(input_string)
print(f"Hash of '{input_string}': {hash_result}")

# Generate a truncated hash
truncated_hash = hash_string(input_string, size=8)
print(f"Truncated hash: {truncated_hash}")
```

### Hash a File

```python
from os_helper import hashfile

# Create a sample file for hashing
with open("example.txt", "w") as f:
    f.write("Hash this content")

# Generate a hash for the file
file_hash = hashfile("example.txt")
print(f"File hash: {file_hash}")
```

### Hash a Folder

```python
from os_helper import hashfolder

# Create a test folder and files
import os
os.makedirs("test_folder", exist_ok=True)
with open("test_folder/file1.txt", "w") as f:
    f.write("File 1 content")
with open("test_folder/file2.txt", "w") as f:
    f.write("File 2 content")

# Generate a hash for the folder based on content
folder_hash = hashfolder("test_folder", hash_content=True)
print(f"Folder content hash: {folder_hash}")

# Generate a hash for the folder based on path only
path_hash = hashfolder("test_folder", hash_content=False, hash_path=True)
print(f"Folder path hash: {path_hash}")

# Generate a hash including the current date
dated_hash = hashfolder("test_folder", date=True)
print(f"Folder hash with date: {dated_hash}")
```


## Duration Helpers

Helpers to render and parse human-readable durations.


### Format Durations into Readable Strings

`time2str` formats a number of seconds into hours / minutes / seconds.

```python
from os_helper import time2str

duration = 3661  # 1 hour, 1 minute, and 1 second

formatted_time = time2str(duration)
print(f"Formatted time: {formatted_time}")          # "1 hr 1 min 1 sec"

compact_time = time2str(duration, no_space=True)
print(f"Compact time: {compact_time}")              # "1hr 1min 1sec"
```

### Parse Strings into Durations

`str2time` parses common duration spellings into seconds.

```python
from os_helper import str2time

print(str2time("1:30:00"))      # 5400.0  (HH:MM:SS)
print(str2time("1 hr 30 min"))  # 5400.0
print(str2time("90 minutes"))   # 5400.0
print(str2time("1.5 days"))     # 129600.0
```

## Miscellaneous Utilities

The `Miscellaneous Utilities` section contains functions for logging, downloading files, and generating verbose messages.


### Verbosity and Logging

`verbosity(n)` sets the global log level on the root logger; called with no
argument it returns the current level. The mapping is symmetric around zero:

| level | logging name |
|------:|:-------------|
|  ``>= 2`` | DEBUG    |
|  ``1``    | INFO     |
|  ``0``    | WARNING  |
|  ``-1``   | ERROR    |
|  ``<= -2``| CRITICAL |

```python
from os_helper import verbosity, debug, info, error, critical, check

verbosity(2)  # show DEBUG + INFO + WARNING + ERROR + CRITICAL

debug("Only visible once verbosity(2) or higher is set.")
info("The process started successfully.")

# `error(...)` and `critical(...)` both log without raising.
# Use `check(cond, msg)` for assert-style failure, or raise explicitly.
error("Something went wrong, but execution continues.")
critical("Unrecoverable state reached, logged, caller decides what's next.")
check(1 + 1 == 2, "arithmetic is broken")
```

For a top-level application, script, notebook, or CLI, `init_logging` wires up a
colored console handler (and optionally a UTF-8 log file) in one call. The
convenience helpers above (`info` / `warning` / …) log through a dedicated
`"os_helper"` logger whose records propagate to whatever `init_logging`
configures.

```python
import logging
from os_helper import init_logging, info

# Root logger: colored console + a log file, DEBUG and up.
init_logging(level=logging.DEBUG, filename="run.log")
info("logging is configured")

# CLI-friendly variant: configure just your tool's logger tree. Idempotent
# (a repeat call adds no duplicate handler), and propagate=True keeps records
# visible to a host's / pytest's root handlers (caplog).
init_logging(name="mytool", propagate=True, live_stream=True)
```

### Timestamps and Byte Sizes

```python
from os_helper import now_string, format_size

# Current timestamp, two flavors: human-readable "log", or filesystem-safe.
print(now_string())              # "2026/08/09-14:32:07"
print(now_string("filename"))    # "2026-08-09-14-32-07"

# Human-readable byte counts (decimal/SI units, like disk vendors quote).
print(format_size(512))          # "512 B"
print(format_size(1_536))        # "1.50 KB"
print(format_size(1_536_000))    # "1.50 MB"
print(format_size(1_500_000_000))  # "1.50 GB"
```

### Download Files

The download_file function lets you download files from a URL to a specified location.

`download_file` is the suite-wide transfer primitive: it streams block-by-block
(flat memory footprint even for a multi-GB file), shows a progress bar on an
interactive terminal (auto-suppressed off-TTY), and by default is **resumable**,
**retried**, **atomic**, and **idempotent**. It returns metadata so you can pick
a file extension from the server's MIME type without a second request.

```python
from os_helper import download_file, file_exists

# Basic download. Bytes land in a "<file>.part" sidecar and are atomically
# renamed onto the destination when complete, so the final path only ever exists
# as a whole file, never a truncated one.
url = "https://example.com/sample.pdf"  # put your own URL instead of this fake example one
file_path = "downloaded_sample.pdf"

meta = download_file(url, file_path)
print(meta)
# {'path': 'downloaded_sample.pdf', 'content_type': 'application/pdf',
#  'bytes': 12345, 'sha256': '', 'resumed': False}

# Idempotent by default: a second call sees the complete file and skips the
# network entirely. Pass overwrite=True to force a fresh download.
download_file(url, file_path)  # no re-download; returns immediately

# Integrity-checked and resumable: if a partial "<file>.part" exists, the
# transfer continues with an HTTP Range request instead of restarting; the
# finished file's SHA-256 is verified and a mismatch raises ValueError. Transient
# network errors are retried with exponential backoff (retries=3 by default).
download_file(
    "https://example.com/model.bin",
    "model.bin",
    sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
)

# Some servers/CDNs reject the pre-flight HEAD check (405/403) even though GET
# works: pass check_url=False to skip it and rely on the GET status instead.
download_file(url, file_path, check_url=False, overwrite=True)

# Verify the file exists
if file_exists(file_path):
    print(f"File downloaded successfully to {file_path}")
else:
    print("File download failed.")
```



### Progress Bars for Custom Transfers

`download_file` uses `progress_bar` internally; reach for it directly when
wrapping your own transfer (an S3/SFTP callback, a custom chunked upload) so
every byte-moving operation in your project shows the same UI: byte-scaled
units, and auto-suppressed when `stderr` isn't an interactive terminal (CI
logs, piped output).

```python
from os_helper import progress_bar

total_bytes = 10_485_760  # e.g. from a Content-Length header
bar = progress_bar(total=total_bytes, desc="uploading")
for chunk in range(0, total_bytes, 1_048_576):
    # ... send/receive one chunk here ...
    bar.update(min(1_048_576, total_bytes - chunk))
bar.close()
```

### Open Files with Default Applications

`openfile` opens a file with the OS default application for its type.

```python
from os_helper import openfile

# Open a PDF file using the default viewer
openfile("example.pdf")  # replace with a real file on your machine
```

## Profiling Helpers

Three context managers and a MATLAB-style pair for measuring how long
code takes. Pick the right tool for the question:

| Question | Use |
|---|---|
| "How long did this take in real time?" (includes sleeps, I/O, GPU waits) | `wall_timer` |
| "How much CPU work did this do?" (excludes sleep / I/O / subprocesses) | `cpu_timer` |
| "How long did the GPU spend on this?" (CUDA Events or MPS sync) | `gpu_timer` |
| "Quick MATLAB-style stopwatch" | `tic` / `toc` |

### Wall-Clock Timer

```python
import time
from os_helper import wall_timer, time2str

with wall_timer() as t:
    time.sleep(0.05)
    # ... work ...

print(f"Real time: {t['seconds']:.3f} s ({time2str(t['seconds'])})")
```

### CPU Timer

`cpu_timer` reports CPU consumed by this process (user + system, summed
across threads); sleeps and I/O don't count, so it isolates "real
computation". Does NOT include subprocesses (use `wall_timer` for those).

```python
from os_helper import cpu_timer

with cpu_timer() as t:
    total = sum(i * i for i in range(10_000_000))

print(f"CPU time: {t['seconds']:.3f} s")
```

### GPU Timer

Lazy `torch` import: `os-helper` itself does NOT depend on PyTorch.
If torch isn't installed or no GPU is available at call time, raises a
clear `RuntimeError` (the helper exists; it just refuses to run).

```python
from os_helper import gpu_timer
import torch

if torch.cuda.is_available():
    x = torch.randn(2048, 2048, device="cuda")
    with gpu_timer() as t:           # backend="auto" picks cuda/mps/raise
        y = x @ x
    print(f"GPU time: {t['milliseconds']:.2f} ms")
```

Apple Silicon: pass `backend="mps"` (or rely on `auto`). PyTorch's MPS
path lacks fine-grained timing events, so the helper falls back to
`torch.mps.synchronize()` + wall-clock around the synchronized block
(accuracy ~1 ms).

### MATLAB-style tic / toc

For sprinkling a quick stopwatch mid-script. Each `tic()` overwrites the
implicit "last tic". For nested timings, capture the handle.

```python
from os_helper import tic, toc

tic()
# ... work ...
elapsed = toc()                  # seconds, does NOT reset
print(f"Took {elapsed:.3f}s")

# Nested timings via explicit handles:
t_outer = tic()
# ...
t_inner = tic()
# ...
print(toc(t_inner))              # inner block
print(toc(t_outer))              # outer block
```

Call `toc(log=True)` to also emit an INFO log line.
