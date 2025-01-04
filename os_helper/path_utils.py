"""
Path Utilities

This module provides helper functions for handling and manipulating file and directory paths.
Functions include checking existence, converting between absolute and relative paths, formatting paths,
and performing file operations like copying and removing files/directories.

Authors:
 - Warith Harchaoui, https://harchaoui.org/warith
 - Mohamed Chelali, https://mchelali.github.io
 - Bachir Zerroug, https://www.linkedin.com/in/bachirzerroug
"""

import os
import glob
import shutil
import pathlib
from typing import List

# Importing necessary functions from other utility modules
from .logging_utils import check, info, error



def folder_name_ext(path: str, checkpath: bool = False) -> tuple:
    """
    Decompose a file or folder path into three components: folder, basename, and extension.

    If it's a directory, the extension is empty.

    Parameters
    ----------
    path : str
        The path to decompose.
    checkpath : bool, optional
        If True, checks if the path actually exists.

    Returns
    -------
    tuple
        A tuple (folder, basename, extension).

    Example
    -------
    >>> folder_name_ext("/path/to/file.txt")
    ("/path/to", "file", "txt")
    """

    path = relative2absolute_path(path)
    if checkpath:
        check(file_exists(path) or dir_exists(path), f"Path does not exist: {path}")

    base_folder = os.path.dirname(path)
    basename = os.path.basename(path)

    # If it's a directory, return empty extension
    if os.path.isdir(path):
        return base_folder, basename, ""

    # Split at the first dot (if any) for multi-part extensions
    if "." in basename:
        name_part, ext_part = basename.split(".", 1)
    else:
        name_part, ext_part = basename, ""

    return base_folder, name_part, ext_part

def file_exists(file_path: str, check_empty: bool = False) -> bool:
    """
    Check if a file exists, with an option to verify it's not empty.

    Parameters
    ----------
    file_path : str
        The path to the file.
    check_empty : bool, optional
        If True, also checks that the file is not empty. Defaults to False.

    Returns
    -------
    bool
        True if the file exists (and is not empty if `check_empty` is True), False otherwise.

    Example
    -------
    >>> file_exists("example.txt")
    True
    >>> file_exists("empty.txt", check_empty=True)
    False
    """
    exists = os.path.isfile(file_path)
    if check_empty and exists:
        size = os.path.getsize(file_path)
        exists = size > 0
    return exists

def dir_exists(path: str, check_empty: bool = False) -> bool:
    """
    Check if a directory exists, with an option to verify it's not empty.

    Parameters
    ----------
    path : str
        The path to the directory.
    check_empty : bool, optional
        If True, also checks that the directory is not empty (excluding hidden files). Defaults to False.

    Returns
    -------
    bool
        True if the directory exists (and is not empty if `check_empty` is True), False otherwise.

    Example
    -------
    >>> dir_exists("/path/to/folder")
    True
    >>> dir_exists("/path/to/empty_folder", check_empty=True)
    False
    """
    if not os.path.isdir(path):
        return False
    if check_empty:
        # Exclude hidden files/directories
        files = [f for f in glob.glob(os.path.join(path, "*")) if not os.path.basename(f).startswith(".")]
        return len(files) > 0
    return True

def absolute2relative_path(path: str, base_path: str = None) -> str:
    """
    Convert an absolute path to a relative path based on a base path.

    Parameters
    ----------
    path : str
        The absolute path to convert.
    base_path : str, optional
        The base path to use for conversion. If None, uses the current working directory. Defaults to None.

    Returns
    -------
    str
        The relative path from `base_path` to `path`.

    Example
    -------
    >>> absolute2relative_path("/home/user/project/file.txt", "/home/user")
    'project/file.txt'
    """
    if base_path is None:
        base_path = os.getcwd()
    abs_path = os.path.abspath(path)
    abs_base = os.path.abspath(base_path)
    return os.path.relpath(abs_path, abs_base)

