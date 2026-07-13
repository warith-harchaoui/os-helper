"""
OS Helper — argparse-based command-line interface.

Thin wrapper around the pure functions exported by :mod:`os_helper` that
exposes the toolkit as subcommands under a single ``os-helper`` entry
point. Written with :mod:`argparse` from the standard library so the CLI
works out of the box on any Python install that has the package
installed — no extra runtime dependency required.

The CLI is deliberately *additive*: it exists on top of the library API,
never replaces it. Every existing public function stays importable from
``os_helper`` unchanged; each subcommand here is a shell-friendly wrapper
that translates flags into keyword arguments.

Subcommand groups
-----------------
- ``os``      — operating-system detection (``system`` / ``unix`` /
                ``linux`` / ``macos`` / ``windows`` / ``pid`` /
                ``workers`` / ``run`` / ``open``)
- ``path``    — path predicates and helpers (``exists`` / ``dir-exists``
                / ``join`` / ``abs`` / ``rel`` / ``no-home`` /
                ``size`` / ``split`` / ``glob`` / ``mkdir`` /
                ``rmdir`` / ``rm`` / ``cp``)
- ``hash``    — hashing (``string`` / ``file`` / ``folder``)
- ``str``     — string utilities (``empty`` / ``ascii``)
- ``config``  — configuration loading (``get``)
- ``temp``    — temporary file helpers (``file`` / ``folder``)
- ``misc``    — misc utilities (``now`` / ``format-size`` / ``describe``
                / ``url-ok`` / ``zip`` / ``download`` / ``time2str`` /
                ``str2time`` / ``ip``)
- ``prof``    — profiling (``wall`` / ``cpu`` / ``gpu``)

Usage Example
-------------
>>> #   os-helper os system
>>> #   os-helper path exists ~/somefile.txt
>>> #   os-helper hash string hello --size 8
>>> #   os-helper hash file ./pyproject.toml
>>> #   os-helper misc now --fmt filename
>>> #   os-helper misc format-size 12345678
>>> #   os-helper temp folder --prefix demo
>>> #   os-helper prof wall -- sleep 0.1

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections.abc import Callable, Sequence

# Import the pure functions once here — every handler is a thin dispatch
# on top of these, no logic duplication with the library.
from . import (
    absolute2relative_path,
    asciistring,
    checkfile,
    copyfile,
    dir_exists,
    download_file,
    emptystring,
    file_exists,
    folder_description,
    folder_name_ext,
    format_size,
    get_config,
    get_nb_workers,
    get_user_ip,
    getpid,
    hash_string,
    hashfile,
    hashfolder,
    is_working_url,
    join,
    linux,
    macos,
    make_directory,
    now_string,
    openfile,
    path_without_home,
    recursive_glob,
    relative2absolute_path,
    remove_directory,
    remove_files,
    size_file,
    str2time,
    system,
    temporary_filename,
    temporary_folder,
    time2str,
    unix,
    windows,
    zip_folder,
)

# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------


def _echo_json(payload) -> None:
    # Structured outputs use JSON so shell pipelines can `| jq` on them.
    print(json.dumps(payload, indent=2, sort_keys=True))


# ---------------------------------------------------------------------------
# os — operating-system probes and process helpers
# ---------------------------------------------------------------------------


def _handle_os_system(_: argparse.Namespace) -> int:
    # `system` here refers to platform.system(); print a short name.
    if windows():
        print("windows")
    elif macos():
        print("macos")
    elif linux():
        print("linux")
    else:
        print("unknown")
    return 0


def _handle_os_flag(fn) -> Callable[[argparse.Namespace], int]:
    # Factory: build a handler that prints "true" / "false" for a bool probe.
    def _run(_: argparse.Namespace) -> int:
        print("true" if fn() else "false")
        return 0
    return _run


def _handle_os_pid(_: argparse.Namespace) -> int:
    print(getpid())
    return 0


def _handle_os_workers(ns: argparse.Namespace) -> int:
    # Mirrors sklearn's n_jobs convention.
    print(get_nb_workers(ns.n))
    return 0


def _handle_os_run(ns: argparse.Namespace) -> int:
    # Execute a shell-style command via os_helper.system() and print stdout.
    result = system(
        cmd=ns.cmd,
        expected_output=ns.expected or "",
        check_exitcode=not ns.no_check_exitcode,
        check_empty=ns.check_empty,
    )
    # Return the captured stdout verbatim; stderr goes to fd 2 so it can be
    # inspected but does not pollute the piped output.
    if result["out"]:
        sys.stdout.write(result["out"])
    if result["err"]:
        sys.stderr.write(result["err"])
    return 0


def _handle_os_open(ns: argparse.Namespace) -> int:
    # Open a file in the platform's default application.
    openfile(ns.path)
    return 0


# ---------------------------------------------------------------------------
# path — filesystem predicates and manipulations
# ---------------------------------------------------------------------------


def _handle_path_exists(ns: argparse.Namespace) -> int:
    ok = file_exists(ns.path, check_empty=ns.non_empty)
    print("true" if ok else "false")
    return 0 if ok else 1


def _handle_path_dir_exists(ns: argparse.Namespace) -> int:
    ok = dir_exists(ns.path, check_empty=ns.non_empty)
    print("true" if ok else "false")
    return 0 if ok else 1


def _handle_path_join(ns: argparse.Namespace) -> int:
    # `join` normalizes and returns an absolute path; ideal for shell pipelines.
    print(join(*ns.parts))
    return 0


def _handle_path_abs(ns: argparse.Namespace) -> int:
    print(relative2absolute_path(ns.path, checkpath=ns.check))
    return 0


def _handle_path_rel(ns: argparse.Namespace) -> int:
    print(absolute2relative_path(ns.path, base_path=ns.base))
    return 0


def _handle_path_no_home(ns: argparse.Namespace) -> int:
    print(path_without_home(ns.path))
    return 0


def _handle_path_size(ns: argparse.Namespace) -> int:
    # -1 signals "does not exist" — that's what the library returns.
    print(size_file(ns.path))
    return 0


def _handle_path_split(ns: argparse.Namespace) -> int:
    folder, name, ext = folder_name_ext(ns.path, checkpath=ns.check)
    _echo_json({"folder": folder, "name": name, "ext": ext})
    return 0


def _handle_path_glob(ns: argparse.Namespace) -> int:
    for match in recursive_glob(ns.root, ns.pattern):
        print(match)
    return 0


def _handle_path_mkdir(ns: argparse.Namespace) -> int:
    make_directory(ns.path, exist_ok=not ns.strict)
    return 0


def _handle_path_rmdir(ns: argparse.Namespace) -> int:
    remove_directory(ns.path)
    return 0


def _handle_path_rm(ns: argparse.Namespace) -> int:
    remove_files(ns.paths)
    return 0


def _handle_path_cp(ns: argparse.Namespace) -> int:
    copyfile(ns.source, ns.dest)
    return 0


def _handle_path_check(ns: argparse.Namespace) -> int:
    # Assertion-flavored: raises if the file is missing / empty.
    checkfile(ns.path, msg=ns.msg or "", check_empty=ns.non_empty)
    return 0


# ---------------------------------------------------------------------------
# hash — hashing strings, files, folders
# ---------------------------------------------------------------------------


def _handle_hash_string(ns: argparse.Namespace) -> int:
    print(hash_string(ns.value, size=ns.size))
    return 0


def _handle_hash_file(ns: argparse.Namespace) -> int:
    print(hashfile(ns.path, hash_content=not ns.path_only, date=ns.date))
    return 0


def _handle_hash_folder(ns: argparse.Namespace) -> int:
    print(hashfolder(
        ns.path,
        hash_content=not ns.no_content,
        hash_path=ns.include_path,
        date=ns.date,
    ))
    return 0


# ---------------------------------------------------------------------------
# str — string utilities
# ---------------------------------------------------------------------------


def _handle_str_empty(ns: argparse.Namespace) -> int:
    result = emptystring(ns.value)
    print("true" if result else "false")
    return 0 if result else 1


def _handle_str_ascii(ns: argparse.Namespace) -> int:
    print(asciistring(
        ns.value,
        replacement_char=ns.replacement,
        lower=not ns.preserve_case,
        allow_digits=not ns.no_digits,
    ))
    return 0


# ---------------------------------------------------------------------------
# config — configuration loader
# ---------------------------------------------------------------------------


def _handle_config_get(ns: argparse.Namespace) -> int:
    # `get_config` raises RuntimeError when nothing is found; let it propagate
    # so the exit code is non-zero and the reason lands on stderr.
    result = get_config(
        keys=ns.keys,
        config_type=ns.name,
        path=ns.path,
        env_files=ns.env_files or None,
    )
    _echo_json(result)
    return 0


# ---------------------------------------------------------------------------
# temp — temporary file / folder scratch space
# ---------------------------------------------------------------------------


def _handle_temp_file(ns: argparse.Namespace) -> int:
    # We deliberately do NOT auto-delete when the CLI creates a scratch
    # path — the caller decides. Print the path so shell pipelines can
    # chain on it. When `--keep` is not set, the file is created and
    # immediately deleted (proof-of-life mode).
    with temporary_filename(
        suffix=ns.suffix or "",
        mode=ns.mode,
        prefix=ns.prefix or "",
        delete=not ns.keep,
    ) as path:
        print(path)
    return 0


def _handle_temp_folder(ns: argparse.Namespace) -> int:
    with temporary_folder(prefix=ns.prefix or "", delete=not ns.keep) as path:
        print(path)
    return 0


# ---------------------------------------------------------------------------
# misc — grab-bag utilities
# ---------------------------------------------------------------------------


def _handle_misc_now(ns: argparse.Namespace) -> int:
    print(now_string(ns.fmt))
    return 0


def _handle_misc_format_size(ns: argparse.Namespace) -> int:
    print(format_size(ns.bytes))
    return 0


def _handle_misc_describe(ns: argparse.Namespace) -> int:
    # Emit the raw {path: size} mapping as JSON. Companion index.html and
    # description.json are written into the folder when flags allow.
    result = folder_description(
        ns.path,
        recursive=not ns.flat,
        index_html=not ns.no_html,
        with_size=not ns.no_size,
        description_json=not ns.no_json,
    )
    _echo_json(result)
    return 0


def _handle_misc_url_ok(ns: argparse.Namespace) -> int:
    ok = is_working_url(ns.url)
    print("true" if ok else "false")
    return 0 if ok else 1


def _handle_misc_zip(ns: argparse.Namespace) -> int:
    zip_folder(ns.folder, zip_file_path=ns.output or "")
    return 0


def _handle_misc_download(ns: argparse.Namespace) -> int:
    download_file(ns.url, file_path=ns.output or "")
    return 0


def _handle_misc_time2str(ns: argparse.Namespace) -> int:
    print(time2str(ns.seconds, no_space=ns.no_space))
    return 0


def _handle_misc_str2time(ns: argparse.Namespace) -> int:
    print(str2time(ns.value))
    return 0


def _handle_misc_ip(_: argparse.Namespace) -> int:
    _echo_json(get_user_ip())
    return 0


# ---------------------------------------------------------------------------
# prof — profiling of an arbitrary command
# ---------------------------------------------------------------------------


def _run_subprocess(argv: list[str]) -> int:
    # Run a caller-provided command as a subprocess, wired to the parent
    # stdio so it behaves like a wrapper (`os-helper prof wall -- sleep 1`).
    # Returns the subprocess exit code.
    return subprocess.call(argv)


def _handle_prof_wall(ns: argparse.Namespace) -> int:
    start = time.perf_counter()
    rc = _run_subprocess(list(ns.argv))
    elapsed = time.perf_counter() - start
    print(f"{elapsed:.6f}", file=sys.stderr)
    return rc


def _handle_prof_cpu(ns: argparse.Namespace) -> int:
    # process_time() only captures Python-side CPU; wrapping a subprocess
    # here would report ~0 s. We measure via os.times() which sums children.
    import os as _os

    before = _os.times()
    rc = _run_subprocess(list(ns.argv))
    after = _os.times()
    cpu_s = (after.children_user + after.children_system) - (
        before.children_user + before.children_system
    )
    print(f"{cpu_s:.6f}", file=sys.stderr)
    return rc


def _handle_prof_gpu(ns: argparse.Namespace) -> int:
    # Not meaningful for a subprocess wrapper, but keeping the surface
    # symmetric with wall / cpu. Prints a clear notice on stderr and
    # falls back to wall-clock timing.
    print("gpu profiling of an external subprocess is not supported; "
          "using wall-clock timing", file=sys.stderr)
    return _handle_prof_wall(ns)


# ---------------------------------------------------------------------------
# Parser construction — one helper per subcommand group keeps this readable
# ---------------------------------------------------------------------------


def _add_os_group(sub: argparse._SubParsersAction) -> None:
    g = sub.add_parser("os", help="Operating-system detection and process helpers.")
    s = g.add_subparsers(dest="action", metavar="ACTION")
    s.required = True

    s.add_parser("system", help="Print the current OS name (macos / linux / windows / unknown).").set_defaults(func=_handle_os_system)
    s.add_parser("unix", help="Print 'true' if the current OS is Unix-based.").set_defaults(func=_handle_os_flag(unix))
    s.add_parser("linux", help="Print 'true' if the current OS is Linux.").set_defaults(func=_handle_os_flag(linux))
    s.add_parser("macos", help="Print 'true' if the current OS is macOS.").set_defaults(func=_handle_os_flag(macos))
    s.add_parser("windows", help="Print 'true' if the current OS is Windows.").set_defaults(func=_handle_os_flag(windows))
    s.add_parser("pid", help="Print the current process ID.").set_defaults(func=_handle_os_pid)

    p = s.add_parser("workers", help="Resolve a worker count following sklearn's n_jobs convention.")
    p.add_argument("--n", type=int, default=-1, help="0 = full pool; >0 = exact count; <0 = pool+n+1 (default -1 = all).")
    p.set_defaults(func=_handle_os_workers)

    p = s.add_parser("run", help="Run a shell-style command and capture stdout / stderr.")
    p.add_argument("cmd", help="Command line (parsed with shlex; no real shell involved).")
    p.add_argument("--expected", default=None, help="File or directory expected to exist after success.")
    p.add_argument("--check-empty", action="store_true", help="Also require --expected to be non-empty.")
    p.add_argument("--no-check-exitcode", action="store_true", help="Do not assert exit code == 0.")
    p.set_defaults(func=_handle_os_run)

    p = s.add_parser("open", help="Open a file in the platform's default application.")
    p.add_argument("path", help="File path to open.")
    p.set_defaults(func=_handle_os_open)


def _add_path_group(sub: argparse._SubParsersAction) -> None:
    g = sub.add_parser("path", help="Filesystem predicates and helpers.")
    s = g.add_subparsers(dest="action", metavar="ACTION")
    s.required = True

    p = s.add_parser("exists", help="Check if a file exists (exit 0 = yes).")
    p.add_argument("path")
    p.add_argument("--non-empty", action="store_true", help="Also require the file to be non-empty.")
    p.set_defaults(func=_handle_path_exists)

    p = s.add_parser("dir-exists", help="Check if a directory exists (exit 0 = yes).")
    p.add_argument("path")
    p.add_argument("--non-empty", action="store_true", help="Also require the directory to be non-empty.")
    p.set_defaults(func=_handle_path_dir_exists)

    p = s.add_parser("join", help="Join components into a normalized absolute path.")
    p.add_argument("parts", nargs="+", help="Path components to join.")
    p.set_defaults(func=_handle_path_join)

    p = s.add_parser("abs", help="Convert a path to absolute (with optional existence check).")
    p.add_argument("path")
    p.add_argument("--check", action="store_true", help="Assert the resulting path exists.")
    p.set_defaults(func=_handle_path_abs)

    p = s.add_parser("rel", help="Convert a path to relative from --base (default cwd).")
    p.add_argument("path")
    p.add_argument("--base", default=None, help="Reference path (default: current working directory).")
    p.set_defaults(func=_handle_path_rel)

    p = s.add_parser("no-home", help="Replace the user's home prefix with '~'.")
    p.add_argument("path")
    p.set_defaults(func=_handle_path_no_home)

    p = s.add_parser("size", help="Print a file's size in bytes (-1 when it does not exist).")
    p.add_argument("path")
    p.set_defaults(func=_handle_path_size)

    p = s.add_parser("split", help="Decompose a path into folder/name/ext as JSON.")
    p.add_argument("path")
    p.add_argument("--check", action="store_true")
    p.set_defaults(func=_handle_path_split)

    p = s.add_parser("glob", help="Recursively glob for files matching PATTERN under ROOT.")
    p.add_argument("root")
    p.add_argument("pattern")
    p.set_defaults(func=_handle_path_glob)

    p = s.add_parser("mkdir", help="Create a directory (and parents).")
    p.add_argument("path")
    p.add_argument("--strict", action="store_true", help="Fail if the directory already exists.")
    p.set_defaults(func=_handle_path_mkdir)

    p = s.add_parser("rmdir", help="Recursively remove a directory (missing = no-op).")
    p.add_argument("path")
    p.set_defaults(func=_handle_path_rmdir)

    p = s.add_parser("rm", help="Remove files best-effort (missing entries skipped).")
    p.add_argument("paths", nargs="+")
    p.set_defaults(func=_handle_path_rm)

    p = s.add_parser("cp", help="Copy a file, preserving metadata.")
    p.add_argument("source")
    p.add_argument("dest")
    p.set_defaults(func=_handle_path_cp)

    p = s.add_parser("check", help="Assert a file exists (and optionally is non-empty).")
    p.add_argument("path")
    p.add_argument("--msg", default=None)
    p.add_argument("--non-empty", action="store_true")
    p.set_defaults(func=_handle_path_check)


def _add_hash_group(sub: argparse._SubParsersAction) -> None:
    g = sub.add_parser("hash", help="Hashing helpers (RIPEMD-160 / BLAKE2b fallback).")
    s = g.add_subparsers(dest="action", metavar="ACTION")
    s.required = True

    p = s.add_parser("string", help="Hash a string; --size N truncates to N chars.")
    p.add_argument("value")
    p.add_argument("--size", type=int, default=-1)
    p.set_defaults(func=_handle_hash_string)

    p = s.add_parser("file", help="Hash a file's content (and optionally the current date).")
    p.add_argument("path")
    p.add_argument("--path-only", action="store_true", help="Hash the file path instead of its content.")
    p.add_argument("--date", action="store_true", help="Mix the current date into the hash.")
    p.set_defaults(func=_handle_hash_file)

    p = s.add_parser("folder", help="Hash a folder's contents (and optionally path / date).")
    p.add_argument("path")
    p.add_argument("--no-content", action="store_true")
    p.add_argument("--include-path", action="store_true")
    p.add_argument("--date", action="store_true")
    p.set_defaults(func=_handle_hash_folder)


def _add_str_group(sub: argparse._SubParsersAction) -> None:
    g = sub.add_parser("str", help="String utilities.")
    s = g.add_subparsers(dest="action", metavar="ACTION")
    s.required = True

    p = s.add_parser("empty", help="Check if a string is None / whitespace-only (exit 0 = yes).")
    p.add_argument("value")
    p.set_defaults(func=_handle_str_empty)

    p = s.add_parser("ascii", help="Normalize a string to a filesystem-safe ASCII slug.")
    p.add_argument("value")
    p.add_argument("--replacement", default="-", help="Character used to replace disallowed chars.")
    p.add_argument("--preserve-case", action="store_true", help="Keep case (default: lowercase).")
    p.add_argument("--no-digits", action="store_true", help="Disallow digits in the result.")
    p.set_defaults(func=_handle_str_ascii)


def _add_config_group(sub: argparse._SubParsersAction) -> None:
    g = sub.add_parser("config", help="Configuration loading (JSON / YAML / .env / env vars).")
    s = g.add_subparsers(dest="action", metavar="ACTION")
    s.required = True

    p = s.add_parser("get", help="Load a set of keys, returning JSON on stdout.")
    p.add_argument("--name", required=True, help="Human-readable label used in log messages.")
    p.add_argument("--keys", required=True, nargs="+", help="Keys to load.")
    p.add_argument("--path", default=None, help="Config file or directory to search.")
    p.add_argument("--env-files", nargs="*", default=None, help="Extra .env files to merge into os.environ.")
    p.set_defaults(func=_handle_config_get)


def _add_temp_group(sub: argparse._SubParsersAction) -> None:
    g = sub.add_parser("temp", help="Temporary file / folder helpers.")
    s = g.add_subparsers(dest="action", metavar="ACTION")
    s.required = True

    p = s.add_parser("file", help="Create a temporary file and print its path.")
    p.add_argument("--suffix", default=None)
    p.add_argument("--prefix", default=None)
    p.add_argument("--mode", default="wt")
    p.add_argument("--keep", action="store_true", help="Do not delete on exit.")
    p.set_defaults(func=_handle_temp_file)

    p = s.add_parser("folder", help="Create a temporary directory and print its path.")
    p.add_argument("--prefix", default=None)
    p.add_argument("--keep", action="store_true", help="Do not delete on exit.")
    p.set_defaults(func=_handle_temp_folder)


def _add_misc_group(sub: argparse._SubParsersAction) -> None:
    g = sub.add_parser("misc", help="Miscellaneous utilities.")
    s = g.add_subparsers(dest="action", metavar="ACTION")
    s.required = True

    p = s.add_parser("now", help="Print a formatted timestamp.")
    p.add_argument("--fmt", default="log", choices=["log", "filename"], help="Format (default 'log').")
    p.set_defaults(func=_handle_misc_now)

    p = s.add_parser("format-size", help="Format a byte count as a human-readable string.")
    p.add_argument("bytes", type=int)
    p.set_defaults(func=_handle_misc_format_size)

    p = s.add_parser("describe", help="Describe a folder's contents as JSON (relative path -> size).")
    p.add_argument("path")
    p.add_argument("--flat", action="store_true", help="Do not descend into subdirectories.")
    p.add_argument("--no-html", action="store_true", help="Do not write index.html.")
    p.add_argument("--no-json", action="store_true", help="Do not write description.json.")
    p.add_argument("--no-size", action="store_true", help="Hide the size column in the HTML index.")
    p.set_defaults(func=_handle_misc_describe)

    p = s.add_parser("url-ok", help="Check whether a URL is syntactically valid + reachable.")
    p.add_argument("url")
    p.set_defaults(func=_handle_misc_url_ok)

    p = s.add_parser("zip", help="Zip a folder (skipping hidden files).")
    p.add_argument("folder")
    p.add_argument("--output", default=None, help="Output archive path (default: folder + '.zip').")
    p.set_defaults(func=_handle_misc_zip)

    p = s.add_parser("download", help="Download a URL to a local file.")
    p.add_argument("url")
    p.add_argument("--output", default=None)
    p.set_defaults(func=_handle_misc_download)

    p = s.add_parser("time2str", help="Convert seconds to a readable duration string.")
    p.add_argument("seconds", type=float)
    p.add_argument("--no-space", action="store_true")
    p.set_defaults(func=_handle_misc_time2str)

    p = s.add_parser("str2time", help="Parse a duration string into seconds.")
    p.add_argument("value")
    p.set_defaults(func=_handle_misc_str2time)

    p = s.add_parser("ip", help="Fetch the caller's public IPv4 / IPv6 addresses.")
    p.set_defaults(func=_handle_misc_ip)


def _add_prof_group(sub: argparse._SubParsersAction) -> None:
    g = sub.add_parser("prof", help="Profile an arbitrary subcommand.")
    s = g.add_subparsers(dest="action", metavar="ACTION")
    s.required = True

    for name, handler, doc in (
        ("wall", _handle_prof_wall, "Wall-clock elapsed time (seconds on stderr)."),
        ("cpu", _handle_prof_cpu, "CPU time consumed by the child subprocess."),
        ("gpu", _handle_prof_gpu, "GPU timing (falls back to wall-clock for subprocesses)."),
    ):
        p = s.add_parser(name, help=doc)
        p.add_argument("argv", nargs=argparse.REMAINDER,
                       help="Command to run (put after '--' to avoid flag collisions).")
        p.set_defaults(func=handler)


def build_parser() -> argparse.ArgumentParser:
    """
    Assemble the top-level ``os-helper`` argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Fully wired parser with every subcommand group attached.
    """
    parser = argparse.ArgumentParser(
        prog="os-helper",
        description=(
            "OS Helper — cross-platform utility CLI (OS detection, path "
            "manipulation, hashing, config loading, temp files, "
            "profiling)."
        ),
    )
    # Every non-trivial CLI benefits from `--version` — cheap to add and
    # oncall people always look for it. We resolve it lazily so a broken
    # importlib.metadata does not break the whole CLI.
    try:
        from importlib.metadata import version as _pkg_version

        parser.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s {_pkg_version('os-helper')}",
        )
    except Exception:  # pragma: no cover — never fatal
        pass

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    _add_os_group(subparsers)
    _add_path_group(subparsers)
    _add_hash_group(subparsers)
    _add_str_group(subparsers)
    _add_config_group(subparsers)
    _add_temp_group(subparsers)
    _add_misc_group(subparsers)
    _add_prof_group(subparsers)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """
    Entry point invoked by ``os-helper`` (see ``[project.scripts]``).

    Parameters
    ----------
    argv : sequence of str, optional
        Arguments to parse. Defaults to ``sys.argv[1:]`` when None.

    Returns
    -------
    int
        Process exit code (``0`` on success).
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    # Every subparser sets ``func`` via ``set_defaults`` — no dispatch
    # table needed, argparse resolved it for us.
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
