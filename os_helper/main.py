"""
OS Helper

This module provides a collection of utility functions aimed at simplifying 
various common programming tasks, including file handling, system operations, 
string manipulation, folder management, and more. The functions are optimized 
for cross-platform compatibility and robust error handling.

Authors:
 - Warith Harchaoui, https://harchaoui.org/warith
 - Mohamed Chelali, https://mchelali.github.io
 - Bachir Zerroug, https://www.linkedin.com/in/bachirzerroug

Dependencies:
- contextlib
- glob
- hashlib
- json
- logging
- os
- pathlib
- shlex
- shutil
- sys
- tempfile
- requests
- datetime (from datetime)
- subprocess (from subprocess)
- platform (from sys)
- numpy
- yaml
- validators
- zipfile
"""

import contextlib
import glob
import hashlib
import json
import logging
import os
import os.path
import pathlib
import shlex
import shutil
import string
import sys
import tempfile
import requests
from datetime import datetime
from subprocess import PIPE, Popen
from sys import platform

import numpy as np
import yaml
import validators

import zipfile
import unicodedata


# Default logging setup
name = os.getcwd().split(os.sep)[-1]
date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
os.makedirs("logs", exist_ok=True)
log_file = os.path.join("logs", f"{name}-{date}.log")
logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s - %(levelname)s - {name} - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(), logging.FileHandler(log_file, mode='wt')]
)

# Default verbosity level
VERBOSITY_LEVEL = 1

def verbosity(level: int = None) -> int:
    """
    Set or retrieve the current verbosity level for logging.

    This function allows for dynamic adjustment of the verbosity level of the logging system, 
    enabling different levels of logging details to be output (e.g., errors only, detailed debugging information, etc.).
    If no level is provided, it returns the current verbosity level.

    Parameters
    ----------
    level : int, optional
        The verbosity level to set (0: None, 1: Error, 2: Info, 3: Debug). 
        If None, retrieves the current verbosity level. Defaults to None.

    Verbosity Levels:
    - 0: Disable all logging.
    - 1: Show only error messages.
    - 2: Show informational messages (default level).
    - 3: Show debugging messages (most detailed).

    Returns
    -------
    int
        The current verbosity level after setting it (if a new level was provided).

    Example
    -------
    >>> verbosity(2)  # Set verbosity to show info-level messages
    >>> verbosity()   # Retrieve the current verbosity level (2)
    """

    global VERBOSITY_LEVEL  # Ensure we modify the global verbosity level

    if level is not None:
        VERBOSITY_LEVEL = level  # Update the global verbosity level based on user input

        # Adjust logging configuration based on the verbosity level
        if level == 0:
            logging.disable(logging.CRITICAL)  # Disable all logging output
        elif level == 1:
            logging.basicConfig(level=logging.ERROR)  # Only show error messages
        elif level == 2:
            logging.basicConfig(level=logging.INFO)  # Show info messages
        elif level == 3:
            logging.basicConfig(level=logging.DEBUG)  # Show debug messages (most verbose)

    return VERBOSITY_LEVEL  # Return the current verbosity level (after possible modification)


def windows() -> bool:
    """
    Determine if the current operating system is Windows.

    This function checks the platform identifier to determine if the script is running on a Windows OS.

    Returns
    -------
    bool
        True if the operating system is Windows, False otherwise.

    Example
    -------
    >>> windows()
    True  # if running on Windows
    """
    return platform.lower().startswith("win")  # Check if the platform starts with "win" (Windows)

def linux() -> bool:
    """
    Determine if the current operating system is Linux.

    This function checks the platform identifier to determine if the script is running on a Linux OS.

    Returns
    -------
    bool
        True if the operating system is Linux, False otherwise.

    Example
    -------
    >>> linux()
    True  # if running on Linux
    """
    return platform.lower().startswith("linux")  # Check if the platform starts with "linux"

def macos() -> bool:
    """
    Determine if the current operating system is macOS.

    This function checks the platform identifier to determine if the script is running on a macOS.

    Returns
    -------
    bool
        True if the operating system is macOS, False otherwise.

    Example
    -------
    >>> macos()
    True  # if running on macOS
    """
    return platform.lower().startswith("darwin")  # Check if the platform starts with "darwin" (macOS identifier)

def unix() -> bool:
    """
    Determine if the current operating system is Unix-based (Linux or macOS).

    This function checks if the operating system is either Linux or macOS, 
    which are both Unix-based systems.

    Returns
    -------
    bool
        True if the operating system is Unix-based (Linux or macOS), False otherwise.

    Example
    -------
    >>> unix()
    True  # if running on Linux or macOS
    """
    return linux() or macos()  # Unix-based systems include Linux and macOS



