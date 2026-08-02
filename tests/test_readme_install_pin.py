"""Guard against stale install instructions on the PyPI project page.

This package is published to PyPI on purpose, so the README / LISEZMOI install
commands must be `pip install <name>` (always the latest release). A hardcoded
`pip install "git+https://github.com/warith-harchaoui/<name>.git@vX.Y.Z"` drifts:
once the README is rendered on the PyPI page it tells users to install a version
that is several releases old. This test fails the build if such a self-pin ever
comes back, in either README or LISEZMOI.
"""

from __future__ import annotations

import re
from pathlib import Path

# Repo root = the directory that holds pyproject.toml (tests/ is one level down).
_ROOT = Path(__file__).resolve().parent.parent


def _package_name() -> str:
    """Read the distribution name from pyproject.toml without a TOML parser.

    A plain regex keeps this working on Python 3.10 (no stdlib ``tomllib``) and
    on every helper regardless of how its version is sourced.
    """
    text = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^\s*name\s*=\s*"([^"]+)"', text)
    assert match, "could not find the project name in pyproject.toml"
    return match.group(1)


# Generated / vendored / local-only trees that are not ours to police. `.private`
# is gitignored working scratch (never shipped, never rendered on PyPI), so a pin
# there cannot mislead anyone.
_SKIP = {
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".git",
    "__pycache__",
    ".private",
}


def _markdown_files() -> list[Path]:
    """Every tracked Markdown file in the repo, minus generated/vendored trees."""
    return [
        p
        for p in _ROOT.rglob("*.md")
        if not any(part in _SKIP for part in p.relative_to(_ROOT).parts)
    ]


def test_no_markdown_pins_a_stale_git_version() -> None:
    """No Markdown file may pin this package's own git install to a fixed tag.

    The package is on PyPI, so install docs read `pip install <name>`; a
    `git+https://...<name>.git@vX.Y.Z` self-pin drifts and misleads users on the
    rendered PyPI page. Scans every Markdown file, not just README/LISEZMOI.
    """
    name = _package_name()
    pin = re.compile(
        rf"git\+https://github\.com/warith-harchaoui/{re.escape(name)}\.git@v[0-9]"
    )
    offenders: list[str] = []
    for path in _markdown_files():
        if pin.search(path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(_ROOT)))
    assert not offenders, (
        f"these Markdown files pin a stale git version tag: {offenders}; "
        f"the package is on PyPI, so use `pip install {name}` instead."
    )
