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
6. [System Commands](#system-commands)
   - [Run a System Command](#run-a-system-command)
7. [Networking](#networking)
   - [Check if a URL is Valid and Reachable](#check-if-a-url-is-valid-and-reachable)
   - [Retrieve Public IP Addresses](#retrieve-public-ip-addresses)
8. [Hashing](#hashing)
   - [Generate a Hash for a String](#generate-a-hash-for-a-string)
   - [Hash a File](#hash-a-file)
   - [Hash a Folder](#hash-a-folder)
9. [Timer Utilities](#timer-utilities)
   - [Measure Execution Time](#measure-execution-time)
   - [Format Durations into Readable Strings](#format-durations-into-readable-strings)
10. [Miscellaneous Utilities](#miscellaneous-utilities)
    - [Verbosity and Logging](#verbosity-and-logging)
    - [Download Files](#download-files)
    - [Generate Random File Names and Temporary Resources](#generate-random-file-names-and-temporary-resources)
    - [Open Files with Default Applications](#open-files-with-default-applications)

---


## Setup and Configuration

Before using `OS Helper`, make sure the required dependencies are installed:

```bash
pip install -r requirements.txt
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

```python
from os_helper import folder_description

# Generate a description of a folder, including file sizes
description = folder_description(
    "/path/to/folder",
    recursive=True,  # Include subdirectories
    index_html=True,  # Generate an HTML index
    with_size=True  # Include file sizes
)

# Output: A dictionary of file names and sizes
print(description)
# {
#     'file1.txt': 1024,
#     'subfolder/file2.txt': 2097152
# }

# Generated outputs:
# - HTML index at /path/to/folder/index.html
# - JSON description at /path/to/folder/description.json
```

### Decompose File/Folder Path

```python
from os_helper import folder_name_ext

# Decompose a file path into folder, base name, and extension
folder, name, ext = folder_name_ext("/path/to/file.tar.gz")
print(folder, name, ext)  # Output: '/path/to', 'file', 'tar.gz'

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


## Timer Utilities

The `Timer Utilities` allow you to measure execution time and format durations in human-readable forms.


### Measure Execution Time

The `tic` and `toc` functions emulate MATLAB-style timing for quick and simple performance measurement.

```python
from os_helper import tic, toc

# Start a timer
start_time = tic()

# Perform some operations
result = sum(range(1000000))  # Example computation

# Stop the timer and get elapsed time
elapsed_time = toc(start_time)
print(f"Elapsed time: {elapsed_time:.2f} seconds")
```

### Format Durations into Readable Strings

The time2str function formats elapsed time into human-readable components (e.g., hours, minutes, and seconds).


```python
from os_helper import time2str

# Example duration in seconds
duration = 3661  # 1 hour, 1 minute, and 1 second

# Format with default spacing
formatted_time = time2str(duration)
print(f"Formatted time: {formatted_time}")

# Format without spaces between units
compact_time = time2str(duration, no_space=True)
print(f"Compact time: {compact_time}")
```

## Networking

The `Networking` utilities include tools to check URL reachability and fetch public IP addresses.


### Check URL Reachability

The `is_working_url` function validates and tests if a given URL is accessible.

```python
from os_helper import is_working_url

# Test a valid URL
url = "https://www.google.com"
if is_working_url(url):
    print(f"{url} is reachable!")
else:
    print(f"{url} is not reachable.")
```

### Fetch Public IP Addresses

The get_user_ip function retrieves the user's public IPv4 and IPv6 addresses.

```python
from os_helper import get_user_ip

# Fetch the public IP addresses
ip_addresses = get_user_ip()
print("Your IP addresses:")
print(f"IPv4: {ip_addresses.get('ipv4')}")
print(f"IPv6: {ip_addresses.get('ipv6')}")
```

## Miscellaneous Utilities

The `Miscellaneous Utilities` section contains functions for logging, downloading files, and generating verbose messages.


### Verbosity and Logging

The verbosity level controls the amount of detail in the logs. Use the `verbosity` function to set or retrieve the verbosity level, and the `info` and `error` functions to log messages.

```python
from os_helper import verbosity, info, error

# Set verbosity level
verbosity(2)  # Info level

# Log an informational message
info("The process started successfully.")

# Log an error message and terminate the program
# Uncomment to test:
# error("Critical failure occurred!", error_code=1)
```

### Download Files

The download_file function lets you download files from a URL to a specified location.

```python
from os_helper import download_file, file_exists

# Download a file from the web
url = "https://example.com/sample.pdf"
file_path = "downloaded_sample.pdf"

download_file(url, file_path)

# Verify the file exists
if file_exists(file_path):
    print(f"File downloaded successfully to {file_path}")
else:
    print("File download failed.")
```

### Generate Random File Names and Temporary Resources

You can use temporary_filename to create temporary files for secure and isolated operations.

```python
from os_helper import temporary_filename

# Create a temporary file
with temporary_filename(suffix=".txt") as temp_file:
    print(f"Temporary file created: {temp_file}")
    # Use the file as needed (e.g., write some data)
```

### Open Files with Default Applications

The openfile function opens a file using the default application for its type.

```python
from os_helper import openfile

# Open a PDF file using the default viewer
openfile("example.pdf")
```