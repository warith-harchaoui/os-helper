"""
os_helper.logging_utils
=======================

ANSI-coloured root-logger setup and verbosity controls for the AI Helpers
suite. Replaces bare ``print(...)`` calls across every helper with
``osh.info`` / ``osh.warning`` / ``osh.error`` (see the suite-wide style
mandate in each helper's ``CONTRIBUTING.md``).

Usage example
-------------
>>> import os_helper as osh
>>> osh.verbosity(2)        # show DEBUG + INFO + WARNING + ERROR
>>> osh.info("hello %s", "world")
>>> osh.warning("disk %d%% full", 92)

Author
------
Warith HARCHAOUI — https://linkedin.com/in/warith-harchaoui
"""

from __future__ import annotations

import contextlib
import logging
import os
import sys
from pathlib import Path
from typing import Any, Final


def _hex_to_ansi_truecolor(hex_color: str) -> str:
    """Convert a hex color like ``#CCE4FF`` to an ANSI truecolor sequence."""
    # Accept both ``#RRGGBB`` and bare ``RRGGBB`` by dropping any leading hash.
    hex_color = hex_color.lstrip("#")
    # We only support full 6-digit hex — reject shorthand/invalid input loudly.
    if len(hex_color) != 6:
        msg = f"Invalid hex color: {hex_color!r}"
        raise ValueError(msg)

    # Split the string into its three 8-bit channels.
    red = int(hex_color[0:2], 16)
    green = int(hex_color[2:4], 16)
    blue = int(hex_color[4:6], 16)
    # ``38;2;r;g;b`` is the SGR sequence for a 24-bit (truecolor) foreground.
    return f"\033[38;2;{red};{green};{blue}m"


