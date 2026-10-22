"""
Integrity tests for the GUI's message catalogues and the page they feed.

These guard the failures a bilingual page produces *silently*. Under the
gettext shape the suite now uses, the msgid **is** the English copy in
``gui.py``, which buys a readable fallback and costs a new failure mode:
reword the English and its French entry is orphaned, gettext serves the
English, and the page half-reverts with nothing raised. Nothing else in the
build would notice, so :func:`test_the_catalogues_are_sound` hands every
source string the module actually uses to
:meth:`os_helper.Catalog.problems` — which is what turns that silent
half-revert into a red build.

The rest guard the ways a catalogue can be right and still not reach a user:
compiled but untracked, tracked but undeclared, declared but stale. That class
of bug has shipped twice in this suite already — a locale file the wheel did
not contain, reached once through a wrong path and once through a blanket
ignore rule, both invisible locally where the file sits on disk either way.

Deterministic and model-free, so they run in CI as readily as locally.

Usage Example
-------------
>>> #   pytest tests/test_gui_i18n.py --cov=os_helper.gui

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import os_helper as osh
import pytest

from os_helper import gui

_ROOT = Path(__file__).resolve().parent.parent

#: The gettext domain, mirrored here so a rename in `gui.py` shows up as a
#: failure in these tests rather than as a silently skipped check.
_DOMAIN = "os_helper"


def _sources_used() -> set[str]:
    """Every English source string the module asks the catalogue for.

    Two places hold them: the ``{{_("…")}}`` sites in the HTML template,
    which :func:`os_helper.extract_sources` finds, and the values of
    :data:`gui._JS_NAME_TO_SOURCE` for the inline script. The extraction used
    to be a regex copied into all eight members' tests; it lives in os-helper
    now, so a change to the marker is made once.
    """
    return osh.extract_sources(gui._GUI_TEMPLATE) | set(gui._JS_NAME_TO_SOURCE.values())


def test_the_catalogues_are_sound() -> None:
    """The one check that covers the fault this shape is exposed to.

    `Catalog.problems` reports, in one call: a catalogue that was never
    compiled or is stale against its `.po`; an entry left untranslated; a
    source string the code uses that no catalogue carries (the reworded-copy
    fault, which would render as English); and a catalogue entry nothing uses
    (its other half — the orphan left behind by that rewording).
    """
    faults = gui._catalog().problems(used=_sources_used())
    assert faults == [], "catalogue faults:\n  " + "\n  ".join(faults)


def test_the_template_actually_uses_the_translation_marker() -> None:
    """A guard against the guard above passing vacuously.

    `test_the_catalogues_are_sound` compares the catalogue to the strings the
    template asks for. If a refactor broke the marker syntax so that nothing
    matched, that comparison would be empty on both sides and pass while the
    page rendered raw markup. So the count is pinned to something non-trivial.
    """
    sites = re.findall(r'\{\{_\("(.*?)"\)\}\}', gui._GUI_TEMPLATE)
    # A floor rather than an exact count: the point is "the regex still matches
    # real markup", and pinning the exact number would turn every copy edit into
    # a test edit. Eight is comfortably below the smallest GUI in the suite and
    # far above what a broken regex would return, which is zero.
    assert len(sites) >= 8, f"only {len(sites)} translation sites found in the template"


def test_every_injected_script_name_is_read_by_the_script() -> None:
    """A string shipped to the browser that no JavaScript reads is dead weight.

    It also hides a rename: if the script starts reading `T.somethingElse`,
    the old entry keeps translating fine and the new one is silently
    undefined.
    """
    unused = [name for name in gui._JS_NAME_TO_SOURCE if f"T.{name}" not in gui._GUI_TEMPLATE]
    assert not unused, f"injected but never read by the script: {unused}"


@pytest.mark.parametrize("lang", ["fr", "en"])
def test_the_page_renders_whole_in_each_language(lang: str) -> None:
    """Every placeholder is filled, in both directions."""
    page = gui.render_gui(lang)
    assert page.startswith("<!DOCTYPE html>")
    leftover = re.findall(r"\{\{[^}]*\}\}", page)
    assert not leftover, f"unfilled placeholders in {lang}: {leftover[:5]}"
    assert f'<html lang="{lang}"' in page


def test_the_two_languages_actually_differ() -> None:
    """Catch a catalogue that loads but translates nothing."""
    assert gui.render_gui("fr") != gui.render_gui("en")
    assert ">Analyser<" in gui.render_gui("fr")
    assert ">Scan<" in gui.render_gui("en")


def test_the_source_language_needs_no_catalogue() -> None:
    """English is the msgid, so it renders by identity and is always offered."""
    assert "en" in gui.supported_languages()
    assert ">Scan<" in gui.render_gui("en")


def test_an_unknown_language_falls_back_rather_than_failing() -> None:
    """An unknown `?lang=` must be a page, deterministically the default one."""
    assert gui.render_gui("tlh") == gui.render_gui(gui.default_language())


def test_the_script_strings_survive_an_apostrophe() -> None:
    """French copy is full of apostrophes; JSON is why they cannot break out.

    The table is injected as JSON precisely so a quote in the copy cannot
    terminate the JavaScript string it sits in. Parsing it back is the check.
    """
    page = gui.render_gui("fr")
    match = re.search(r"const T = (\{.*?\});", page, re.S)
    assert match, "the injected T table is missing from the page"
    table = json.loads(match.group(1))
    assert set(table) == set(gui._JS_NAME_TO_SOURCE)
    assert any("'" in value or "’" in value for value in table.values()), (
        "no apostrophe anywhere in the French script strings — is this really French?"
    )


def test_an_apostrophe_in_an_attribute_is_escaped() -> None:
    """A French apostrophe in an attribute would close it early.

    Every string is escaped with ``quote=True`` on the way in, which is also
    why any test matching French page text has to escape the same way — look
    for the raw apostrophe and you look for text the page never contains.
    """
    page = gui.render_gui("fr")
    for attribute in re.findall(r'(?:placeholder|aria-label|alt|title)="([^"]*)"', page):
        assert "'" not in attribute or "&#x27;" in attribute or "&" in attribute, (
            f"unescaped apostrophe inside an attribute: {attribute!r}"
        )


def test_no_user_visible_text_is_hard_coded_in_the_template() -> None:
    """Anything between tags must go through the translation marker.

    The regex skips any run containing a brace, which is exactly what a
    translated site looks like now — so what it finds is text that bypassed
    the catalogue. The exceptions are names and machine tokens: `width`,
    `height`, `method` and `vcodec` each name the form field the request
    actually carries, so the wire's spelling is what makes an input checkable
    against the API docs, and codec values are identifiers rather than words.
    """
    allowed = {
        "OS Helper",
        "os-helper",
        "Warith Harchaoui",
        "Tree Radar",
        "OS Helper — Tree Radar",
    }
    literals = {
        text.strip()
        for text in re.findall(r">([^<>{}$]{4,60})<", gui._GUI_TEMPLATE)
        if re.fullmatch(r"[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9'’ .,/—-]{3,}", text.strip())
    }
    assert literals <= allowed, f"user-visible text bypassing i18n: {sorted(literals - allowed)}"


def test_the_language_toggle_offers_the_other_language() -> None:
    """The toggle is computed, not translated, so it needs its own check.

    Its three parts all mean "the other language". Keeping them out of the
    catalogue is what stops a msgid of `/gui?lang=fr` from being treated as
    prose that had drifted — but it also means no catalogue test covers them.
    """
    assert 'href="/gui?lang=en"' in gui.render_gui("fr")
    assert 'href="/gui?lang=fr"' in gui.render_gui("en")
    assert "English version" in gui.render_gui("fr")
    assert "Version française" in gui.render_gui("en")


def test_the_route_serves_the_language_it_is_asked_for() -> None:
    """End to end, through the actual FastAPI route."""
    pytest.importorskip("fastapi", reason="the GUI lives behind the [gui] extra")
    from fastapi.testclient import TestClient

    client = TestClient(gui.create_app(default_root="."))
    assert ">Analyser<" in client.get("/gui?lang=fr").text
    assert ">Scan<" in client.get("/gui?lang=en").text
    unknown = client.get("/gui?lang=tlh")
    assert unknown.status_code == 200
    assert unknown.text == client.get("/gui").text


def test_the_catalogue_sits_inside_the_package() -> None:
    """Outside the package directory it is not package data at all.

    best-engine shipped `locales/` one level above its package: `pip install`
    then gave a package whose every GUI string raised FileNotFoundError, while
    a source checkout worked perfectly.
    """
    import os_helper

    package_dir = Path(os_helper.__file__).resolve().parent
    assert gui._LOCALES_DIR.exists()
    assert gui._LOCALES_DIR.is_relative_to(package_dir), (
        f"{gui._LOCALES_DIR} is outside {package_dir}; it will not travel in the wheel"
    )


def test_the_build_declares_the_catalogue_as_package_data() -> None:
    """Living inside the package is necessary and not sufficient.

    setuptools ships `.py` files on its own; anything else needs declaring.
    Read with a regex rather than ``tomllib``: this package supports Python
    3.10, where ``tomllib`` is not in the standard library, and a test that
    errors on the floor of the supported range is not a test.
    """
    text = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    section = re.search(r"^\[tool\.setuptools\.package-data\](.*?)(?=^\[)", text, re.S | re.M)
    assert section, "pyproject.toml declares no [tool.setuptools.package-data]"
    body = section.group(1)
    assert ".mo" in body, f"package-data does not ship the compiled catalogue:\n{body}"


def test_the_compiled_catalogue_is_tracked_by_git() -> None:
    """The trap this package walked into, one `.gitignore` line away.

    The stock Python `.gitignore` carries a blanket `*.mo`, where a `.mo` is a
    build artifact. Here it is the file the GUI reads at run time. Left
    ignored it is absent from the repository, therefore from the sdist,
    therefore from the wheel — and every string renders as English on an
    installed copy while looking perfect locally, where the file is on disk
    either way. Same broken package as a wrong path, reached by a different
    route, and equally invisible without this test.
    """
    for suffix in (".po", ".mo"):
        rel = f"os_helper/locales/fr/LC_MESSAGES/{_DOMAIN}{suffix}"
        listed = subprocess.run(
            ["git", "ls-files", rel],
            cwd=_ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        assert listed, f"{rel} is not tracked by git (check .gitignore)"


def test_the_shared_loader_is_what_resolves_the_strings() -> None:
    """The suite has one mechanism, and this package is where it lives.

    There is no os-helper floor to check here — this *is* os-helper — so what
    the other seven members assert about their dependency, this one asserts
    about itself: the GUI resolves through `Catalog`, the loader this package
    provides, and not through a second reader grown locally.
    """
    assert isinstance(gui._catalog(), osh.Catalog)
