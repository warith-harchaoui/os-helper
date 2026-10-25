"""os-helper ships no command line, and this is what keeps it that way.

The decision (2026-10-25): os-helper is the suite's library foundation — nine
packages reach it with ``import os_helper as osh`` and none ever shelled out to
it. A wrapper over ``path exists`` or ``str ascii`` restated the shell's own
vocabulary, so both CLIs (argparse and click) were deleted along with the
``[cli]`` extra.

A deletion with nothing holding it is an invitation to drift: the next person
adding a convenience command would find no objection in the repo. These three
assertions are that objection, and each one fails on its own property —
a CLI module reappearing, a console script pointing at one, or ``click``
creeping back into the dependency list.

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
    assert not stale, "document(s) still advertising a removed CLI:\n  " + "\n  ".join(stale)


def test_click_is_not_a_dependency() -> None:
    """``click`` is gone from dependencies and from every extra.

    It was only ever there for the click CLI; leaving it behind would make the
    core install pay for a library nothing imports.
    """
    text = _PYPROJECT.read_text(encoding="utf-8")
    # Strip comments: prose explaining the removal is allowed to say "click".
    code = "\n".join(line.split("#", 1)[0] for line in text.splitlines())
    assert "click" not in code, "click must not be declared anywhere in pyproject.toml"
