"""
OS Helper — click-based command-line interface.

Twin of :mod:`os_helper.cli_argparse`: same public surface (identical
subcommand groups, identical flag semantics), but implemented with
:mod:`click` so users who already have a click-native shell setup
(``click.shell_completion`` for bash / zsh / fish, colored ``--help``,
nested command groups) can plug it in without friction. Installed as
the ``os-helper-click`` entry point in ``pyproject.toml``.

Design notes
------------
- Subcommand *groups* mirror ``os-helper`` (the argparse twin) so both
  CLIs can be introspected identically by higher layers.
- Flag names match the argparse names (``--path`` / ``--size`` / …)
  rather than the more idiomatic click positional style — consistency
  across the two CLIs beats micro-idiomaticity here.
- Errors from the library propagate unchanged; click handles the
  formatting.

Usage Example
-------------
>>> #   os-helper-click os system
>>> #   os-helper-click path exists /etc/hosts
>>> #   os-helper-click hash string hello --size 8
>>> #   os-helper-click misc now --fmt filename
>>> #   os-helper-click temp folder --prefix demo

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from collections.abc import Callable

try:
    import click
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "The click CLI requires the [cli] extra. Install with: pip install 'os-helper[cli]'"
    ) from exc

# Same underlying functions as the argparse twin — one source of truth.
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
# Top-level group
# ---------------------------------------------------------------------------


@click.group(
    context_settings={"help_option_names": ["-h", "--help"], "max_content_width": 100},
)
@click.version_option(package_name="os-helper", prog_name="os-helper-click")
def cli() -> None:
    """OS Helper — click twin of the argparse CLI. Same subcommand groups."""
    # Nothing to do at the group level — every subcommand carries its own
    # arguments and side effects.


# ---------------------------------------------------------------------------
# os — OS detection / process helpers
# ---------------------------------------------------------------------------


@cli.group("os")
def os_grp() -> None:
    """Operating-system detection and process helpers."""


@os_grp.command("system")
def os_system() -> None:
    """Print the current OS name."""
    # Probe in priority order and emit a single canonical short name; the final
    # ``unknown`` branch keeps the output well-defined on exotic platforms.
    if windows():
        click.echo("windows")
    elif macos():
        click.echo("macos")
    elif linux():
        click.echo("linux")
    else:
        click.echo("unknown")


def _make_flag(name: str, probe: Callable[[], bool]) -> None:
    """Register a click command that prints ``true``/``false`` for a probe.

    Parameters
    ----------
    name : str
        Subcommand name (also used in the generated help text).
    probe : Callable[[], bool]
        Zero-argument predicate whose result is surfaced to the shell.
    """

    # Factory pattern: generating the six OS-detection commands from one closure
    # avoids six near-identical copy-pasted command bodies.
    @os_grp.command(name)
    def _cmd() -> None:  # noqa: D401 — docstring set dynamically below
        """Print the boolean probe result as ``true``/``false``."""
        click.echo("true" if probe() else "false")

    # Set the help text per-command since the shared body cannot hardcode it.
    _cmd.__doc__ = f"Print 'true' if the current OS is {name}."


_make_flag("unix", unix)
_make_flag("linux", linux)
_make_flag("macos", macos)
_make_flag("windows", windows)


@os_grp.command("pid")
def os_pid() -> None:
    """Print the current process ID."""
    click.echo(getpid())


@os_grp.command("workers")
@click.option(
    "--n", type=int, default=-1, show_default=True, help="0 = full pool; >0 = exact; <0 = pool+n+1."
)
def os_workers(n: int) -> None:
    """Resolve a worker count (sklearn n_jobs convention)."""
    click.echo(get_nb_workers(n))


@os_grp.command("run")
@click.argument("cmd_string")
@click.option("--expected", default=None, help="File or directory expected to exist after success.")
@click.option("--check-empty", is_flag=True, help="Also require --expected to be non-empty.")
@click.option("--no-check-exitcode", is_flag=True, help="Do not assert exit code == 0.")
def os_run(
    cmd_string: str, expected: str | None, check_empty: bool, no_check_exitcode: bool
) -> None:
    """Run CMD_STRING as a subprocess and capture stdout / stderr."""
    result = system(
        cmd=cmd_string,
        expected_output=expected or "",
        check_exitcode=not no_check_exitcode,
        check_empty=check_empty,
    )
    # Relay the child's streams to our own: ``nl=False`` preserves the captured
    # bytes exactly (the command already produced its own newlines), and stderr
    # is kept on fd 2 so it never contaminates a stdout pipe.
    if result["out"]:
        click.echo(result["out"], nl=False)
    if result["err"]:
        click.echo(result["err"], nl=False, err=True)


@os_grp.command("open")
@click.argument("path", type=click.Path(exists=True))
def os_open(path: str) -> None:
    """Open PATH in the platform's default application."""
    openfile(path)


