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


def _emit(text: object) -> None:
    """Write one result line to stdout (the CLI's data channel).

    Parameters
    ----------
    text : object
        Value to print; stringified then followed by a single newline.

    Notes
    -----
    This is the CLI's *data* output surface, deliberately distinct from the
    package logging surface (rule 6). A CLI must be able to write its computed
    result to stdout so shell pipelines can consume it; routing that through a
    single helper (rather than scattering bare ``print`` calls) keeps the
    output channel in one place and byte-for-byte identical to ``print(text)``.
    """
    # Mirror ``print(text)`` exactly: stringify, then append one newline.
    sys.stdout.write(f"{text}\n")


def _emit_err(text: object) -> None:
    """Write one diagnostic line to stderr, away from the piped data stream.

    Parameters
    ----------
    text : object
        Value to print to stderr; stringified then followed by a newline.
    """
    # Diagnostics (timings, notices) go to fd 2 so they never pollute the
    # stdout data channel that callers may be piping elsewhere.
    sys.stderr.write(f"{text}\n")


def _echo_json(payload: object) -> None:
    """Emit a structured payload as pretty-printed, sorted JSON on stdout.

    Parameters
    ----------
    payload : object
        Any JSON-serializable value (dict, list, scalar).
    """
    # Structured outputs use JSON so shell pipelines can `| jq` on them;
    # ``sort_keys`` makes the output deterministic across runs.
    _emit(json.dumps(payload, indent=2, sort_keys=True))


# ---------------------------------------------------------------------------
# os — operating-system probes and process helpers
# ---------------------------------------------------------------------------


def _handle_os_system(_: argparse.Namespace) -> int:
    """Print the current operating-system short name on stdout.

    Parameters
    ----------
    _ : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    # `system` here refers to platform.system(); print a short name.
    if windows():
        _emit("windows")
    elif macos():
        _emit("macos")
    elif linux():
        _emit("linux")
    else:
        _emit("unknown")
    return 0


def _handle_os_flag(fn: Callable[[], bool]) -> Callable[[argparse.Namespace], int]:
    """Build a handler that prints ``true``/``false`` for a boolean OS probe.

    Parameters
    ----------
    fn : Callable[[], bool]
        A zero-argument predicate such as :func:`os_helper.unix` whose result
        should be surfaced to the shell.

    Returns
    -------
    Callable[[argparse.Namespace], int]
        A subcommand handler that emits the stringified boolean and returns 0.
    """

    # Factory: build a handler that prints "true" / "false" for a bool probe.
    def _run(_: argparse.Namespace) -> int:
        """Emit the probe result as ``true``/``false``.

        Parameters
        ----------
        _ : argparse.Namespace
            Unused parsed CLI arguments (probes take no options).

        Returns
        -------
        int
            Always 0 — the boolean value is carried on stdout, not the exit code.
        """
        _emit("true" if fn() else "false")
        return 0

    return _run


def _handle_os_pid(_: argparse.Namespace) -> int:
    """Print the current process ID on stdout.

    Parameters
    ----------
    _ : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    _emit(getpid())
    return 0


def _handle_os_workers(ns: argparse.Namespace) -> int:
    """Resolve and print a worker count (sklearn n_jobs convention).

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    # Mirrors sklearn's n_jobs convention.
    _emit(get_nb_workers(ns.n))
    return 0


def _handle_os_run(ns: argparse.Namespace) -> int:
    """Run a shell-style command and stream its captured stdout/stderr.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
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
    """Open a file in the platform's default application.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    # Open a file in the platform's default application.
    openfile(ns.path)
    return 0


# ---------------------------------------------------------------------------
# path — filesystem predicates and manipulations
# ---------------------------------------------------------------------------


def _handle_path_exists(ns: argparse.Namespace) -> int:
    """Report whether a file exists (exit 0 when it does).

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    ok = file_exists(ns.path, check_empty=ns.non_empty)
    _emit("true" if ok else "false")
    return 0 if ok else 1


