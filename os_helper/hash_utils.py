"""
Hashing Utilities

This module provides functions to perform hashing of strings, files,
and entire folders. It supports optional date stamping, partial content
hashing, and path-based hashing.

Author:
 - Warith HARCHAOUI, https://linkedin.com/in/warith-harchaoui
"""

import hashlib
import os

from .misc_utils import now_string  # or from .main import now_string

# If you keep 'file_exists' and 'dir_exists' in path_utils:
from .path_utils import dir_exists, file_exists


def _hash_engine():
    """
    Create a new 160-bit hash engine.

    Prefers RIPEMD-160 when the local OpenSSL build exposes it (legacy
    provider on OpenSSL 3 is often disabled by default on Linux), and falls
    back to BLAKE2b truncated to 20 bytes so the digest length stays 40 hex
    characters across platforms.

    You should not need to use this function directly.

    Returns
    -------
    hashlib hash object
        A fresh hash object producing 40-char hex digests.
    """
    try:
        return hashlib.new("ripemd160")
    except (ValueError, AttributeError):
        return hashlib.blake2b(digest_size=20)


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
    >>> isinstance(hash_string("example"), str)
    True
    >>> len(hash_string("example"))
    40
    >>> len(hash_string("example", size=8))
    8

    Note
    ----
    The exact digest depends on the underlying hash engine (RIPEMD-160 when
    available, BLAKE2b truncated to 20 bytes otherwise). The output length
    stays 40 hex characters either way.
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
        The resulting hash of the file as a 40-character hex string.
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
        The resulting hash of the folder and/or its contents as a
        40-character hex string.
    """
    h = _hash_engine()

    # Optionally incorporate current date into the hash
    if date:
        h.update(now_string("log").encode("utf-8"))

    if hash_content and dir_exists(path):
        for root, _dirs, files in os.walk(path):
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
