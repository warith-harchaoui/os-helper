"""
Integrity tests for the GUI's localization file and the page it feeds.

:mod:`tests.test_i18n_utils` covers the loader itself. This file covers the
*use* of it by :mod:`os_helper.gui`, and guards the failures a bilingual page
produces silently: a key present in one language and not the other, a
``{{TOKEN}}`` that no key fills (it renders as itself and reads like a layout
bug), and a string written straight into the template where no translator will
ever find it.

Deterministic and model-free, so they run in CI as readily as locally. The
packaging tests at the end exist because the same class of bug shipped twice
in this suite: a locale file that the wheel did not contain, reached once
through a wrong path and once through a blanket ``*.yaml`` in ``.gitignore``,
both invisible locally where the file sits on disk either way.

Usage Example
-------------
>>> #   pytest tests/test_gui_i18n.py --cov=os_helper.gui

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from os_helper import gui

_ROOT = Path(__file__).resolve().parent.parent


def test_the_shared_validator_finds_nothing_wrong() -> None:
    """The section 21.3.7 check, in one line thanks to the shared loader.

    It covers the faults nobody thought to write a test for — a locale the
    file declares and a key forgets, a placeholder present in French and
    absent from English — which the targeted assertions below cannot reach.
    """
    assert gui._locales().problems() == []


def test_every_template_token_is_filled_by_a_key() -> None:
    """An unfilled `{{TOKEN}}` renders as itself, which reads as a layout bug."""
    tokens = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", gui._GUI_TEMPLATE))
    # LANG, T_JSON and ROOT_JSON are substituted by render_gui itself, not
    # from a key: one is the resolved locale, one the whole string table, one
    # the server's launch folder.
    declared = set(gui._HTML_TOKEN_TO_KEY) | {"LANG", "T_JSON", "ROOT_JSON"}
    assert tokens <= declared, f"template tokens no key fills: {sorted(tokens - declared)}"


def test_every_declared_token_is_actually_in_the_template() -> None:
    """The other direction: a map entry for a token that no longer exists.

    Harmless at runtime, which is why it rots — and it leaves a locale key
    looking used when nothing uses it.
    """
    tokens = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", gui._GUI_TEMPLATE))
    assert set(gui._HTML_TOKEN_TO_KEY) <= tokens, (
        f"declared but absent from the template: {sorted(set(gui._HTML_TOKEN_TO_KEY) - tokens)}"
    )


def test_every_key_the_gui_asks_for_exists_in_the_locale_file() -> None:
    asked = set(gui._HTML_TOKEN_TO_KEY.values()) | set(gui._JS_NAME_TO_KEY.values())
    known = set(gui._locales().section("gui"))
    assert asked, "neither key map was read; the test is broken, not the code"
    assert asked <= known, f"gui.py asks for keys the locale file lacks: {sorted(asked - known)}"


def test_every_injected_script_name_is_read_by_the_script() -> None:
    """A string shipped to the page that no line of JavaScript consumes.

    Dead weight in the payload, and a translated sentence nobody will ever
    see — the kind of thing that survives a rename of its only caller.
    """
    script = gui._GUI_TEMPLATE
    unused = [name for name in gui._JS_NAME_TO_KEY if f"T.{name}" not in script]
    assert not unused, f"injected but never read by the page: {sorted(unused)}"


@pytest.mark.parametrize("lang", ["fr", "en"])
def test_the_page_renders_whole_in_each_language(lang: str) -> None:
    page = gui.render_gui(lang, root="/tmp")
    assert page.lstrip().startswith("<!DOCTYPE html>")
    assert "{{" not in page, f"{lang}: a token survived rendering"
    assert f'<html lang="{lang}"' in page


def test_the_two_languages_actually_differ() -> None:
    """A localized page that renders identically is a wiring bug, not a translation."""
    assert gui.render_gui("fr") != gui.render_gui("en")


def test_an_unknown_language_falls_back_rather_than_failing() -> None:
    """A mistyped ``?lang=`` must return a page, not a 500."""
    assert gui.render_gui("tlh") == gui.render_gui(gui.default_language())
    assert gui.render_gui("") == gui.render_gui(gui.default_language())


def test_the_script_strings_survive_an_apostrophe() -> None:
    """French copy is full of apostrophes; JSON is what they cannot break out of."""
    page = gui.render_gui("fr")
    assert "const T = {" in page
    # The French "Indiquez d'abord…" carries one, and it must reach the page
    # intact rather than closing a JavaScript string early.
    assert "d'abord" in page


def test_the_launch_root_is_embedded_as_a_json_literal() -> None:
    """A Windows path's backslashes must not break the script.

    ``C:\\Users\\me`` pasted raw into JavaScript is ``C:Usersme`` at best and
    a syntax error at worst; as a JSON literal it survives intact.
    """
    page = gui.render_gui("fr", root=r"C:\Users\me")
    assert r'"C:\\Users\\me" || ""' in page


def test_no_user_visible_text_is_hard_coded_in_the_template() -> None:
    """Anything between tags must come from the locale file.

    The exceptions are names and machine tokens, which are not translated.
    """
    allowed = {"OS Helper", "os-helper", "Warith Harchaoui"}
    literals = {
        text.strip()
        for text in re.findall(r">([^<>{}$]{4,60})<", gui._GUI_TEMPLATE)
        if re.fullmatch(r"[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9'’ .,/—-]{3,}", text.strip())
    }
    assert literals <= allowed, f"user-visible text bypassing i18n: {sorted(literals - allowed)}"


def test_the_route_serves_the_language_it_is_asked_for() -> None:
    """End to end, through the actual FastAPI route."""
    fastapi = pytest.importorskip("fastapi", reason="the GUI lives behind the [gui] extra")
    from fastapi.testclient import TestClient

    assert fastapi  # the import above is the point; keep the name used
    client = TestClient(gui.create_app(default_root="."))
    assert ">Analyser<" in client.get("/gui?lang=fr").text
    assert ">Scan<" in client.get("/gui?lang=en").text
    # Unknown locale: a page, not a 500.
    unknown = client.get("/gui?lang=tlh")
    assert unknown.status_code == 200
    assert unknown.text == client.get("/gui").text


def test_the_locale_file_sits_inside_the_package() -> None:
    """Data beside the package is not data in the wheel.

    best-engine shipped `locales/i18n.yaml` one level above its package with
    `packages.find` limited to the package itself, so the file never entered
    the wheel: on PyPI 1.5.0, a clean `pip install` produced a package whose
    every GUI string raised FileNotFoundError. Nothing caught it because a
    repo checkout and an editable install both have the file right where the
    code looks.

    This asserts the property that survives packaging: the file is under the
    importable package directory, which is what `package-data` can ship.
    """
    import os_helper

    package_dir = Path(os_helper.__file__).resolve().parent
    assert gui._LOCALES_PATH.exists()
    assert gui._LOCALES_PATH.is_relative_to(package_dir), (
        f"{gui._LOCALES_PATH} is outside {package_dir}; it will not travel in the wheel"
    )


def test_the_build_declares_the_locale_file_as_package_data() -> None:
    """Living inside the package is necessary and not sufficient.

    setuptools ships `.py` files on its own; anything else needs declaring.

    Read with a regex rather than ``tomllib``: this package supports Python
    3.10, where ``tomllib`` is not in the standard library, and a test that
    errors on the floor of the supported range is not a test.
    """
    text = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    section = re.search(
        r"^\[tool\.setuptools\.package-data\](.*?)(?=^\[)", text, re.S | re.M
    )
    assert section, "pyproject.toml declares no [tool.setuptools.package-data]"
    assert re.search(r"locales/\*?\.?\w*\.?yaml", section.group(1)), (
        f"package-data does not cover the locale file:\n{section.group(1)}"
    )


def test_the_locale_file_is_tracked_by_git() -> None:
    """Living inside the package and being declared is still not enough.

    This repository's `.gitignore` carries a blanket `*.yaml`, so the locale
    file was invisible to git when first added: it would have been absent
    from the repository, therefore from the sdist, therefore from the wheel —
    the same broken package as a wrong path, reached by a different route,
    and equally invisible locally where the file sits on disk either way.
    """
    listed = subprocess.run(
        ["git", "ls-files", "os_helper/locales/i18n.yaml"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    assert listed, "the locale file is not tracked by git (check .gitignore's *.yaml)"
