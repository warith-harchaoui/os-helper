"""
Tests for os_helper.hash_utils.

Usage Example
-------------
>>> #   pytest tests/test_hash_utils.py --cov=os_helper.hash_utils

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import pytest

from os_helper import hash_utils as hu


def test_hash_engine_prefers_ripemd160_falls_back_to_blake2b(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = hu._hash_engine()
    assert engine.digest_size == 20  # 40 hex chars, whichever algorithm won

    # Force the RIPEMD-160-disabled path (e.g. OpenSSL 3 legacy provider off).
    def _no_ripemd(name):
        raise ValueError("unsupported hash type ripemd160")

    monkeypatch.setattr(hu.hashlib, "new", _no_ripemd)
    fallback = hu._hash_engine()
    assert fallback.digest_size == 20
    assert fallback.name == "blake2b"


def test_hash_string_truncation_and_padding() -> None:
    full = hu.hash_string("example")
    assert len(full) == 40

    truncated = hu.hash_string("example", size=8)
    assert truncated == full[:8]

    # Requesting MORE than the native 40 chars repeats the digest to fill it.
    padded = hu.hash_string("example", size=64)
    assert len(padded) == 64
    assert padded.startswith(full)


def test_hashfile_content_path_and_date_variants(tmp_path) -> None:
    f = tmp_path / "data.txt"
    f.write_text("hello")

    content_hash = hu.hashfile(str(f), hash_content=True)
    # Changing the content changes the hash.
    f.write_text("hello world")
    assert hu.hashfile(str(f), hash_content=True) != content_hash

    # hash_content=False hashes the PATH string instead — deterministic per
    # path, and different paths must yield different hashes.
    other = tmp_path / "other-name.txt"
    other.write_text("hello world")  # same content, different path
    assert hu.hashfile(str(f), hash_content=False) == hu.hashfile(str(f), hash_content=False)
    assert hu.hashfile(str(f), hash_content=False) != hu.hashfile(str(other), hash_content=False)

    # A missing file with hash_content=True also falls back to hashing the path.
    missing = tmp_path / "missing.txt"
    assert hu.hashfile(str(missing), hash_content=True) == hu.hashfile(str(missing), hash_content=False)

    # date=True perturbs the digest relative to date=False.
    assert hu.hashfile(str(f), hash_content=True, date=True) != content_hash


def test_hashfolder_content_path_and_date_variants(tmp_path) -> None:
    folder = tmp_path / "hashfolder_test"
    folder.mkdir()
    (folder / "file1.txt").write_text("File 1 content")
    (folder / "file2.txt").write_text("File 2 content")
    (folder / ".hidden").write_text("must be ignored")

    initial = hu.hashfolder(str(folder), hash_content=True)
    (folder / "file1.txt").write_text("Modified File 1 content")
    modified = hu.hashfolder(str(folder), hash_content=True)
    assert initial != modified

    # hash_path=True folds the folder path into the digest.
    with_path = hu.hashfolder(str(folder), hash_content=True, hash_path=True)
    assert with_path != modified

    # date=True perturbs the digest too.
    with_date = hu.hashfolder(str(folder), hash_content=True, date=True)
    assert with_date != modified

    # A hidden file's content must not affect the hash.
    control_folder = tmp_path / "hashfolder_control"
    control_folder.mkdir()
    (control_folder / "file1.txt").write_text("Modified File 1 content")
    (control_folder / "file2.txt").write_text("File 2 content")
    assert hu.hashfolder(str(control_folder), hash_content=True) == modified
