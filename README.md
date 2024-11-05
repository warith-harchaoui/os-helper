# OS Helper

`OS Helper` belongs to a collection of libraries called `AI Helpers` developped for building Artificial Intelligence

[🕸️ AI Helpers](https://harchaoui.org/warith/ai-helpers)

[![logo](assets/logo.png)](https://harchaoui.org/warith/ai-helpers)


OS Helper is a Python library that provides utility functions for working with different operating systems.  

It offers a set of tools to simplify common system operations, file handling, and OS-specific tasks.

# Features

- Operating system detection (Windows, Linux, macOS, Unix)
- File system operations (create, delete, move, copy)
- System information retrieval (CPU, memory, disk usage)
- Cross-platform path handling
- File hashing and string hashing utilities
- Process management and execution

# Installation

## Install Package

We can recommand python environments. Check this link if you don't know how

[🥸 Tech tips](https://harchaoui.org/warith/4ml/#install)


```bash
pip install --force-reinstall --no-cache-dir git+https://github.com/warith-harchaoui/os-helper.git@main
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

# Remove the copied file
osh.remove_files([destination_file], verbose=True)
```



5. Decompose a Path and Temporary File Creation
```python
# Decompose a file path into folder, basename, and extension
folder, basename, ext = osh.folder_name_ext("/path/to/myfile.tar.gz")
osh.info(f"Folder: {folder}, Basename: {basename}, Extension: {ext}")

# Create and write to a temporary file
with osh.temporary_filename(suffix=".log") as temp_log:
    osh.info(f"Temporary file created at: {temp_log}")
    with osh.open(temp_log, "w") as log_file:
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

# Authors
 - [Warith Harchaoui](https://harchaoui.org/warith)
 - [Mohamed Chelali](https://mchelali.github.io)
 - [Bachir Zerroug](https://www.linkedin.com/in/bachirzerroug)