# ---------------------------------------------------------------------------
# path — filesystem predicates and helpers
# ---------------------------------------------------------------------------


@cli.group("path")
def path_grp() -> None:
    """Filesystem predicates and helpers."""


@path_grp.command("exists")
@click.argument("path")
@click.option("--non-empty", is_flag=True)
def path_exists(path: str, non_empty: bool) -> None:
    """Check if PATH exists (exit 0 = yes)."""
    ok = file_exists(path, check_empty=non_empty)
    click.echo("true" if ok else "false")
    # Encode the boolean in the EXIT CODE too, so shell ``if`` guards can branch
    # on it directly without parsing stdout.
    sys.exit(0 if ok else 1)


@path_grp.command("dir-exists")
@click.argument("path")
@click.option("--non-empty", is_flag=True)
def path_dir_exists(path: str, non_empty: bool) -> None:
    """Check if PATH is an existing directory (exit 0 = yes)."""
    ok = dir_exists(path, check_empty=non_empty)
    click.echo("true" if ok else "false")
    # Same dual stdout+exit-code contract as ``path exists`` above.
    sys.exit(0 if ok else 1)


@path_grp.command("join")
@click.argument("parts", nargs=-1, required=True)
def path_join(parts: tuple[str, ...]) -> None:
    """Join PARTS into a normalized absolute path."""
    click.echo(join(*parts))


@path_grp.command("abs")
@click.argument("path")
@click.option("--check", is_flag=True, help="Assert the resulting path exists.")
def path_abs(path: str, check: bool) -> None:
    """Convert PATH to absolute."""
    click.echo(relative2absolute_path(path, checkpath=check))


@path_grp.command("rel")
@click.argument("path")
@click.option("--base", default=None, help="Reference path (default: cwd).")
def path_rel(path: str, base: str | None) -> None:
    """Convert PATH to relative from --base."""
    click.echo(absolute2relative_path(path, base_path=base))


@path_grp.command("no-home")
@click.argument("path")
def path_no_home(path: str) -> None:
    """Replace the user's home prefix with '~'."""
    click.echo(path_without_home(path))


@path_grp.command("size")
@click.argument("path")
def path_size(path: str) -> None:
    """Print PATH's size in bytes (-1 when it does not exist)."""
    click.echo(size_file(path))


@path_grp.command("split")
@click.argument("path")
@click.option("--check", is_flag=True)
def path_split(path: str, check: bool) -> None:
    """Decompose PATH into folder/name/ext as JSON."""
    folder, name, ext = folder_name_ext(path, checkpath=check)
    # Emit JSON (not three lines) so callers can consume the parts with ``jq``.
    click.echo(json.dumps({"folder": folder, "name": name, "ext": ext}, indent=2))


@path_grp.command("glob")
@click.argument("root")
@click.argument("pattern")
def path_glob(root: str, pattern: str) -> None:
    """Recursively glob for files matching PATTERN under ROOT."""
    for match in recursive_glob(root, pattern):
        click.echo(match)


