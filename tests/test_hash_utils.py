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

import os
import time

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

    # A missing file is fine as long as only the PATH is being hashed; that is
    # the whole point of hash_content=False. (Asking for its content instead is
    # an error -- see test_hashfile_refuses_to_fingerprint_what_it_cannot_read.)
    missing = tmp_path / "missing.txt"
    assert hu.hashfile(str(missing), hash_content=False) == hu.hash_string(str(missing))

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


def test_hashfolder_is_independent_of_directory_entry_order(tmp_path) -> None:
    # os.walk's own traversal/listing order reflects the filesystem's
    # directory-entry order, not alphabetical order, so two folders with
    # identical content created in the opposite sequence must still hash
    # the same -- otherwise the function's "same input, same fingerprint"
    # promise silently breaks depending on how a folder was populated.
    forward = tmp_path / "forward"
    forward.mkdir()
    (forward / "a.txt").write_text("A")
    (forward / "b.txt").write_text("B")
    (forward / "c.txt").write_text("C")

    reverse = tmp_path / "reverse"
    reverse.mkdir()
    (reverse / "c.txt").write_text("C")
    (reverse / "b.txt").write_text("B")
    (reverse / "a.txt").write_text("A")

    assert hu.hashfolder(str(forward), hash_content=True) == hu.hashfolder(
        str(reverse), hash_content=True
    )


# ---------------------------------------------------------------------------
# Defect class 1: a plausible digest for something the function never read.
#
# `hashfile` used to answer the PATH digest whenever it could not read the
# content, so `hashfile("/gone")` returned a valid-looking 40-hex-char value
# and the one job you take a file's fingerprint for -- noticing the file is
# not there -- could not be done with it. `hashfolder` was worse: it returned
# the digest of the empty string, the SAME constant for every missing folder,
# for an empty existing folder, and for a file handed in by mistake.
# ---------------------------------------------------------------------------


def test_hashfile_refuses_to_fingerprint_what_it_cannot_read(tmp_path) -> None:
    """Content (or mtime) that cannot be read is an error, not a path digest."""
    missing = tmp_path / "missing.txt"

    # The headline case: content was asked for and there is no content.
    with pytest.raises(FileNotFoundError):
        hu.hashfile(str(missing), hash_content=True)

    # date=True is a claim about the file's mtime, so it needs the file too --
    # even when the content itself was not requested.
    with pytest.raises(FileNotFoundError):
        hu.hashfile(str(missing), hash_content=False, date=True)

    # Same defect wearing a disguise: `file_exists` is `os.path.isfile`, so a
    # DIRECTORY used to take the missing-file branch and come back with a path
    # digest although nothing was missing at all.
    folder = tmp_path / "a-folder"
    folder.mkdir()
    (folder / "inside.txt").write_text("content that was never hashed")
    with pytest.raises(IsADirectoryError):
        hu.hashfile(str(folder), hash_content=True)

    # And the legitimate escape hatch still works: a path digest is available
    # on request, for a file that need not exist.
    assert len(hu.hashfile(str(missing), hash_content=False)) == 40


def test_hashfolder_refuses_to_fingerprint_what_it_cannot_walk(tmp_path) -> None:
    """A missing folder must not hash to the same constant as an empty one."""
    missing = tmp_path / "no-such-folder"
    other_missing = tmp_path / "another-missing-folder"
    empty = tmp_path / "empty"
    empty.mkdir()
    a_file = tmp_path / "plain.txt"
    a_file.write_text("not a folder")

    # All three used to return hashlib ripemd160(b"") -- one constant standing
    # in for three different situations, which is why "have these two folders
    # diverged" answered "no" when neither of them existed.
    with pytest.raises(FileNotFoundError):
        hu.hashfolder(str(missing), hash_content=True)
    with pytest.raises(FileNotFoundError):
        hu.hashfolder(str(other_missing), hash_content=True)
    with pytest.raises(NotADirectoryError):
        hu.hashfolder(str(a_file), hash_content=True)

    # date=True needs the folder as well, content request or not.
    with pytest.raises(FileNotFoundError):
        hu.hashfolder(str(missing), hash_content=False, hash_path=True, date=True)

    # An empty folder that really exists keeps its (constant) digest: it is a
    # measurement of something, unlike the three cases above.
    assert hu.hashfolder(str(empty), hash_content=True) == hu._hash_engine().hexdigest()

    # Asking for neither content, nor path, nor date is asking for the digest
    # of nothing -- which silently returned that same empty-string constant.
    with pytest.raises(ValueError):
        hu.hashfolder(str(empty), hash_content=False, hash_path=False, date=False)

    # The path-only digest stays available for a folder that need not exist.
    assert len(hu.hashfolder(str(missing), hash_content=False, hash_path=True)) == 40


