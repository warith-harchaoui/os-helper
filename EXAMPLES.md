# OS Helper Examples

This document provides detailed examples for using the `OS Helper` module to simplify common programming tasks.

---

## Table of Contents

1. [Setup and Configuration](#setup-and-configuration)
2. [System Information](#system-information)
3. [File and Directory Utilities](#file-and-directory-utilities)
4. [String Utilities](#string-utilities)
5. [Temporary Resources](#temporary-resources)
6. [System Commands](#system-commands)
7. [Networking](#networking)
8. [Hashing](#hashing)
9. [Timer Utilities](#timer-utilities)
10. [Miscellaneous Utilities](#miscellaneous-utilities)

---

## Setup and Configuration

Before using `OS Helper`, make sure the required dependencies are installed:

```bash
pip install -r requirements.txt
```

## System Information

### Check Operating System

Use the following functions to determine the platform your script is running on:

```python
from os_helper.main import windows, linux, macos, unix

# Check if the system is Windows
print(windows())  # True if Windows

# Check if the system is Linux
print(linux())  # True if Linux

# Check if the system is macOS
print(macos())  # True if macOS

# Check if the system is Unix-based
print(unix())  # True if Linux or macOS
```

## File and Directory Utilities

### Check File or Directory Existence

```python
from os_helper.main import file_exists, dir_exists

# Check if a file exists
print(file_exists("example.txt"))  # True if the file exists

# Check if a directory exists and is not empty
print(dir_exists("/path/to/folder", check_empty=True))  # True if the directory is non-empty
```

## Manage Directories

```python
from os_helper.main import make_directory, remove_directory

# Create a directory
make_directory("/path/to/new_folder")

# Remove a directory
remove_directory("/path/to/new_folder")
```

## File Size and Path Operations

```python
from os_helper.main import size_file, absolute2relative_path, relative2absolute_path

# Get the size of a file
print(size_file("example.txt"))  # File size in bytes

# Convert an absolute path to a relative path
print(absolute2relative_path("/home/user/project/file.txt", "/home/user"))  # 'project/file.txt'

# Convert a relative path to an absolute path
print(relative2absolute_path("relative/path"))  # '/absolute/path/to/relative/path'
```

## String Utilities
### ASCII String Conversion

```python
from os_helper.main import asciistring

# Convert a string to a safe ASCII representation
print(asciistring("Café-Con-Leche!", replacement_char="_"))  # 'cafe_con_leche'
```

## Temporary Resources

```python
from os_helper.main import temporary_filename, temporary_folder

# Create a temporary file
with temporary_filename(suffix=".txt") as temp_file:
    print(f"Temporary file: {temp_file}")

# Create a temporary folder
with temporary_folder(prefix="tempdir") as temp_dir:
    print(f"Temporary folder: {temp_dir}")
```

## System Commands

```python
from os_helper.main import system

# Run a system command
output = system("ls -la")
print(output['out'])  # Command output
print(output['err'])  # Command error (if any)
```

## Networking

```python
from os_helper.main import is_working_url, get_user_ip

# Check if a URL is valid and reachable
print(is_working_url("https://www.google.com"))  # True if reachable

# Get user's public IP addresses
print(get_user_ip())  # {'ipv4': 'x.x.x.x', 'ipv6': 'y:y:y:y'}
```

## Hashing

### Hashing Strings, Files, and Folders

```python
from os_helper.main import hash_string, hashfile, hashfolder

# Generate a hash for a string
print(hash_string("example"))  # String hash

# Generate a hash for a file (taking into account content)
print(hashfile("example.txt"))  # File hash

# Generate a hash for a folder (recursively taking into account content)
print(hashfolder("/path/to/folder"))  # Folder hash
```

## Timer Utilities

### Time Measurements

In matlab fashion 

```python
from os_helper.main import tic, toc

# Start a timer
start_time = tic()

# Perform some operations
result = sum(range(1000000))

# Stop the timer and get elapsed time
elapsed_time = toc(start_time)
print(f"Elapsed time: {elapsed_time:.2f} seconds")
```

### Retrieve Current Timestamp

```python
from os_helper.main import now_string

# Get the current timestamp as a formatted string
print(now_string("log"))  # 'YYYY/MM/DD-HH:MM:SS'
```


## Miscellaneous Utilities

### Verbosity and logging

```python
from os_helper.main import verbosity, info, error

# Set verbosity level
verbosity(2)  # Set to info level

# Log informational messages
info("Process completed successfully.")

# Log error and terminate
error("Critical failure", error_code=2)
```

### Download file

```python
from os_helper.main import download_file

# Download a file from a URL
download_file("https://example.com/file.txt", "downloaded_file.txt")
print("File downloaded successfully.")
```