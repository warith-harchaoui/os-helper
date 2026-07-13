# OS Helper Examples

This document provides detailed examples for using the `OS Helper` module to simplify common programming tasks.

---

## Table of Contents

1. [Setup and Configuration](#setup-and-configuration)
2. [System Information](#system-information)
3. [File and Directory Utilities](#file-and-directory-utilities)
   - [Check File or Directory Existence](#check-file-or-directory-existence)
   - [Manage Directories](#manage-directories)
   - [File Size and Path Operations](#file-size-and-path-operations)
   - [Describe Folder Contents](#describe-folder-contents)
   - [Decompose File/Folder Path](#decompose-filefolder-path)
   - [Compress a Folder into a ZIP File](#compress-a-folder-into-a-zip-file)
4. [String Utilities](#string-utilities)
   - [ASCII String Conversion](#ascii-string-conversion)
5. [Temporary Resources](#temporary-resources)
   - [Create a Temporary File](#create-a-temporary-file)
   - [Create a Temporary Folder](#create-a-temporary-folder)
   - [Stage a File on a Remote Backend](#stage-a-file-on-a-remote-backend)
6. [System Commands](#system-commands)
   - [Run a System Command](#run-a-system-command)
7. [Networking](#networking)
   - [Check if a URL is Valid and Reachable](#check-if-a-url-is-valid-and-reachable)
   - [Retrieve Public IP Addresses](#retrieve-public-ip-addresses)
8. [Hashing](#hashing)
   - [Generate a Hash for a String](#generate-a-hash-for-a-string)
   - [Hash a File](#hash-a-file)
   - [Hash a Folder](#hash-a-folder)
9. [Duration Helpers](#duration-helpers)
   - [Format Durations into Readable Strings](#format-durations-into-readable-strings)
   - [Parse Strings into Durations](#parse-strings-into-durations)
10. [Miscellaneous Utilities](#miscellaneous-utilities)
    - [Verbosity and Logging](#verbosity-and-logging)
    - [Download Files](#download-files)
    - [Open Files with Default Applications](#open-files-with-default-applications)
11. [Profiling Helpers](#profiling-helpers)
    - [Wall-Clock Timer](#wall-clock-timer)
    - [CPU Timer](#cpu-timer)
    - [GPU Timer](#gpu-timer)
    - [MATLAB-style tic / toc](#matlab-style-tic--toc)

---


## Setup and Configuration

Install the package from PyPI (or directly from GitHub — see the README):

```bash
pip install -r requirements.txt
```

Then import the library — examples below use the conventional `osh` alias:

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

### Stage a File on a Remote Backend

`temporary_remote_file` uploads a local file to wherever you point it (S3,
GCS, SFTP, an HTTP endpoint, an in-memory dict…) and guarantees the remote
artifact is deleted when the `with` block exits — even if the body raises.

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
from os_helper import verbosity, info, error, check

verbosity(2)  # show DEBUG + INFO + WARNING + ERROR

info("The process started successfully.")

# `error(...)` logs at ERROR level but does NOT raise.
# Use `check(cond, msg)` for assert-style failure, or raise explicitly.
error("Something went wrong, but execution continues.")
check(1 + 1 == 2, "arithmetic is broken")
```

### Download Files

The download_file function lets you download files from a URL to a specified location.

```python
from os_helper import download_file, file_exists

# Download a file from the web
url = "https://example.com/sample.pdf" # put your own URL instead of this fake example one
file_path = "downloaded_sample.pdf"

download_file(url, file_path)

# Verify the file exists
if file_exists(file_path):
    print(f"File downloaded successfully to {file_path}")
else:
    print("File download failed.")
```



### Open Files with Default Applications

The openfile function opens a file using the default application for its type.

```python
from os_helper import openfile

# Open a PDF file using the default viewer
openfile("example.pdf") # put your own file to open by your own OS instead of this fake example one
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
across threads) — sleeps and I/O don't count, so it isolates "real
computation". Does NOT include subprocesses (use `wall_timer` for those).

```python
from os_helper import cpu_timer

with cpu_timer() as t:
    total = sum(i * i for i in range(10_000_000))

print(f"CPU time: {t['seconds']:.3f} s")
```

### GPU Timer

Lazy `torch` import — `os-helper` itself does NOT depend on PyTorch.
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