def get_nb_workers() -> int:
    """
    Get the number of available CPU workers for parallel processing.

    This function returns the number of CPU cores available on the machine.
    If the environment variable "NB_WORKERS" is set, its value will override the default CPU count,
    allowing you to control the number of workers manually.

    Returns
    -------
    int
        The number of available CPU cores, or the value of the "NB_WORKERS" environment variable (if set and valid).

    Example
    -------
    >>> get_nb_workers()
    8  # Depending on the number of CPU cores available
    """
    nb_workers = os.cpu_count()  # Default to the number of CPU cores
    if "NB_WORKERS" in os.environ:
        try:
            nb_workers = int(os.environ["NB_WORKERS"])  # Override with NB_WORKERS if it's set and valid
        except ValueError:
            logging.info("NB_WORKERS environment variable is not a valid integer. Using default CPU count.")
    return nb_workers


def emptystring(s: str) -> bool:
    """
    Check if a string is empty or None.

    This utility function checks if the given string is either None or an empty string. 
    It is useful for quickly validating user input or file paths.

    Parameters
    ----------
    s : str
        The string to check.

    Returns
    -------
    bool
        True if the string is None or empty, False otherwise.

    Example
    -------
    >>> emptystring("")
    True

    >>> emptystring("hello")
    False
    """
    return (s is None) or (isinstance(s, str) and len(s) == 0)  # Check if string is None or empty



def now_string(format: str = "log") -> str:
    """
    Get the current timestamp as a formatted string.

    This function generates a string representation of the current date and time.
    The format can be adjusted for logging or file naming purposes.

    Parameters
    ----------
    format : str, optional
        The format of the timestamp. 
        "log" (default) provides a log-friendly format (YYYY/MM/DD-HH:MM:SS).
        "filename" replaces special characters (e.g., slashes and colons) with hyphens to make the string file-system safe.

    Returns
    -------
    str
        A string representing the current date and time.

    Example
    -------
    >>> now_string("log")
    '2024/10/10-14:33:21'

    >>> now_string("filename")
    '2024-10-10-14-33-21'
    """
    now = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")  # Default log format
    if format == "filename":
        # Adjust for filename-safe format by replacing slashes and colons with hyphens
        now = now.replace("/", "-").replace(":", "-")
    return now



# UTF-8 enforced open function
pythonopen = open


def open(
    filename: str,
    mode: str = "r",
    buffering: int = -1,
    encoding: str = "utf-8",
    errors=None,
    newline=None,
    closefd: bool = True,
    opener=None,
):
    """
    UTF-8 enforced open function.

    This function overrides the built-in `open()` function to enforce UTF-8 encoding by default 
    when reading or writing text files. It falls back to the default behavior for binary files.

    Parameters
    ----------
    filename : str
        The path to the file to be opened.
    mode : str, optional
        The mode in which the file is opened (e.g., "r" for reading, "w" for writing). Defaults to "r".
    buffering : int, optional
        Buffering policy. Defaults to -1 (use system default).
    encoding : str, optional
        Encoding to use for text files. Defaults to "utf-8".
    errors : str, optional
        Error handling strategy (e.g., "ignore", "replace"). Defaults to None.
    newline : str, optional
        How to handle newlines. Defaults to None.
    closefd : bool, optional
        Whether to close the file descriptor after use. Defaults to True.
    opener : callable, optional
        Custom file opener. Defaults to None.

    Returns
    -------
    file object
        The opened file object.

    Example
    -------
    >>> with open("example.txt", "w") as f:
    ...     f.write("Hello, world!")
    """
    if "b" in mode:
        # If the mode is binary (e.g., "rb", "wb"), use the default behavior (no encoding)
        return pythonopen(filename, mode=mode, buffering=buffering, errors=errors, closefd=closefd, opener=opener)
    else:
        # Enforce UTF-8 encoding for text mode (e.g., "r", "w", "a")
        return pythonopen(filename, mode=mode, encoding=encoding, buffering=buffering, errors=errors, newline=newline, closefd=closefd, opener=opener)

