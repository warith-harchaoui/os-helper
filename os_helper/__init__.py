"""
OS Helper

This package provides a collection of utility functions aimed at simplifying various common programming tasks, including:
- File handling
- System operations
- String manipulation
- Folder management
- Hashing
- URL validation

Authors:
 - Warith Harchaoui, https://harchaoui.org/warith
 - Mohamed Chelali, https://mchelali.github.io
 - Bachir Zerroug, https://www.linkedin.com/in/bachirzerroug
"""

# Re-export everything you want at the top level. 
# We'll assume you’ve moved your functions into multiple modules like this:

from .logging_utils import (
    verbosity,
    error,
    info,
    check,
    tic,
    toc,
)

from .system_utils import (
    windows,
    linux,
    macos,
    unix,
    get_nb_workers,
    system,
    openfile,
    getpid,
)

from .temp_utils import (
    temporary_filename,
    temporary_folder,
)

from .path_utils import (
    file_exists,
    dir_exists,
    absolute2relative_path,
    relative2absolute_path,
    path_without_home,
    recursive_glob,
    os_path_constructor,
    size_file,
    checkfile,
    copyfile,
    remove_directory,
    remove_files,
    make_directory,
    join,
    folder_name_ext,
)

from .hash_utils import (
    hash_string,
    hashfile,
    hashfolder,
)


from .config_utils import (
    get_config,
)

from .string_utils import (
    emptystring,
    asciistring,
)

from .misc_utils import (
    now_string,
    format_size,
    folder_description,
    is_working_url,
    zip_folder,
    download_file,
    time2str,
    str2time,
)

# If you don’t have a main.py (or if everything is distributed among the modules above),
# then just import from those modules directly.

__all__ = [
    # logging_utils
    "verbosity",
    "error",
    "info",
    "check",
    "tic",
    "toc",

    # system_utils
    "windows",
    "linux",
    "macos",
    "unix",
    "get_nb_workers",
    "system",
    "openfile",
    "getpid",

    # temp_utils
    "temporary_filename",
    "temporary_folder",

    # path_utils
    "file_exists",
    "dir_exists",
    "absolute2relative_path",
    "relative2absolute_path",
    "path_without_home",
    "recursive_glob",
    "os_path_constructor",
    "size_file",
    "checkfile",
    "copyfile",
    "remove_directory",
    "remove_files",
    "make_directory",
    "join",

    # hash_utils
    "hash_string",
    "hashfile",
    "hashfolder",

    # config_utils
    "valid_config_file",
    "get_config",

    # string_utils
    "emptystring",
    "asciistring",
    "time2str",
    "str2time",

    # main (or wherever you place these if not in main.py)
    "now_string",
    "format_size",
    "folder_description",
    "folder_name_ext",
    "is_working_url",
    "zip_folder",
    "download_file",
]
