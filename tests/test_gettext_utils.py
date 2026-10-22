"""
Tests for the gettext-backed message catalogues.

Two things have to hold for :mod:`os_helper.gettext_utils` to be trustworthy.

First, the ``.mo`` this package writes must be a real ``.mo``. The whole point
of writing the format here is to avoid depending on GNU ``msgfmt``, so the
proof cannot be "our reader reads our writer" — every round-trip below is
checked with **stdlib** :mod:`gettext`, which knows nothing about this code.

Second, the drift guard must actually bite. Keying on the English source
string means rewording a sentence orphans its translation and the page
half-reverts to English with nothing raised; :meth:`Catalog.problems` is the
only thing standing between that and a release, so each fault it claims to
detect is provoked here rather than assumed.

Author
------
[Warith HARCHAOUI](https://linkedin.com/in/warith-harchaoui/)
"""

from __future__ import annotations

import gettext as stdlib_gettext
from pathlib import Path

import pytest

import os_helper as osh

#: A catalogue with the three cases French copy actually produces: an ordinary
#: sentence, one carrying an apostrophe and an accent, and one left untranslated.
_PO = """# Test catalogue.
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Convert a document"
msgstr "Convertir un document"

msgid "The bench couldn't start"
msgstr "Le banc n'a pas pu démarrer"

msgid "Still in English"
msgstr ""
"""


@pytest.fixture
def catalogue(tmp_path: Path) -> Path:
    """A compiled ``locales/`` tree, returned as its root directory."""
    messages = tmp_path / "locales" / "fr" / "LC_MESSAGES"
    messages.mkdir(parents=True)
    (messages / "demo.po").write_text(_PO, encoding="utf-8")
    osh.compile_catalogs(tmp_path / "locales")
    return tmp_path / "locales"


def test_the_written_mo_is_readable_by_stdlib_gettext(catalogue: Path) -> None:
    """The format check that matters: a reader that is not ours.

    `build_mo` exists so that no machine needs GNU `msgfmt` installed. If the
    bytes it produces were subtly wrong — a bad offset, the wrong byte order —
    a test that read them back through this same module would still pass. So
    the assertion goes through `gettext.translation` instead.
    """
    translator = stdlib_gettext.translation("demo", localedir=str(catalogue), languages=["fr"])
    assert translator.gettext("Convert a document") == "Convertir un document"


def test_french_punctuation_survives_the_round_trip(catalogue: Path) -> None:
    """An apostrophe and an accent in one string, read back by stdlib gettext.

    French copy is full of both, and they are exactly what a hand-rolled
    binary writer gets wrong: the apostrophe because of escaping, the accent
    because the length fields count *bytes* while Python counts characters.
    """
    translator = stdlib_gettext.translation("demo", localedir=str(catalogue), languages=["fr"])
    assert translator.gettext("The bench couldn't start") == "Le banc n'a pas pu démarrer"


def test_an_untranslated_entry_falls_back_to_its_english_source(catalogue: Path) -> None:
    """`msgstr ""` must serve the msgid, not an empty string.

    This is the property that makes a half-finished catalogue acceptable: the
    interface is partly translated rather than partly blank.
    """
    cat = osh.Catalog.from_package(catalogue, "demo")
    assert cat.gettext("fr", "Still in English") == "Still in English"


def test_a_string_absent_from_the_catalogue_renders_as_english(catalogue: Path) -> None:
    """An unknown msgid is returned unchanged rather than raising."""
    cat = osh.Catalog.from_package(catalogue, "demo")
    assert cat.gettext("fr", "Never written down") == "Never written down"


def test_the_source_language_needs_no_catalogue(catalogue: Path) -> None:
    """English is the msgid, so it is always available and always identity."""
    cat = osh.Catalog.from_package(catalogue, "demo")
    assert "en" in cat.languages
    assert cat.gettext("en", "Convert a document") == "Convert a document"


