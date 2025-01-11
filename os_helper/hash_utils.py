"""
Hashing Utilities

This module provides functions to perform hashing of strings, files,
and entire folders. It supports optional date stamping, partial content
hashing, and path-based hashing.

Authors:
 - Warith Harchaoui, https://harchaoui.org/warith
 - Mohamed Chelali, https://mchelali.github.io
 - Bachir Zerroug, https://www.linkedin.com/in/bachirzerroug
"""

import hashlib
import os

# If you keep 'file_exists' and 'dir_exists' in path_utils:
from .path_utils import file_exists, dir_exists

from .misc_utils import now_string  # or from .main import now_string

# If you need logging or error-checking:
# from .logging_utils import check, info, error
import logging

def _hash_engine() -> hashlib:
    """
    Create a new hash engine using the RIPEMD-160 algorithm.

    Your are not supposed to use this function directly.

    Returns
    -------
    hashlib
        A new hash engine instance using the RIPEMD-160 algorithm.
    """
    return hashlib.new("ripemd160")


def hash_string(s: str, size: int = -1) -> str:
    """
    Generate a hash of a given string and optionally returns a truncated version.

    Parameters
    ----------
    s : str
        The input string to hash.
    size : int, optional
        If positive, truncates the hash to the specified length. Defaults to -1 (no truncation).

    Returns
    -------
    str
        The hashed string, optionally truncated.

    Example
    -------
    >>> hash_string("example")
    '9c1185a5c5e9fc54612808977ee8f548b2258d31'
    >>> hash_string("example", size=8)
    '9c1185a5'
    """
    h = _hash_engine()
    h.update(s.encode("utf-8"))
    full_hash = h.hexdigest()
    if size > 0:
        while size > len(full_hash):
            full_hash += full_hash
        full_hash = full_hash[:size]
    return full_hash


def hashfile(path: str, hash_content: bool = True, date: bool = False) -> str:
    """
    Generate a hash for a file's content and/or its last modification date.

    Parameters
    ----------
    path : str
        The path to the file to hash.
    hash_content : bool, optional
        If True, includes the file's content in the hash (default: True).
    date : bool, optional
        If True, includes the current date in the hash (default: False).

    Returns
    -------
    str
        The resulting hash of the file.

    Example
    -------
    >>> hashfile("example.txt")
    '9c1185a5c5e9fc54612808977ee8f548b2258d31'
    """
    h = _hash_engine()

    # Optionally incorporate current date into the hash
    if date:
        h.update(now_string("log").encode("utf-8"))

    # If the file exists and we want to hash its content
    if hash_content and file_exists(path):
        with open(path, "rb") as fi:
            h.update(fi.read())
    else:
        # Otherwise, just hash the path
        h.update(path.encode("utf-8"))

    return h.hexdigest()


def hashfolder(path: str, hash_content: bool = True, hash_path: bool = False, date: bool = False) -> str:
    """
    Generate a hash for the contents of a folder and/or its path.

    Parameters
    ----------
    path : str
        The path to the folder to hash.
    hash_content : bool, optional
        If True, includes the folder's contents in the hash (default: True).
    hash_path : bool, optional
        If True, includes the folder's path in the hash (default: False).
    date : bool, optional
        If True, includes the current date in the hash (default: False).

    Returns
    -------
    str
        The resulting hash of the folder and/or its contents.

    Example
    -------
    >>> hashfolder("/path/to/folder")
    '9c1185a5c5e9fc54612808977ee8f548b2258d31'
    """
    h = _hash_engine()
    
    # Optionally incorporate current date into the hash
    if date:
        h.update(now_string("log").encode("utf-8"))

    if hash_content and dir_exists(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                # Optionally skip hidden files
                if not file.startswith("."):
                    full_path = os.path.join(root, file)
                    # Hash the contents of each file
                    with open(full_path, "rb") as fi:
                        h.update(fi.read())

    if hash_path:
        # Include the folder path in the hash
        h.update(path.encode("utf-8"))

    return h.hexdigest()