def _handle_path_dir_exists(ns: argparse.Namespace) -> int:
    """Report whether a directory exists (exit 0 when it does).

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    ok = dir_exists(ns.path, check_empty=ns.non_empty)
    _emit("true" if ok else "false")
    return 0 if ok else 1


def _handle_path_join(ns: argparse.Namespace) -> int:
    """Join path components into one normalized absolute path.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    # `join` normalizes and returns an absolute path; ideal for shell pipelines.
    _emit(join(*ns.parts))
    return 0


def _handle_path_abs(ns: argparse.Namespace) -> int:
    """Print the absolute form of a path.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    _emit(relative2absolute_path(ns.path, checkpath=ns.check))
    return 0


def _handle_path_rel(ns: argparse.Namespace) -> int:
    """Print a path relative to a base directory.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    _emit(absolute2relative_path(ns.path, base_path=ns.base))
    return 0


def _handle_path_no_home(ns: argparse.Namespace) -> int:
    """Print a path with the home-directory prefix collapsed to '~'.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    _emit(path_without_home(ns.path))
    return 0


def _handle_path_size(ns: argparse.Namespace) -> int:
    """Print a file's size in bytes (-1 when it does not exist).

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    # -1 signals "does not exist" — that's what the library returns.
    _emit(size_file(ns.path))
    return 0


def _handle_path_split(ns: argparse.Namespace) -> int:
    """Print a path decomposed into folder/name/ext as JSON.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    folder, name, ext = folder_name_ext(ns.path, checkpath=ns.check)
    _echo_json({"folder": folder, "name": name, "ext": ext})
    return 0


def _handle_path_glob(ns: argparse.Namespace) -> int:
    """Print every file matching a glob pattern recursively.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    for match in recursive_glob(ns.root, ns.pattern):
        _emit(match)
    return 0


def _handle_path_mkdir(ns: argparse.Namespace) -> int:
    """Create a directory (and any missing parents).

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    make_directory(ns.path, exist_ok=not ns.strict)
    return 0


def _handle_path_rmdir(ns: argparse.Namespace) -> int:
    """Recursively remove a directory (missing is a no-op).

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    remove_directory(ns.path)
    return 0


def _handle_path_rm(ns: argparse.Namespace) -> int:
    """Remove a list of files on a best-effort basis.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    remove_files(ns.paths)
    return 0


def _handle_path_cp(ns: argparse.Namespace) -> int:
    """Copy a file, preserving metadata.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    copyfile(ns.source, ns.dest)
    return 0


def _handle_path_check(ns: argparse.Namespace) -> int:
    """Assert a file exists (and optionally is non-empty).

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    # Assertion-flavored: raises if the file is missing / empty.
    checkfile(ns.path, msg=ns.msg or "", check_empty=ns.non_empty)
    return 0


# ---------------------------------------------------------------------------
# hash — hashing strings, files, folders
# ---------------------------------------------------------------------------


def _handle_hash_string(ns: argparse.Namespace) -> int:
    """Print the hash of a string (optionally truncated).

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    _emit(hash_string(ns.value, size=ns.size))
    return 0


def _handle_hash_file(ns: argparse.Namespace) -> int:
    """Print the hash of a file's content and/or date.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    _emit(hashfile(ns.path, hash_content=not ns.path_only, date=ns.date))
    return 0


def _handle_hash_folder(ns: argparse.Namespace) -> int:
    """Print the hash of a folder's contents and/or path/date.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    _emit(
        hashfolder(
            ns.path,
            hash_content=not ns.no_content,
            hash_path=ns.include_path,
            date=ns.date,
        )
    )
    return 0


# ---------------------------------------------------------------------------
# str — string utilities
# ---------------------------------------------------------------------------