def test_an_unknown_language_resolves_to_the_default(catalogue: Path) -> None:
    """An unknown `?lang=` must never 500, and must be deterministic."""
    cat = osh.Catalog.from_package(catalogue, "demo", default_language="fr")
    assert cat.resolve("tlh") == "fr"
    assert cat.gettext("tlh", "Convert a document") == "Convertir un document"


def test_a_language_without_a_compiled_catalogue_is_not_offered(tmp_path: Path) -> None:
    """A `.po` with no `.mo` cannot be served, so it must not be listed.

    Announcing it would offer the user a language that silently renders
    English — worse than not offering it, because the failure looks like a
    translation nobody finished rather than a build step nobody ran.
    """
    messages = tmp_path / "locales" / "de" / "LC_MESSAGES"
    messages.mkdir(parents=True)
    (messages / "demo.po").write_text(_PO, encoding="utf-8")  # deliberately not compiled
    cat = osh.Catalog.from_package(tmp_path / "locales", "demo")
    assert "de" not in cat.languages


def test_problems_reports_an_untranslated_entry(catalogue: Path) -> None:
    """A translator who stopped halfway is a fault a test should see."""
    faults = osh.Catalog.from_package(catalogue, "demo").problems()
    assert any("Still in English" in f for f in faults), faults


def test_problems_reports_a_stale_mo(catalogue: Path) -> None:
    """A translation edited without recompiling must not reach a release.

    Provoked, not assumed: the `.po` is rewritten and the `.mo` left alone,
    which is precisely what an editor does.
    """
    po_path = catalogue / "fr" / "LC_MESSAGES" / "demo.po"
    po_path.write_text(
        po_path.read_text(encoding="utf-8").replace(
            "Convertir un document", "Convertir un fichier"
        ),
        encoding="utf-8",
    )
    faults = osh.Catalog.from_package(catalogue, "demo").problems()
    assert any("stale" in f for f in faults), faults


def test_problems_reports_a_missing_mo(tmp_path: Path) -> None:
    """A catalogue that was never compiled at all."""
    messages = tmp_path / "locales" / "fr" / "LC_MESSAGES"
    messages.mkdir(parents=True)
    (messages / "demo.po").write_text(_PO, encoding="utf-8")
    faults = osh.Catalog.from_package(tmp_path / "locales", "demo").problems()
    assert any("missing" in f for f in faults), faults


def test_problems_catches_a_reworded_source_string(catalogue: Path) -> None:
    """The fault this whole shape is exposed to, and the reason `used` exists.

    Rewording the English in the template leaves the French catalogue keyed to
    the old sentence. gettext then falls back to English, so the page
    half-reverts and nothing raises. Both halves of the fault must be named:
    the string the code now asks for, and the entry left orphaned.
    """
    used = {"Convert a file", "The bench couldn't start", "Still in English"}
    faults = osh.Catalog.from_package(catalogue, "demo").problems(used=used)
    assert any("'Convert a file'" in f and "render as English" in f for f in faults), faults
    assert any("'Convert a document'" in f and "no code uses" in f for f in faults), faults


def test_problems_is_quiet_on_a_sound_catalogue(tmp_path: Path) -> None:
    """The guard must not cry wolf, or nobody will keep it green.

    Same fixture minus the deliberately untranslated entry, checked against
    exactly the strings it carries.
    """
    messages = tmp_path / "locales" / "fr" / "LC_MESSAGES"
    messages.mkdir(parents=True)
    (messages / "demo.po").write_text(
        _PO.replace('msgid "Still in English"\nmsgstr ""\n', ""), encoding="utf-8"
    )
    osh.compile_catalogs(tmp_path / "locales")
    cat = osh.Catalog.from_package(tmp_path / "locales", "demo")
    assert cat.problems(used={"Convert a document", "The bench couldn't start"}) == []


