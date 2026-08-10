"""
Tests for os_helper.path_utils.

Functional, filesystem-real tests against ``tmp_path`` rather than mocked
``os`` calls — path resolution, existence checks, and copy/remove behavior
are exactly the kind of logic that's easy to get subtly wrong under mocks
and right under a real (temporary) filesystem.

Usage Example
-------------
>>> #   pytest tests/test_path_utils.py --cov=os_helper.path_utils

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import os

import pytest

from os_helper import path_utils as pu


def test_folder_name_ext_splits_on_last_dot_only(tmp_path) -> None:
    # Multi-part suffix: only the LAST dot is the split point.
    folder, name, ext = pu.folder_name_ext(str(tmp_path / "archive.tar.gz"))
    assert (name, ext) == ("archive.tar", "gz")
    assert folder == str(tmp_path)

    # No dot in the basename -> empty extension.
    folder, name, ext = pu.folder_name_ext(str(tmp_path / "README"))
    assert (name, ext) == ("README", "")

    # An existing directory -> empty extension too, even with a dot in the name.
    a_dir = tmp_path / "pkg.egg-info"
    a_dir.mkdir()
    folder, name, ext = pu.folder_name_ext(str(a_dir))
    assert (name, ext) == ("pkg.egg-info", "")

    # checkpath=True raises for a path that doesn't exist.
    with pytest.raises(AssertionError):
        pu.folder_name_ext(str(tmp_path / "nope.txt"), checkpath=True)


def test_file_and_dir_exists(tmp_path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("content")
    assert pu.file_exists(str(f)) is True
    assert pu.file_exists(str(tmp_path / "missing.txt")) is False

    empty = tmp_path / "empty.txt"
    empty.write_text("")
    assert pu.file_exists(str(empty), check_empty=True) is False

    d = tmp_path / "dir"
    d.mkdir()
    assert pu.dir_exists(str(d)) is True
    assert pu.dir_exists(str(d), check_empty=True) is False  # empty
    assert pu.dir_exists(str(tmp_path / "no_such_dir")) is False
    (d / "child.txt").write_text("x")
    assert pu.dir_exists(str(d), check_empty=True) is True


def test_absolute_relative_path_round_trip(tmp_path) -> None:
    # absolute2relative_path against an explicit base.
    target = tmp_path / "project" / "file.txt"
    rel = pu.absolute2relative_path(str(target), str(tmp_path))
    assert rel == os.path.join("project", "file.txt")

    # absolute2relative_path defaulting base_path to the CWD.
    monkeypatch_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        rel_from_cwd = pu.absolute2relative_path(str(target))
        assert rel_from_cwd == os.path.join("project", "file.txt")
    finally:
        os.chdir(monkeypatch_cwd)

    # relative2absolute_path: round-trips back to an absolute path.
    abs_path = pu.relative2absolute_path(rel_from_cwd)
    assert os.path.isabs(abs_path)

    # checkpath=True raises FileNotFoundError for a path that doesn't exist.
    with pytest.raises(FileNotFoundError):
        pu.relative2absolute_path(str(tmp_path / "definitely_missing.xyz"), checkpath=True)


def test_path_without_home() -> None:
    home = os.path.expanduser("~")
    nested = os.path.join(home, "project", "file.txt")
    assert pu.path_without_home(nested) == os.path.join("~", "project", "file.txt")

    # A path outside the home directory is returned unchanged (normalized).
    outside = "/opt/somewhere/file.txt"
    assert pu.path_without_home(outside) == os.path.normpath(outside)


def test_recursive_glob_finds_nested_matches(tmp_path) -> None:
    nested = tmp_path / "sub"
    nested.mkdir()
    top = tmp_path / "top.txt"
    top.write_text("x")
    deep = nested / "deep.txt"
    deep.write_text("x")
    (tmp_path / "ignored.md").write_text("x")

    found = pu.recursive_glob(str(tmp_path), "*.txt")
    assert set(found) == {str(top), str(deep)}


def test_join_accepts_positional_args_and_a_single_list() -> None:
    from_args = pu.join("a", "b", "file.txt")
    from_list = pu.join(["a", "b", "file.txt"])
    assert from_args == from_list
    assert from_args.endswith(os.path.join("a", "b", "file.txt"))
    assert os.path.isabs(from_args)


def test_size_file_and_checkfile(tmp_path) -> None:
    f = tmp_path / "sized.txt"
    f.write_text("hello")
    assert pu.size_file(str(f)) == 5
    assert pu.size_file(str(tmp_path / "missing.txt")) == -1

    pu.checkfile(str(f), check_empty=True)  # must not raise
    with pytest.raises(AssertionError):
        pu.checkfile(str(tmp_path / "missing.txt"))
    empty = tmp_path / "empty.txt"
    empty.write_text("")
    with pytest.raises(AssertionError):
        pu.checkfile(str(empty), check_empty=True)


def test_copyfile_into_directory_and_failure_and_self_copy_guard(tmp_path) -> None:
    src = tmp_path / "source.txt"
    src.write_text("payload")

    # Destination is an existing directory: source's basename is appended.
    dest_dir = tmp_path / "dest_dir"
    dest_dir.mkdir()
    pu.copyfile(str(src), str(dest_dir))
    assert (dest_dir / "source.txt").read_text() == "payload"

    # Copying onto itself is rejected.
    with pytest.raises(AssertionError):
        pu.copyfile(str(src), str(src))

    # A destination whose parent doesn't exist propagates a real OSError.
    bad_dest = tmp_path / "no_such_subdir" / "dst.txt"
    with pytest.raises((OSError, FileNotFoundError)):
        pu.copyfile(str(src), str(bad_dest))


def test_make_directory_idempotent_and_propagates_failure(tmp_path) -> None:
    target = tmp_path / "new_folder"
    pu.make_directory(str(target))
    assert target.is_dir()
    pu.make_directory(str(target))  # exist_ok=True by default: no raise

    # A parent that is a regular file makes directory creation impossible.
    blocker = tmp_path / "blocker_file"
    blocker.write_text("not a directory")
    with pytest.raises((OSError, FileExistsError, NotADirectoryError)):
        pu.make_directory(str(blocker / "child"))


def test_remove_directory_missing_is_noop_present_is_removed_failure_propagates(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    missing = tmp_path / "totally_absent_dir"
    pu.remove_directory(str(missing))  # must not raise

    present = tmp_path / "present_dir"
    present.mkdir()
    (present / "f.txt").write_text("x")
    pu.remove_directory(str(present))
    assert not present.exists()

    # A failure from shutil.rmtree is logged and re-raised, not swallowed.
    another = tmp_path / "another_dir"
    another.mkdir()

    def _boom(path):
        raise OSError("permission denied")

    monkeypatch.setattr(pu.shutil, "rmtree", _boom)
    with pytest.raises(OSError):
        pu.remove_directory(str(another))


def test_remove_files_is_best_effort(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_a = tmp_path / "a.txt"
    real_b = tmp_path / "b.txt"
    real_a.write_text("x")
    real_b.write_text("x")
    missing = tmp_path / "missing.txt"

    pu.remove_files([str(real_a), str(missing), str(real_b)])  # must not raise
    assert not real_a.exists()
    assert not real_b.exists()

    # A per-file failure (e.g. permissions) is logged and swallowed, not raised.
    still_there = tmp_path / "locked.txt"
    still_there.write_text("x")

    def _boom(self):
        raise OSError("locked")

    monkeypatch.setattr(pu.pathlib.Path, "unlink", _boom)
    pu.remove_files([str(still_there)])  # must not raise
