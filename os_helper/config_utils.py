"""
Configuration Utilities

Load and validate configuration settings from multiple sources with a
deterministic fallback order:
1. an explicit JSON or YAML file (or the first valid one in a folder),
2. one or more ``.env`` files merged into ``os.environ``,
3. plain environment variables.

The helpers verify that every required key is present and raise a clear
``RuntimeError`` when none of the sources can satisfy the request.

Author:
 - Warith HARCHAOUI, https://linkedin.com/in/warith-harchaoui
"""

# Defer annotation evaluation so ``dict | None`` unions parse on Python 3.10.
from __future__ import annotations

import glob
import json
import os

# PyYAML is loaded lazily-but-eagerly here because YAML is one of the two
# accepted on-disk config formats (the other being JSON).
import yaml
from dotenv import load_dotenv

from .logging_utils import error, info
from .path_utils import checkfile, dir_exists, file_exists, folder_name_ext, join
from .string_utils import emptystring


def _valid_config_file(a_path: str, keys: list[str], config_type: str) -> dict | None:
    """
    Check if a configuration file is valid by verifying it contains the required keys.

    This function loads a configuration file (in JSON or YAML format) and checks if it contains
    all the specified keys.

    You should not use it directly.

    Parameters
    ----------
    a_path : str
        The path to the configuration file.
    keys : List[str]
        List of keys that must be present in the configuration file.
    config_type : str
        The type of configuration (for logging purposes).

    Returns
    -------
    Optional[Dict]
        The loaded configuration dictionary if valid, otherwise None.

    Example
    -------
    >>> valid_config_file("config.yaml", ["host", "port"], "database")
    {'host': 'localhost', 'port': 5432}
    """
    # Fail early if the file is missing — the caller passed us a path it
    # believed existed, so a missing file is a hard error, not a soft miss.
    checkfile(a_path, f"Configuration file for {config_type} does not exist: {a_path}")

    # Dispatch on the file extension to pick the right parser.
    _, _, ext = folder_name_ext(a_path)
    ext = ext.lower()

    config = None
    with open(a_path) as fin:
        # JSON and YAML are the only two supported on-disk formats.
        if "json" in ext:
            config = json.load(fin)
        elif any(e in ext for e in ["yaml", "yml"]):
            # ``SafeLoader`` refuses arbitrary object construction — never load
            # untrusted YAML with the full loader.
            config = yaml.load(fin, Loader=yaml.SafeLoader)

    # An unrecognized extension leaves ``config`` as None: treat it as a soft
    # miss so the caller can fall through to the next config source.
    if config is None:
        info(f"Unsupported configuration file format {ext}: {a_path}")
        return None

    # A file only counts as valid when it satisfies EVERY required key.
    if all(key in config for key in keys):
        info(f"Configuration '{config_type}' successfully loaded from '{a_path}'")
        return config
    else:
        # Otherwise report exactly which keys are missing to aid debugging.
        missing = [key for key in keys if key not in config]
        m = ", ".join(missing)
        info(f"Configuration file '{a_path}' does not have all keys. Missing keys are {m}")

    return None


def _config_from_env(keys: list[str]) -> dict[str, str | int | float] | None:
    """
    Extract configuration from system environment variables.

    You should not use it directly.

    Parameters
    ----------
    keys : List[str]
        Keys to retrieve from the environment.

    Returns
    -------
    Optional[Dict[str, Union[str, int, float]]]
        A dictionary of key-value pairs if all keys are found, otherwise None.
    """
    config = {}
    missing_keys = []
    for key in keys:
        cap_key = key.upper()
        # Environment variables are conventionally UPPER_CASE, so try that
        # spelling first...
        if cap_key in os.environ:
            config[key] = os.environ[cap_key]
        # ...then fall back to the exact-case key for callers who set it verbatim.
        elif key in os.environ:
            config[key] = os.environ[key]
        else:
            # Track misses so we can report all of them at once below.
            missing_keys.append(key)
    # Only a fully-satisfied key set counts as a successful environment load.
    if len(missing_keys) == 0:
        return config

    # Partial matches are treated as a miss so the caller can try another source.
    m = ", ".join(missing_keys)
    info(f"Missing keys in environment variables: {m}")
    return None


def get_config(
    keys: list[str],
    config_type: str,
    path: str | None = None,
    env_files: list[str] | None = None,
) -> dict[str, str | int | float]:
    """
    Load configuration settings using a fixed fallback order.

    Precedence (first match wins):
    1. ``path`` pointing to a JSON/YAML file (or, if a directory, the first
       ``.json``, ``.yaml`` or ``.yml`` file in it that contains all keys);
    2. one or more ``.env`` files merged into ``os.environ``;
    3. the current process environment.

    Parameters
    ----------
    keys : List[str]
        Keys required to be present in the resolved configuration.
    config_type : str
        Human-readable label used only in log messages.
    path : Optional[str], optional
        Path to a configuration file or a directory containing one. If None
        or empty, this step is skipped.
    env_files : Optional[List[str]], optional
        ``.env`` files to load into ``os.environ`` before reading variables.
        Defaults to ``[".env"]``.

    Returns
    -------
    Dict[str, Union[str, int, float]]
        Mapping with one entry per requested key.

    Raises
    ------
    RuntimeError
        If none of the sources provide all required keys.

    Example
    -------
    >>> config = get_config(["host", "port"], "database", path="config.yaml")
    >>> config
    {'host': 'localhost', 'port': 5432}
    """

    if env_files is None:
        env_files = [".env"]

    # Step 1: Attempt to load from a specific file or folder if `path` is provided
    info(f"Loading configuration for '{config_type}'")
    config = None
    if not emptystring(path):
        if file_exists(path):
            config = _valid_config_file(path, keys, config_type)
            if config is not None:
                info(f"Configuration '{config_type}' loaded from file: {path}")
                return config
        if dir_exists(path):
            ext = ["json", "yaml", "yml"]
            candidates = []
            for e in ext:
                candidates.extend(glob.glob(join(path, f"*.{e}")))
            candidates = sorted(candidates)
            for candidate_path in candidates:
                config = _valid_config_file(candidate_path, keys, config_type)
                if config is not None:
                    info(f"Configuration '{config_type}' loaded from file: {candidate_path}")
                    return config
        info(f"No valid configuration found in path: {path}")

    # Step 2: Merge all .env files into os.environ
    info("Loading configuration from env files")
    for env_file in env_files:
        if file_exists(env_file):
            load_dotenv(env_file)
            info(f"Loaded env file: {env_file}")

    # Step 3: Check os.environ for required keys
    info("Loading configuration from environment variables (possibly merged with .env files)")
    config = _config_from_env(keys)
    if config is not None:
        info(f"Configuration '{config_type}' successfully loaded from environment variables.")
        return config

    # Step 4: Raise if no configuration was found
    msg = (
        f"Missing required keys for '{config_type}' configuration "
        f"in files, .env files, or environment variables."
    )
    error(msg)
    raise RuntimeError(msg)
