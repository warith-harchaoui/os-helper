"""
Hashing Utilities

A content hash turns any string, file, or folder into a short, fixed-length
fingerprint: the same input always produces the same fingerprint, and two
different inputs almost never collide. That single property answers three
everyday questions: is this file the one I already downloaded (compare
fingerprints instead of full bytes), have these two folders diverged
(compare their folder hash), and can I use a file's own content as its cache
key (a name that never needs inventing and never goes stale).

:func:`hash_string`, :func:`hashfile`, and :func:`hashfolder` compute that
fingerprint with RIPEMD-160 (BLAKE2b as a fallback where RIPEMD-160 is
unavailable), always as a 40-character hex string regardless of which engine
ran. This is content hashing, not password hashing: there is no salting and
no key-stretching, so never use these for storing or checking passwords (see
``CREDENTIALS_MANAGEMENT.md``).

Usage example
-------------
>>> import os_helper as osh
>>> osh.hash_string("hello")[:8]
'108f07b8'
>>> len(osh.hash_string("hello"))
40

Author
------
Warith HARCHAOUI, https://linkedin.com/in/warith-harchaoui
"""

# Postpone annotation evaluation for consistent modern typing on Python 3.10.
from __future__ import annotations

import hashlib
import os
from typing import TYPE_CHECKING

from .path_utils import dir_exists, file_exists

# ``hashlib._Hash`` is a private runtime type; guard the import behind
# TYPE_CHECKING so the annotation never triggers an import at runtime.
if TYPE_CHECKING:
    from hashlib import _Hash


