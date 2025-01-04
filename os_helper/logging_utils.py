"""
Logging Utilities

This module provides helper functions and variables for controlling log levels,
logging messages, and error handling. It also includes an optional global verbosity
setting that can be used to manage logging detail at runtime.

Authors:
- Warith Harchaoui, https://harchaoui.org/warith
- Mohamed Chelali, https://mchelali.github.io
- Bachir Zerroug, https://www.linkedin.com/in/bachirzerroug
"""

import logging
import sys
import time

# A global verbosity level, modified by the `verbosity()` function
VERBOSITY_LEVEL = 1

def verbosity(level: int = None) -> int:
    """
    Set or retrieve the current verbosity level for logging.

    This function allows for dynamic adjustment of the verbosity level 
    of the logging system, enabling different levels of logging details 
    to be output (e.g., errors only, detailed debugging information, etc.).
    
    If no level is provided, it returns the current verbosity level.

    Parameters
    ----------
    level : int, optional
        The verbosity level to set (0: None, 1: Error, 2: Info, 3: Debug).
        If None, retrieves the current verbosity level. Defaults to None.

    Verbosity Levels:
    - 0: Disable all logging.
    - 1: Show only error messages.
    - 2: Show informational messages (default level).
    - 3: Show debugging messages (most detailed).

    Returns
    -------
    int
        The current verbosity level after setting it (if a new level was provided).

    Example
    -------
    >>> verbosity(2)  # Set verbosity to show info-level messages
    >>> verbosity()   # Retrieve the current verbosity level (2)
    """
    global VERBOSITY_LEVEL
    if level is not None:
        VERBOSITY_LEVEL = level
        logger = logging.getLogger()  # Root logger or your package logger
        if level == 0:
            # effectively disables all logging (including critical)
            logger.setLevel(logging.CRITICAL + 1)
        elif level == 1:
            logger.setLevel(logging.ERROR)
        elif level == 2:
            logger.setLevel(logging.INFO)
        elif level == 3:
            logger.setLevel(logging.DEBUG)
    return VERBOSITY_LEVEL


def error(msg: str, error_code: int = 1) -> None:
    """
    Log an error message and exit the program with a specified error code.

    Parameters
    ----------
    msg : str
        The error message to log.
    error_code : int, optional
        The exit code to use when terminating the program. Defaults to 1.

    Example
    -------
    >>> error("Critical failure", error_code=2)
    """
    logging.error(msg)
    raise SystemExit((error_code, msg))


def info(msg: str) -> None:
    """
    Log an informational message.

    Parameters
    ----------
    msg : str
        The message to log.

    Example
    -------
    >>> info("Process completed successfully.")
    """
    logging.info(msg)


def check(condition: bool, msg: str = "Something went wrong", error_code: int = 1) -> None:
    """
    Check a condition and log an error message (and exit) if it is not met.

    Parameters
    ----------
    condition : bool
        The condition to check. If False, logs the error message and exits.
    msg : str, optional
        The error message to log if the condition is not met. Defaults to "Something went wrong".
    error_code : int, optional
        The exit code to use if the condition fails. Defaults to 1.

    Example
    -------
    >>> check(1 == 2, msg="Condition failed", error_code=2)
    """
    if not condition:
        error(f"{msg} (error code: {error_code})")


def tic() -> float:
    """
    Start a timer and return current time (seconds since epoch).
    
    Returns
    -------
    float
        Current timestamp in seconds.
        
    Example
    -------
    (tic and toc)
    >>> start_time = tic()
    >>> time.sleep(5)
    >>> elapsed = toc(start_time)
    >>> print(f"Elapsed time: {elapsed:.2f} seconds")
    """
    return time.time()


def toc(start_time: float) -> float:
    """
    Return the elapsed time (in seconds) since 'start_time'.

    Parameters
    ----------
    start_time : float
        A timestamp obtained by calling tic().

    Returns
    -------
    float
        The elapsed time in seconds since 'start_time'.
    """
    return time.time() - start_time
