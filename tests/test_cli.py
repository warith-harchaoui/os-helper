"""
Smoke tests for the argparse and click CLIs.

These tests exercise the CLI *parsing* layer and the trivial subcommands
that do not need the network or a real HTTP server. The goal is to
prevent regressions in the CLI entry points — subcommand names, flag
names, dispatch wiring — without pulling in extra runtime deps.

Usage Example
-------------
>>> #   pytest tests/test_cli.py

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import pytest

# The click CLI needs the ``click`` runtime dep, which lives in the
# ``[cli]`` optional extra. Skip cleanly if it is not installed.
click = pytest.importorskip("click")

from click.testing import CliRunner  # noqa: E402

# ---------------------------------------------------------------------------
# argparse CLI
# ---------------------------------------------------------------------------


EXPECTED_GROUPS = {"os", "path", "hash", "str", "config", "temp", "misc", "prof"}


def test_argparse_parser_builds_without_error():
    """Building the parser should never fail (imports, subcommand wiring)."""
    from os_helper.cli_argparse import build_parser

    parser = build_parser()
    subparsers_action = next(
        a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction"
    )
    assert EXPECTED_GROUPS.issubset(set(subparsers_action.choices.keys()))


def test_argparse_help_exits_zero(capsys):
    """``os-helper --help`` should exit with code 0 and print usage."""
    from os_helper.cli_argparse import main

    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "os-helper" in captured.out.lower()


@pytest.mark.parametrize("group", sorted(EXPECTED_GROUPS))
def test_argparse_group_help_exits_zero(group):
    """Every top-level group's ``--help`` should exit 0."""
    from os_helper.cli_argparse import main

    with pytest.raises(SystemExit) as exc:
        main([group, "--help"])
    assert exc.value.code == 0


def test_argparse_os_system_runs(capsys):
    """`os-helper os system` should print a known OS name."""
    from os_helper.cli_argparse import main

    rc = main(["os", "system"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out in {"macos", "linux", "windows", "unknown"}


def test_argparse_hash_string_runs(capsys):
    """`os-helper hash string hello --size 8` should print an 8-char hash."""
    from os_helper.cli_argparse import main

    rc = main(["hash", "string", "hello", "--size", "8"])
    assert rc == 0
    assert len(capsys.readouterr().out.strip()) == 8


def test_argparse_str_ascii_runs(capsys):
    """`os-helper str ascii 'Café'` should print a lowercased ASCII slug."""
    from os_helper.cli_argparse import main

    rc = main(["str", "ascii", "Café-Con-Leche!"])
    assert rc == 0
    assert capsys.readouterr().out.strip() == "cafe-con-leche"


def test_argparse_misc_format_size_runs(capsys):
    """`os-helper misc format-size 12345678` should print a MB string."""
    from os_helper.cli_argparse import main

    rc = main(["misc", "format-size", "12345678"])
    assert rc == 0
    assert "MB" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# click CLI
# ---------------------------------------------------------------------------


def test_click_group_has_expected_subgroups():
    """The click root group must expose the same top-level groups."""
    from os_helper.cli_click import cli

    assert EXPECTED_GROUPS.issubset(set(cli.commands.keys()))


def test_click_help_exits_zero():
    """``os-helper-click --help`` should exit 0."""
    from os_helper.cli_click import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "os helper" in result.output.lower()


@pytest.mark.parametrize("group", sorted(EXPECTED_GROUPS))
def test_click_group_help_exits_zero(group):
    """Every top-level click group's ``--help`` should exit 0."""
    from os_helper.cli_click import cli

    runner = CliRunner()
    result = runner.invoke(cli, [group, "--help"])
    assert result.exit_code == 0


def test_click_hash_string_runs():
    """`os-helper-click hash string hello --size 8` should print an 8-char hash."""
    from os_helper.cli_click import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["hash", "string", "hello", "--size", "8"])
    assert result.exit_code == 0
    assert len(result.output.strip()) == 8


def test_click_str_ascii_runs():
    """`os-helper-click str ascii Café-Con-Leche!` should print a slug."""
    from os_helper.cli_click import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["str", "ascii", "Café-Con-Leche!"])
    assert result.exit_code == 0
    assert result.output.strip() == "cafe-con-leche"
