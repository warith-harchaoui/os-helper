"""
OS Helper

A collection of cross-platform utility functions covering:
- file and directory handling
- system / OS detection and process helpers
- string manipulation and ASCII normalization
- temporary files and folders (including remote staging)
- hashing of strings, files, and folders
- configuration loading (JSON / YAML / .env / environment)
- URL checks, downloads, zipping
- logging and verbosity helpers

Usage Example
-------------
>>> import os_helper as osh
>>> osh.verbosity(1)
>>> if osh.unix():
...     osh.info("running on a Unix-based OS")
>>> osh.info(osh.now_string("filename"))
>>> h = osh.hash_string("hello", size=8)

The same helpers are also exposed as an argparse CLI (``os-helper``) and a
click CLI (``os-helper-click``, install ``[cli]`` extra). See the README
and ``GUI.md`` for the multi-surface story.

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

__author__ = "Warith Harchaoui, Ph.D."
__email__ = "warithmetics@deraison.ai"

from .config_utils import (
    get_config,
)
from .hash_utils import (
    hash_string,
    hashfile,
    hashfolder,
)
from .logging_utils import (
    check,
    critical,
    debug,
    error,
    info,
    init_logging,
    verbosity,
    warning,
)
from .misc_utils import (
    download_file,
    folder_description,
    format_size,
    get_user_ip,
    is_working_url,
    now_string,
    str2time,
    time2str,
    zip_folder,
)
from .path_utils import (
    absolute2relative_path,
    checkfile,
    copyfile,
    dir_exists,
    file_exists,
    folder_name_ext,
    join,
    make_directory,
    path_without_home,
    recursive_glob,
    relative2absolute_path,
    remove_directory,
    remove_files,
    size_file,
)
from .profile_utils import (
    cpu_timer,
    gpu_timer,
    tic,
    toc,
    wall_timer,
)
from .string_utils import (
    asciistring,
    emptystring,
)
from .system_utils import (
    get_nb_workers,
    getpid,
    linux,
    macos,
    openfile,
    system,
    unix,
    windows,
)
from .temp_utils import (
    temporary_filename,
    temporary_folder,
    temporary_remote_file,
)

__all__ = [
    # system_utils
    "windows",
    "linux",
    "macos",
    "unix",
    "get_nb_workers",
    "system",
    "openfile",
    "getpid",
    # logging_utils
    "init_logging",
    "debug",
    "info",
    "warning",
    "error",
    "critical",
    "check",
    "verbosity",
    # temp_utils
    "temporary_filename",
    "temporary_folder",
    "temporary_remote_file",
    # path_utils
    "file_exists",
    "dir_exists",
    "absolute2relative_path",
    "relative2absolute_path",
    "path_without_home",
    "recursive_glob",
    "size_file",
    "checkfile",
    "copyfile",
    "remove_directory",
    "remove_files",
    "make_directory",
    "join",
    "folder_name_ext",
    # hash_utils
    "hash_string",
    "hashfile",
    "hashfolder",
    # config_utils
    "get_config",
    # string_utils
    "emptystring",
    "asciistring",
    # misc_utils
    "now_string",
    "format_size",
    "folder_description",
    "is_working_url",
    "zip_folder",
    "download_file",
    "time2str",
    "str2time",
    "get_user_ip",
    # profile_utils
    "wall_timer",
    "cpu_timer",
    "gpu_timer",
    "tic",
    "toc",
]