def _hash_engine() -> _Hash:
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
        # RIPEMD-160 gives a compact 40-hex-char digest, but OpenSSL 3 often
        # ships it disabled in its legacy provider.
        return hashlib.new("ripemd160")
    except (ValueError, AttributeError):
        # Fall back to BLAKE2b truncated to 20 bytes so the digest is still
        # exactly 40 hex characters regardless of the OpenSSL build.
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
    # Encode explicitly to UTF-8 so the digest is stable across platforms
    # regardless of the default filesystem/locale encoding.
    h.update(s.encode("utf-8"))
    full_hash = h.hexdigest()
    if size > 0:
        # Callers may request a digest LONGER than the native 40 chars; repeat
        # the hex string until it is long enough, then slice to the exact size.
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
        If False, the digest is computed from the path *string* instead — the
        way to fingerprint a name rather than bytes, for a file that need not
        exist.
    date : bool, optional
        If True, includes the file's own last modification time
        (``os.stat().st_mtime_ns``) in the hash (default: False). It is the
        file's mtime, never the current clock: a digest that moved on every
        call could not be a cache key.

    Returns
    -------
    str
        The resulting hash of the file as a 40-character hex string.

    Raises
    ------
    FileNotFoundError
        If ``hash_content`` or ``date`` is True and ``path`` names nothing.
    IsADirectoryError
        If ``hash_content`` or ``date`` is True and ``path`` names a directory.

    Notes
    -----
    Asking for content (or an mtime) that cannot be read is an error, not a
    fallback. This function used to answer a *path* digest in that case, so
    ``hashfile("/gone")`` returned a plausible 40-hex-char value for a file
    nobody had read — which made ``hashfile`` useless for noticing that a file
    is missing, the very reason one fingerprints a file. Callers who want a
    path digest ask for it with ``hash_content=False``.
    """
    h = _hash_engine()

    # Reading the bytes and reading the mtime both need the file to be there,
    # so refuse before hashing anything rather than quietly measuring the path
    # instead. The directory case is the same mistake wearing a disguise:
    # `file_exists` is `os.path.isfile`, so a folder handed to `hashfile` used
    # to take the missing-file branch even though nothing was missing. Both
    # exceptions are OSError subclasses, which is what callers walking a tree
    # (see `os_helper.gui._dedupe_groups`) already guard against for a file
    # that vanishes mid-walk.
    if hash_content or date:
        if os.path.isdir(path):
            msg = f"hashfile() needs a file, but '{path}' is a directory (see hashfolder())."
            raise IsADirectoryError(msg)
        if not file_exists(path):
            msg = (
                f"Cannot hash the content or the modification time of '{path}': "
                "no such file. Pass hash_content=False to hash the path string instead."
            )
            raise FileNotFoundError(msg)

    # The file's last modification time, as integer nanoseconds: exact, with no
    # float formatting to argue about, and it only moves when the file does.
    if date:
        h.update(str(os.stat(path).st_mtime_ns).encode("utf-8"))

    # Content, or the path string when the caller deliberately asked for a name
    # rather than bytes. The two are now exclusive branches of an explicit
    # request, not a guess about what is on disk.
    if hash_content:
        with open(path, "rb") as fi:
            h.update(fi.read())
    else:
        h.update(path.encode("utf-8"))

    return h.hexdigest()


def hashfolder(
    path: str, hash_content: bool = True, hash_path: bool = False, date: bool = False
) -> str:
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
        If True, includes the folder's own last modification time
        (``os.stat().st_mtime_ns``) in the hash (default: False). It is the
        folder's mtime, never the current clock. Note that a directory's mtime
        tracks entries appearing and disappearing, not edits made *inside* a
        file it holds — that is what ``hash_content=True`` is for.

    Returns
    -------
    str
        The resulting hash of the folder and/or its contents as a
        40-character hex string.

    Raises
    ------
    FileNotFoundError
        If ``hash_content`` or ``date`` is True and ``path`` names nothing.
    NotADirectoryError
        If ``hash_content`` or ``date`` is True and ``path`` names a file.
    ValueError
        If ``hash_content``, ``hash_path`` and ``date`` are all False, which
        asks for a fingerprint of nothing.

    Notes
    -----
    Asking to walk a folder that is not there is an error, not a fallback.
    This function used to return the digest of the empty string in that case —
    the same constant for every missing folder, which is also what an *empty*
    existing folder hashes to and what a file handed in by mistake hashed to.
    Four different situations collapsed onto one plausible 40-hex-char answer,
    so "have these two folders diverged" replied "no" when neither existed.
    """
    h = _hash_engine()

    # Hashing nothing yields the engine's empty digest: a constant that looks
    # like a measurement and is not one. Say so instead of returning it.
    if not (hash_content or hash_path or date):
        msg = (
            "hashfolder() was asked for a digest of nothing: set at least one of "
            "hash_content, hash_path or date."
        )
        raise ValueError(msg)

    # Walking the tree and reading the folder's mtime both need the folder to
    # be there. Mirrors hashfile(): refuse up front rather than hand back a
    # digest nobody measured, and raise OSError subclasses so a caller already
    # guarding a tree walk keeps working.
    if hash_content or date:
        if os.path.isfile(path):
            msg = f"hashfolder() needs a directory, but '{path}' is a file (see hashfile())."
            raise NotADirectoryError(msg)
        if not dir_exists(path):
            msg = (
                f"Cannot hash the contents or the modification time of '{path}': "
                "no such directory. Pass hash_path=True alone to hash the path string."
            )
            raise FileNotFoundError(msg)

    # The folder's last modification time, as integer nanoseconds — exact, and
    # it only moves when the directory listing does.
    if date:
        h.update(str(os.stat(path).st_mtime_ns).encode("utf-8"))

    if hash_content:
        for root, dirs, files in os.walk(path):
            # os.walk's traversal and per-directory listing order come from
            # os.scandir(), which reflects filesystem/directory-entry order,
            # NOT alphabetical order -- it can differ between two folders with
            # identical content that were populated in a different sequence
            # (or between filesystems), which would silently break this
            # function's own documented promise ("the same input always
            # produces the same fingerprint", "have these two folders
            # diverged"). Sorting `dirs` in place steers os.walk's own
            # traversal order; sorting `files` fixes the per-directory hash
            # order.
            dirs.sort()
            for file in sorted(files):
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