@contextlib.contextmanager
def temporary_filename(suffix: str = "", mode: str = "wt", prefix: str = "") -> str:
    """
    Create a temporary file with a unique name that persists even after closing.

    This function generates a temporary file with a unique name, which is removed after use.
    It can be used to safely create and use a temporary file for writing or reading data.

    Parameters
    ----------
    suffix : str, optional
        File suffix (e.g., .txt). Defaults to "".
    mode : str, optional
        Mode in which the file is opened (e.g., "wt" for writing text). Defaults to "wt".
    prefix : str, optional
        Prefix for the file name. Defaults to "".

    Yields
    ------
    str
        The name of the temporary file.

    Example
    -------
    >>> with temporary_filename(suffix=".txt") as temp_file:
    ...     with open(temp_file, "w") as f:
    ...         f.write("Temporary content")
    """
    s = suffix if suffix.startswith(".") else f".{suffix}"  # Ensure suffix starts with a dot
    p = f"{prefix}-{now_string('filename')}-" if prefix else ""  # Create a prefix if provided
    h = hashlib.new("ripemd160").hexdigest()[:8]  # Generate a hash for uniqueness
    with tempfile.NamedTemporaryFile(mode=mode, suffix=s, delete=False, prefix=p) as f:
        yield f.name  # Yield the temporary file name
    os.unlink(f.name)  # Remove the file after use




def error(msg: str, error_code: int = 1) -> None:
    """
    Log an error message and exit the program with a specified error code.

    Parameters
    ----------
    msg : str
        The error message to log.
    error_code : int, optional
        The exit code to use when terminating the program. Defaults to 1.

    Example
    -------
    >>> error("Critical failure", error_code=2)
    """
    logging.error(msg)
    sys.exit(error_code)  # Exit the program with the specified error code


def info(msg: str, error: bool = False, error_code: int = 1) -> None:
    """
    Log an informational message or error message based on the 'error' flag.

    Parameters
    ----------
    msg : str
        The message to log.
    error : bool, optional
        If True, logs the message as an error and exits. Defaults to False.
    error_code : int, optional
        The exit code to use if 'error' is True. Defaults to 1.

    Example
    -------
    >>> info("Process completed successfully.")
    >>> info("Process failed.", error=True, error_code=2)
    """
    logging.info(msg)
    if error:
        error(msg, error_code)



def check(condition: bool, msg: str = "Something went wrong", error_code: int = 1) -> None:
    """
    Check a condition and log an error message if it is not met.

    Parameters
    ----------
    condition : bool
        The condition to check. If False, logs the error message and exits.
    msg : str, optional
        The error message to log if the condition is not met. Defaults to "Something went wrong".
    error_code : int, optional
        The exit code to use if the condition fails. Defaults to 1.

    Example
    -------
    >>> check(1 == 2, msg="Condition failed", error_code=2)
    """
    if not condition:
        info(f"{msg} (error code: {error_code})", error=True)



def file_exists(file_path: str, check_empty: bool = False) -> bool:
    """
    Check if a file exists, with an option to check if it is empty.

    Parameters
    ----------
    file_path : str
        The path to the file.
    check_empty : bool, optional
        If True, checks if the file is not empty. Defaults to False.

    Returns
    -------
    bool
        True if the file exists (and is not empty, if check_empty is True).

    Example
    -------
    >>> file_exists("example.txt")
    True
    """
    return os.path.isfile(file_path) and (not check_empty or os.path.getsize(file_path) > 0)


def dir_exists(path: str, check_empty: bool = False) -> bool:
    """
    Check if a directory exists, with an option to check if it is empty.

    Parameters
    ----------
    path : str
        The path to the directory.
    check_empty : bool, optional
        If True, checks if the directory contains files. Defaults to False.

    Returns
    -------
    bool
        True if the directory exists (and is not empty, if check_empty is True).

    Example
    -------
    >>> dir_exists("/path/to/folder", check_empty=True)
    True
    """
    if not os.path.isdir(path):
        return False
    if check_empty:
        files = [f for f in glob.glob(f"{path}/*") if not f.startswith(".")]
        return len(files) > 0
    return True

def absolute2relative_path(path: str, base_path: str = None) -> str:
    """
    Convert an absolute path to a relative path, using a specified base path.

    This function converts a given absolute path to a relative path, based on a provided base path.
    If no base path is given, it uses the current working directory as the base.

    Parameters
    ----------
    path : str
        The absolute path to convert to a relative path.
    base_path : str, optional
        The base path to use for conversion. If None, uses the current working directory. Defaults to None.

    Returns
    -------
    str
        The relative path from the base path.

    Example
    -------
    >>> absolute2relative_path("/home/user/project/file.txt", "/home/user")
    'project/file.txt'
    """
    if base_path is None:
        base_path = os.getcwd()  # Use the current working directory as the default base path

    # Ensure both the path and the base_path are absolute
    abs_path = os.path.abspath(path)
    abs_base = os.path.abspath(base_path)

    # Convert the absolute path to a relative path based on the base path
    return os.path.relpath(abs_path, abs_base)


