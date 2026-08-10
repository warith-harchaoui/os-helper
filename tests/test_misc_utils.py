"""
Tests for os_helper.misc_utils.

Every `download_file` scenario (fresh download, resume, idempotent skip,
sha256 verify/mismatch, retry, keep-alive chunks, filename derivation) lives
here as the single owner, sharing one fake-response helper instead of each
scenario redefining its own response class. Network boundaries
(``requests.get``/``requests.head``) are stubbed; everything else — the
streaming loop, the sidecar rename, the hashing, the filesystem checks —
runs for real against ``tmp_path``.

Usage Example
-------------
>>> #   pytest tests/test_misc_utils.py --cov=os_helper.misc_utils

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import hashlib
import os
import zipfile

import pytest
import requests

from os_helper import misc_utils as mu

# ---------------------------------------------------------------------------
# now_string / folder_description / progress_bar / _adaptive_chunk_size
# ---------------------------------------------------------------------------


def test_now_string_and_format_size() -> None:
    log_format = mu.now_string("log")
    filename_format = mu.now_string("filename")
    assert "/" in log_format
    assert "-" in filename_format
    assert ":" not in filename_format

    cases = {
        500: "500 B",
        1_500: "1.50 KB",
        1_500_000: "1.50 MB",
        1_500_000_000: "1.50 GB",
        1_500_000_000_000: "1.50 TB",
    }
    for size, expected in cases.items():
        assert mu.format_size(size) == expected, size


def test_folder_description_recursive_and_flat(tmp_path) -> None:
    test_dir = tmp_path / "folder_description_test"
    nested = test_dir / "sub"
    nested.mkdir(parents=True)
    (test_dir / "a.txt").write_text("aaa")  # 3 bytes
    (nested / "b.txt").write_text("bbbb")  # 4 bytes
    (test_dir / ".hidden").write_text("ignored")  # hidden file must be skipped

    description = mu.folder_description(
        str(test_dir), recursive=True, index_html=True, with_size=True, description_json=True
    )
    assert description == {"a.txt": 3, os.path.join("sub", "b.txt"): 4}
    assert (test_dir / "index.html").exists()

    import json

    desc_json = test_dir / "description.json"
    assert desc_json.exists()
    assert json.loads(desc_json.read_text()) == description

    # Non-recursive variant on a fresh folder excludes nested entries and
    # emits no companion files.
    flat_dir = tmp_path / "folder_description_flat"
    (flat_dir / "sub").mkdir(parents=True)
    (flat_dir / "a.txt").write_text("aaa")
    (flat_dir / "sub" / "b.txt").write_text("bbbb")

    flat = mu.folder_description(
        str(flat_dir), recursive=False, index_html=False, description_json=False
    )
    assert flat == {"a.txt": 3}
    assert not (flat_dir / "index.html").exists()
    assert not (flat_dir / "description.json").exists()


def test_progress_bar_and_adaptive_chunk_size(monkeypatch: pytest.MonkeyPatch) -> None:
    # progress_bar: explicit disable is honoured verbatim, known total wired through.
    bar = mu.progress_bar(total=2048, desc="x", disable=True)
    assert bar.total == 2048 and bar.disable is True
    bar.close()

    # disable=None + a non-TTY stderr -> auto-disabled (no control-char spam in CI).
    monkeypatch.setattr("sys.stderr.isatty", lambda: False)
    off = mu.progress_bar(total=10, disable=None)
    assert off.disable is True
    off.close()

    # _adaptive_chunk_size: scales toward ~512 chunks, clamped [64 KiB, 4 MiB].
    lo, hi, default = 64 * 1024, 4 * 1024 * 1024, 1 << 20
    # ~750 MB -> 786432000 // 512 = 1_536_000 B, inside the clamp window.
    assert mu._adaptive_chunk_size(750 * 1024 * 1024) == 1_536_000
    # 5 GB -> would be ~10 MiB, clamped down to the 4 MiB ceiling.
    assert mu._adaptive_chunk_size(5 * 1024**3) == hi
    # 10 KB -> would be tiny, clamped up to the 64 KiB floor so it still streams.
    assert mu._adaptive_chunk_size(10 * 1024) == lo
    # Unknown / zero size (server sent no Content-Length) -> fixed 1 MiB fallback.
    assert mu._adaptive_chunk_size(None) == default
    assert mu._adaptive_chunk_size(0) == default


# ---------------------------------------------------------------------------
# time2str / str2time — table-driven, one collected test each
# ---------------------------------------------------------------------------


def test_time2str_formats_durations() -> None:
    cases = [
        (0.0, False, "0 sec"),
        (5.0, False, "5 sec"),
        (120.0, False, "2 min"),
        (5400.0, False, "1 hr 30 min"),
        (3661.0, False, "1 hr 1 min 1 sec"),
        (3661.0, True, "1hr 1min 1sec"),
    ]
    for seconds, no_space, expected in cases:
        assert mu.time2str(seconds, no_space=no_space) == expected, (seconds, no_space)


def test_str2time_parses_known_formats(monkeypatch: pytest.MonkeyPatch) -> None:
    assert mu.str2time("") == 0.0
    assert mu.str2time("   ") == 0.0
    assert mu.str2time("1:2:3:4") == 0.0  # wrong part count
    assert mu.str2time("a:b:c") == 0.0  # non-numeric colon parts
    assert mu.str2time("not a duration at all") == 0.0

    cases = {
        "1:30:00": 5400.0,
        "1:30": 90.0,
        "1 hr 30 min": 5400.0,
        "120 s": 120.0,
        "1.5 hours": 5400.0,
        "1.5 days": 129600.0,
        "90": 90.0,  # bare number -> seconds
    }
    for text, expected in cases.items():
        assert mu.str2time(text) == pytest.approx(expected), text

    # The unit regex only ever captures digit strings, so float() on that
    # capture cannot realistically fail — the except ValueError branch is a
    # defensive backstop. Force it by breaking float() itself for this case.
    monkeypatch.setattr("builtins.float", lambda *_: (_ for _ in ()).throw(ValueError("nope")))
    assert mu.str2time("5 min") == 0.0


# ---------------------------------------------------------------------------
# is_working_url / get_user_ip
# ---------------------------------------------------------------------------


def test_is_working_url_covers_malformed_ok_and_failure_cases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert mu.is_working_url("not a url") is False  # syntactic gate, no network

    class _Resp:
        def __init__(self, status: int) -> None:
            self.status_code = status

    monkeypatch.setattr(mu.requests, "head", lambda url, timeout=5: _Resp(200))
    assert mu.is_working_url("https://example.com") is True

    monkeypatch.setattr(mu.requests, "head", lambda url, timeout=5: _Resp(404))
    assert mu.is_working_url("https://example.com") is False

    def _raise(*a, **k):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(mu.requests, "head", _raise)
    assert mu.is_working_url("https://example.com") is False


def test_get_user_ip_success_partial_and_total_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        def __init__(self, ip: str) -> None:
            self._ip = ip

        def json(self) -> dict:
            return {"ip": self._ip}

    # Both endpoints answer.
    monkeypatch.setattr(
        mu.requests,
        "get",
        lambda url, timeout=5: _Resp("::1") if "api64" in url else _Resp("1.2.3.4"),
    )
    assert mu.get_user_ip() == {"ipv4": "1.2.3.4", "ipv6": "::1"}

    # ipv6 endpoint fails: the ipv4 result still comes back.
    def _v6_fails(url: str, timeout: int = 5):
        if "api64" in url:
            raise requests.ConnectionError("boom")
        return _Resp("1.2.3.4")

    monkeypatch.setattr(mu.requests, "get", _v6_fails)
    assert mu.get_user_ip() == {"ipv4": "1.2.3.4", "ipv6": None}

    # Both endpoints fail: only then does it raise.
    def _both_fail(*a, **k):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(mu.requests, "get", _both_fail)
    with pytest.raises(AssertionError, match="Failed to retrieve IP"):
        mu.get_user_ip()


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
    with zipfile.ZipFile(default_zip) as zf:
        assert zf.namelist() == ["keep.txt"]

    # An explicit destination is honored too.
    custom_zip = tmp_path / "custom.zip"
    mu.zip_folder(str(src), str(custom_zip))
    assert custom_zip.exists()


# ---------------------------------------------------------------------------
# download_file — one fake-response helper shared by every scenario
# ---------------------------------------------------------------------------


class _StreamResp:
    """Minimal stand-in for ``requests.get(..., stream=True)``'s context manager.

    ``leading_empty_chunk`` covers the keep-alive-chunk-must-be-skipped branch;
    a 206 status (when ``range_start`` is set) covers the resume branch.
    """

    def __init__(
        self,
        payload: bytes,
        *,
        content_type: str = "application/octet-stream",
        range_start: int | None = None,
        leading_empty_chunk: bool = False,
    ) -> None:
        self._payload = payload
        self._leading_empty_chunk = leading_empty_chunk
        if range_start:
            self.status_code = 206
            end = len(payload) - 1
            self.headers = {
                "Content-Type": content_type,
                "Content-Range": f"bytes {range_start}-{end}/{len(payload)}",
            }
            self._body = payload[range_start:]
        else:
            self.status_code = 200
            self.headers = {"Content-Type": content_type, "Content-Length": str(len(payload))}
            self._body = payload

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size=1):
        if self._leading_empty_chunk:
            yield b""  # keep-alive chunk carrying no data, must be skipped
        yield self._body


def _range_aware_get(payload: bytes):
    """``requests.get`` stub honouring an incoming ``Range`` header, for resume tests."""

    def _get(*a, **k):
        headers = k.get("headers") or {}
        rng = headers.get("Range", "")
        start = int(rng.split("=", 1)[1].split("-", 1)[0]) if rng.startswith("bytes=") else 0
        return _StreamResp(payload, range_start=start or None)

    return _get


def test_download_file_fresh_download_then_idempotent_skip(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    payload = b"\x89PNG\r\n\x1a\nfake"
    monkeypatch.setattr(mu, "is_working_url", lambda url: True)
    monkeypatch.setattr(
        mu.requests, "get", lambda *a, **k: _StreamResp(payload, content_type="image/png")
    )

    dest = str(tmp_path / "out.bin")
    meta = mu.download_file("https://example.invalid/x.png", dest, progress=False)
    assert meta["content_type"] == "image/png"
    assert meta["bytes"] == len(payload)
    assert not os.path.exists(dest + ".part")  # atomic finalize leaves no sidecar

    # Second call: existing complete file is reused, network is never touched.
    def _boom(*a, **k):
        raise AssertionError("network should not be touched for a present file")

    monkeypatch.setattr(mu.requests, "get", _boom)
    meta = mu.download_file("https://example.invalid/x.png", dest, progress=False)
    assert meta["bytes"] == len(payload)


def test_download_file_derives_name_and_skips_keepalive_chunks(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    payload = b"data"
    monkeypatch.setattr(mu, "is_working_url", lambda url: True)
    monkeypatch.setattr(
        mu.requests, "get", lambda *a, **k: _StreamResp(payload, leading_empty_chunk=True)
    )
    monkeypatch.chdir(tmp_path)

    meta = mu.download_file("https://example.invalid/dir/name.bin?query=1", progress=False)
    assert meta["path"] == "name.bin"
    with open("name.bin", "rb") as fh:
        assert fh.read() == payload


def test_download_file_resumes_from_partial_sidecar(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    payload = b"0123456789abcdef" * 8  # 128 bytes
    monkeypatch.setattr(mu, "is_working_url", lambda url: True)
    monkeypatch.setattr(mu.requests, "get", _range_aware_get(payload))

    dest = str(tmp_path / "big.bin")
    with open(dest + ".part", "wb") as fh:
        fh.write(payload[:40])  # seed a partial sidecar, as an interrupted run would

    meta = mu.download_file("https://example.invalid/big.bin", dest, progress=False)
    assert meta["resumed"] is True
    with open(dest, "rb") as fh:
        assert fh.read() == payload
    assert not os.path.exists(dest + ".part")


def test_download_file_resume_false_discards_stale_sidecar(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    payload = b"fresh content"
    dest = tmp_path / "fresh.bin"
    (tmp_path / "fresh.bin.part").write_bytes(b"stale garbage that must not survive")

    monkeypatch.setattr(mu, "is_working_url", lambda url: True)
    monkeypatch.setattr(mu.requests, "get", lambda *a, **k: _StreamResp(payload))

    meta = mu.download_file(
        "https://example.invalid/fresh.bin", str(dest), progress=False, resume=False
    )
    assert meta["bytes"] == len(payload)
    with open(dest, "rb") as fh:
        assert fh.read() == payload


def test_download_file_sha256_verify_and_mismatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    payload = b"verify me"
    good = hashlib.sha256(payload).hexdigest()
    monkeypatch.setattr(mu, "is_working_url", lambda url: True)
    monkeypatch.setattr(mu.requests, "get", lambda *a, **k: _StreamResp(payload))

    # Matching digest: verified, sidecar finalized.
    dest = str(tmp_path / "v.bin")
    meta = mu.download_file("https://example.invalid/v.bin", dest, progress=False, sha256=good)
    assert meta["sha256"] == good

    # Wrong digest on a fresh download: raises, no partial left behind.
    bad_dest = str(tmp_path / "bad.bin")
    with pytest.raises(ValueError):
        mu.download_file("https://example.invalid/v.bin", bad_dest, progress=False, sha256="00" * 32)
    assert not os.path.exists(bad_dest + ".part")


def test_download_file_sha256_against_existing_file_skip_or_redownload(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.setattr(mu, "is_working_url", lambda url: True)

    # Existing file already matches the pinned digest: skip, network untouched.
    good_payload = b"already here"
    good_digest = hashlib.sha256(good_payload).hexdigest()
    cached = tmp_path / "cached.bin"
    cached.write_bytes(good_payload)

    def _boom(*a, **k):
        raise AssertionError("network should not be touched")

    monkeypatch.setattr(mu.requests, "get", _boom)
    meta = mu.download_file(
        "https://example.invalid/cached.bin", str(cached), progress=False, sha256=good_digest
    )
    assert meta["sha256"] == good_digest

    # Existing file does NOT match: mismatch triggers a real re-download.
    fresh_payload = b"correct content"
    fresh_digest = hashlib.sha256(fresh_payload).hexdigest()
    mismatch = tmp_path / "mismatch.bin"
    mismatch.write_bytes(b"stale wrong content")
    monkeypatch.setattr(mu.requests, "get", lambda *a, **k: _StreamResp(fresh_payload))

    meta = mu.download_file(
        "https://example.invalid/mismatch.bin", str(mismatch), progress=False, sha256=fresh_digest
    )
    assert meta["sha256"] == fresh_digest
    with open(mismatch, "rb") as fh:
        assert fh.read() == fresh_payload


def test_download_file_retries_then_succeeds_or_raises_when_exhausted(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.setattr(mu, "is_working_url", lambda url: True)
    monkeypatch.setattr(mu.time, "sleep", lambda s: None)  # no real backoff wait

    # One transient failure, then success.
    payload = b"eventually"
    calls = {"n": 0}

    def _flaky(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise requests.ConnectionError("boom")
        return _StreamResp(payload)

    monkeypatch.setattr(mu.requests, "get", _flaky)
    dest = str(tmp_path / "r.bin")
    meta = mu.download_file("https://example.invalid/r.bin", dest, progress=False)
    assert meta["bytes"] == len(payload) and calls["n"] == 2

    # Permanently failing: raises once retries are exhausted.
    def _always_fails(*a, **k):
        raise requests.ConnectionError("permanently down")

    monkeypatch.setattr(mu.requests, "get", _always_fails)
    never_dest = str(tmp_path / "never.bin")
    with pytest.raises(requests.ConnectionError):
        mu.download_file("https://example.invalid/never.bin", never_dest, progress=False, retries=1)