def relative2absolute_path(path: str, checkpath: bool = False) -> str:
    """
    Convert a relative path to an absolute path.

    Parameters
    ----------
    path : str
        The relative or absolute path to convert.
    checkpath : bool, optional
        If True, verifies that the resulting absolute path exists (as a file or directory). Defaults to False.

    Returns
    -------
    str
        The absolute path.

    Raises
    ------
    SystemExit
        If `checkpath` is True and the path does not exist.

    Example
    -------
    >>> relative2absolute_path("docs/readme.md")
    '/home/user/project/docs/readme.md'
    """
    abs_path = os.path.abspath(path)
    if checkpath:
        if not (file_exists(abs_path) or dir_exists(abs_path)):
            error(f"File or directory does not exist: {abs_path}")
    return abs_path

def path_without_home(path: str) -> str:
    """
    Convert an absolute path to be relative to the user's home directory by replacing the home path with '~'.

    Parameters
    ----------
    path : str
        The absolute path to convert.

    Returns
    -------
    str
        The path with the home directory replaced by '~', if applicable.

    Example
    -------
    >>> path_without_home("/home/user/project/file.txt")
    '~/project/file.txt'
    """
    home_dir = os.path.expanduser("~")
    norm_path = os.path.normpath(path)
    if norm_path.startswith(home_dir):
        return norm_path.replace(home_dir, "~", 1)
    return norm_path

def recursive_glob(root_dir: str, pattern: str) -> List[str]:
    """
    Recursively search for files matching a specified pattern within a directory.

    Parameters
    ----------
    root_dir : str
        The root directory to start searching from.
    pattern : str
        The glob pattern to match files (e.g., "*.txt").

    Returns
    -------
    List[str]
        A list of file paths that match the pattern.

    Example
    -------
    >>> recursive_glob("/home/user", "*.txt")
    ['/home/user/file1.txt', '/home/user/docs/file2.txt']
    """
    matches = []
    for root, dirs, files in os.walk(root_dir):
        # Use glob.glob to match the pattern within the current directory
        for file in glob.glob(os.path.join(root, pattern)):
            matches.append(file)
    return matches

def join(*args: str) -> str:
    """
    Join multiple path components into a single absolute path.

    Parameters
    ----------
    *args : str
        The path components to join.

    Returns
    -------
    str
        The absolute, normalized path.

    Example
    -------
    >>> join("folder1", "subfolder2", "file.txt")
    '/home/user/project/folder1/subfolder2/file.txt'
    """
    normalized_path = os.path.normpath(os.path.join(*args))
    return relative2absolute_path(normalized_path, checkpath=False)