def relative2absolute_path(path: str, checkpath: bool = False) -> str:
    """
    Convert a relative path to an absolute path.

    Parameters
    ----------
    path : str
        The relative or absolute file path.
    checkpath : bool, optional
        If True, checks if the path exists. Defaults to False.

    Returns
    -------
    str
        The absolute path.

    Example
    -------
    >>> relative2absolute_path("relative/path")
    '/absolute/relative/path'
    """
    path = os.path.abspath(path)  # Convert to absolute path
    if checkpath:
        check(file_exists(path) or dir_exists(path), f"File/folder does not exist: {path}")
    return path

def path_without_home(path: str) -> str:
    """
    Convert an absolute path to be relative to the user's home directory.

    This function replaces the home directory portion of the given path with a tilde (`~`), 
    making it shorter and easier to read while still maintaining functionality. 
    It works on both Unix-like systems and Windows.

    Parameters
    ----------
    path : str
        The absolute file or directory path to convert.

    Returns
    -------
    str
        The path with the home directory replaced by `~`, or the original path if the home directory 
        is not part of the path or if the path is already relative to `~`.

    Example
    -------
    >>> path_without_home("/home/user/project/file.txt")
    '~/project/file.txt'

    >>> path_without_home("/Users/myuser/project/file.txt")
    '~/project/file.txt'  # On macOS

    >>> path_without_home("C:\\Users\\myuser\\project\\file.txt")
    '~\\project\\file.txt'  # On Windows
    """
    home_dir = os.path.expanduser("~")  # Get the home directory, works cross-platform
    norm_path = os.path.normpath(path)  # Normalize the path to ensure consistency

    if norm_path.startswith(home_dir):  # Check if the path starts with the home directory
        # Replace the home directory part with "~"
        return norm_path.replace(home_dir, "~", 1)
    
    return norm_path  # Return the normalized original path if home is not part of it


def recursive_glob(root_dir: str, pattern: str) -> list:
    """
    Perform a recursive search for files matching a specified pattern.

    This function searches for files within a directory (and its subdirectories) 
    that match a given pattern using `glob`.

    Parameters
    ----------
    root_dir : str
        The root directory to start the recursive search from.
    pattern : str
        The file matching pattern (e.g., "*.txt" for text files).

    Returns
    -------
    list
        A list of file paths that match the specified pattern.

    Example
    -------
    >>> recursive_glob("/home/user", "*.txt")
    ['/home/user/file1.txt', '/home/user/docs/file2.txt']
    """
    matches = []  # List to hold all matching files
    for root, dirs, files in os.walk(root_dir):  # Walk through the directory tree
        for file in glob.glob(os.path.join(root, pattern)):
            matches.append(file)  # Append matching files to the list
    return matches


def os_path_constructor(ell: list) -> str:
    """
    Construct a path from a list of path elements.

    Parameters
    ----------
    ell : list
        List of path components.

    Returns
    -------
    str
        The constructed absolute path.

    Example
    -------
    >>> os_path_constructor(["/home/user", "folder", "file.txt"])
    '/home/user/folder/file.txt'
    """
    return relative2absolute_path(os.path.join(*ell), checkpath=False)


def size_file(filepath: str) -> int:
    """
    Get the size of a file in bytes.

    Parameters
    ----------
    filepath : str
        The path to the file.

    Returns
    -------
    int
        The size of the file in bytes, or -1 if the file does not exist.

    Example
    -------
    >>> size_file("example.txt")
    1024
    """
    return os.path.getsize(filepath) if file_exists(filepath) else -1


def checkfile(filepath: str, msg: str = "", check_empty: bool = False) -> None:
    """
    Check if a file exists and is optionally not empty.

    Parameters
    ----------
    filepath : str
        The path to the file.
    msg : str, optional
        Message to log if the check fails. Defaults to "".
    check_empty : bool, optional
        If True, also checks if the file is not empty. Defaults to False.

    Example
    -------
    >>> checkfile("example.txt", msg="File not found", check_empty=True)
    """
    check(file_exists(filepath), msg=f"{msg} File {filepath} does not exist")
    if check_empty:
        check(size_file(filepath) > 0, msg=f"{msg} File {filepath} is empty")


def getpid() -> str:
    """
    Get the process ID of the current Python process.

    Returns
    -------
    str
        The process ID as a string.

    Example
    -------
    >>> getpid()
    '12345'
    """
    return str(os.getpid())



def copyfile(a: str, b: str) -> None:
    """
    Copy a file from source to destination.

    Parameters
    ----------
    a : str
        Source file path.
    b : str
        Destination file path.

    Example
    -------
    >>> copyfile("source.txt", "destination.txt")
    """
    checkfile(a, msg=f"Copying {a} to {b} failed")
    a2 = relative2absolute_path(a)
    b2 = relative2absolute_path(b)
    check(not(a2 == b2), msg=f"Source and destination are the same: {a2}")
    shutil.copy2(a, b)
    checkfile(b, msg=f"File {a} not copied into {b}")


