# config_utils.py

"""
Configuration Utilities

This module provides helper functions for loading and validating configuration settings
from various sources, including JSON/YAML files, .env files, and environment variables.
It ensures that required configuration keys are present and facilitates flexible configuration
management for your application.

Authors:
 - Warith Harchaoui, https://harchaoui.org/warith
 - Mohamed Chelali, https://mchelali.github.io
 - Bachir Zerroug, https://www.linkedin.com/in/bachirzerroug
"""

import os
import json
import glob
import re
from typing import List, Dict, Optional, Union

import yaml
from dotenv import load_dotenv

# Importing necessary functions from other utility modules
from .logging_utils import info, error, check
from .path_utils import file_exists, dir_exists, join, checkfile, folder_name_ext
from .string_utils import emptystring

def valid_config_file(a_path: str, keys: List[str], config_type: str) -> Optional[Dict]:
    """
    Check if a configuration file is valid by verifying it contains the required keys.

    This function loads a configuration file (in JSON or YAML format) and checks if it contains 
    all the specified keys.

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
    checkfile(f"Configuration file for {config_type} does not exist: {a_path}")
    
    _, _, ext = folder_name_ext(a_path)
    ext = ext.lower()

    config = None
    with open(a_path, "r") as fin:
        if "json" in ext:
            config = json.load(fin)
        elif any([e in ext for e in ["yaml", "yml"]]):
            config = yaml.load(fin, Loader=yaml.SafeLoader)
    
    if config is None:
        info(f"Unsupported configuration file format {ext}: {a_path}")
        return None

    if all(key in config for key in keys):
        info(f"Configuration '{config_type}' successfully loaded from '{a_path}'")
        return config
    else:
        missing = [key for key in keys if key not in config]
        m = ", ".join(missing)
        info(f"Configuration file '{a_path}' does not have all keys. Missing keys are {m}")
    
    return None

def get_config(
    keys: List[str],
    config_type: str,
    path: Optional[str] = None,
    env_files: List[str] = [".env"]
) -> Dict[str, Union[str, int, float]]:
    """
    Load configuration settings with a fallback approach with this decreasing order of precedence (ignoring the others if successful): 
        1. JSON/YAML files
        2. .env files 
        3. environment variables.
    but 2 and 3 are merged into os.environ.

    Parameters
    ----------
    keys : List[str]
        List of keys that must be present in the configuration file or environment.
    config_type : str
        The type of configuration (mandatory for logging purposes).
    path : Optional[str], optional
        The path to a specific configuration file or folder containing configuration files. If None, then config. Defaults to None.
    env_files : List[str], optional
        List of .env files to check for configuration. Defaults to [".env"].

    Returns
    -------
    Dict[str, Union[str, int, float]]
        The loaded configuration dictionary with keys and their associated values.

    Raises
    ------
    SystemExit
        If required configuration keys are missing in all sources.

    Example
    -------
    >>> config = get_config(["host", "port"], "database", path="config.yaml")
    >>> config
    {'host': 'localhost', 'port': 5432}
    """
    def config_from_env(keys: List[str]) -> Optional[Dict[str, Union[str, int, float]]]:
        """
        Extract configuration from system environment variables.

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
            # capitals case
            if cap_key in os.environ:
                config[key] = os.environ[cap_key]
            # lowercase case
            elif key in os.environ:
                config[key] = os.environ[key]
            else:
                missing_keys.append(key)
        if len(missing_keys) == 0:
            return config
        
        m = ", ".join(missing_keys)
        info(f"Missing keys in environment variables: {m}")
        return None

    def config_from_files(path: str, keys: List[str]) -> Optional[Dict[str, Union[str, int, float]]]:
        """
        Extract configuration from JSON or YAML files.

        Parameters
        ----------
        path : str
            Path to a specific file or folder containing configuration files.
        keys : List[str]
            Keys to retrieve from the configuration file.

        Returns
        -------
        Optional[Dict[str, Union[str, int, float]]]
            A dictionary of key-value pairs if all keys are found, otherwise None.
        """
        if file_exists(path):
            config = valid_config_file(path, keys, config_type=config_type)
            if config:
                return config

        if dir_exists(path):
            # Search for all JSON and YAML files in the directory
            formats = ["*.json", "*.yaml", "*.yml"]
            formats += [f"*.{fmt.upper()}" for fmt in formats]
            candidates = []
            for fmt in formats:
                candidates.extend(glob.glob(join(path, fmt)))
            
            candidates = sorted(candidates)

            for candidate in candidates:
                config = valid_config_file(candidate, keys, config_type=config_type)
                if config:
                    return config
        return None

    # Step 1: Attempt to load from a specific file or folder if `path` is provided
    info(f"Loading configuration for '{config_type}'")
    if not emptystring(path):
        config = config_from_files(path, keys)
        if config:
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
    config = config_from_env(keys)
    if config:
        info(f"Configuration '{config_type}' successfully loaded from environment variables.")
        return config

    # Step 4: Raise an error if no configuration was found
    error(f"Missing required keys for '{config_type}' configuration in files, .env files, or environment variables.")