@path_grp.command("mkdir")
@click.argument("path")
@click.option("--strict", is_flag=True, help="Fail if the directory already exists.")
def path_mkdir(path: str, strict: bool) -> None:
    """Create PATH (and parents)."""
    make_directory(path, exist_ok=not strict)


@path_grp.command("rmdir")
@click.argument("path")
def path_rmdir(path: str) -> None:
    """Recursively remove PATH (missing = no-op)."""
    remove_directory(path)


@path_grp.command("rm")
@click.argument("paths", nargs=-1, required=True)
def path_rm(paths: tuple[str, ...]) -> None:
    """Remove PATHS best-effort (missing entries skipped)."""
    remove_files(list(paths))


@path_grp.command("cp")
@click.argument("source", type=click.Path(exists=True))
@click.argument("dest")
def path_cp(source: str, dest: str) -> None:
    """Copy SOURCE to DEST, preserving metadata."""
    copyfile(source, dest)


@path_grp.command("check")
@click.argument("path")
@click.option("--msg", default=None)
@click.option("--non-empty", is_flag=True)
def path_check(path: str, msg: str | None, non_empty: bool) -> None:
    """Assert PATH exists (and optionally is non-empty)."""
    checkfile(path, msg=msg or "", check_empty=non_empty)


# ---------------------------------------------------------------------------
# hash — hashing helpers
# ---------------------------------------------------------------------------


@cli.group("hash")
def hash_grp() -> None:
    """Hashing helpers (RIPEMD-160 / BLAKE2b fallback)."""


@hash_grp.command("string")
@click.argument("value")
@click.option("--size", type=int, default=-1, show_default=True)
def hash_string_cmd(value: str, size: int) -> None:
    """Hash VALUE; --size N truncates the digest to N chars."""
    click.echo(hash_string(value, size=size))


@hash_grp.command("file")
@click.argument("path", type=click.Path(exists=True))
@click.option("--path-only", is_flag=True, help="Hash the file path instead of its content.")
@click.option("--date", is_flag=True, help="Mix the current date into the hash.")
def hash_file_cmd(path: str, path_only: bool, date: bool) -> None:
    """Hash PATH's content."""
    click.echo(hashfile(path, hash_content=not path_only, date=date))


@hash_grp.command("folder")
@click.argument("path", type=click.Path(exists=True, file_okay=False))
@click.option("--no-content", is_flag=True)
@click.option("--include-path", is_flag=True)
@click.option("--date", is_flag=True)
def hash_folder_cmd(path: str, no_content: bool, include_path: bool, date: bool) -> None:
    """Hash PATH's contents."""
    click.echo(hashfolder(path, hash_content=not no_content, hash_path=include_path, date=date))


# ---------------------------------------------------------------------------
# str — string utilities
# ---------------------------------------------------------------------------


@cli.group("str")
def str_grp() -> None:
    """String utilities."""


@str_grp.command("empty")
@click.argument("value")
def str_empty(value: str) -> None:
    """Check if VALUE is None / whitespace-only (exit 0 = yes)."""
    result = emptystring(value)
    click.echo("true" if result else "false")
    # Predicate result mirrored into the exit code for shell-friendly use.
    sys.exit(0 if result else 1)


@str_grp.command("ascii")
@click.argument("value")
@click.option("--replacement", default="-", show_default=True)
@click.option("--preserve-case", is_flag=True)
@click.option("--no-digits", is_flag=True)
def str_ascii(value: str, replacement: str, preserve_case: bool, no_digits: bool) -> None:
    """Normalize VALUE to a filesystem-safe ASCII slug."""
    click.echo(
        asciistring(
            value,
            replacement_char=replacement,
            lower=not preserve_case,
            allow_digits=not no_digits,
        )
    )


# ---------------------------------------------------------------------------
# config — configuration loader
# ---------------------------------------------------------------------------


@cli.group("config")
def config_grp() -> None:
    """Configuration loading (JSON / YAML / .env / env vars)."""