def remove_directory(folder_path: str) -> None:
    """
    Remove a directory and its contents.

    Parameters
    ----------
    folder_path : str
        Path to the directory to remove.

    Example
    -------
    >>> remove_directory("/path/to/folder")
    """
    if dir_exists(folder_path):
        shutil.rmtree(folder_path)
        info(f"Folder {folder_path} removed")
    info(f"Folder {folder_path} does not exist so it cannot be removed")



def remove_files(files_list: list, verbose: bool = False) -> None:
    """
    Remove a list of files.

    Parameters
    ----------
    files_list : list
        List of file paths to remove.
    verbose : bool, optional
        If True, logs the removal of each file. Defaults to False.

    Example
    -------
    >>> remove_files(["file1.txt", "file2.txt"], verbose=True)
    """
    for f in files_list:
        if file_exists(f):
            pathlib.Path(f).unlink()
            if verbose:
                info(f"File {f} removed")

def make_directory(folder_path: str, exist_ok: bool = True) -> None:
    """
    Create a directory, optionally ignoring if it already exists.

    Parameters
    ----------
    folder_path : str
        Path to the directory to create.
    exist_ok : bool, optional
        If True, does not raise an error if the directory already exists. Defaults to True.

    Example
    -------
    >>> make_directory("/path/to/folder")
    """
    os.makedirs(folder_path, exist_ok=exist_ok)
    check(dir_exists(folder_path), f"{folder_path} was not created")



def system(
    cmd: str, expected_output: str = "", check_exitcode: bool = True, check_empty: bool = False
) -> dict:
    """
    Run a system command and return its output.

    Parameters
    ----------
    cmd : str
        The system command to run.
    expected_output : str, optional
        Expected output file or directory. If provided, checks for its existence after the command runs. Defaults to "".
    check_exitcode : bool, optional
        If True, checks that the command returns a zero exit code. Defaults to True.
    check_empty : bool, optional
        If True, checks if the expected output is not empty. Defaults to False.

    Returns
    -------
    dict
        A dictionary with the command's output ('out') and error messages ('err').

    Example
    -------
    >>> system("ls -la", expected_output="/path/to/file")
    {'out': '...', 'err': ''}
    """
    info(cmd)
    args = shlex.split(cmd)
    proc = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    out, err = out.decode("utf-8"), err.decode("utf-8")
    check(proc.returncode == 0, f"Command {cmd} failed with exit code {proc.returncode}")
    isfile = not(emptystring(expected_output))
    if isfile and not (file_exists(expected_output, check_empty=check_empty) or dir_exists(expected_output, check_empty=check_empty)):
        error(f"Expected output {expected_output} does not exist")
    if check_exitcode:
        check(proc.returncode == 0, f"Command failed with exit code {proc.returncode}:\n\t{cmd}")
    return {"out": out, "err": err}



def openfile(filename: str) -> None:
    """
    Open a file with the default application based on the operating system.

    This function attempts to open a file using the system's default application 
    for the file type, based on the current operating system (Windows, Linux, or macOS).

    Parameters
    ----------
    filename : str
        The path to the file to open.

    Example
    -------
    >>> openfile("example.txt")
    """
    info(f"Opening file {filename} with default application of your OS {platform}")
    if windows():
        os.startfile(filename)  # Use os.startfile for Windows
    elif linux():
        system(f"xdg-open {filename}")  # Use xdg-open for Linux
    elif macos():
        system(f"open {filename}")  # Use open for macOS
    else:
        error(f"OS not supported: {platform}")

hashlib_code = "ripemd160"

def hash_string(s: str, size: int = -1) -> str:
    """
    Generate a hash of a given string using the specified hashing algorithm.

    This function hashes a string using the RIPMD-160 algorithm and returns the full hash or a truncated version based on the size parameter.

    Parameters
    ----------
    s : str
        The input string to hash.
    size : int, optional
        If positive, truncates the hash to the specified length. Defaults to -1 (no truncation).

    Returns
    -------
    str
        The hashed string, optionally truncated to the specified size.

    Example
    -------
    >>> hash_string("example")
    '9c1185a5c5e9fc54612808977ee8f548b2258d31'
    >>> hash_string("example", size=8)
    '9c1185a5'
    """
    h = hashlib.new("ripemd160")
    h.update(s.encode("utf-8"))  # Encode the string and hash it
    res = h.hexdigest()  # Get the hex digest of the hash
    return "".join(np.random.choice(list(res), size=size)) if size > 0 else res