def _handle_str_empty(ns: argparse.Namespace) -> int:
    """Report whether a string is empty/whitespace (exit 0 when it is).

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    result = emptystring(ns.value)
    _emit("true" if result else "false")
    return 0 if result else 1


def _handle_str_ascii(ns: argparse.Namespace) -> int:
    """Print an ASCII-safe slug derived from the input string.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    _emit(
        asciistring(
            ns.value,
            replacement_char=ns.replacement,
            lower=not ns.preserve_case,
            allow_digits=not ns.no_digits,
        )
    )
    return 0


# ---------------------------------------------------------------------------
# config — configuration loader
# ---------------------------------------------------------------------------


def _handle_config_get(ns: argparse.Namespace) -> int:
    """Load configuration keys and print the result as JSON.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
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
    """Create a temporary file and print its path.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
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
        _emit(path)
    return 0


def _handle_temp_folder(ns: argparse.Namespace) -> int:
    """Create a temporary directory and print its path.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    with temporary_folder(prefix=ns.prefix or "", delete=not ns.keep) as path:
        _emit(path)
    return 0


# ---------------------------------------------------------------------------
# misc — grab-bag utilities
# ---------------------------------------------------------------------------


def _handle_misc_now(ns: argparse.Namespace) -> int:
    """Print a formatted current timestamp.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    _emit(now_string(ns.fmt))
    return 0


def _handle_misc_format_size(ns: argparse.Namespace) -> int:
    """Print a byte count as a human-readable size.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    _emit(format_size(ns.bytes))
    return 0


def _handle_misc_describe(ns: argparse.Namespace) -> int:
    """Describe a folder's contents and print the mapping as JSON.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
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
    """Report whether a URL is valid and reachable (exit 0 when so).

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    ok = is_working_url(ns.url)
    _emit("true" if ok else "false")
    return 0 if ok else 1


def _handle_misc_zip(ns: argparse.Namespace) -> int:
    """Zip a folder, skipping hidden files.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    zip_folder(ns.folder, zip_file_path=ns.output or "")
    return 0


def _handle_misc_download(ns: argparse.Namespace) -> int:
    """Download a URL to a local file.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    download_file(ns.url, file_path=ns.output or "")
    return 0


def _handle_misc_time2str(ns: argparse.Namespace) -> int:
    """Convert a seconds value to a readable duration string.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    _emit(time2str(ns.seconds, no_space=ns.no_space))
    return 0


def _handle_misc_str2time(ns: argparse.Namespace) -> int:
    """Parse a duration string into seconds and print it.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    _emit(str2time(ns.value))
    return 0


def _handle_misc_ip(_: argparse.Namespace) -> int:
    """Fetch and print the caller's public IP addresses as JSON.

    Parameters
    ----------
    _ : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    _echo_json(get_user_ip())
    return 0


# ---------------------------------------------------------------------------
# prof — profiling of an arbitrary command
# ---------------------------------------------------------------------------


def _run_subprocess(argv: list[str]) -> int:
    """Run a caller-provided command as a child process, inheriting stdio.

    Parameters
    ----------
    argv : list of str
        The command and its arguments (e.g. ``["sleep", "1"]``).

    Returns
    -------
    int
        The subprocess's own exit code, so the wrapper is transparent.
    """
    # ``subprocess.call`` wires the child to the parent's stdio, so the command
    # behaves exactly as if run directly (`os-helper prof wall -- sleep 1`).
    return subprocess.call(argv)


def _handle_prof_wall(ns: argparse.Namespace) -> int:
    """Time a subprocess by wall-clock and print the seconds on stderr.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    start = time.perf_counter()
    rc = _run_subprocess(list(ns.argv))
    elapsed = time.perf_counter() - start
    _emit_err(f"{elapsed:.6f}")
    return rc


def _handle_prof_cpu(ns: argparse.Namespace) -> int:
    """Time a subprocess by child CPU time and print seconds on stderr.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    # process_time() only captures Python-side CPU; wrapping a subprocess
    # here would report ~0 s. We measure via os.times() which sums children.
    import os as _os

    before = _os.times()
    rc = _run_subprocess(list(ns.argv))
    after = _os.times()
    cpu_s = (after.children_user + after.children_system) - (
        before.children_user + before.children_system
    )
    _emit_err(f"{cpu_s:.6f}")
    return rc


