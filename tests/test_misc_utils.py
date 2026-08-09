"""
Tests for os_helper.misc_utils.

``download_file``'s happy paths (fresh download, resume, sha256, retry,
skip-when-present) are already covered in ``test_os_helpers.py``; this file
adds the branches that were still missing there (URL-derived filename,
sha256-verified skip, resume=False sidecar reset, keep-alive empty chunks,
exhausted retries) plus full coverage of the smaller helpers that had no
tests at all yet: ``format_size``, ``is_working_url``, ``zip_folder``'s
default-path/hidden-file branches, ``time2str``, ``str2time``, and
``get_user_ip``. Network boundaries (``requests.get``/``requests.head``) are
stubbed; everything else runs for real against ``tmp_path``.

Usage Example
-------------
>>> #   pytest tests/test_misc_utils.py --cov=os_helper.misc_utils

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import os

import pytest
import requests

from os_helper import misc_utils as mu


# ---------------------------------------------------------------------------
# format_size
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (500, "500 B"),
        (1_500, "1.50 KB"),
        (1_500_000, "1.50 MB"),
        (1_500_000_000, "1.50 GB"),
        (1_500_000_000_000, "1.50 TB"),
    ],
)
def test_format_size_picks_the_right_unit(size: int, expected: str) -> None:
    assert mu.format_size(size) == expected


# ---------------------------------------------------------------------------
# is_working_url
# ---------------------------------------------------------------------------


def test_is_working_url_rejects_malformed_url() -> None:
    assert mu.is_working_url("not a url") is False


def test_is_working_url_true_on_200(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        status_code = 200

    monkeypatch.setattr(mu.requests, "head", lambda url, timeout=5: _Resp())
    assert mu.is_working_url("https://example.com") is True


def test_is_working_url_false_on_non_200(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        status_code = 404

    monkeypatch.setattr(mu.requests, "head", lambda url, timeout=5: _Resp())
    assert mu.is_working_url("https://example.com") is False


def test_is_working_url_false_on_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*a, **k):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(mu.requests, "head", _raise)
    assert mu.is_working_url("https://example.com") is False


# ---------------------------------------------------------------------------
# zip_folder
# ---------------------------------------------------------------------------


def test_zip_folder_default_path_and_skips_hidden_files(tmp_path) -> None:
    src = tmp_path / "payload"
    src.mkdir()
    (src / "keep.txt").write_text("kept")
    (src / ".hidden").write_text("skip me")

    mu.zip_folder(str(src))  # no explicit zip_file_path -> "<folder>.zip"
    default_zip = str(src) + ".zip"
    assert os.path.exists(default_zip)

    import zipfile

    with zipfile.ZipFile(default_zip) as zf:
        assert zf.namelist() == ["keep.txt"]


# ---------------------------------------------------------------------------
# time2str
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("seconds", "no_space", "expected"),
    [
        (0.0, False, "0 sec"),
        (5.0, False, "5 sec"),
        (120.0, False, "2 min"),
        (5400.0, False, "1 hr 30 min"),
        (3661.0, False, "1 hr 1 min 1 sec"),
        (3661.0, True, "1hr 1min 1sec"),
    ],
)
def test_time2str_formats_durations(seconds: float, no_space: bool, expected: str) -> None:
    assert mu.time2str(seconds, no_space=no_space) == expected


# ---------------------------------------------------------------------------
# str2time
# ---------------------------------------------------------------------------


def test_str2time_empty_string_is_zero() -> None:
    assert mu.str2time("") == 0.0
    assert mu.str2time("   ") == 0.0


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1:30:00", 5400.0),
        ("1:30", 90.0),
        ("1 hr 30 min", 5400.0),
        ("120 s", 120.0),
        ("1.5 hours", 5400.0),
        ("1.5 days", 129600.0),
        ("90", 90.0),  # bare number -> seconds
    ],
)
def test_str2time_parses_known_formats(text: str, expected: float) -> None:
    assert mu.str2time(text) == pytest.approx(expected)


def test_str2time_malformed_colon_format_returns_zero() -> None:
    assert mu.str2time("1:2:3:4") == 0.0  # wrong part count
    assert mu.str2time("a:b:c") == 0.0  # non-numeric parts


def test_str2time_unparseable_garbage_returns_zero() -> None:
    assert mu.str2time("not a duration at all") == 0.0


def test_str2time_numeric_conversion_error_is_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    # The unit regex only ever captures digit strings, so float() on that
    # capture cannot realistically fail — the except ValueError branch is a
    # defensive backstop. Force it by breaking float() itself for this test.
    monkeypatch.setattr("builtins.float", lambda *_: (_ for _ in ()).throw(ValueError("nope")))
    assert mu.str2time("5 min") == 0.0


# ---------------------------------------------------------------------------
# get_user_ip
# ---------------------------------------------------------------------------


def test_get_user_ip_both_succeed(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        def __init__(self, ip: str) -> None:
            self._ip = ip

        def json(self) -> dict:
            return {"ip": self._ip}

    def _get(url: str, timeout: int = 5):
        return _Resp("1.2.3.4") if "api64" not in url else _Resp("::1")

    monkeypatch.setattr(mu.requests, "get", _get)
    result = mu.get_user_ip()
    assert result == {"ipv4": "1.2.3.4", "ipv6": "::1"}


def test_get_user_ip_partial_failure_still_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        def json(self) -> dict:
            return {"ip": "1.2.3.4"}

    def _get(url: str, timeout: int = 5):
        if "api64" in url:
            raise requests.ConnectionError("boom")
        return _Resp()

    monkeypatch.setattr(mu.requests, "get", _get)
    result = mu.get_user_ip()
    assert result == {"ipv4": "1.2.3.4", "ipv6": None}


def test_get_user_ip_raises_when_both_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*a, **k):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(mu.requests, "get", _raise)
    with pytest.raises(AssertionError, match="Failed to retrieve IP"):
        mu.get_user_ip()


# ---------------------------------------------------------------------------
# download_file — branches not already covered in test_os_helpers.py
# ---------------------------------------------------------------------------


def test_download_file_derives_name_from_url(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    payload = b"data"

    class _Resp:
        status_code = 200
        headers = {"Content-Type": "application/octet-stream", "Content-Length": str(len(payload))}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size=1):
            yield b""  # keep-alive chunk carrying no data, must be skipped
            yield payload

    monkeypatch.setattr(mu, "is_working_url", lambda url: True)
    monkeypatch.setattr(mu.requests, "get", lambda *a, **k: _Resp())
    monkeypatch.chdir(tmp_path)

    meta = mu.download_file("https://example.invalid/dir/name.bin?query=1", progress=False)
    assert meta["path"] == "name.bin"
    assert os.path.exists("name.bin")
    with open("name.bin", "rb") as fh:
        assert fh.read() == payload


def test_download_file_sha256_verified_skip_of_existing_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    import hashlib

    payload = b"already here"
    digest = hashlib.sha256(payload).hexdigest()
    dest = tmp_path / "cached.bin"
    dest.write_bytes(payload)

    def _boom(*a, **k):
        raise AssertionError("network should not be touched")

    monkeypatch.setattr(mu, "is_working_url", lambda url: True)
    monkeypatch.setattr(mu.requests, "get", _boom)

    meta = mu.download_file(
        "https://example.invalid/cached.bin", str(dest), progress=False, sha256=digest
    )
    assert meta["sha256"] == digest
    assert meta["bytes"] == len(payload)


def test_download_file_sha256_mismatch_on_existing_file_redownloads(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    import hashlib

    stale_payload = b"stale wrong content"
    fresh_payload = b"correct content"
    good_digest = hashlib.sha256(fresh_payload).hexdigest()

    dest = tmp_path / "mismatch.bin"
    dest.write_bytes(stale_payload)  # present, but does not match `sha256=` below

    class _Resp:
        status_code = 200
        headers = {"Content-Type": "text/plain", "Content-Length": str(len(fresh_payload))}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size=1):
            yield fresh_payload

    monkeypatch.setattr(mu, "is_working_url", lambda url: True)
    monkeypatch.setattr(mu.requests, "get", lambda *a, **k: _Resp())

    meta = mu.download_file(
        "https://example.invalid/mismatch.bin", str(dest), progress=False, sha256=good_digest
    )
    assert meta["sha256"] == good_digest
    with open(dest, "rb") as fh:
        assert fh.read() == fresh_payload


def test_download_file_resume_false_discards_stale_sidecar(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    payload = b"fresh content"
    dest = tmp_path / "fresh.bin"
    part = tmp_path / "fresh.bin.part"
    part.write_bytes(b"stale garbage that must not survive")

    class _Resp:
        status_code = 200
        headers = {"Content-Type": "text/plain", "Content-Length": str(len(payload))}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size=1):
            yield payload

    monkeypatch.setattr(mu, "is_working_url", lambda url: True)
    monkeypatch.setattr(mu.requests, "get", lambda *a, **k: _Resp())

    meta = mu.download_file(
        "https://example.invalid/fresh.bin", str(dest), progress=False, resume=False
    )
    assert meta["bytes"] == len(payload)
    with open(dest, "rb") as fh:
        assert fh.read() == payload


def test_download_file_raises_after_exhausting_retries(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    def _always_fails(*a, **k):
        raise requests.ConnectionError("permanently down")

    monkeypatch.setattr(mu, "is_working_url", lambda url: True)
    monkeypatch.setattr(mu.requests, "get", _always_fails)
    monkeypatch.setattr(mu.time, "sleep", lambda s: None)

    dest = tmp_path / "never.bin"
    with pytest.raises(requests.ConnectionError):
        mu.download_file("https://example.invalid/never.bin", str(dest), progress=False, retries=1)
