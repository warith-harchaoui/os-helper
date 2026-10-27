"""os-helper ships no command line, and this is what keeps it that way.

The decision (2026-10-25): os-helper is the suite's library foundation — every
one of the sixteen other suite members reaches it with ``import os_helper as
osh`` and none ever shelled out to it. A wrapper over ``path exists`` or ``str ascii`` restated the shell's own
vocabulary, so both CLIs (argparse and click) were deleted along with the
``[cli]`` extra.

A deletion with nothing holding it is an invitation to drift: the next person
adding a convenience command would find no objection in the repo. These
assertions are that objection, and each one fails on its own property —
a CLI module reappearing, a console script pointing at one, a shipped
document advertising a removed command, or ``click`` creeping into the
*core* dependencies (the ``[gui]`` extra may declare it: the GUI launcher
imports it).

The surviving entry points (``os-helper-api``, ``-mcp``, ``-gui``) are
*launchers* for other surfaces, not command lines, so they are explicitly
allowed.

Usage Example
-------------
>>> #   pytest tests/test_no_cli.py

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_PKG = _REPO / "os_helper"
_PYPROJECT = _REPO / "pyproject.toml"

# The three launchers that may legitimately own a console script. Anything else
# would be a command line by another name.
_ALLOWED_SCRIPTS = {"os-helper-api", "os-helper-mcp", "os-helper-gui"}

# A shell fence: ```bash / ```sh / ```console / ```shell.
_SHELL_FENCE = re.compile(r"^```(?:bash|sh|shell|console)\s*$(.*?)^```", re.M | re.S)
# Inside one of those, a line that *runs* `os-helper ...`. The three launcher
# suffixes are excluded by the lookahead.
#
# Scoping to shell fences is not fussiness: anchoring on the start of any line
# flagged both READMEs, whose body paragraphs happen to open with the package
# name ("os-helper is part of a local-first suite..."). A guard that cries wolf
# on prose is one the next person deletes instead of reading.
_INVOCATION = re.compile(r"^os-helper(?!-(?:api|mcp|gui))\s+(\S.*)$", re.M)


def _shell_invocations(text: str) -> list[str]:
    """Every ``os-helper <something>`` run inside a shell code fence."""
    return [
        hit
        for fence in _SHELL_FENCE.findall(text)
        for hit in _INVOCATION.findall(fence)
    ]


def _scripts() -> dict[str, str]:
    """Parse ``[project.scripts]`` with a regex rather than ``tomllib``.

    ``tomllib`` is stdlib only from 3.11 and this package supports 3.10, so a
    plain read of the one section we care about keeps the test running on the
    declared floor instead of silently skipping there.
    """
    text = _PYPROJECT.read_text(encoding="utf-8")
    block = re.search(r"^\[project\.scripts\]\s*$(.*?)(?=^\[)", text, re.M | re.S)
    if not block:
        return {}
    return {
        m.group(1): m.group(2)
        for m in re.finditer(
            r'^([A-Za-z0-9_.-]+)\s*=\s*"([^"]+)"', block.group(1), re.M
        )
    }


def test_no_cli_module_in_the_package() -> None:
    """No ``cli*.py`` lives in ``os_helper/``."""
    offenders = sorted(p.name for p in _PKG.glob("cli*.py"))
    assert not offenders, f"os-helper must ship no CLI module, found: {offenders}"


def test_no_console_script_points_at_a_cli() -> None:
    """Every console script is one of the three surface launchers."""
    scripts = _scripts()
    assert scripts, "[project.scripts] should still declare the surface launchers"
    unexpected = sorted(set(scripts) - _ALLOWED_SCRIPTS)
    assert not unexpected, f"unexpected console script(s): {unexpected}"
    pointing_at_cli = sorted(n for n, target in scripts.items() if ".cli" in target)
    assert not pointing_at_cli, f"script(s) pointing at a CLI module: {pointing_at_cli}"


def test_no_document_still_advertises_a_cli() -> None:
    """No shipped document points a reader at a command that no longer exists.

    Prose rots more quietly than code: four files kept advertising
    ``pip install "os-helper[cli]"`` after the extra was gone, including the
    package docstring that feeds the published API docs. The CHANGELOG is
    exempt — recording the removal is its job.
    """
    docs = [
        p
        for p in _REPO.glob("*.md")
        if p.name != "CHANGELOG.md"
    ]
    docs += sorted((_REPO / "skills").rglob("*.md"))
    docs += [_REPO / "requirements.txt", _PKG / "__init__.py"]

    stale: list[str] = []
    for doc in docs:
        if not doc.is_file():
            continue
        text = doc.read_text(encoding="utf-8")
        for needle in ("os-helper-click", "[cli]", "os_helper.cli"):
            if needle in text:
                stale.append(f"{doc.relative_to(_REPO)}: {needle}")
        # Widened on 2026-10-27. The needles above are all *names* of removed
        # things, so they missed the worst case: SKILL.md told an agent to run
        # `os-helper --help` to check the install. The command does not exist,
        # so the check reported "not installed" for a perfectly good install.
        # What matters is an invocation, not a mention -- `pip install
        # os-helper` and prose about the package must stay legal.
        for line in _shell_invocations(text):
            stale.append(f"{doc.relative_to(_REPO)}: runs `os-helper {line.strip()}`")
    assert not stale, "document(s) still advertising a removed CLI:\n  " + "\n  ".join(stale)


def _core_dependencies() -> str:
    """The ``dependencies = [...]`` block only, comments stripped.

    Regex rather than ``tomllib`` for the reason given in :func:`_scripts`:
    3.10 is a declared floor and must not silently skip this test.
    """
    text = _PYPROJECT.read_text(encoding="utf-8")
    block = re.search(r"^dependencies = \[\n(.*?)^\]", text, re.M | re.S)
    assert block, "pyproject.toml should declare a core dependencies block"
    # Prose explaining a removal is allowed to say "click".
    return "\n".join(line.split("#", 1)[0] for line in block.group(1).splitlines())


def test_click_is_not_a_core_dependency() -> None:
    """``click`` stays out of the *core* install, which nothing there imports.

    Narrowed on 2026-10-27, when the ``os-helper-gui`` launcher moved from
    argparse to click like the rest of the suite. click is a real dependency
    again — but of the ``[gui]`` extra, not of the library. The sixteen other
    suite members that reach os-helper with ``import os_helper as osh`` never
    start that launcher, so the rule that matters is the one this test now states: a
    plain ``pip install os-helper`` must not pull a CLI framework.

    The wider form ("click nowhere in pyproject.toml") would have had to be
    deleted outright to let the conversion land, which is how a guard turns
    into a formality. This keeps the half that still protects something.
    """
    assert "click" not in _core_dependencies(), (
        "click must not be a core dependency — the [gui] extra is where it belongs"
    )


def test_the_gui_launcher_declares_the_click_it_imports() -> None:
    """The flip side: an extra whose code imports click must say so.

    ``flip.py`` shipped four suite repos with click imported and undeclared,
    because click sat in their ``[dev]`` extra and every development
    environment therefore had it. Nothing failed until a user installed one.
    """
    launcher = (_PKG / "gui.py").read_text(encoding="utf-8")
    if "import click" not in launcher:
        return  # no click imported, nothing to declare
    text = _PYPROJECT.read_text(encoding="utf-8")
    gui_extra = re.search(r"^gui = \[\n(.*?)^\]", text, re.M | re.S)
    assert gui_extra, "pyproject.toml should declare a [gui] extra"
    code = "\n".join(line.split("#", 1)[0] for line in gui_extra.group(1).splitlines())
    assert "click" in code, "os_helper/gui.py imports click; the [gui] extra must declare it"