def test_compile_catalogs_check_mode_writes_nothing(catalogue: Path) -> None:
    """`check=True` is for CI, so it must not repair what it is auditing."""
    mo_path = catalogue / "fr" / "LC_MESSAGES" / "demo.mo"
    mo_path.write_bytes(b"deliberately corrupt")
    stale = osh.compile_catalogs(catalogue, check=True)
    assert stale == [mo_path]
    assert mo_path.read_bytes() == b"deliberately corrupt"


def test_parse_po_drops_empty_translations_and_keeps_real_ones(catalogue: Path) -> None:
    """The parser's contract, which `build_mo` depends on."""
    entries = osh.parse_po(catalogue / "fr" / "LC_MESSAGES" / "demo.po")
    assert entries["Convert a document"] == "Convertir un document"
    assert "Still in English" not in entries


# --------------------------------------------------------------------------- #
# Language negotiation: region fallback, plurals, Accept-Language
# --------------------------------------------------------------------------- #


def test_a_regional_tag_falls_back_to_its_base_language(catalogue: Path) -> None:
    """`fr-CA` has no catalogue, but `fr` does, and that is what it wants.

    A Québécois browser asking for `fr-CA` should get French, not the default
    served as if it had asked for nothing.
    """
    cat = osh.Catalog.from_package(catalogue, "demo")
    assert cat.resolve("fr-CA") == "fr"
    assert cat.resolve("fr_CA.UTF-8@euro") == "fr"
    assert cat.gettext("fr-CA", "Convert a document") == "Convertir un document"


def test_language_candidates_normalises_both_spellings() -> None:
    """BCP 47 writes `fr-CA`; POSIX writes `fr_CA.UTF-8`; gettext wants `fr_CA`."""
    assert osh.language_candidates("fr-CA") == ["fr_CA", "fr"]
    assert osh.language_candidates("fr_CA.UTF-8@euro") == ["fr_CA", "fr"]
    assert osh.language_candidates("fr") == ["fr"]
    assert osh.language_candidates("") == []
    assert osh.language_candidates(None) == []


def test_ngettext_asks_the_catalogue_which_form_to_use(catalogue: Path) -> None:
    """Plural choice belongs to the language, not to an `n == 1` at the call site.

    With no plural entry the English source is returned, picked by gettext's
    own default rule — which is still the right answer, and still not a
    branch the caller had to write.
    """
    cat = osh.Catalog.from_package(catalogue, "demo")
    assert cat.ngettext("fr", "one file", "many files", 1) == "one file"
    assert cat.ngettext("fr", "one file", "many files", 3) == "many files"


def test_negotiate_honours_q_weights(catalogue: Path) -> None:
    """The strongest weight wins, not the first tag listed."""
    cat = osh.Catalog.from_package(catalogue, "demo")
    assert cat.negotiate("en;q=0.2, fr;q=0.9") == "fr"


def test_negotiate_returns_none_when_the_visitor_wants_the_source_language(
    catalogue: Path,
) -> None:
    """English is *offered* even though it has no catalogue, and that matters.

    Without counting it, a visitor who asked for English first and French
    second would be served French — the language they actually wanted being
    the one the loop could not see. `None` means "leave the source alone",
    which a caller can tell apart from "nothing we have was asked for".
    """
    cat = osh.Catalog.from_package(catalogue, "demo")
    assert cat.negotiate("en;q=0.9, fr;q=0.8") is None


def test_negotiate_falls_back_from_a_region_and_ignores_wildcards(
    catalogue: Path,
) -> None:
    """`fr-CA` should reach the `fr` catalogue; `*` is not a language."""
    cat = osh.Catalog.from_package(catalogue, "demo")
    assert cat.negotiate("fr-CA;q=0.9, de;q=0.8") == "fr"
    assert cat.negotiate("*") is None


def test_negotiate_survives_a_malformed_q_value(catalogue: Path) -> None:
    """A browser's broken header is not a reason to refuse it a language."""
    cat = osh.Catalog.from_package(catalogue, "demo")
    assert cat.negotiate("fr;q=notanumber") == "fr"


