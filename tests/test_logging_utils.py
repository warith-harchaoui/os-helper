"""
Tests for os_helper.logging_utils.

Usage Example
-------------
>>> #   pytest tests/test_logging_utils.py --cov=os_helper.logging_utils

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import io
import logging
import sys
import types

import pytest

from os_helper import logging_utils as lu


def test_hex_to_ansi_truecolor_valid_and_invalid() -> None:
    assert lu._hex_to_ansi_truecolor("#FF0000") == "\033[38;2;255;0;0m"
    assert lu._hex_to_ansi_truecolor("00FF00") == "\033[38;2;0;255;0m"  # no leading '#'
    with pytest.raises(ValueError, match="Invalid hex color"):
        lu._hex_to_ansi_truecolor("#FFF")  # shorthand not supported


def test_color_formatter_wraps_and_restores_levelname() -> None:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "hello", None, None)
    original = record.levelname

    colored = lu._ColorFormatter(fmt="%(levelname)s: %(message)s", use_colors=True)
    formatted = colored.format(record)
    assert "\033[" in formatted
    assert record.levelname == original  # mutation undone after formatting

    plain = lu._ColorFormatter(fmt="%(levelname)s: %(message)s", use_colors=False)
    assert "\033[" not in plain.format(record)


def test_running_in_notebook_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    # IPython not importable at all.
    monkeypatch.setitem(sys.modules, "IPython", None)
    assert lu._running_in_notebook() is False

    fake = types.ModuleType("IPython")

    # Installed, but not running inside any IPython shell.
    fake.get_ipython = lambda: None
    monkeypatch.setitem(sys.modules, "IPython", fake)
    assert lu._running_in_notebook() is False

    # A plain terminal IPython session is not a notebook.
    class TerminalInteractiveShell:
        pass

    fake.get_ipython = lambda: TerminalInteractiveShell()
    assert lu._running_in_notebook() is False

    # The Jupyter kernel's shell class name is the actual signal.
    class ZMQInteractiveShell:
        pass

    fake.get_ipython = lambda: ZMQInteractiveShell()
    assert lu._running_in_notebook() is True


def test_supports_ansi_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Stream:
        def __init__(self, tty: bool = True, raises: bool = False) -> None:
            self._tty, self._raises = tty, raises

        def isatty(self) -> bool:
            if self._raises:
                raise OSError("no tty")
            return self._tty

    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("TERM", raising=False)

    assert lu._supports_ansi(_Stream(tty=True)) is True
    assert lu._supports_ansi(_Stream(tty=False)) is False
    assert lu._supports_ansi(_Stream(raises=True)) is False  # isatty() raising -> False
    assert lu._supports_ansi(object()) is False  # no isatty attribute at all

    monkeypatch.setenv("NO_COLOR", "1")
    assert lu._supports_ansi(_Stream(tty=True)) is False
    monkeypatch.delenv("NO_COLOR", raising=False)

    monkeypatch.setenv("TERM", "dumb")
    assert lu._supports_ansi(_Stream(tty=True)) is False


def test_verbosity_get_and_set() -> None:
    previous = lu.verbosity()
    try:
        assert lu.verbosity(2) == 2  # DEBUG
        assert lu.verbosity() == 2
        assert lu.verbosity(0) == 0  # WARNING
        assert lu.verbosity(-1) == -1  # ERROR
        assert lu.verbosity(3) == 2  # clamped to DEBUG
        assert lu.verbosity(-5) == -2  # clamped to CRITICAL
    finally:
        lu.verbosity(previous)


def test_debug_info_warning_error_critical_and_check(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG, logger="os_helper"):
        lu.debug("d")
        lu.info("i")
        lu.warning("w")
        lu.error("e")
        lu.critical("c")
    assert [r.message for r in caplog.records] == ["d", "i", "w", "e", "c"]

    lu.check(True, "never raised")  # must not raise
    with pytest.raises(AssertionError, match="boom"):
        lu.check(False, "boom")


def test_init_logging_named_live_stream() -> None:
    """`init_logging(name=..., live_stream=True)` is CLI-friendly: named,
    idempotent, live-stderr, and propagating — the mode a CLI needs to route
    diagnostics through os_helper without losing pytest's capsys/caplog.
    """
    lg = lu.init_logging(
        name="oshtest",
        level=logging.ERROR,
        stdout=False,
        log_format="%(message)s",
        use_colors=False,
        capture_warnings=False,
        live_stream=True,
        propagate=True,
    )
    try:
        assert lg.name == "oshtest" and lg.level == logging.ERROR and lg.propagate is True

        # Idempotency: a second call must not add a second owned console handler.
        lu.init_logging(
            name="oshtest", level=logging.ERROR, stdout=False, log_format="%(message)s",
            use_colors=False, live_stream=True, propagate=True,
        )
        owned = [h for h in logging.getLogger("oshtest").handlers if getattr(h, "_osh_owned", False)]
        assert len(owned) == 1

        # Live-stderr: swap sys.stderr AFTER config; the record lands in the
        # new one, bare (no level/timestamp prefix); sub-ERROR is dropped.
        child = logging.getLogger("oshtest.sub")
        buf = io.StringIO()
        old = sys.stderr
        sys.stderr = buf
        try:
            child.warning("dropped below ERROR")
            child.error("bare message")
        finally:
            sys.stderr = old
        assert buf.getvalue() == "bare message\n"

        # propagate=True -> a root handler still observes the record.
        seen: list[str] = []
        probe = logging.Handler()
        probe.emit = lambda r: seen.append(r.getMessage())
        logging.getLogger().addHandler(probe)
        try:
            child.error("also at root")
        finally:
            logging.getLogger().removeHandler(probe)
        assert "also at root" in seen
    finally:
        for h in logging.getLogger("oshtest").handlers[:]:
            logging.getLogger("oshtest").removeHandler(h)


def test_init_logging_file_handler_and_named_reset_preserves_foreign_handlers(tmp_path) -> None:
    log_file = tmp_path / "run.log"
    name = "oshtest_file"
    try:
        lg = lu.init_logging(name=name, filename=str(log_file), use_colors=False, propagate=True)
        lg.info("hello file")
        for h in lg.handlers:
            h.flush()
        assert log_file.exists()
        assert "hello file" in log_file.read_text()

        # A foreign (not osh-owned) handler on the same named logger — e.g. a
        # caplog-style handler a host already attached — survives a reset=True
        # re-configuration; only OUR handlers get torn down and replaced.
        foreign = logging.Handler()
        lg.addHandler(foreign)
        lu.init_logging(name=name, filename=str(log_file), use_colors=False, reset=True)
        assert foreign in logging.getLogger(name).handlers
    finally:
        for h in logging.getLogger(name).handlers[:]:
            logging.getLogger(name).removeHandler(h)
