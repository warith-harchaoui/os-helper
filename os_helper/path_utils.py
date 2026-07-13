"""
Path Utilities

This module provides helper functions for handling and manipulating file and directory paths.
Functions include checking existence, converting between absolute and relative paths, formatting paths,
and performing file operations like copying and removing files/directories.

Author:
 - Warith HARCHAOUI, https://linkedin.com/in/warith-harchaoui
"""

import glob
import os
import pathlib
import shutil

from .logging_utils import error, info


def folder_name_ext(path: str, checkpath: bool = False) -> tuple[str, str, str]:
    """
    Decompose a file or folder path into (folder, basename, extension).

    The split happens at the **last** dot in the basename, so multi-part
    suffixes like ``.tar.gz`` are not collapsed into one extension. Use
    ``"basename.extension"`` to recover the original file name.

    Returns an empty extension for:
    - directories,
    - files whose basename contains no dot.

    Parameters
    ----------
    path : str
        The path to decompose. Resolved to an absolute path internally.
    checkpath : bool, optional
        If True, asserts that the path exists on disk.

    Returns
    -------
    tuple of (str, str, str)
        ``(folder, basename, extension)`` where ``extension`` excludes the
        leading dot.

    Examples
    --------
    >>> folder_name_ext("/path/to/file.txt")
    ('/path/to', 'file', 'txt')
    >>> folder_name_ext("/path/to/archive.tar.gz")
    ('/path/to', 'archive.tar', 'gz')
    >>> folder_name_ext("/path/to/folder")          # existing directory
    ('/path/to', 'folder', '')
    """

    path = relative2absolute_path(path)
    if checkpath:
        assert file_exists(path) or dir_exists(path), f"Path does not exist: {path}"

    base_folder = os.path.dirname(path)
    basename = os.path.basename(path)

    if os.path.isdir(path):
        return base_folder, basename, ""

    if "." not in basename:
        return base_folder, basename, ""

    name_part, _, ext_part = basename.rpartition(".")
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
    Convert a path to a relative path expressed from ``base_path``.

    Parameters
    ----------
    path : str
        The path to convert (absolute or relative).
    base_path : str, optional
        Reference path. Defaults to the current working directory.

    Returns
    -------
    str
        The relative path from ``base_path`` to ``path``.

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
    FileNotFoundError
        If `checkpath` is True and the path does not exist.

    Example
    -------
    >>> relative2absolute_path("docs/readme.md")
    '/home/user/project/docs/readme.md'
    """
    abs_path = os.path.abspath(path)
    if checkpath and not (file_exists(abs_path) or dir_exists(abs_path)):
        msg = f"File or directory does not exist: {abs_path}"
        error(msg)
        raise FileNotFoundError(msg)
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

def recursive_glob(root_dir: str, pattern: str) -> list[str]:
    """
    Recursively search for files matching a glob pattern under ``root_dir``.

    Each subdirectory is walked and the pattern applied in turn, so patterns
    like ``"*.txt"`` match in nested folders as well as at the top level.

    Parameters
    ----------
    root_dir : str
        The root directory to start searching from.
    pattern : str
        The glob pattern to match against file names (e.g., ``"*.txt"``).

    Returns
    -------
    List[str]
        File paths matching the pattern, in walk order.

    Example
    -------
    >>> recursive_glob("/home/user", "*.txt")
    ['/home/user/file1.txt', '/home/user/docs/file2.txt']
    """
    matches: list[str] = []
    for root, _dirs, _files in os.walk(root_dir):
        matches.extend(glob.glob(os.path.join(root, pattern)))
    return matches

def join(*args: str) -> str:
    """
    Join multiple path components into a single absolute, normalized path.

    This is the canonical path-construction helper exposed by ``os_helper``
    and replaces the older ``os_path_constructor`` function (removed in
    v1.1.0). It accepts either positional components or a single iterable.

    Parameters
    ----------
    *args : str
        The path components to join, or a single iterable of path components.

    Returns
    -------
    str
        The absolute, normalized path.

    Example
    -------
    >>> join("folder1", "subfolder2", "file.txt")
    '/home/user/project/folder1/subfolder2/file.txt'
    >>> join(["folder1", "subfolder2", "file.txt"])
    '/home/user/project/folder1/subfolder2/file.txt'
    """
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        # If a single iterable is passed, unpack it
        args = args[0]
    normalized_path = os.path.normpath(os.path.join(*args))
    return relative2absolute_path(normalized_path, checkpath=False)


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
    Assert that a file exists and, optionally, that it is non-empty.

    Parameters
    ----------
    filepath : str
        The path to the file.
    msg : str, optional
        Prefix added to the assertion message on failure.
    check_empty : bool, optional
        If True, also asserts that the file size is greater than zero.

    Raises
    ------
    AssertionError
        If the file does not exist (or is empty when ``check_empty`` is True).

    Example
    -------
    >>> checkfile("data.csv", msg="Data file missing", check_empty=True)
    """
    assert file_exists(filepath), f"{msg} File '{filepath}' does not exist."
    if check_empty:
        size = size_file(filepath)
        assert size > 0, f"{msg} File '{filepath}' exists but is empty."