class _ColorFormatter(logging.Formatter):
    """Formatter adding ANSI colors based on the log level."""

    RESET: Final[str] = "\033[0m"

    COLORS: Final[dict[int, str]] = {
        logging.DEBUG: _hex_to_ansi_truecolor("#CCE4FF"),  # Cyan
        logging.INFO: _hex_to_ansi_truecolor("#28CD41"),  # Green
        logging.WARNING: _hex_to_ansi_truecolor("#FFCC00"),  # Yellow
        logging.ERROR: _hex_to_ansi_truecolor("#FF3B30"),  # Red
        logging.CRITICAL: _hex_to_ansi_truecolor("#FF2D55"),  # Magenta
    }

    def __init__(
        self,
        fmt: str,
        datefmt: str | None = None,
        use_colors: bool = True,
    ) -> None:
        """Initialize the formatter.

        Parameters
        ----------
        fmt : str
            Log message format.
        datefmt : str | None, optional
            Datetime format.
        use_colors : bool, optional
            Whether to inject ANSI colors into the level name.
        """
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record, optionally coloring its level name."""
        # Stash the original level name: log records are shared objects, so we
        # must restore it afterwards or other handlers would see the ANSI codes.
        original_levelname = record.levelname

        # Wrap the level name in the level-specific color, if any is configured.
        if self.use_colors:
            color = self.COLORS.get(record.levelno, "")
            if color:
                record.levelname = f"{color}{original_levelname}{self.RESET}"

        try:
            return super().format(record)
        finally:
            # Always undo the mutation, even if formatting raised.
            record.levelname = original_levelname


def _running_in_notebook() -> bool:
    """Return True if the code appears to run inside a Jupyter notebook."""
    # IPython is an optional dependency; its absence simply means "not a notebook".
    try:
        from IPython import get_ipython  # type: ignore
    except Exception:
        return False

    # ``get_ipython`` returns None outside any IPython shell.
    shell = get_ipython()
    if shell is None:
        return False

    # ``ZMQInteractiveShell`` is the class used specifically by the Jupyter
    # kernel; a plain terminal IPython uses ``TerminalInteractiveShell`` instead.
    return shell.__class__.__name__ == "ZMQInteractiveShell"


def _supports_ansi(stream: object) -> bool:
    """Return True if the given stream likely supports ANSI escape codes."""
    # Honour the informal ``NO_COLOR`` standard (https://no-color.org/): its
    # mere presence disables coloring regardless of value.
    if os.environ.get("NO_COLOR"):
        return False

    # A "dumb" terminal explicitly advertises no escape-sequence support.
    if os.environ.get("TERM") == "dumb":
        return False

    # Objects without ``isatty`` (e.g. a plain file) cannot be interactive TTYs.
    if not hasattr(stream, "isatty"):
        return False

    try:
        # The real test: only a genuine terminal gets colored output.
        return bool(stream.isatty())
    except Exception:
        # Some wrapped streams raise on ``isatty``; treat that as "no color".
        return False


def init_logging(
    *,
    level: int = logging.INFO,
    stdout: bool = True,
    log_format: str = "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    date_format: str = "%Y-%m-%d %H:%M:%S",
    filename: str | Path | None = None,
    capture_warnings: bool = True,
    reset: bool = True,
    use_colors: bool = True,
    propagate: bool = False,
) -> logging.Logger:
    """Initialize application-wide logging.

    This function configures the root logger with a console handler and,
    optionally, a file handler. It is designed for applications, scripts,
    notebooks, and machine learning experiments where deterministic logging
    setup is useful.

    Parameters
    ----------
    level : int, optional
        Logging level applied to the root logger and its handlers.
        Typical values are ``logging.DEBUG``, ``logging.INFO``,
        ``logging.WARNING``, ``logging.ERROR``, and ``logging.CRITICAL``.
    stdout : bool, optional
        If True, console logs are sent to ``sys.stdout``. Otherwise, they are
        sent to ``sys.stderr``.
    log_format : str, optional
        Format string used for log records.
    date_format : str, optional
        Format string used for timestamps in log records.
    filename : str | pathlib.Path | None, optional
        Optional path to a log file. If provided, logs are also written to this
        file using UTF-8 encoding.
    capture_warnings : bool, optional
        If True, warnings emitted through the ``warnings`` module are redirected
        to the logging system.
    reset : bool, optional
        If True, existing handlers attached to the root logger are removed
        before adding new ones. This is often desirable in notebooks and
        interactive sessions to avoid duplicated messages.
    use_colors : bool, optional
        If True, colorize console log levels when ANSI colors are supported.
        File logs are never colorized.
    propagate : bool, optional
        Value assigned to the root logger propagation flag. In most application
        contexts, ``False`` is appropriate to avoid duplicates.

    Returns
    -------
    logging.Logger
        The configured root logger.

    Notes
    -----
    This function is intended for top-level applications, notebooks, and
    experimentation code. Reusable libraries should generally avoid configuring
    global logging and should instead use:

    ``logger = logging.getLogger(__name__)``

    Examples
    --------
    >>> logger = init_logging(level=logging.DEBUG, filename="experiment.log")
    >>> logger.info("Logging is configured.")

    >>> logger = init_logging(use_colors=True, reset=True)
    >>> logger.warning("This is a warning.")
    """
    root_logger = logging.getLogger()

    # In notebooks and re-run scripts, stale handlers cause duplicate lines;
    # tearing them down first makes this function idempotent.
    if reset:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            # Closing releases file descriptors; suppress errors from handlers
            # that are already closed or non-closable.
            with contextlib.suppress(Exception):
                handler.close()

    root_logger.setLevel(level)
    root_logger.propagate = propagate

    # Pick the console destination; stdout by default so logs interleave with
    # normal program output, stderr when the caller wants them out of the way.
    stream = sys.stdout if stdout else sys.stderr
    console_handler = logging.StreamHandler(stream)
    console_handler.setLevel(level)

    # Only colorize when the user allows it AND the sink can render ANSI —
    # either a real TTY or a notebook front-end.
    enable_colors = use_colors and (_supports_ansi(stream) or _running_in_notebook())

    console_formatter = _ColorFormatter(
        fmt=log_format,
        datefmt=date_format,
        use_colors=enable_colors,
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Optional second sink: a UTF-8 log file that never carries color codes.
    if filename is not None:
        log_path = Path(filename)
        # Create any missing parent directories so the caller need not pre-make them.
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        # Deliberately a plain ``Formatter`` (no colors) — ANSI codes in a file
        # are noise when grepping later.
        file_formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Route ``warnings.warn(...)`` through logging so nothing bypasses our sinks.
    logging.captureWarnings(capture_warnings)

    return root_logger


# ---------------------------------------------------------------------------
#  Convenience helpers – thin wrappers around the root logger
# ---------------------------------------------------------------------------


def debug(msg: str, *args: Any, **kwargs: Any) -> None:
    """Log a message at DEBUG level via the root logger.

    Parameters
    ----------
    msg : str
        The (possibly %-style) message template.
    *args : Any
        Positional interpolation arguments forwarded to ``logging.debug``.
    **kwargs : Any
        Keyword options (e.g. ``exc_info``) forwarded to ``logging.debug``.
    """
    # Thin passthrough so callers get lazy %-formatting for free.
    logging.debug(msg, *args, **kwargs)


def info(msg: str, *args: Any, **kwargs: Any) -> None:
    """Log a message at INFO level via the root logger.

    Parameters
    ----------
    msg : str
        The (possibly %-style) message template.
    *args : Any
        Positional interpolation arguments forwarded to ``logging.info``.
    **kwargs : Any
        Keyword options forwarded to ``logging.info``.
    """
    logging.info(msg, *args, **kwargs)


def warning(msg: str, *args: Any, **kwargs: Any) -> None:
    """Log a message at WARNING level via the root logger.

    Parameters
    ----------
    msg : str
        The (possibly %-style) message template.
    *args : Any
        Positional interpolation arguments forwarded to ``logging.warning``.
    **kwargs : Any
        Keyword options forwarded to ``logging.warning``.
    """
    logging.warning(msg, *args, **kwargs)


def error(msg: str, *args: Any, **kwargs: Any) -> None:
    """Log a message at ERROR level via the root logger.

    Note: this is a non-raising logger call. It will *not* terminate the
    program. Use :func:`check` (assertion-style) or raise an exception
    explicitly if you need failure semantics.

    Parameters
    ----------
    msg : str
        The (possibly %-style) message template.
    *args : Any
        Positional interpolation arguments forwarded to ``logging.error``.
    **kwargs : Any
        Keyword options forwarded to ``logging.error``.
    """
    logging.error(msg, *args, **kwargs)


def critical(msg: str, *args: Any, **kwargs: Any) -> None:
    """Log a message at CRITICAL level via the root logger.

    Parameters
    ----------
    msg : str
        The (possibly %-style) message template.
    *args : Any
        Positional interpolation arguments forwarded to ``logging.critical``.
    **kwargs : Any
        Keyword options forwarded to ``logging.critical``.
    """
    logging.critical(msg, *args, **kwargs)


def check(condition: bool, msg: str = "Assertion failed") -> None:
    """Assert a condition, logging an error and raising if it fails.

    Parameters
    ----------
    condition : bool
        The predicate that must hold.
    msg : str, optional
        Message logged and attached to the raised error on failure.

    Raises
    ------
    AssertionError
        If ``condition`` is falsy.
    """
    # Unlike ``error``, this variant DOES stop the program — we log first so
    # the failure is captured by every sink, then raise for control flow.
    if not condition:
        logging.error(msg)
        raise AssertionError(msg)


_INT_TO_LEVEL: Final[dict[int, int]] = {
    2: logging.DEBUG,
    1: logging.INFO,
    0: logging.WARNING,
    -1: logging.ERROR,
    -2: logging.CRITICAL,
}

_LEVEL_TO_INT: Final[dict[int, int]] = {
    logging.DEBUG: 2,
    logging.INFO: 1,
    logging.WARNING: 0,
    logging.ERROR: -1,
    logging.CRITICAL: -2,
}


def verbosity(level: int | None = None) -> int:
    """Get or set the current root logger verbosity.

    Called with no argument, returns the current verbosity as an integer.
    Called with an integer, updates the root logger (and its existing
    handlers) accordingly and returns the new effective verbosity.

    Mapping (higher = more verbose):

    - ``>= 2`` → DEBUG
    - ``1`` → INFO
    - ``0`` → WARNING
    - ``-1`` → ERROR
    - ``<= -2`` → CRITICAL

    Values outside ``[-2, 2]`` are clamped (e.g. ``verbosity(3)`` is
    treated as DEBUG, matching the convenience usage shown in the README).

    Parameters
    ----------
    level : int | None, optional
        New verbosity level to apply, or None to just read the current value.

    Returns
    -------
    int
        Current (post-update, when setting) verbosity as an integer in the
        range ``[-2, 2]``.

    Examples
    --------
    >>> verbosity(2)   # turn on DEBUG-level logging
    2
    >>> verbosity()    # read current level
    2
    """
    root = logging.getLogger()

    # Setter branch: translate the friendly integer scale into a logging level.
    if level is not None:
        # Clamp out-of-range values to the extremes so ``verbosity(3)`` still
        # means "maximum detail" rather than raising a KeyError.
        if level >= 2:
            target = logging.DEBUG
        elif level <= -2:
            target = logging.CRITICAL
        else:
            target = _INT_TO_LEVEL[level]
        root.setLevel(target)
        # Handlers have their own thresholds; update them too or the new level
        # would be silently filtered at the handler stage.
        for handler in root.handlers:
            handler.setLevel(target)

    # Getter/return: map the effective level back to the integer scale,
    # defaulting to 0 (WARNING) for any unmapped custom level.
    return _LEVEL_TO_INT.get(root.getEffectiveLevel(), 0)
