"""
System Utilities

Cross-platform helpers for operating-system detection, worker-count
resolution, executing external commands, and opening files in the system
default application.

Author:
- Warith HARCHAOUI, https://linkedin.com/in/warith-harchaoui
"""

# Postpone annotation evaluation so ``str | None`` style unions work on every
# supported interpreter and never cost anything at import time.
from __future__ import annotations

import os
import platform
import shlex

# We use ``Popen`` directly (rather than ``subprocess.run``) so callers get
# both captured stdout and stderr back as a dict without extra plumbing.
from subprocess import PIPE, Popen

from .logging_utils import info
from .path_utils import dir_exists, file_exists
from .string_utils import emptystring


def windows() -> bool:
    """
    Determine if the current operating system is Windows.

    Returns
    -------
    bool
        True if the operating system is Windows, False otherwise.
    """
    # ``platform.system()`` returns "Windows"; lower-casing makes the check
    # robust against any casing quirk across Python builds.
    return platform.system().lower().startswith("win")


def linux() -> bool:
    """
    Determine if the current operating system is Linux.

    Returns
    -------
    bool
        True if the operating system is Linux, False otherwise.
    """
    # Linux reports "Linux"; the prefix match tolerates any suffix variants.
    return platform.system().lower().startswith("linux")


def macos() -> bool:
    """
    Determine if the current operating system is macOS.

    Returns
    -------
    bool
        True if the operating system is macOS, False otherwise.
    """
    # macOS identifies itself as "Darwin" (the kernel), not "macOS".
    return platform.system().lower().startswith("darwin")


def unix() -> bool:
    """
    Determine if the current operating system is Unix-based (Linux or macOS).

    Returns
    -------
    bool
        True if the operating system is Unix-based (Linux or macOS), False otherwise.
    """
    # "Unix-like" here means the POSIX pair we support; both share the same
    # ``xdg-open``/``open`` and forking behaviour the rest of the module relies on.
    return linux() or macos()


def get_nb_workers(workers: int = -1) -> int:
    """
    Resolve a worker count, following scikit-learn's ``n_jobs`` convention.

    The default pool size is ``os.cpu_count()`` (or 1 if that returns None),
    overridable via the ``NB_WORKERS`` environment variable.

    Parameters
    ----------
    workers : int, optional
        - ``0``  : use the full pool size.
        - ``> 0``: use exactly that many workers.
        - ``< 0``: use ``pool_size + workers + 1`` (e.g. ``-1`` → all CPUs,
          ``-2`` → all but one), clamped to at least 1.

    Returns
    -------
    int
        The resolved worker count (always >= 1).

    Example
    -------
    >>> get_nb_workers()  # -1 → all available CPU cores
    4
    """
    # Start from the physical pool size; ``cpu_count`` may return None on
    # exotic platforms, so fall back to a single worker.
    nb_workers = os.cpu_count() or 1
    # Allow ops to override the detected count via the environment (handy in
    # containers where the visible CPU count lies about the real quota).
    if "NB_WORKERS" in os.environ:
        try:
            nb_workers = int(os.environ["NB_WORKERS"])
        except ValueError:
            # A malformed value must not crash the caller — warn and keep the
            # auto-detected default instead.
            info("NB_WORKERS environment variable is invalid. Using default CPU count.")

    # ``0`` is the explicit "use the whole pool" request.
    if workers == 0:
        return nb_workers
    # A positive value is taken literally as an exact worker count.
    if workers > 0:
        return workers

    # Negative values count down from the pool (sklearn ``n_jobs`` convention):
    # -1 → all cores, -2 → all but one, ... never dropping below a single worker.
    return max(1, nb_workers + workers + 1)


def getpid() -> str:
    """
    Return the current process ID as a string.

    Returns
    -------
    str
        ``str(os.getpid())``.
    """
    return str(os.getpid())


def system(
    cmd: str,
    expected_output: str = "",
    check_exitcode: bool = True,
    check_empty: bool = False,
) -> dict:
    """
    Run a shell-style command via ``subprocess`` and capture its output.

    The command string is parsed with :func:`shlex.split` and executed without
    spawning an actual shell (``shell=False``), which avoids shell-injection
    pitfalls while still accepting a familiar command string.

    Parameters
    ----------
    cmd : str
        Command line to execute (e.g., ``"ffmpeg -i in.mp4 out.mp3"``).
    expected_output : str, optional
        If non-empty, a file or directory path expected to be present once
        the command completes successfully.
    check_exitcode : bool, optional
        If True, assert that the process exit code is 0.
    check_empty : bool, optional
        If True, also assert that ``expected_output`` is non-empty (file size
        > 0 / directory not empty).

    Returns
    -------
    dict
        ``{"out": <stdout as str>, "err": <stderr as str>}``.

    Raises
    ------
    AssertionError
        If the exit code check or the expected-output check fails.
    """
    info(f"Executing system command: {cmd}")

    # ``shlex.split`` turns the string into an argv list; combined with
    # ``shell=False`` below this sidesteps shell-injection entirely.
    args = shlex.split(cmd)
    proc = Popen(args, stdout=PIPE, stderr=PIPE, shell=False)
    # ``communicate`` blocks until completion and drains both pipes, avoiding
    # the classic deadlock where a full pipe buffer stalls the child.
    out_bytes, err_bytes = proc.communicate()

    # Decode leniently: external tools may emit non-UTF-8 bytes, and we would
    # rather surface replacement characters than raise mid-capture.
    out_str = out_bytes.decode("utf-8", errors="replace") if out_bytes else ""
    err_str = err_bytes.decode("utf-8", errors="replace") if err_bytes else ""

    # Optional hard gate on the process exit status.
    if check_exitcode:
        assert proc.returncode == 0, f"Command '{cmd}' failed with exit code {proc.returncode}"

    # When the caller names an expected artefact, verify it actually landed on
    # disk (as a file or a directory) before declaring success.
    if not emptystring(expected_output) and not (
        file_exists(expected_output, check_empty=check_empty)
        or dir_exists(expected_output, check_empty=check_empty)
    ):
        raise AssertionError(f"Expected output '{expected_output}' does not exist or is empty.")

    return {"out": out_str, "err": err_str}


def openfile(filename: str) -> None:
    """
    Open a file in the platform's default application.

    Uses ``os.startfile`` on Windows, ``open`` on macOS, and ``xdg-open`` on
    Linux. Exceptions from the underlying call are propagated as-is so the
    caller can react to them.

    Parameters
    ----------
    filename : str
        The path to the file to open.

    Raises
    ------
    OSError
        If the platform is unsupported or the underlying open call fails.
    """
    info(f"Opening file '{filename}' with default application.")

    # Windows has a dedicated stdlib call; it needs no external launcher.
    if windows():
        os.startfile(filename)
        return

    # POSIX platforms shell out to their conventional opener.
    if macos():
        cmd = "open"
    elif linux():
        cmd = "xdg-open"
    else:
        # Anything else (e.g. a BSD we do not special-case) is unsupported.
        raise OSError("Unsupported operating system for openfile().")

    # ``shlex.quote`` protects paths containing spaces or shell metacharacters.
    system(f"{cmd} {shlex.quote(filename)}", check_exitcode=True)