def test_missing_target_raises_oserror_so_tree_walkers_keep_their_guard(tmp_path) -> None:
    """The raised types must stay under ``OSError``.

    ``os_helper.gui._dedupe_groups`` is the only caller of ``hashfile`` inside
    this package, and it already wraps the call in ``except OSError`` so a file
    that vanishes between the scan and the hash is skipped with a warning
    instead of aborting the whole dedupe pass. Signalling a missing file with
    ``AssertionError`` (the ``check`` / ``checkfile`` convention elsewhere in
    the repo) would slip straight through that guard, so the choice of
    exception family is load-bearing, not cosmetic.
    """
    missing_file = tmp_path / "vanished.txt"
    missing_dir = tmp_path / "vanished-dir"

    with pytest.raises(OSError):
        hu.hashfile(str(missing_file), hash_content=True)
    with pytest.raises(OSError):
        hu.hashfolder(str(missing_dir), hash_content=True)


# ---------------------------------------------------------------------------
# Defect class 2: `date=True` folded in the CURRENT clock, not the file's
# modification time, so a digest meant to change when the file changes changed
# on every call -- unusable as the cache key the option exists for, and a flat
# contradiction of the docstring ("its last modification date").
# ---------------------------------------------------------------------------


def test_hashfile_date_follows_the_file_mtime_not_the_clock(tmp_path) -> None:
    """``date=True`` is a function of the file's mtime and of nothing else."""
    f = tmp_path / "data.txt"
    f.write_text("unchanging content")

    # Two mtimes set by hand, content untouched throughout.
    old = (1_000_000_000, 1_000_000_000)
    new = (1_600_000_000, 1_600_000_000)

    os.utime(f, old)
    at_old = hu.hashfile(str(f), date=True)

    os.utime(f, new)
    at_new = hu.hashfile(str(f), date=True)
    # This is the assertion the old implementation fails: all three calls here
    # happen inside the same wall-clock second, so a `now_string("log")`-based
    # digest comes back IDENTICAL even though the mtime moved by 19 years.
    assert at_new != at_old

    # Restoring the mtime restores the digest -- the property that makes it
    # usable as a cache key at all.
    os.utime(f, old)
    assert hu.hashfile(str(f), date=True) == at_old

    # date=False must stay a pure content digest, untouched by any mtime.
    content_only = hu.hashfile(str(f), hash_content=True)
    os.utime(f, new)
    assert hu.hashfile(str(f), hash_content=True) == content_only


def test_hashfolder_date_follows_the_folder_mtime_not_the_clock(tmp_path) -> None:
    """Same contract for ``hashfolder``: the folder's mtime, not ``now``."""
    folder = tmp_path / "folder"
    folder.mkdir()
    (folder / "file.txt").write_text("unchanging content")

    old = (1_000_000_000, 1_000_000_000)
    new = (1_600_000_000, 1_600_000_000)

    os.utime(folder, old)
    at_old = hu.hashfolder(str(folder), date=True)

    os.utime(folder, new)
    assert hu.hashfolder(str(folder), date=True) != at_old

    os.utime(folder, old)
    assert hu.hashfolder(str(folder), date=True) == at_old


def test_date_digests_are_stable_across_a_real_clock_tick(tmp_path) -> None:
    """Two calls with the wall clock genuinely advanced must agree.

    The ``os.utime`` tests above pin the digest to the mtime; this one pins it
    AGAINST the clock, which needs the clock to actually move. The sleep is
    load-bearing: ``now_string("log")`` is second-granularity, so without it
    both calls can land inside the same second and this test would pass on the
    broken implementation -- green for the wrong reason.
    """
    f = tmp_path / "data.txt"
    f.write_text("unchanging content")
    folder = tmp_path / "folder"
    folder.mkdir()
    (folder / "file.txt").write_text("unchanging content")

    file_before = hu.hashfile(str(f), date=True)
    folder_before = hu.hashfolder(str(folder), date=True)

    time.sleep(1.1)  # strictly more than one second of `now_string("log")`

    assert hu.hashfile(str(f), date=True) == file_before
    assert hu.hashfolder(str(folder), date=True) == folder_before


