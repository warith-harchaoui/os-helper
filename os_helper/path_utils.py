"""
Path Utilities

This module provides helper functions for handling and manipulating file and directory paths.
Functions include checking existence, converting between absolute and relative paths, formatting paths,
and performing file operations like copying and removing files/directories.

Author:
 - Warith HARCHAOUI, https://linkedin.com/in/warith-harchaoui
"""

# ``from __future__ import annotations`` keeps every annotation below as a
# string at runtime. That lets us write modern syntax such as ``str | None``
# uniformly even on the oldest supported interpreter (Python 3.10).
from __future__ import annotations

import glob
import os
import pathlib
import shutil

# We route all human-facing messages through the package logging surface
# (rule 6: no bare ``print`` in library code) rather than writing to stdout.
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

    # Normalize to an absolute path first so the split is independent of the
    # caller's current working directory.
    path = relative2absolute_path(path)
    # Optional guard: fail loudly when the caller expects the path to exist.
    if checkpath:
        assert file_exists(path) or dir_exists(path), f"Path does not exist: {path}"

    base_folder = os.path.dirname(path)
    basename = os.path.basename(path)

    # Directories have no meaningful extension — return an empty one.
    if os.path.isdir(path):
        return base_folder, basename, ""

    # A basename with no dot (e.g. ``README``) also has no extension.
    if "." not in basename:
        return base_folder, basename, ""

    # Split on the LAST dot only: this preserves multi-part names such as
    # ``archive.tar`` while still peeling off the final ``gz`` suffix.
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
    # Only stat the file for its size when it exists AND the caller asked for
    # the emptiness check — avoids a needless syscall in the common case.
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
        # ``glob("*")`` deliberately skips dotfiles, so a folder that only
        # holds hidden housekeeping files (e.g. ``.DS_Store``) still counts as
        # "empty" for the caller's intent.
        files = [
            f for f in glob.glob(os.path.join(path, "*")) if not os.path.basename(f).startswith(".")
        ]
        return len(files) > 0
    return True


def absolute2relative_path(path: str, base_path: str | None = None) -> str:
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
    # Default the reference point to the current working directory so callers
    # can ask "where is this relative to where I am right now?".
    if base_path is None:
        base_path = os.getcwd()
    # Absolutize both ends before diffing them; ``os.path.relpath`` needs a
    # common, unambiguous frame of reference to compute the ``..`` hops.
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
    # When asked, verify the target exists as either a file or a directory;
    # we log before raising so the failure is traceable even if the caller
    # swallows the exception.
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
    # Normalize first so ``/home/user/../user/x`` still matches the home prefix.
    norm_path = os.path.normpath(path)
    # Only collapse the leading home segment (``count=1``) — a literal home
    # path appearing deeper in the string must stay untouched.
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
    # Walk every directory under the root and re-apply the glob at each level;
    # this makes a flat pattern like ``*.txt`` behave recursively without the
    # caller having to spell out ``**`` and enable ``recursive=True``.
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
    # Ergonomic overload: accept either ``join("a", "b")`` or
    # ``join(["a", "b"])`` so callers holding a list need not splat it.
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        args = args[0]
    # ``normpath`` collapses redundant separators and ``..`` segments; we then
    # absolutize so the returned path is always fully qualified.
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
    # Return the sentinel ``-1`` instead of raising for a missing file, so
    # callers can branch on the value rather than wrap this in try/except.
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
    # Existence is the primary contract; the caller-supplied ``msg`` is
    # prefixed so the assertion text stays actionable in a stack trace.
    assert file_exists(filepath), f"{msg} File '{filepath}' does not exist."
    # A zero-byte file often signals a truncated download or a half-written
    # output — treat it as a failure when the caller opts in.
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
    # Fail fast if the source is missing or empty — copying nothing is almost
    # always a bug in the caller, not something to silently tolerate.
    checkfile(source, msg=f"Copying from '{source}' to '{destination}' failed.", check_empty=True)
    source_abs = relative2absolute_path(source)
    destination_abs = relative2absolute_path(destination)

    # Mirror shell ``cp`` semantics: copying into a directory keeps the source
    # file name rather than overwriting the directory itself.
    if dir_exists(destination_abs):
        _, basename, ext = folder_name_ext(source_abs)
        filename = f"{basename}.{ext}" if ext else basename
        destination_abs = join(destination_abs, filename)

    # Guard against a self-copy, which ``shutil`` would happily truncate.
    assert source_abs != destination_abs, (
        f"Source and destination paths are the same: '{source_abs}'"
    )
    try:
        # ``copy2`` preserves metadata (mtime, permissions), unlike ``copy``.
        shutil.copy2(source_abs, destination_abs)
    except Exception as e:
        # Log with both original paths for context, then re-raise unchanged so
        # the caller still sees the real ``OSError``.
        error(f"Error copying file '{source}' to '{destination}': {e}")
        raise
    # Post-condition: confirm the destination now exists and is non-empty.
    checkfile(
        destination_abs, msg=f"Failed to copy '{source}' to '{destination}'", check_empty=True
    )
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
    # Idempotent by design: removing an already-absent directory is a no-op,
    # which keeps cleanup code free of existence checks at every call site.
    if not dir_exists(folder_path):
        info(f"Directory '{folder_path}' does not exist, nothing to remove.")
        return
    try:
        # ``rmtree`` recursively deletes the tree; any failure (permissions,
        # busy file) is logged and re-raised for the caller to handle.
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
    # Best-effort batch delete: we intentionally keep going after a failure so
    # one locked file cannot block cleanup of the rest of the list.
    for file_path in files_list:
        if file_exists(file_path):
            try:
                pathlib.Path(file_path).unlink()
                info(f"Removed file: '{file_path}'")
            except Exception as e:
                # Log and swallow: this helper's contract is not to raise.
                error(f"Failed to remove file '{file_path}': {e}")
        else:
            # Missing files are simply skipped — nothing to remove.
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
        # ``makedirs`` creates intermediate parents too; ``exist_ok`` decides
        # whether a pre-existing leaf is tolerated or is an error.
        os.makedirs(folder_path, exist_ok=exist_ok)
    except Exception as e:
        error(f"Error creating directory '{folder_path}': {e}")
        raise
    # Defensive post-condition: guard against exotic filesystems where the
    # call returns cleanly but the directory is not actually visible.
    assert dir_exists(folder_path), f"Failed to create directory: '{folder_path}'"
    info(f"Directory created: '{folder_path}'")
