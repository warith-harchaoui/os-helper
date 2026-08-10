"""
Tests for os_helper.temp_utils.

Usage Example
-------------
>>> #   pytest tests/test_temp_utils.py --cov=os_helper.temp_utils

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import os

import pytest

from os_helper import temp_utils as tu


def test_temporary_filename_lifecycle_suffix_and_directory(tmp_path) -> None:
    # Basic lifecycle: exists inside the block, gone after.
    with tu.temporary_filename() as temp_file:
        assert os.path.isfile(temp_file)
    assert not os.path.exists(temp_file)

    # A suffix without a leading dot is normalized to have one.
    with tu.temporary_filename(suffix="txt") as temp_file:
        assert temp_file.endswith(".txt")

    # directory=... places the file INSIDE the given directory (so sibling
    # paths still resolve for tools that expect that).
    with tu.temporary_filename(suffix=".md", directory=str(tmp_path)) as tmp:
        assert os.path.dirname(os.path.realpath(tmp)) == os.path.realpath(str(tmp_path))
        assert os.path.isfile(tmp)


def test_temporary_filename_cleanup_failure_is_logged_not_raised(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_unlink = tu.os.unlink

    def _boom(path):
        raise OSError("locked")

    monkeypatch.setattr(tu.os, "unlink", _boom)
    with tu.temporary_filename() as temp_file:
        pass
    assert os.path.exists(temp_file)  # cleanup failed, but no exception escaped
    real_unlink(temp_file)  # actually clean up, bypassing the monkeypatch


def test_temporary_folder_lifecycle_and_error_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    with tu.temporary_folder() as temp_folder:
        assert os.path.isdir(temp_folder)
        probe = os.path.join(temp_folder, "test.txt")
        with open(probe, "w") as f:
            f.write("content")
        assert os.path.isfile(probe)
    assert not os.path.isdir(temp_folder)

    # A body that raises still propagates (the wrapping except re-raises).
    with pytest.raises(ValueError, match="boom"), tu.temporary_folder() as temp_folder:
        raise ValueError("boom")
    assert not os.path.isdir(temp_folder)  # cleanup still ran on the way out

    # A cleanup failure (rmtree raising) is logged, not raised.
    real_rmtree = tu.shutil.rmtree

    def _boom(path):
        raise OSError("locked")

    monkeypatch.setattr(tu.shutil, "rmtree", _boom)
    with tu.temporary_folder() as temp_folder:
        pass
    assert os.path.isdir(temp_folder)  # cleanup failed, but no exception escaped
    real_rmtree(temp_folder)  # actually clean up, bypassing the monkeypatch


def test_make_temporary_directory_persists_until_caller_removes_it() -> None:
    d = tu.make_temporary_directory(prefix="oshtest-")
    try:
        assert os.path.isdir(d)
        probe = os.path.join(d, "keep.txt")
        with open(probe, "w") as fh:
            fh.write("x")
        assert os.path.isfile(probe)  # no auto-cleanup on any scope exit
    finally:
        tu.shutil.rmtree(d)
    assert not os.path.isdir(d)


def test_temporary_remote_file_happy_paths() -> None:
    storage: dict[str, bytes] = {}

    def upload(local_path: str) -> str:
        with open(local_path, "rb") as f:
            storage[local_path] = f.read()
        return local_path

    def delete(remote_path: str) -> None:
        storage.pop(remote_path, None)

    # Mode B: a fresh temp file is created, seeded, uploaded, then cleaned up
    # both locally and remotely. suffix without a leading dot is normalized.
    with tu.temporary_remote_file(
        upload, delete, prefix="trf", suffix="bin", initial_content=b"hello"
    ) as remote:
        assert storage[remote] == b"hello"
    assert remote not in storage

    # Mode A: from_local_file is uploaded as-is and survives the block —
    # only the remote copy is cleaned up.
    local_path = str(tu.tempfile.mktemp())
    with open(local_path, "wb") as f:
        f.write(b"local content")
    try:
        with tu.temporary_remote_file(upload, delete, from_local_file=local_path) as remote:
            assert storage[remote] == b"local content"
        assert remote not in storage
        assert os.path.isfile(local_path)  # local file must NOT be removed
    finally:
        os.unlink(local_path)


def test_temporary_remote_file_error_paths() -> None:
    def upload(p: str) -> str:
        return "remote://" + os.path.basename(p)

    deleted: list[str] = []

    def delete(r: str) -> None:
        deleted.append(r)

    # Non-callable arguments are rejected immediately, before any I/O.
    with pytest.raises(TypeError, match="upload_function"):
        with tu.temporary_remote_file("not-callable", delete):
            pass
    with pytest.raises(TypeError, match="delete_function"):
        with tu.temporary_remote_file(upload, "not-callable"):
            pass
    with pytest.raises(TypeError, match="checkfile_function"):
        with tu.temporary_remote_file(upload, delete, checkfile_function="not-callable"):
            pass

    # from_local_file pointing at nothing raises FileNotFoundError.
    with pytest.raises(FileNotFoundError):
        with tu.temporary_remote_file(upload, delete, from_local_file="/no/such/file.bin"):
            pass

    # A failing checkfile_function raises RuntimeError but cleanup still runs.
    with (
        pytest.raises(RuntimeError),
        tu.temporary_remote_file(
            upload, delete, suffix=".bin", checkfile_function=lambda _: False, initial_content=b"x"
        ),
    ):
        pass
    assert len(deleted) == 1


def test_temporary_remote_file_delete_failure_is_logged_not_raised(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def upload(p: str) -> str:
        return "remote://" + os.path.basename(p)

    def failing_delete(r: str) -> None:
        raise OSError("remote unreachable")

    with tu.temporary_remote_file(upload, failing_delete, initial_content=b"x"):
        pass  # the delete failure inside `finally` must not escape as an exception
