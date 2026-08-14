"""
Smoke tests for the argparse and click CLIs.

These tests exercise the CLI *parsing* layer and the trivial subcommands
that do not need the network or a real HTTP server. The goal is to
prevent regressions in the CLI entry points — subcommand names, flag
names, dispatch wiring — without pulling in extra runtime deps.

Both surfaces are meant to be exact twins, so each test below drives BOTH
the argparse and the click CLI for the same scenario in one function
(a loop, not `@pytest.mark.parametrize`) rather than duplicating every
case into a separate `test_argparse_*` / `test_click_*` pair — that
duplication is exactly the kind of drift this suite exists to catch, so
collapsing it into one shared assertion per scenario is *more* rigorous,
not less: a fix applied to only one surface now fails in the same place.

Usage Example
-------------
>>> #   pytest tests/test_cli.py

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import json

import pytest

# The click CLI needs the ``click`` runtime dep, which lives in the
# ``[cli]`` optional extra. Skip cleanly if it is not installed.
click = pytest.importorskip("click")

from click.testing import CliRunner  # noqa: E402

from os_helper.cli_argparse import build_parser, main as argparse_main  # noqa: E402
from os_helper.cli_click import cli as click_cli  # noqa: E402
from os_helper.cli_click import main as click_main  # noqa: E402

EXPECTED_GROUPS = {"os", "hardware", "path", "hash", "str", "config", "temp", "misc", "prof"}


def _run_argparse(args: list[str], capsys) -> tuple[int, str]:
    """Invoke the argparse CLI in-process, returning (exit_code, stdout)."""
    try:
        rc = argparse_main(args)
    except SystemExit as exc:
        rc = exc.code
    return rc, capsys.readouterr().out


def _run_click(args: list[str]) -> tuple[int, str]:
    """Invoke the click CLI in-process, returning (exit_code, stdout)."""
    result = CliRunner().invoke(click_cli, args)
    return result.exit_code, result.output


def test_both_clis_expose_the_expected_subcommand_groups() -> None:
    parser = build_parser()
    subparsers_action = next(
        a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction"
    )
    assert EXPECTED_GROUPS.issubset(set(subparsers_action.choices.keys()))
    assert EXPECTED_GROUPS.issubset(set(click_cli.commands.keys()))


def test_both_clis_help_exits_zero_for_root_and_every_group(capsys) -> None:
    rc, out = _run_argparse(["--help"], capsys)
    assert rc == 0 and "os-helper" in out.lower()
    code, out = _run_click(["--help"])
    assert code == 0 and "os helper" in out.lower()

    for group in sorted(EXPECTED_GROUPS):
        rc, _ = _run_argparse([group, "--help"], capsys)
        assert rc == 0, f"argparse group '{group}' --help"
        code, _ = _run_click([group, "--help"])
        assert code == 0, f"click group '{group}' --help"


def test_both_clis_run_representative_subcommands(capsys) -> None:
    # (args, assertion over stdout) — one representative leaf command per
    # group that needs neither the network nor a real HTTP server.
    cases: list[tuple[list[str], "callable"]] = [
        (["os", "system"], lambda out: out.strip() in {"macos", "linux", "windows", "unknown"}),
        (["hash", "string", "hello", "--size", "8"], lambda out: len(out.strip()) == 8),
        (["str", "ascii", "Café-Con-Leche!"], lambda out: out.strip() == "cafe-con-leche"),
        (["misc", "format-size", "12345678"], lambda out: "MB" in out),
    ]
    for args, check in cases:
        rc, out = _run_argparse(args, capsys)
        assert rc == 0 and check(out), f"argparse {args}"
        code, out = _run_click(args)
        assert code == 0 and check(out), f"click {args}"


def test_both_clis_print_clean_error_instead_of_traceback(capsys, monkeypatch) -> None:
    # A library RuntimeError (get_config's normal failure mode for keys that
    # resolve from no source) used to propagate as a raw Python traceback on
    # both CLI twins. Both entry points now catch it and print one clean
    # "Error: ..." line, exit 1.
    args = ["config", "get", "--name", "test", "--keys", "nonexistent_key_xyz"]

    try:
        rc = argparse_main(args)
    except SystemExit as exc:
        rc = exc.code
    captured = capsys.readouterr()
    assert rc == 1
    assert "Traceback" not in captured.err
    assert "Error:" in captured.err

    monkeypatch.setattr("sys.argv", ["os-helper-click", *args])
    with pytest.raises(SystemExit) as exc_info:
        click_main()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert "Error:" in err


def test_both_clis_hardware_info_prints_a_valid_snapshot(capsys) -> None:
    rc, out = _run_argparse(["hardware", "info"], capsys)
    assert rc == 0
    payload = json.loads(out)
    assert payload["ram_gb"] > 0
    assert payload["cpu"]["logical_cores"] >= 1

    code, out = _run_click(["hardware", "info"])
    assert code == 0
    payload = json.loads(out)
    assert payload["ram_gb"] > 0
