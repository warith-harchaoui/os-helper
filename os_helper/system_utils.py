"""
System Utilities

Cross-platform helpers for operating-system detection, worker-count
resolution, executing external commands, and opening files in the system
default application.

Author:
- Warith HARCHAOUI, https://linkedin.com/in/warith-harchaoui
"""

import os
import platform
import shlex
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
    return platform.system().lower().startswith("win")


def linux() -> bool:
    """
    Determine if the current operating system is Linux.

    Returns
    -------
    bool
        True if the operating system is Linux, False otherwise.
    """
    return platform.system().lower().startswith("linux")


def macos() -> bool:
    """
    Determine if the current operating system is macOS.

    Returns
    -------
    bool
        True if the operating system is macOS, False otherwise.
    """
    return platform.system().lower().startswith("darwin")


def unix() -> bool:
    """
    Determine if the current operating system is Unix-based (Linux or macOS).

    Returns
    -------
    bool
        True if the operating system is Unix-based (Linux or macOS), False otherwise.
    """
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
    nb_workers = os.cpu_count() or 1
    if "NB_WORKERS" in os.environ:
        try:
            nb_workers = int(os.environ["NB_WORKERS"])
        except ValueError:
            info("NB_WORKERS environment variable is invalid. Using default CPU count.")

    if workers == 0:
        return nb_workers
    if workers > 0:
        return workers

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

    args = shlex.split(cmd)
    proc = Popen(args, stdout=PIPE, stderr=PIPE, shell=False)
    out_bytes, err_bytes = proc.communicate()

    out_str = out_bytes.decode("utf-8", errors="replace") if out_bytes else ""
    err_str = err_bytes.decode("utf-8", errors="replace") if err_bytes else ""

    if check_exitcode:
        assert proc.returncode == 0, f"Command '{cmd}' failed with exit code {proc.returncode}"

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

    if windows():
        os.startfile(filename)
        return

    if macos():
        cmd = "open"
    elif linux():
        cmd = "xdg-open"
    else:
        raise OSError("Unsupported operating system for openfile().")

    system(f"{cmd} {shlex.quote(filename)}", check_exitcode=True)