@config_grp.command("get")
@click.option("--name", required=True, help="Human-readable label used in log messages.")
@click.option("--keys", required=True, multiple=True, help="Repeat --keys for each key to load.")
@click.option("--path", default=None, help="Config file or directory to search.")
@click.option("--env-files", multiple=True, help="Repeat --env-files for each .env file.")
def config_get(
    name: str, keys: tuple[str, ...], path: str | None, env_files: tuple[str, ...]
) -> None:
    """Load a set of KEYS and print JSON."""
    # click gathers repeated ``--keys``/``--env-files`` into tuples; convert to
    # lists for the library API, and pass None (not an empty list) so the
    # loader falls back to its own default env-file set.
    result = get_config(
        keys=list(keys),
        config_type=name,
        path=path,
        env_files=list(env_files) if env_files else None,
    )
    click.echo(json.dumps(result, indent=2, sort_keys=True))


# ---------------------------------------------------------------------------
# temp — temporary file / folder helpers
# ---------------------------------------------------------------------------


@cli.group("temp")
def temp_grp() -> None:
    """Temporary file / folder helpers."""


@temp_grp.command("file")
@click.option("--suffix", default=None)
@click.option("--prefix", default=None)
@click.option("--mode", default="wt", show_default=True)
@click.option("--keep", is_flag=True, help="Do not delete on exit.")
def temp_file(suffix: str | None, prefix: str | None, mode: str, keep: bool) -> None:
    """Create a temporary file and print its path."""
    # Print the path inside the context so it is emitted before cleanup; when
    # ``--keep`` is absent the file is deleted on block exit (proof-of-life).
    with temporary_filename(
        suffix=suffix or "",
        mode=mode,
        prefix=prefix or "",
        delete=not keep,
    ) as path:
        click.echo(path)


@temp_grp.command("folder")
@click.option("--prefix", default=None)
@click.option("--keep", is_flag=True, help="Do not delete on exit.")
def temp_folder_cmd(prefix: str | None, keep: bool) -> None:
    """Create a temporary directory and print its path."""
    # Same emit-then-cleanup pattern as ``temp file``.
    with temporary_folder(prefix=prefix or "", delete=not keep) as path:
        click.echo(path)


# ---------------------------------------------------------------------------
# misc — grab-bag utilities
# ---------------------------------------------------------------------------


@cli.group("misc")
def misc_grp() -> None:
    """Miscellaneous utilities."""


@misc_grp.command("now")
@click.option("--fmt", type=click.Choice(["log", "filename"]), default="log", show_default=True)
def misc_now(fmt: str) -> None:
    """Print a formatted timestamp."""
    click.echo(now_string(fmt))


@misc_grp.command("format-size")
@click.argument("nb_bytes", type=int)
def misc_format_size(nb_bytes: int) -> None:
    """Format NB_BYTES as a human-readable size."""
    click.echo(format_size(nb_bytes))


@misc_grp.command("describe")
@click.argument("path", type=click.Path(exists=True, file_okay=False))
@click.option("--flat", is_flag=True, help="Do not descend into subdirectories.")
@click.option("--no-html", is_flag=True)
@click.option("--no-json", is_flag=True)
@click.option("--no-size", is_flag=True)
def misc_describe(path: str, flat: bool, no_html: bool, no_json: bool, no_size: bool) -> None:
    """Describe PATH's contents as JSON."""
    result = folder_description(
        path,
        recursive=not flat,
        index_html=not no_html,
        with_size=not no_size,
        description_json=not no_json,
    )
    click.echo(json.dumps(result, indent=2, sort_keys=True))


@misc_grp.command("url-ok")
@click.argument("url")
def misc_url_ok(url: str) -> None:
    """Check whether URL is syntactically valid + reachable."""
    ok = is_working_url(url)
    click.echo("true" if ok else "false")
    # Reachability reflected in the exit code for scripting.
    sys.exit(0 if ok else 1)


