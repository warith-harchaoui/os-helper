"""
Temporary Utilities

This module provides helper functions and context managers for creating and managing
temporary files and directories. It ensures that temporary resources are handled safely
and cleaned up appropriately after use.

Authors:
 - Warith Harchaoui, https://harchaoui.org/warith
 - Mohamed Chelali, https://mchelali.github.io
 - Bachir Zerroug, https://www.linkedin.com/in/bachirzerroug
"""

import tempfile
import hashlib
import os
import contextlib
from typing import Generator

# Importing necessary functions from other utility modules
from .logging_utils import info, error
from .path_utils import join, relative2absolute_path
from .misc_utils import now_string
from .hash_utils import hash_string


@contextlib.contextmanager
def temporary_filename(
    suffix: str = "",
    mode: str = "wt",
    prefix: str = "",
    delete: bool = True
) -> Generator[str, None, None]:
    """
    Create a temporary file with a unique name that persists even after closing.

    This context manager generates a temporary file with a unique name, which is
    optionally removed after use. It ensures that temporary files are managed
    safely and are cleaned up to prevent clutter or security issues.

    Parameters
    ----------
    suffix : str, optional
        File suffix (e.g., ".txt"). Defaults to "".
    mode : str, optional
        Mode in which the file is opened (e.g., "wt" for writing text).
        Defaults to "wt".
    prefix : str, optional
        Prefix for the file name. Defaults to "".
    delete : bool, optional
        Whether to delete the file after exiting the context. Defaults to True.

    Yields
    ------
    str
        The name of the temporary file.

    Example
    -------
    >>> with temporary_filename(suffix=".txt") as temp_file:
    ...     with open(temp_file, "wt") as fout:
    ...         fout.write("Temporary content")
    ...     # temp_file is automatically deleted after the block
    """
    try:
        # Ensure the suffix starts with a dot if provided
        suffix = suffix if suffix.startswith(".") else f".{suffix}"
        
        # Create a unique prefix using the current timestamp and a hash
        unique_prefix = f"{prefix}-{now_string('filename')}-" if prefix else ""
        unique_prefix += hash_string(now_string(), size=8)
        
        # Create the temporary file
        with tempfile.NamedTemporaryFile(
            mode=mode,
            suffix=suffix,
            prefix=unique_prefix,
            delete=not delete
        ) as tmp:
            temp_path = relative2absolute_path(tmp.name)
            info(f"Created temporary file: {temp_path}")
            yield temp_path
    except Exception as e:
        error(f"Failed to create temporary file: {e}")
    finally:
        if delete and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                info(f"Deleted temporary file: {temp_path}")
            except Exception as e:
                error(f"Failed to delete temporary file '{temp_path}': {e}")


@contextlib.contextmanager
def temporary_folder(prefix: str = "", delete: bool = True) -> Generator[str, None, None]:
    """
    Create a temporary directory with a unique name that persists during the context.

    This context manager generates a temporary directory with a unique name, which is
    optionally removed after use. It ensures that temporary directories are managed
    safely and are cleaned up to prevent clutter or security issues.

    Parameters
    ----------
    prefix : str, optional
        Prefix for the folder name. Defaults to "".
    delete : bool, optional
        Whether to delete the directory and its contents after exiting the context.
        Defaults to True.

    Yields
    ------
    str
        The name of the temporary directory.

    Example
    -------
    >>> with temporary_folder(prefix="tempdir") as temp_dir:
    ...     # Use the temporary directory
    ...     with open(os.path.join(temp_dir, "file.txt"), "w") as f:
    ...         f.write("Temporary content")
    ...     # temp_dir and its contents are automatically deleted after the block
    """
    try:
        # Create a unique prefix using the current timestamp and a hash
        unique_prefix = f"{prefix}-{now_string('filename')}-" if prefix else ""
        unique_prefix += hashlib.md5(now_string().encode()).hexdigest()[:8]
        
        # Create the temporary directory
        temp_dir = tempfile.mkdtemp(prefix=unique_prefix)
        temp_dir = relative2absolute_path(temp_dir)
        info(f"Created temporary directory: {temp_dir}")
        yield temp_dir
    except Exception as e:
        error(f"Failed to create temporary directory: {e}")
    finally:
        if delete and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
                info(f"Deleted temporary directory: {temp_dir}")
            except Exception as e:
                error(f"Failed to delete temporary directory '{temp_dir}': {e}")