def _handle_prof_gpu(ns: argparse.Namespace) -> int:
    """GPU-profile a subprocess (falls back to wall-clock timing).

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    # Not meaningful for a subprocess wrapper, but keeping the surface
    # symmetric with wall / cpu. Prints a clear notice on stderr and
    # falls back to wall-clock timing.
    _emit_err("gpu profiling of an external subprocess is not supported; using wall-clock timing")
    return _handle_prof_wall(ns)


# ---------------------------------------------------------------------------
# gui — optional Tree Radar treemap dashboard (needs the [gui] extra)
# ---------------------------------------------------------------------------


def _handle_gui(ns: argparse.Namespace) -> int:
    """Launch the optional Tree Radar treemap GUI.

    The GUI and its web stack (FastAPI/uvicorn) live behind the optional
    ``os-helper[gui]`` extra, so the import happens *here*, inside the
    handler — never at module load. This keeps the plain CLI (and the
    library) usable without the web dependencies.

    Parameters
    ----------
    ns : argparse.Namespace
        Parsed CLI arguments for this subcommand.

    Returns
    -------
    int
        Process exit code (0 on success, 1 if the ``gui`` extra is missing).
    """
    # Import lazily so `os-helper` (and `import os_helper`) never require
    # FastAPI. A missing extra becomes a clear message + exit 1, not a stack.
    try:
        from .gui import run as _run_gui
    except ImportError as exc:  # pragma: no cover — only without the extra
        _emit_err(f"GUI unavailable: {exc}")
        return 1
    # run() blocks until Ctrl-C; it raises a friendly ImportError itself if
    # FastAPI/uvicorn are absent, which we catch and surface as a clean exit.
    try:
        _run_gui(root=ns.root, host=ns.host, port=ns.port)
    except ImportError as exc:
        _emit_err(f"GUI unavailable: {exc}")
        return 1
    return 0


def _add_gui_group(sub: argparse._SubParsersAction) -> None:
    """Attach the ``gui`` subcommand to the parser.

    Parameters
    ----------
    sub : argparse._SubParsersAction
        The top-level subparser action to register this command on.
    """
    # A single verb (no sub-actions): `os-helper gui --root ~/Downloads`.
    p = sub.add_parser(
        "gui",
        help="Launch the optional Tree Radar treemap dashboard (needs the [gui] extra).",
    )
    p.add_argument(
        "--root", default=None, help="Folder to pre-fill and scan (default: current directory)."
    )
    p.add_argument(
        "--host", default="127.0.0.1", help="Bind interface (default: 127.0.0.1, localhost only)."
    )
    p.add_argument("--port", type=int, default=8017, help="Port to serve on (default: 8017).")
    p.set_defaults(func=_handle_gui)


# ---------------------------------------------------------------------------
# Parser construction — one helper per subcommand group keeps this readable
# ---------------------------------------------------------------------------


def _add_os_group(sub: argparse._SubParsersAction) -> None:
    """Attach the ``os`` subcommand group to the parser.

    Parameters
    ----------
    sub : argparse._SubParsersAction
        The top-level subparser action to register this group on.
    """
    g = sub.add_parser("os", help="Operating-system detection and process helpers.")
    s = g.add_subparsers(dest="action", metavar="ACTION")
    s.required = True
    # Each action registers its handler via set_defaults(func=...); main()
    # then dispatches on that attribute, so no manual command table is needed.

    s.add_parser(
        "system", help="Print the current OS name (macos / linux / windows / unknown)."
    ).set_defaults(func=_handle_os_system)
    s.add_parser("unix", help="Print 'true' if the current OS is Unix-based.").set_defaults(
        func=_handle_os_flag(unix)
    )
    s.add_parser("linux", help="Print 'true' if the current OS is Linux.").set_defaults(
        func=_handle_os_flag(linux)
    )
    s.add_parser("macos", help="Print 'true' if the current OS is macOS.").set_defaults(
        func=_handle_os_flag(macos)
    )
    s.add_parser("windows", help="Print 'true' if the current OS is Windows.").set_defaults(
        func=_handle_os_flag(windows)
    )
    s.add_parser("pid", help="Print the current process ID.").set_defaults(func=_handle_os_pid)

    p = s.add_parser(
        "workers", help="Resolve a worker count following sklearn's n_jobs convention."
    )
    p.add_argument(
        "--n",
        type=int,
        default=-1,
        help="0 = full pool; >0 = exact count; <0 = pool+n+1 (default -1 = all).",
    )
    p.set_defaults(func=_handle_os_workers)

    p = s.add_parser("run", help="Run a shell-style command and capture stdout / stderr.")
    p.add_argument("cmd", help="Command line (parsed with shlex; no real shell involved).")
    p.add_argument(
        "--expected", default=None, help="File or directory expected to exist after success."
    )
    p.add_argument(
        "--check-empty", action="store_true", help="Also require --expected to be non-empty."
    )
    p.add_argument("--no-check-exitcode", action="store_true", help="Do not assert exit code == 0.")
    p.set_defaults(func=_handle_os_run)

    p = s.add_parser("open", help="Open a file in the platform's default application.")
    p.add_argument("path", help="File path to open.")
    p.set_defaults(func=_handle_os_open)


def _add_path_group(sub: argparse._SubParsersAction) -> None:
    """Attach the ``path`` subcommand group to the parser.

    Parameters
    ----------
    sub : argparse._SubParsersAction
        The top-level subparser action to register this group on.
    """
    g = sub.add_parser("path", help="Filesystem predicates and helpers.")
    s = g.add_subparsers(dest="action", metavar="ACTION")
    s.required = True
    # Predicate commands (exists / dir-exists) additionally encode their result
    # in the process exit code; mutating commands (mkdir / rm / cp) return 0.

    p = s.add_parser("exists", help="Check if a file exists (exit 0 = yes).")
    p.add_argument("path")
    p.add_argument(
        "--non-empty", action="store_true", help="Also require the file to be non-empty."
    )
    p.set_defaults(func=_handle_path_exists)

    p = s.add_parser("dir-exists", help="Check if a directory exists (exit 0 = yes).")
    p.add_argument("path")
    p.add_argument(
        "--non-empty", action="store_true", help="Also require the directory to be non-empty."
    )
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
    p.add_argument(
        "--base", default=None, help="Reference path (default: current working directory)."
    )
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
    """Attach the ``hash`` subcommand group to the parser.

    Parameters
    ----------
    sub : argparse._SubParsersAction
        The top-level subparser action to register this group on.
    """
    g = sub.add_parser("hash", help="Hashing helpers (RIPEMD-160 / BLAKE2b fallback).")
    s = g.add_subparsers(dest="action", metavar="ACTION")
    s.required = True

    p = s.add_parser("string", help="Hash a string; --size N truncates to N chars.")
    p.add_argument("value")
    p.add_argument("--size", type=int, default=-1)
    p.set_defaults(func=_handle_hash_string)

    p = s.add_parser("file", help="Hash a file's content (and optionally the current date).")
    p.add_argument("path")
    p.add_argument(
        "--path-only", action="store_true", help="Hash the file path instead of its content."
    )
    p.add_argument("--date", action="store_true", help="Mix the current date into the hash.")
    p.set_defaults(func=_handle_hash_file)

    p = s.add_parser("folder", help="Hash a folder's contents (and optionally path / date).")
    p.add_argument("path")
    p.add_argument("--no-content", action="store_true")
    p.add_argument("--include-path", action="store_true")
    p.add_argument("--date", action="store_true")
    p.set_defaults(func=_handle_hash_folder)


def _add_str_group(sub: argparse._SubParsersAction) -> None:
    """Attach the ``str`` subcommand group to the parser.

    Parameters
    ----------
    sub : argparse._SubParsersAction
        The top-level subparser action to register this group on.
    """
    g = sub.add_parser("str", help="String utilities.")
    s = g.add_subparsers(dest="action", metavar="ACTION")
    s.required = True
    # ``empty`` doubles as a shell test: its exit code mirrors the boolean.

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
    """Attach the ``config`` subcommand group to the parser.

    Parameters
    ----------
    sub : argparse._SubParsersAction
        The top-level subparser action to register this group on.
    """
    g = sub.add_parser("config", help="Configuration loading (JSON / YAML / .env / env vars).")
    s = g.add_subparsers(dest="action", metavar="ACTION")
    s.required = True
    # ``--keys`` takes one-or-more names; the loader fails (non-zero) if any
    # requested key is missing from every configured source.

    p = s.add_parser("get", help="Load a set of keys, returning JSON on stdout.")
    p.add_argument("--name", required=True, help="Human-readable label used in log messages.")
    p.add_argument("--keys", required=True, nargs="+", help="Keys to load.")
    p.add_argument("--path", default=None, help="Config file or directory to search.")
    p.add_argument(
        "--env-files", nargs="*", default=None, help="Extra .env files to merge into os.environ."
    )
    p.set_defaults(func=_handle_config_get)


def _add_temp_group(sub: argparse._SubParsersAction) -> None:
    """Attach the ``temp`` subcommand group to the parser.

    Parameters
    ----------
    sub : argparse._SubParsersAction
        The top-level subparser action to register this group on.
    """
    g = sub.add_parser("temp", help="Temporary file / folder helpers.")
    s = g.add_subparsers(dest="action", metavar="ACTION")
    s.required = True
    # ``--keep`` flips the library's auto-delete off so the printed path
    # survives past the CLI process for downstream shell steps.

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
    """Attach the ``misc`` subcommand group to the parser.

    Parameters
    ----------
    sub : argparse._SubParsersAction
        The top-level subparser action to register this group on.
    """
    g = sub.add_parser("misc", help="Miscellaneous utilities.")
    s = g.add_subparsers(dest="action", metavar="ACTION")
    s.required = True
    # A grab-bag group: some commands print scalars, others emit JSON so the
    # richer results (describe / ip) stay machine-parseable.

    p = s.add_parser("now", help="Print a formatted timestamp.")
    p.add_argument(
        "--fmt", default="log", choices=["log", "filename"], help="Format (default 'log')."
    )
    p.set_defaults(func=_handle_misc_now)

    p = s.add_parser("format-size", help="Format a byte count as a human-readable string.")
    p.add_argument("bytes", type=int)
    p.set_defaults(func=_handle_misc_format_size)

    p = s.add_parser(
        "describe", help="Describe a folder's contents as JSON (relative path -> size)."
    )
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
    """Attach the ``prof`` subcommand group to the parser.

    Parameters
    ----------
    sub : argparse._SubParsersAction
        The top-level subparser action to register this group on.
    """
    g = sub.add_parser("prof", help="Profile an arbitrary subcommand.")
    s = g.add_subparsers(dest="action", metavar="ACTION")
    s.required = True

    # The three prof subcommands share identical wiring (only the handler
    # differs), so build them from a table instead of copy-pasting three blocks.
    for name, handler, doc in (
        ("wall", _handle_prof_wall, "Wall-clock elapsed time (seconds on stderr)."),
        ("cpu", _handle_prof_cpu, "CPU time consumed by the child subprocess."),
        ("gpu", _handle_prof_gpu, "GPU timing (falls back to wall-clock for subprocesses)."),
    ):
        p = s.add_parser(name, help=doc)
        # ``REMAINDER`` swallows everything after the subcommand verbatim, so
        # the wrapped command's own flags (e.g. ``ffmpeg -i ...``) are not
        # mis-parsed as flags for os-helper itself.
        p.add_argument(
            "argv",
            nargs=argparse.REMAINDER,
            help="Command to run (put after '--' to avoid flag collisions).",
        )
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
    _add_gui_group(subparsers)

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
