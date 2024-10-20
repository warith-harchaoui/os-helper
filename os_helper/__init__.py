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

__all__ = [
    "verbosity",
    "windows",
    "linux",
    "macos",
    "unix",
    "get_nb_workers",
    "emptystring",
    "now_string",
    "temporary_filename",
    "temporary_folder",
    "error",
    "info",
    "check",
    "file_exists",
    "dir_exists",
    "absolute2relative_path",
    "relative2absolute_path",
    "path_without_home",
    "recursive_glob",
    "os_path_constructor",
    "size_file",
    "checkfile",
    "getpid",
    "copyfile",
    "remove_directory",
    "remove_files",
    "make_directory",
    "system",
    "openfile",
    "hash_string",
    "hashfile",
    "hashfolder",
    "format_size",
    "folder_description",
    "folder_name_ext",
    "get_config",
    "is_working_url",
    "asciistring",
    "zip_folder",
    "time2str",
    "download_file",
    "tic",
    "toc",
]

# Import all the necessary functions from the main module
from .main import (
    verbosity,
    windows,
    linux,
    macos,
    unix,
    get_nb_workers,
    emptystring,
    now_string,
    temporary_filename,
    temporary_folder,
    error,
    info,
    check,
    file_exists,
    dir_exists,
    absolute2relative_path,
    relative2absolute_path,
    path_without_home,
    recursive_glob,
    os_path_constructor,
    size_file,
    checkfile,
    getpid,
    copyfile,
    remove_directory,
    remove_files,
    make_directory,
    system,
    openfile,
    hash_string,
    hashfile,
    hashfolder,
    format_size,
    folder_description,
    folder_name_ext,
    valid_config_file,
    get_config,
    is_working_url,
    asciistring,
    zip_folder,
    time2str,
    download_file,
    tic,
    toc,
)