def hashfile(path: str, hash_content: bool = True, date: bool = False) -> str:
    """
    Generate a hash for a file's content and/or its last modification date.

    Parameters
    ----------
    path : str
        The path to the file to hash.
    hash_content : bool, optional
        If True, includes the file's content in the hash. Defaults to True.
    date : bool, optional
        If True, includes the current date in the hash. Defaults to False.

    Returns
    -------
    str
        The resulting hash of the file.

    Example
    -------
    >>> hashfile("example.txt")
    '9c1185a5c5e9fc54612808977ee8f548b2258d31'
    """
    h = hashlib.new("ripemd160")
    if date:
        h.update(now_string("log").encode("utf-8"))  # Include the current date in the hash if requested
    if hash_content and file_exists(path):
        with open(path, "rb") as fi:
            h.update(fi.read())  # Include file content in the hash
        return h.hexdigest()
    h.update(path.encode("utf-8"))  # Hash the file path if content is not included
    return h.hexdigest()



def hashfolder(path: str, hash_content: bool = True, hash_path: bool = False, date: bool = False) -> str:
    """
    Generate a hash for the contents of a folder and/or its path.

    Parameters
    ----------
    path : str
        The path to the folder to hash.
    hash_content : bool, optional
        If True, includes the folder's contents in the hash. Defaults to True.
    hash_path : bool, optional
        If True, includes the folder's path in the hash. Defaults to False.
    date : bool, optional
        If True, includes the current date in the hash. Defaults to False.

    Returns
    -------
    str
        The resulting hash of the folder and/or its contents.

    Example
    -------
    >>> hashfolder("/path/to/folder")
    '9c1185a5c5e9fc54612808977ee8f548b2258d31'
    """
    h = hashlib.new("ripemd160")
    if date:
        h.update(now_string("log").encode("utf-8"))  # Include the current date in the hash
    if hash_content and dir_exists(path):
        for root, dirs, files in os.walk(path):  # Traverse all files in the directory
            for file in files:
                if not file.startswith("."):  # Skip hidden files
                    full_path = os.path.join(root, file)
                    with open(full_path, "rb") as f:
                        h.update(f.read())  # Include file content in the hash
    if hash_path:
        h.update(path.encode("utf-8"))  # Include the folder path in the hash
    return h.hexdigest()


def format_size(size: int) -> str:
    """
    Helper function to format file size in human-readable form.

    Parameters
    ----------
    size : int
        Size of the file in bytes.

    Returns
    -------
    str
        Human-readable file size.
    """
    if size > 1e9:
        return "%.2f GB" % (size / 1e9)
    elif size > 1e6:
        return "%.2f MB" % (size / 1e6)
    elif size > 1e3:
        return "%.2f KB" % (size / 1e3)
    else:
        return "%d B" % size
    
def folder_description(path: str, recursive: bool = True, index_html: bool = True, with_size:bool = True) -> dict:
    """
    Describe the contents of a folder, optionally recursively, and generate an HTML index.

    Parameters
    ----------
    path : str
        The path to the folder to describe.
    recursive : bool, optional
        If True, includes subdirectories in the description. Defaults to True.
    index_html : bool, optional
        If True, generates an HTML index of the folder contents. Defaults to True.
    with_size : bool, optional
        If True, includes the size of each file in the description. Defaults to True.

    Returns
    -------
    dict
        A dictionary describing the contents of the folder.

    Example
    -------
    >>> folder_description("/path/to/folder")
    {'file1.txt': 1024, 'subfolder': None}
    """
    check(dir_exists(path), f"Folder {path} cannot be described because it does not exist")  # Ensure folder exists

    res = {}
    for root, dirs, files in os.walk(path):
        for file in files:
            if not file.startswith("."):  # Skip hidden files
                res[file] = size_file(os.path.join(root, file))  # Get file size

    # Optionally generate an HTML index of the folder
    if index_html:
        index_html_file = os_path_constructor([path, "index.html"])
        with open(index_html_file, mode="wt") as fout:
            fout.write(f'<html><body><h1>Folder: {path}</h1>\n')
            for k, v in sorted(res.items()):
                s = format_size(v)
                s = f" ({s})" if with_size else ""
                fout.write(f'<a href="{k}">{k}</a>{s}</br>\n')
            fout.write("</body></html>")
        info(f"HTML index generated: {index_html_file}")

    # Save the folder description as a JSON file
    description_file = os_path_constructor([path, "description.json"])
    with open(description_file, "wt") as fout:
        json.dump(res, fout, indent=2)
    info(f"Description generated: {description_file}")

    return res