def copyfile(source: str, destination: str) -> None:
    """
    Copy a file from ``source`` to ``destination``, preserving metadata.

    If ``destination`` is an existing directory, the source file name is
    appended to it (mirroring ``cp`` semantics).

    Parameters
    ----------
    source : str
        The path to the source file (must exist and be non-empty).
    destination : str
        The path to the destination file or existing directory.

    Raises
    ------
    AssertionError
        If the source file does not exist or is empty, or if source and
        destination resolve to the same path.
    OSError
        If the underlying ``shutil.copy2`` call fails (propagated as-is).

    Example
    -------
    >>> copyfile("source.txt", "backup/source_backup.txt")
    """
    checkfile(source, msg=f"Copying from '{source}' to '{destination}' failed.", check_empty=True)
    source_abs = relative2absolute_path(source)
    destination_abs = relative2absolute_path(destination)

    if dir_exists(destination_abs):
        _, basename, ext = folder_name_ext(source_abs)
        filename = f"{basename}.{ext}" if ext else basename
        destination_abs = join(destination_abs, filename)

    assert source_abs != destination_abs, f"Source and destination paths are the same: '{source_abs}'"
    try:
        shutil.copy2(source_abs, destination_abs)
    except Exception as e:
        error(f"Error copying file '{source}' to '{destination}': {e}")
        raise
    checkfile(destination_abs, msg=f"Failed to copy '{source}' to '{destination}'", check_empty=True)
    info(f"Copied '{source}' to '{destination_abs}' successfully.")

def remove_directory(folder_path: str) -> None:
    """
    Remove a directory and all its contents.

    A missing directory is treated as a no-op (logged at INFO); any other
    failure from ``shutil.rmtree`` is propagated to the caller.

    Parameters
    ----------
    folder_path : str
        The path to the directory to remove.

    Raises
    ------
    OSError
        If the directory exists but cannot be removed (propagated from
        ``shutil.rmtree``).

    Example
    -------
    >>> remove_directory("/path/to/temp_folder")
    """
    if not dir_exists(folder_path):
        info(f"Directory '{folder_path}' does not exist, nothing to remove.")
        return
    try:
        shutil.rmtree(folder_path)
    except Exception as e:
        error(f"Failed to remove directory '{folder_path}': {e}")
        raise
    info(f"Removed directory: '{folder_path}'")

def remove_files(files_list: list[str]) -> None:
    """
    Remove a list of files on a best-effort basis.

    Missing entries are skipped and individual removal failures are logged
    at ERROR level without aborting the rest of the batch. This function
    does **not** raise — if you need hard-fail-on-first semantics, call
    ``pathlib.Path(p).unlink()`` yourself.

    Parameters
    ----------
    files_list : List[str]
        A list of file paths to remove.

    Example
    -------
    >>> remove_files(["temp1.txt", "temp2.log"])
    """
    for file_path in files_list:
        if file_exists(file_path):
            try:
                pathlib.Path(file_path).unlink()
                info(f"Removed file: '{file_path}'")
            except Exception as e:
                error(f"Failed to remove file '{file_path}': {e}")
        else:
            info(f"File '{file_path}' does not exist, skipping.")

def make_directory(folder_path: str, exist_ok: bool = True) -> None:
    """
    Create a directory (and missing parents), optionally tolerating prior existence.

    Parameters
    ----------
    folder_path : str
        The path to the directory to create.
    exist_ok : bool, optional
        If True (the default), succeed silently when the directory already
        exists. If False, ``FileExistsError`` is raised in that case.

    Raises
    ------
    OSError
        If the directory cannot be created (propagated from ``os.makedirs``).
    AssertionError
        If ``os.makedirs`` returned without error but the directory is still
        not visible on disk afterwards.

    Example
    -------
    >>> make_directory("/path/to/new_folder")
    """
    try:
        os.makedirs(folder_path, exist_ok=exist_ok)
    except Exception as e:
        error(f"Error creating directory '{folder_path}': {e}")
        raise
    assert dir_exists(folder_path), f"Failed to create directory: '{folder_path}'"
    info(f"Directory created: '{folder_path}'")