@misc_grp.command("zip")
@click.argument("folder", type=click.Path(exists=True, file_okay=False))
@click.option("--output", default=None, help="Output archive path (default: folder + '.zip').")
def misc_zip(folder: str, output: str | None) -> None:
    """Zip FOLDER (skipping hidden files)."""
    zip_folder(folder, zip_file_path=output or "")


@misc_grp.command("download")
@click.argument("url")
@click.option("--output", default=None)
def misc_download(url: str, output: str | None) -> None:
    """Download URL to a local file."""
    download_file(url, file_path=output or "")


@misc_grp.command("time2str")
@click.argument("seconds", type=float)
@click.option("--no-space", is_flag=True)
def misc_time2str(seconds: float, no_space: bool) -> None:
    """Convert SECONDS to a readable duration string."""
    click.echo(time2str(seconds, no_space=no_space))


@misc_grp.command("str2time")
@click.argument("value")
def misc_str2time(value: str) -> None:
    """Parse VALUE as a duration and print seconds."""
    click.echo(str2time(value))


@misc_grp.command("ip")
def misc_ip() -> None:
    """Fetch the caller's public IPv4 / IPv6 addresses."""
    click.echo(json.dumps(get_user_ip(), indent=2, sort_keys=True))


# ---------------------------------------------------------------------------
# prof — profile an arbitrary child command
# ---------------------------------------------------------------------------


@cli.group("prof")
def prof_grp() -> None:
    """Profile an arbitrary subcommand."""


def _run_subprocess(argv: list[str]) -> int:
    """Run a caller-provided command as a child process, inheriting stdio.

    Parameters
    ----------
    argv : list of str
        Command and arguments to execute.

    Returns
    -------
    int
        The child's exit code, so the profiling wrapper stays transparent.
    """
    # Inherit the parent's stdio so the wrapped command behaves as if run direct.
    return subprocess.call(argv)


@prof_grp.command("wall", context_settings={"ignore_unknown_options": True})
@click.argument("argv", nargs=-1, type=click.UNPROCESSED)
def prof_wall(argv: tuple[str, ...]) -> None:
    """Wall-clock elapsed time (seconds on stderr)."""
    # Bracket the child run with a monotonic clock; the timing goes to stderr so
    # the child's own stdout stays clean, and we propagate its exit code.
    start = time.perf_counter()
    rc = _run_subprocess(list(argv))
    elapsed = time.perf_counter() - start
    click.echo(f"{elapsed:.6f}", err=True)
    sys.exit(rc)


@prof_grp.command("cpu", context_settings={"ignore_unknown_options": True})
@click.argument("argv", nargs=-1, type=click.UNPROCESSED)
def prof_cpu(argv: tuple[str, ...]) -> None:
    """CPU time consumed by the child subprocess."""
    import os as _os

    # ``time.process_time`` measures only THIS process, so for a subprocess we
    # read the ``children_*`` counters from ``os.times()`` and diff them across
    # the run to isolate the child's user+system CPU consumption.
    before = _os.times()
    rc = _run_subprocess(list(argv))
    after = _os.times()
    cpu_s = (after.children_user + after.children_system) - (
        before.children_user + before.children_system
    )
    click.echo(f"{cpu_s:.6f}", err=True)
    sys.exit(rc)


@prof_grp.command("gpu", context_settings={"ignore_unknown_options": True})
@click.argument("argv", nargs=-1, type=click.UNPROCESSED)
def prof_gpu(argv: tuple[str, ...]) -> None:
    """GPU timing (falls back to wall-clock for subprocesses)."""
    # A separate child process has its own CUDA context we cannot instrument
    # from here, so we warn and degrade gracefully to wall-clock timing rather
    # than fail — keeping the ``prof`` surface symmetric with wall/cpu.
    click.echo(
        "gpu profiling of an external subprocess is not supported; using wall-clock timing",
        err=True,
    )
    start = time.perf_counter()
    rc = _run_subprocess(list(argv))
    elapsed = time.perf_counter() - start
    click.echo(f"{elapsed:.6f}", err=True)
    sys.exit(rc)


if __name__ == "__main__":  # pragma: no cover
    cli()