def os_path_constructor(ell: List[str]) -> str:
    """
    Construct a path from a list of path components.

    Note:
        This function is retained for legacy support.
        It is recommended to use `join` instead by passing individual arguments.

    Parameters
    ----------
    ell : List[str]
        A list of path components.

    Returns
    -------
    str
        The constructed absolute path.

    Example
    -------
    >>> os_path_constructor(["/home/user", "folder", "file.txt"])
    '/home/user/folder/file.txt'
    """
    return join(*ell)

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
    Check if a file exists and optionally verify it's not empty.

    Parameters
    ----------
    filepath : str
        The path to the file.
    msg : str, optional
        Custom message to include in the error if the check fails. Defaults to "".
    check_empty : bool, optional
        If True, also checks that the file is not empty. Defaults to False.

    Raises
    ------
    SystemExit
        If the file does not exist (or is empty if `check_empty` is True).

    Example
    -------
    >>> checkfile("data.csv", msg="Data file missing", check_empty=True)
    """
    check(file_exists(filepath), msg=f"{msg} File '{filepath}' does not exist.")
    if check_empty:
        size = size_file(filepath)
        check(size > 0, msg=f"{msg} File '{filepath}' is empty.")

def copyfile(source: str, destination: str) -> None:
    """
    Copy a file from source to destination.

    Parameters
    ----------
    source : str
        The path to the source file.
    destination : str
        The path to the destination file or directory.

    Raises
    ------
    SystemExit
        If the source file does not exist or if copying fails.

    Example
    -------
    >>> copyfile("source.txt", "backup/source_backup.txt")
    """
    checkfile(source, msg=f"Copying from '{source}' to '{destination}' failed.", check_empty=True)
    source_abs = relative2absolute_path(source)
    destination_abs = relative2absolute_path(destination)

    if dir_exists(destination_abs):
        _, basename, ext = folder_name_ext(source_abs)
        destination_abs = join(destination_abs, f"{basename}.{ext}")

    check(source_abs != destination_abs, msg=f"Source and destination paths are the same: '{source_abs}'")
    try:
        shutil.copy2(source_abs, destination_abs)
        checkfile(destination_abs, msg=f"Failed to copy '{source}' to '{destination}'", check_empty=True)
        info(f"Copied '{source}' to '{destination_abs}' successfully.")
    except Exception as e:
        error(f"Error copying file: {e}")

def remove_directory(folder_path: str) -> None:
    """
    Remove a directory and all its contents.

    Parameters
    ----------
    folder_path : str
        The path to the directory to remove.

    Raises
    ------
    SystemExit
        If the directory removal fails.

    Example
    -------
    >>> remove_directory("/path/to/temp_folder")
    """
    if dir_exists(folder_path):
        try:
            shutil.rmtree(folder_path)
            info(f"Removed directory: '{folder_path}'")
        except Exception as e:
            error(f"Failed to remove directory '{folder_path}': {e}")
    else:
        info(f"Directory '{folder_path}' does not exist, nothing to remove.")

def remove_files(files_list: List[str], verbose: bool = False) -> None:
    """
    Remove a list of files.

    Parameters
    ----------
    files_list : List[str]
        A list of file paths to remove.
    verbose : bool, optional
        If True, logs the removal of each file. Defaults to False.

    Raises
    ------
    SystemExit
        If any file removal fails.

    Example
    -------
    >>> remove_files(["temp1.txt", "temp2.log"], verbose=True)
    """
    for file_path in files_list:
        if file_exists(file_path):
            try:
                pathlib.Path(file_path).unlink()
                if verbose:
                    info(f"Removed file: '{file_path}'")
            except Exception as e:
                error(f"Failed to remove file '{file_path}': {e}")
        else:
            if verbose:
                info(f"File '{file_path}' does not exist, skipping.")

def make_directory(folder_path: str, exist_ok: bool = True) -> None:
    """
    Create a directory, optionally ignoring if it already exists.

    Parameters
    ----------
    folder_path : str
        The path to the directory to create.
    exist_ok : bool, optional
        If True, does not raise an error if the directory already exists. Defaults to True.

    Raises
    ------
    SystemExit
        If the directory creation fails.

    Example
    -------
    >>> make_directory("/path/to/new_folder")
    """
    try:
        os.makedirs(folder_path, exist_ok=exist_ok)
        check(dir_exists(folder_path), msg=f"Failed to create directory: '{folder_path}'")
        info(f"Directory created: '{folder_path}'")
    except Exception as e:
        error(f"Error creating directory '{folder_path}': {e}")

def checkfile(filepath: str, msg: str = "", check_empty: bool = False) -> None:
    """
    Check if a file exists and optionally verify it's not empty.

    Parameters
    ----------
    filepath : str
        The path to the file.
    msg : str, optional
        Custom message to include in the error if the check fails. Defaults to "".
    check_empty : bool, optional
        If True, also checks that the file is not empty. Defaults to False.

    Raises
    ------
    SystemExit
        If the file does not exist (or is empty if `check_empty` is True).

    Example
    -------
    >>> checkfile("data.csv", msg="Data file missing", check_empty=True)
    """
    check(file_exists(filepath), msg=f"{msg} File '{filepath}' does not exist.")
    if check_empty:
        size = size_file(filepath)
        check(size > 0, msg=f"{msg} File '{filepath}' is empty.")