def test_digests_of_readable_targets_did_not_move(tmp_path) -> None:
    """The fix changed the error paths only.

    Anyone holding a digest produced by an earlier release for a file that
    existed must still get the same 40 characters, so the two working branches
    are pinned to their definitions: content bytes through the engine, and the
    path string through ``hash_string``.
    """
    f = tmp_path / "data.txt"
    f.write_bytes(b"hello")

    engine = hu._hash_engine()
    engine.update(b"hello")
    assert hu.hashfile(str(f), hash_content=True) == engine.hexdigest()
    assert hu.hashfile(str(f), hash_content=False) == hu.hash_string(str(f))


# ---------------------------------------------------------------------------
# hashfile(): path AND/OR content
#
# `hashfolder` has taken three independent flags (hash_content, hash_path,
# date) for as long as it has existed, so a caller can fingerprint a folder by
# its contents, by its name, or by both. `hashfile` took only hash_content,
# with the path as its `else` branch -- so "this file, at this path" was the
# one combination its sibling could express and it could not. A cache keyed on
# a file that can legitimately appear at two paths with the same bytes needs
# exactly that combination.
# ---------------------------------------------------------------------------


def test_hashfile_can_hash_path_and_content_together(tmp_path) -> None:
    """The combination neither flag could reach alone."""
    f = tmp_path / "data.txt"
    f.write_bytes(b"hello")

    content_only = hu.hashfile(str(f), hash_content=True)
    path_only = hu.hashfile(str(f), hash_content=False, hash_path=True)
    both = hu.hashfile(str(f), hash_content=True, hash_path=True)

    # Three distinct questions, three distinct answers.
    assert len({content_only, path_only, both}) == 3
    assert len(both) == 40


def test_hashfile_both_mode_moves_with_either_half(tmp_path) -> None:
    """Content and path each have to reach the digest, or the mode is a lie."""
    a = tmp_path / "a.txt"
    a.write_bytes(b"hello")
    both_before = hu.hashfile(str(a), hash_content=True, hash_path=True)

    # Same path, different bytes.
    a.write_bytes(b"goodbye")
    assert hu.hashfile(str(a), hash_content=True, hash_path=True) != both_before

    # Same bytes, different path -- the case content-only cannot distinguish,
    # which is the whole reason the combination has to exist.
    c, d = tmp_path / "c.txt", tmp_path / "d.txt"
    c.write_bytes(b"hello")
    d.write_bytes(b"hello")
    assert hu.hashfile(str(c), hash_content=True) == hu.hashfile(str(d), hash_content=True)
    assert hu.hashfile(str(c), hash_content=True, hash_path=True) != hu.hashfile(
        str(d), hash_content=True, hash_path=True
    )


def test_hashfile_both_mode_pins_its_composition_order(tmp_path) -> None:
    """Fix the order, so the digest cannot drift when the body is rearranged."""
    f = tmp_path / "data.txt"
    f.write_bytes(b"hello")

    # Mirrors hashfolder's order: date, then content, then path.
    engine = hu._hash_engine()
    engine.update(b"hello")
    engine.update(str(f).encode("utf-8"))
    assert hu.hashfile(str(f), hash_content=True, hash_path=True) == engine.hexdigest()


def test_hashfile_refuses_a_digest_of_nothing(tmp_path) -> None:
    """Asking for neither half must say so, as hashfolder already does."""
    f = tmp_path / "data.txt"
    f.write_bytes(b"hello")
    with pytest.raises(ValueError, match="nothing"):
        hu.hashfile(str(f), hash_content=False, hash_path=False)


def test_hashfile_keeps_its_old_two_spellings(tmp_path) -> None:
    """Adding a flag must not move a digest anybody already stored."""
    f = tmp_path / "data.txt"
    f.write_bytes(b"hello")

    engine = hu._hash_engine()
    engine.update(b"hello")
    assert hu.hashfile(str(f), hash_content=True) == engine.hexdigest()
    # hash_content=False, with hash_path left unsaid, still means "the path".
    assert hu.hashfile(str(f), hash_content=False) == hu.hash_string(str(f))
    missing = tmp_path / "gone.txt"
    assert hu.hashfile(str(missing), hash_content=False) == hu.hash_string(str(missing))