def test_negotiate_on_an_empty_or_absent_header_is_none(catalogue: Path) -> None:
    """No header is not a preference, so there is nothing to honour."""
    cat = osh.Catalog.from_package(catalogue, "demo")
    assert cat.negotiate(None) is None
    assert cat.negotiate("") is None


# --------------------------------------------------------------------------- #
# Extraction and context — the two steps the guide names that were missing
# --------------------------------------------------------------------------- #


def test_extract_sources_finds_every_marked_string() -> None:
    """The step a gettext workflow normally gets from `pybabel`.

    Eight members each kept their own copy of this regex before it moved
    here, which is the duplication a shared loader exists to end.
    """
    template = '<h1>{{_("Run")}}</h1><p>{{_("Done.")}}</p><em>{{_("Run")}}</em>'
    assert osh.extract_sources(template) == {"Run", "Done."}


def test_extract_sources_unions_several_texts() -> None:
    """A member's strings live in the markup and in its script table."""
    assert osh.extract_sources('{{_("A")}}', '{{_("B")}}') == {"A", "B"}


def test_extract_sources_keeps_two_markers_on_one_line_apart() -> None:
    """Non-greedy, or the first marker would swallow through to the last."""
    assert osh.extract_sources('{{_("one")}} and {{_("two")}}') == {"one", "two"}


def test_extract_sources_ignores_an_unterminated_marker() -> None:
    """A broken marker must not eat the rest of the page."""
    assert osh.extract_sources('{{_("fine")}} {{_("oops) <p>text</p>') == {"fine"}


def test_a_context_separates_two_identical_source_strings(tmp_path: Path) -> None:
    """One English word, two French words — the case `msgctxt` exists for.

    Without context both uses share a msgid, so a translator has to pick one
    French word for both and one of the two screens is wrong.
    """
    messages = tmp_path / "locales" / "fr" / "LC_MESSAGES"
    messages.mkdir(parents=True)
    (messages / "demo.po").write_text(
        '''msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

msgctxt "month name"
msgid "May"
msgstr "mai"

msgctxt "verb"
msgid "May"
msgstr "pouvoir"
''',
        encoding="utf-8",
    )
    osh.compile_catalogs(tmp_path / "locales")
    cat = osh.Catalog.from_package(tmp_path / "locales", "demo")
    assert cat.pgettext("fr", "month name", "May") == "mai"
    assert cat.pgettext("fr", "verb", "May") == "pouvoir"


def test_an_unknown_context_falls_back_to_the_source_not_to_the_key(
    catalogue: Path,
) -> None:
    """The fallback must never leak the `context\\x04message` key.

    gettext returns the key it looked up when it finds nothing, and that key
    carries a control character — putting it in front of a reader would be
    worse than showing untranslated English.
    """
    cat = osh.Catalog.from_package(catalogue, "demo")
    assert cat.pgettext("fr", "no such context", "Convert a document") == "Convert a document"


def test_a_context_entry_does_not_disturb_the_plain_one(tmp_path: Path) -> None:
    """Parsing `msgctxt` must not break the ordinary entries beside it.

    Provoked because it did: adding context support first dropped the commit
    between entries, so every msgid overwrote the previous one and the header
    itself vanished.
    """
    messages = tmp_path / "locales" / "fr" / "LC_MESSAGES"
    messages.mkdir(parents=True)
    (messages / "demo.po").write_text(
        '''msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Plain"
msgstr "Simple"

msgctxt "ctx"
msgid "Plain"
msgstr "Avec contexte"

msgid "After"
msgstr "Après"
''',
        encoding="utf-8",
    )
    osh.compile_catalogs(tmp_path / "locales")
    cat = osh.Catalog.from_package(tmp_path / "locales", "demo")
    assert cat.gettext("fr", "Plain") == "Simple"
    assert cat.pgettext("fr", "ctx", "Plain") == "Avec contexte"
    assert cat.gettext("fr", "After") == "Après"