def folder_name_ext(path: str, checkpath: bool = False) -> tuple:
    """
    Decompose a file or folder path into three components: folder, basename, and extension.

    This function splits a given path into its directory, filename (without extension), and the extension.
    It handles both single and multi-part extensions (e.g., .tar.gz).

    Parameters
    ----------
    path : str
        The file or folder path to decompose.
    checkpath : bool, optional
        If True, checks if the path exists. Defaults to False.

    Returns
    -------
    tuple
        A tuple (folder, basename, extension) where:
        - folder: The absolute path of the directory containing the file or folder.
        - basename: The name of the file or folder without its extension.
        - extension: The extension of the file (empty if it's a folder or no extension).

    Example
    -------
    >>> folder_name_ext("/path/to/file.txt")
    ('/path/to', 'file', 'txt')

    >>> folder_name_ext("/path/to/file.tar.gz")
    ('/path/to', 'file', 'tar.gz')

    >>> folder_name_ext("/path/to/folder")
    ('/path/to', 'folder', '')
    """
    # Normalize the path and get the absolute version
    path = relative2absolute_path(path)

    # Raise an error if the path doesn't exist and checkpath is True
    if checkpath:
        check(file_exists(path) or dir_exists(path), f"Path does not exist: {path}")

    # Extract the base name (last component of the path)
    basename = os.path.basename(path)

    # If it's a directory, return the path with an empty extension
    if os.path.isdir(path):
        return os.path.dirname(path), basename, ""

    # Split into basename and extension
    if "." in basename:
        basename, ext = basename.split('.', 1)  # Handle multi-part extensions (e.g., .tar.gz)
    else:
        ext = ''

    return os.path.dirname(path), basename, ext

def valid_config_file(a_path: str, keys: list, config_type: str) -> dict:
    """
    Check if a configuration file is valid by verifying it contains the required keys.

    This function loads a configuration file (in JSON or YAML format) and checks if it contains 
    all the specified keys.

    Parameters
    ----------
    a_path : str
        The path to the configuration file.
    keys : list
        List of keys that must be present in the configuration file.
    config_type : str
        The type of configuration (for logging purposes).

    Returns
    -------
    dict or None
        The loaded configuration dictionary if valid, otherwise None.

    Example
    -------
    >>> valid_config_file("config.json", keys=["api_key", "url"], config_type="API")
    {'api_key': 'abcdef', 'url': 'https://api.example.com'}
    """
    if not file_exists(a_path):
        return None
    
    _,_,ext = folder_name_ext(a_path)
    ext = ext.lower()

    with open(a_path, "r") as fin:
        if ext in [".json"]:
            j = json.load(fin)  # Load JSON configuration
        elif ext in [".yml", ".yaml"]:
            j = yaml.load(fin, Loader=yaml.FullLoader)  # Load YAML configuration
        else:
            return None  # Unsupported file format

        # Check if all required keys are present
        if all(k in j for k in keys):
            return j

    return None  # Return None if keys are missing


def get_config(path: str, keys: list, config_type: str) -> dict:
    """
    Retrieve a valid configuration file from a path or directory.

    This function searches for a valid configuration file in the provided path or directory.
    If the path is a file, it checks if the file contains the required keys. If the path is a directory, 
    it searches for configuration files and returns the first valid one.

    Parameters
    ----------
    path : str
        The path to the configuration file or directory.
    keys : list
        List of required keys for the configuration.
    config_type : str
        Type of configuration (for logging purposes).

    Returns
    -------
    dict
        The loaded configuration dictionary if valid.

    Raises
    ------
    SystemExit
        If no valid configuration file is found.

    Example
    -------
    >>> get_config("config_folder", keys=["api_key", "url"], config_type="API")
    {'api_key': 'abcdef', 'url': 'https://api.example.com'}
    """
    config = None
    if emptystring(path):

        # pydantic is here

        if not(all([k in config for k in keys])):     
            # Check environment variables
            config = {}
            for k in keys:
                k_capital = k.upper()
                if k_capital in os.environ:
                    config[k] = os.environ[k_capital]

        check(all([k in config for k in keys]), msg = f"All keys are not present in .env nor environment variables" )
        return config
    else:
        # Check file
        if file_exists(path):
            config = valid_config_file(path, keys, config_type=config_type)
            if config:
                return config
        # Check folder
        check(dir_exists(path), f"{config_type} Config folder {path} has no valid file")
        candidates = sorted(glob.glob(os_path_constructor([path, "*"])))  # Find all files in the folder
        for c in candidates:
            config = valid_config_file(c, keys, config_type)
            if config:
                return config
        error(f"No valid {config_type} config file found in {path}")


