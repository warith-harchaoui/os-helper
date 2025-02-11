"""
System Utilities

This module provides various system-related functions, such as OS detection,
worker count retrieval, running external commands, and opening files with
the system's default application.

Authors:
- Warith Harchaoui, https://harchaoui.org/warith
- Mohamed Chelali, https://mchelali.github.io
- Bachir Zerroug, https://www.linkedin.com/in/bachirzerroug
"""

import logging
import os
import platform
import shlex
from subprocess import PIPE, Popen
import sys

# Assuming these come from your other utility modules:
from .path_utils import file_exists, dir_exists


def init_logging(
    stdout: bool = True,
    immediate_flush: bool = True,
    format: str = "%(asctime)s - %(levelname)s - %(message)s",
    level: int = logging.DEBUG,
    file: str = None,
):
    """Initialize global logging configuration.

    This function configures logging globally with the specified log level and output options.
    Messages are formatted with timestamp, level, and content.

    Parameters
    ----------
    stdout : bool, optional
        Whether to output logs to stdout (True) or stderr (False), by default True.
    immediate_flush : bool, optional
        Whether to flush log messages immediately, by default True.
    format : str, optional
        Format string for log messages, by default "%(asctime)s - %(levelname)s - %(message)s".
    level : int, optional
        Log level, by default logging.DEBUG.
    file : str, optional
        If provided, log messages will also be written to this file.
    """
    handlers = []
    
    # Add console handler
    stream = sys.stdout if stdout else sys.stderr
    handlers.append(logging.StreamHandler(stream))
    
    # Add file handler if needed
    if file:
        handlers.append(logging.FileHandler(file))

    if not logging.getLogger().hasHandlers():  # Avoid duplicate handlers
        logging.basicConfig(
            level=level,
            format=format,
            handlers=handlers,
            force=True,  # Ensure reconfiguration if logging is already set
        )

    # Ensure immediate flush if required
    if immediate_flush:
        logger = logging.getLogger()
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.flush()



def windows() -> bool:
    """
    Determine if the current operating system is Windows.

    Returns
    -------
    bool
        True if the operating system is Windows, False otherwise.
    """
    return platform.lower().startswith("win")


def linux() -> bool:
    """
    Determine if the current operating system is Linux.

    Returns
    -------
    bool
        True if the operating system is Linux, False otherwise.
    """
    return platform.lower().startswith("linux")


def macos() -> bool:
    """
    Determine if the current operating system is macOS.

    Returns
    -------
    bool
        True if the operating system is macOS, False otherwise.
    """
    return platform.lower().startswith("darwin")


def unix() -> bool:
    """
    Determine if the current operating system is Unix-based (Linux or macOS).

    Returns
    -------
    bool
        True if the operating system is Unix-based (Linux or macOS), False otherwise.
    """
    return linux() or macos()


def get_nb_workers(workers:int = -1) -> int:
    """
    Retrieve or ser the number of workers to use for parallel processing.
    
    Parameters
    ----------
    workers : int, optional
        The number of workers to use. If set to 0, the function will use the number of CPUs
        available on the system. If set to a positive integer, it will use that number of workers.
        If set to a negative integer, it will use the number of CPUs minus that integer. Defaults to -1.
        (following scikit-learn's convention)
        
    Returns
    -------
    int
        The number of workers to use.
        
    Example
    -------
    >>> get_nb_workers()  # Retrieve the number of workers
    4 # corresponding to the number of CPU cores available on the system
    """
    nb_workers = os.cpu_count() or 1  # Fallback to 1 if somehow os.cpu_count() is None
    if "NB_WORKERS" in os.environ:
        try:
            nb_workers = int(os.environ["NB_WORKERS"])
        except ValueError:
            logging.info("NB_WORKERS environment variable is invalid. Using default CPU count.")
        
    if workers == 0:
        return nb_workers
    elif workers > 0:
        return workers
    
    # else workers < 0

    w = max(1, nb_workers + workers + 1)
    return w

# TODO: remove
def getpid() -> str:
    """
    Get the process ID of the current Python process.

    Returns
    -------
    str
        The process ID as a string.
    """
    return str(os.getpid())

def system(
    cmd: str,
    expected_output: str = "",
    check_exitcode: bool = True,
    check_empty: bool = False
) -> dict:
    """
    Run a system command and return its output.

    Parameters
    ----------
    cmd : str
        The system command to run.
    expected_output : str, optional
        Expected output file or directory. If provided, checks for its existence
        after the command runs. Defaults to "".
    check_exitcode : bool, optional
        If True, checks that the command returns a zero exit code. Defaults to True.
    check_empty : bool, optional
        If True, checks if the expected output is not empty. Defaults to False.

    Returns
    -------
    dict
        A dictionary with the command's standard output ('out') and error messages ('err').

    Raises
    ------
    AssertionError
        If the command fails (non-zero exit code) or if the expected output
        does not exist or is empty (depending on `check_empty`).
    """
    logging.info(f"Executing system command: {cmd}")
    
    args = shlex.split(cmd)
    proc = Popen(args, stdout=PIPE, stderr=PIPE, shell=False)
    out_bytes, err_bytes = proc.communicate()

    out_str = out_bytes.decode("utf-8", errors="replace") if out_bytes else ""
    err_str = err_bytes.decode("utf-8", errors="replace") if err_bytes else ""

    # Check exit code
    if check_exitcode:
        assert proc.returncode == 0, f"Command '{cmd}' failed with exit code {proc.returncode}"

    # Check for expected output presence (and optionally non-emptiness)
    if expected_output:
        # Either a file or directory. If it doesn't exist or is empty, raise error
        if not (file_exists(expected_output, check_empty=check_empty) or 
                dir_exists(expected_output, check_empty=check_empty)):
            raise AssertionError(f"Expected output '{expected_output}' does not exist or is empty.")

    return {"out": out_str, "err": err_str}


def openfile(filename: str) -> None:
    """
    Open a file with the default application based on the operating system.

    Parameters
    ----------
    filename : str
        The path to the file to open.

    Raises
    ------
    OSError
        If there's an error opening the file with the system's default application.
    """
    logging.info(f"Opening file '{filename}' with default application.")
    
    try:
        if windows():
            os.startfile(filename)
            return
            
        if macos():
            cmd = "open"

        if linux():
            cmd = "xdg-open"
        
        system(f"{cmd} {filename}", check_exitcode=True)
        
    except Exception as e:
        raise SystemExit(f"Failed to open file '{filename}': System OS is not supported.")
