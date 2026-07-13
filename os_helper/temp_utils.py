"""
Temporary Utilities

This module provides helper functions and context managers for creating and managing
temporary files and directories. It ensures that temporary resources are handled safely
and cleaned up appropriately after use.

Author:
 - Warith HARCHAOUI, https://linkedin.com/in/warith-harchaoui
"""

import contextlib
import os
import shutil
import tempfile
from collections.abc import Callable, Generator

from .hash_utils import hash_string
from .logging_utils import error, info
from .misc_utils import now_string
from .path_utils import relative2absolute_path
from .string_utils import emptystring


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
    temp_path: str | None = None
    try:
        # Normalize the suffix: keep empty as-is, otherwise ensure a leading dot.
        if emptystring(suffix):
            suffix = ""
        elif not suffix.startswith("."):
            suffix = f".{suffix}"

        # Build a recognizable, collision-resistant prefix.
        unique_prefix = f"{prefix}-{now_string('filename')}-" if not emptystring(prefix) else ""
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
        raise
    finally:
        if delete and temp_path is not None and os.path.exists(temp_path):
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
    temp_dir: str | None = None
    try:
        # Build a recognizable, collision-resistant prefix without depending on
        # MD5 (consistent with `temporary_filename`).
        unique_prefix = f"{prefix}-{now_string('filename')}-" if not emptystring(prefix) else ""
        unique_prefix += hash_string(now_string(), size=8)

        temp_dir = tempfile.mkdtemp(prefix=unique_prefix)
        temp_dir = relative2absolute_path(temp_dir)
        info(f"Created temporary directory: {temp_dir}")
        yield temp_dir
    except Exception as e:
        error(f"Failed to create temporary directory: {e}")
        raise
    finally:
        if delete and temp_dir is not None and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                info(f"Deleted temporary directory: {temp_dir}")
            except Exception as e:
                error(f"Failed to delete temporary directory '{temp_dir}': {e}")


@contextlib.contextmanager
def temporary_remote_file(
    upload_function: Callable[[str], str],
    delete_function: Callable[[str], None],
    *,
    prefix: str = "",
    suffix: str = "",
    from_local_file: str | None = None,
    checkfile_function: Callable[[str], bool] | None = None,
    mode: str = "wb",
    initial_content: bytes | str | None = None,
) -> Generator[str, None, None]:
    """
    Context manager that uploads a file to a remote location and guarantees
    deletion of the remote artifact when the context exits.

    Two modes:

    - If ``from_local_file`` is given, that existing local file is uploaded
      as-is and left untouched on cleanup; only the remote copy is deleted.
    - Otherwise, a uniquely named local temp file is created (optionally
      pre-populated with ``initial_content``), uploaded, and removed locally
      when the context manager exits.

    Useful for staging files to S3/GCS/SFTP/anywhere when you only need them
    briefly: pass in the upload + delete callables for your storage backend
    and the helper handles the lifecycle.

    Parameters
    ----------
    upload_function : Callable[[str], str]
        Called with a local file path; must return the remote path/URI.
    delete_function : Callable[[str], None]
        Called with the remote path/URI to remove the remote artifact.
    prefix : str, optional
        Prefix for the temporary file name (ignored when ``from_local_file``
        is provided).
    suffix : str, optional
        File extension for the temporary file (with or without leading ".").
    from_local_file : str, optional
        Path to an existing local file to upload instead of creating one.
    checkfile_function : Callable[[str], bool], optional
        Optional post-upload sanity check; must return True for success.
    mode : str, optional
        Open mode used when writing ``initial_content`` to the temp file.
        Defaults to ``"wb"``.
    initial_content : bytes | str, optional
        Optional content written into the new temp file before upload. Type
        must match ``mode`` (bytes for ``"wb"``, str for ``"wt"``).

    Yields
    ------
    str
        The remote file path/URI returned by ``upload_function``.

    Raises
    ------
    TypeError
        If any supplied callable is not actually callable.
    FileNotFoundError
        If ``from_local_file`` is given but the path does not exist.
    RuntimeError
        If ``checkfile_function`` is provided and returns False after upload.

    Examples
    --------
    >>> storage = {}
    >>> def upload(p):
    ...     with open(p, "rb") as f: storage[p] = f.read()
    ...     return p
    >>> def delete(r):
    ...     storage.pop(r, None)
    >>> with temporary_remote_file(upload, delete, suffix=".bin",
    ...                            initial_content=b"hello") as remote:
    ...     assert storage[remote] == b"hello"
    >>> # remote artifact is gone after the block
    """
    if not callable(upload_function):
        raise TypeError("upload_function must be callable")
    if not callable(delete_function):
        raise TypeError("delete_function must be callable")
    if checkfile_function is not None and not callable(checkfile_function):
        raise TypeError("checkfile_function must be callable")

    sfx = "" if emptystring(suffix) else suffix
    if not emptystring(sfx) and not sfx.startswith("."):
        sfx = "." + sfx

    remote_file_path: str | None = None

    def _do_upload(local_path: str) -> str:
        nonlocal remote_file_path
        if not os.path.isfile(local_path):
            raise FileNotFoundError(f"Local file does not exist: {local_path}")
        # Capture the remote handle BEFORE the optional check so the finally
        # block can still clean up a remote artifact created by a successful
        # upload whose post-upload validation later failed.
        remote_file_path = upload_function(local_path)
        if checkfile_function is not None and not checkfile_function(remote_file_path):
            raise RuntimeError(f"Upload check failed for remote: {remote_file_path}")
        info(f"Uploaded '{local_path}' to remote '{remote_file_path}'")
        return remote_file_path

    try:
        if not emptystring(from_local_file):
            _do_upload(from_local_file)
            yield remote_file_path
        else:
            ts = now_string("filename")
            h = hash_string(f"{os.getpid()}-{ts}", size=8)
            unique_prefix = (
                f"{prefix}-{ts}-{h}-" if not emptystring(prefix) else f"{ts}-{h}-"
            )
            with temporary_filename(suffix=sfx, prefix=unique_prefix, mode=mode) as local_path:
                if initial_content is not None:
                    with open(local_path, mode=mode) as fout:
                        fout.write(initial_content)
                _do_upload(local_path)
                yield remote_file_path
    finally:
        if remote_file_path is not None:
            try:
                delete_function(remote_file_path)
                info(f"Deleted remote file: {remote_file_path}")
            except Exception as e:
                error(f"Failed to delete remote file '{remote_file_path}': {e}")