def is_working_url(url: str) -> bool:
    """
    Check if a URL is valid and reachable.

    This function validates a URL and attempts to send a HEAD request to check if the URL is reachable.

    Parameters
    ----------
    url : str
        The URL to check.

    Returns
    -------
    bool
        True if the URL is valid and reachable, False otherwise.

    Example
    -------
    >>> is_working_url("https://www.google.com")
    True
    """
    if not validators.url(url):
        return False  # Check if the URL format is valid

    try:
        response = requests.head(url, timeout=5)  # Attempt to make a HEAD request
        return response.status_code == 200  # Return True if the status code is 200 (OK)
    except requests.RequestException:
        return False  # Return False if there is an exception (e.g., timeout, network error)

def asciistring(input_string: str, replacement_char: str = "-", lower: bool = True, allow_digits: bool = True) -> str:
    """
    Converts a given string into a "safe" ASCII string, replacing accented and non-ASCII characters with their ASCII equivalents.
    Non-ASCII characters that cannot be converted will be replaced with a specified character.

    Parameters
    ----------
    input_string : str
        The input string to be converted.
    replacement_char : str, optional
        The character to replace non-ASCII or unwanted characters with. Defaults to '-'.
    lower : bool, optional
        Whether to convert the string to lowercase. Defaults to True.
    allow_digits : bool, optional
        Whether to allow digits in the resulting string. Defaults to True.
    
    Returns
    -------
    str
        A "safe" ASCII string with unwanted characters replaced and case adjusted.

    Examples
    --------
    >>> asciistring("MyFile@2024.txt")
    'myfile-2024-txt'

    >>> asciistring("Café-Con-Leche!", replacement_char="_")
    'cafe_con_leche'

    >>> asciistring("Special#File$2024", lower=False)
    'Special-File-2024'
    """
    # Normalize Unicode characters to decompose accents (e.g., é -> e + ´)
    normalized_string = unicodedata.normalize('NFKD', input_string)
    
    # Only keep ASCII characters and replace non-ASCII with the replacement_char
    allowed_chars = string.ascii_letters
    if allow_digits:
        allowed_chars += string.digits

    # Optionally convert to lowercase
    if lower:
        normalized_string = normalized_string.lower()

    # Create the output string
    result = ''.join(c if c in allowed_chars else replacement_char for c in normalized_string if ord(c) < 128)

    # Ensure there are no multiple replacement characters in a row
    change = True
    while change:
        change = False
        old_result = str(result)
        result = result.replace(replacement_char * 2, replacement_char)
        change = old_result != result
    
    # Strip any leading/trailing replacement characters
    return result.strip(replacement_char)


def zip_folder(folder_path: str, zip_file_path: str = ""):
    """
    Zips the contents of a folder (including subdirectories) into a ZIP file.

    Parameters
    ----------
    folder_path : str
        Path to the folder to be zipped.
    zip_file_path : str, optional
        Path to the output ZIP file. If not provided, defaults to folder_path.zip.

    Returns
    -------
    None
    """
    # Ensure the folder exists
    check(dir_exists(folder_path), f"Folder {folder_path} does not exist")

    # If no zip file path is provided, default to the folder name with .zip extension
    if emptystring(zip_file_path):
        zip_file_path = folder_path + ".zip"

    # Create the zip file
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through all files and subdirectories inside the folder
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if not file.startswith("."):  # Skip hidden files
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arcname)

    info(f"Folder {folder_path} successfully zipped into {zip_file_path}")

def time2str(time: float, no_space: bool = False) -> str:
    """
    Convert time in seconds to a human-readable string format (hours, minutes, seconds).

    Parameters
    ----------
    time : float
        Time in seconds.
    no_space : bool, optional
        If True, removes spaces between numbers and units (default is False).

    Returns
    -------
    str
        A formatted string representing the time in hours, minutes, and seconds.

    Examples
    --------
    >>> time2str(3661)
    '1 hr 1 min 1 sec'
    >>> time2str(61)
    '1 min 1 sec'
    >>> time2str(61, no_space=True)
    '1min1sec'
    """

    # Calculate hours, minutes, and seconds
    hours = int(time // 3600)
    minutes = int((time % 3600) // 60)
    seconds = int(time % 60)

    # Build the time string based on non-zero values
    res = []
    if hours > 0:
        res.append(f"{hours} hr")
    if minutes > 0:
        res.append(f"{minutes} min")
    if seconds > 0 or (hours == 0 and minutes == 0):  # Always show seconds if no hours or minutes
        res.append(f"{seconds} sec")

    # Join the result with spaces or no spaces based on the no_space flag
    if no_space:
        res = [r.replace(" ", "") for r in res]       

    time_str = " ".join(res)

    return time_str
