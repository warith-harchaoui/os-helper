"""
Tests for os_helper.system_utils.

OS-detection dispatches purely on ``platform.system()``, so tests drive the
real ``windows``/``linux``/``macos``/``unix``/``openfile`` logic by mocking
that one boundary rather than each function individually. ``system()`` is
exercised with real subprocess calls (``python -c ...``) since it is a thin,
security-relevant wrapper (``shell=False``) worth testing for real.

Usage Example
-------------
>>> #   pytest tests/test_system_utils.py --cov=os_helper.system_utils

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import os
import sys

import pytest

from os_helper import system_utils


@pytest.mark.parametrize(
    ("reported", "windows", "linux_", "macos_", "unix_"),
    [
        ("Windows", True, False, False, False),
        ("Linux", False, True, False, True),
        ("Darwin", False, False, True, True),
        ("FreeBSD", False, False, False, False),
    ],
)
def test_os_detection_dispatches_on_platform_system(
    monkeypatch: pytest.MonkeyPatch,
    reported: str,
    windows: bool,
    linux_: bool,
    macos_: bool,
    unix_: bool,
) -> None:
    monkeypatch.setattr(system_utils.platform, "system", lambda: reported)
    assert system_utils.windows() is windows
    assert system_utils.linux() is linux_
    assert system_utils.macos() is macos_
    assert system_utils.unix() is unix_


def test_get_nb_workers_pool_size_and_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(system_utils.os, "cpu_count", lambda: 4)
    monkeypatch.delenv("NB_WORKERS", raising=False)

    assert system_utils.get_nb_workers(0) == 4  # explicit "whole pool"
    assert system_utils.get_nb_workers(2) == 2  # positive -> taken literally
    assert system_utils.get_nb_workers(-1) == 4  # sklearn convention: all cores
    assert system_utils.get_nb_workers(-2) == 3  # all but one
    assert system_utils.get_nb_workers(-10) == 1  # clamped at a single worker

    monkeypatch.setenv("NB_WORKERS", "8")
    assert system_utils.get_nb_workers(0) == 8

    # A malformed override must not crash: warn and fall back to auto-detect.
    monkeypatch.setenv("NB_WORKERS", "not-a-number")
    assert system_utils.get_nb_workers(0) == 4


def test_get_nb_workers_falls_back_to_one_without_cpu_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(system_utils.os, "cpu_count", lambda: None)
    monkeypatch.delenv("NB_WORKERS", raising=False)
    assert system_utils.get_nb_workers(0) == 1


def test_getpid_matches_real_process() -> None:
    assert system_utils.getpid() == str(os.getpid())


def test_system_runs_command_and_captures_output() -> None:
    result = system_utils.system(f"{sys.executable} -c \"print('hello')\"")
    assert result["out"].strip() == "hello"
    assert result["err"] == ""


def test_system_raises_on_nonzero_exit_when_checked() -> None:
    with pytest.raises(AssertionError, match="failed with exit code"):
        system_utils.system(f"{sys.executable} -c \"import sys; sys.exit(1)\"")


def test_system_tolerates_nonzero_exit_when_not_checked() -> None:
    result = system_utils.system(
        f"{sys.executable} -c \"import sys; sys.exit(1)\"", check_exitcode=False
    )
    assert result["out"] == ""


def test_system_expected_output_check(tmp_path) -> None:
    target = tmp_path / "out.txt"
    # The command itself creates the expected artefact. ``repr()`` rather
    # than raw interpolation: a Windows path is full of backslashes, and
    # splicing it straight into a Python string literal risks forming an
    # accidental escape sequence (e.g. ``\U`` reads as the 8-hex-digit
    # Unicode escape, a SyntaxError in the spawned interpreter for anything
    # but a coincidental hex run) -- ``repr()`` escapes it correctly for
    # re-parsing regardless of the host OS's path separator.
    system_utils.system(
        f"{sys.executable} -c \"open({str(target)!r}, 'w').write('x')\"",
        expected_output=str(target),
    )
    assert target.exists()

    # Declaring an expected artefact that never appears raises.
    missing = tmp_path / "never-created.txt"
    with pytest.raises(AssertionError, match="does not exist or is empty"):
        system_utils.system(f"{sys.executable} -c \"pass\"", expected_output=str(missing))


def _capture_popen_args(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[str]]:
    """Fake ``windows()`` True and ``Popen`` to record its argv, without
    spawning a real process -- lets these Windows-only branches run on any
    (POSIX) test runner instead of requiring a real Windows machine."""
    captured: dict[str, list[str]] = {}

    class _FakeProc:
        returncode = 0

        def communicate(self):
            return b"", b""

    def _fake_popen(args, **kwargs):
        captured["args"] = args
        return _FakeProc()

    monkeypatch.setattr(system_utils, "windows", lambda: True)
    monkeypatch.setattr(system_utils, "Popen", _fake_popen)
    return captured


def test_system_preserves_windows_backslash_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    # Regression test: plain ``shlex.split`` is POSIX-oriented and treats an
    # unescaped backslash as an escape character, so on a real Windows box a
    # command built from ``sys.executable`` (e.g.
    # ``C:\hostedtoolcache\...\python.exe``) got mangled into
    # ``C:hostedtoolcache...python.exe`` and the spawned process could never
    # be found.
    captured = _capture_popen_args(monkeypatch)

    windows_path = r"C:\hostedtoolcache\windows\Python\3.12.10\x64\python.exe"
    system_utils.system(f'{windows_path} -c "print(1)"')

    assert captured["args"] == [windows_path, "-c", "print(1)"]


def test_system_preserves_backslashes_inside_quoted_argument(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Regression test for a second, subtler bite of the same POSIX-vs-Windows
    # mismatch: an argument that is ITSELF a Python source string embedding a
    # Windows path, e.g. an inline ``-c "open(r'C:\...\out.txt', 'w')"`` used
    # to create ``expected_output``. An early fix that blanket-doubled every
    # backslash in the whole command corrupted this case even after fixing
    # the bare-executable-path case above: doubling backslashes that were
    # already correctly escaped for the *subprocess's own* Python parser
    # left it with twice as many as intended.
    captured = _capture_popen_args(monkeypatch)

    exe = r"C:\hostedtoolcache\windows\Python\3.12.10\x64\python.exe"
    target = r"C:\Users\runneradmin\AppData\Local\Temp\out.txt"
    code = f"open({target!r}, 'w').write('x')"
    system_utils.system(f'{exe} -c "{code}"')

    assert captured["args"] == [exe, "-c", code]


def test_openfile_dispatches_by_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(system_utils, "system", lambda cmd, **kw: calls.append(cmd))

    monkeypatch.setattr(system_utils.platform, "system", lambda: "Darwin")
    system_utils.openfile("/tmp/some file.txt")
    assert calls[-1] == "open '/tmp/some file.txt'"

    monkeypatch.setattr(system_utils.platform, "system", lambda: "Linux")
    system_utils.openfile("/tmp/report.pdf")
    assert calls[-1] == "xdg-open /tmp/report.pdf"

    monkeypatch.setattr(system_utils.platform, "system", lambda: "FreeBSD")
    with pytest.raises(OSError, match="Unsupported operating system"):
        system_utils.openfile("/tmp/report.pdf")


def test_openfile_uses_startfile_on_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(system_utils.platform, "system", lambda: "Windows")
    calls: list[str] = []
    # os.startfile only exists on Windows; inject a stand-in for this test.
    monkeypatch.setattr(system_utils.os, "startfile", lambda path: calls.append(path), raising=False)
    system_utils.openfile("C:\\report.pdf")
    assert calls == ["C:\\report.pdf"]
