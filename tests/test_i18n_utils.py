"""
Tests for os_helper.i18n_utils.

The properties worth pinning here are the ones a localized product gets
wrong silently: a sentence that exists in one language and not the other, a
placeholder present in one translation and absent from its twin, and a key
that resolves to a developer's identifier in front of a user.

Usage Example
-------------
>>> #   pytest tests/test_i18n_utils.py --cov=os_helper.i18n_utils

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

from pathlib import Path

import pytest

from os_helper.i18n_utils import Locales, _placeholders


def _write(tmp_path: Path, body: str) -> Path:
    target = tmp_path / "i18n.yaml"
    target.write_text(body, encoding="utf-8")
    return target


SOUND = """
meta:
  default_locale: fr
  supported_locales: [fr, en]
gui:
  submit_button:
    fr: Envoyer
    en: Send
  greeting:
    fr: Bonjour {name}
    en: Hello {name}
  product_name: Standpoint
"""


# -- loading ---------------------------------------------------------------


def test_a_sound_file_loads_and_reports_its_metadata(tmp_path: Path) -> None:
    loc = Locales.from_path(_write(tmp_path, SOUND))
    assert loc.default_locale == "fr"
    assert loc.supported_locales == ["fr", "en"]
    assert loc.sections() == ["gui"]


def test_a_missing_file_names_itself(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="locale file not found"):
        Locales.from_path(tmp_path / "absent.yaml")


def test_a_file_without_meta_fails_at_load_not_at_first_lookup(tmp_path: Path) -> None:
    """The whole point of validating here is that the stack trace names the file."""
    with pytest.raises(RuntimeError, match="missing its 'meta' section"):
        Locales.from_path(_write(tmp_path, "gui:\n  a:\n    fr: x\n"))


def test_a_default_locale_outside_supported_is_refused(tmp_path: Path) -> None:
    """A fallback pointing at a locale the file does not carry cannot fall back."""
    body = "meta:\n  default_locale: de\n  supported_locales: [fr, en]\ngui: {}\n"
    with pytest.raises(RuntimeError, match="not among supported_locales"):
        Locales.from_path(_write(tmp_path, body))


def test_a_file_that_is_not_a_mapping_is_refused(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="must parse as a YAML mapping"):
        Locales.from_path(_write(tmp_path, "- just\n- a list\n"))


# -- resolution ------------------------------------------------------------


def test_text_returns_the_asked_for_locale(tmp_path: Path) -> None:
    loc = Locales.from_path(_write(tmp_path, SOUND))
    assert loc.text("gui", "submit_button", "en") == "Send"
    assert loc.text("gui", "submit_button", "fr") == "Envoyer"


def test_text_defaults_to_the_declared_default_locale(tmp_path: Path) -> None:
    loc = Locales.from_path(_write(tmp_path, SOUND))
    assert loc.text("gui", "submit_button") == "Envoyer"


def test_a_bare_string_is_the_same_in_every_locale(tmp_path: Path) -> None:
    """A product name has no translation; forcing one per locale would be noise."""
    loc = Locales.from_path(_write(tmp_path, SOUND))
    assert loc.text("gui", "product_name", "en") == "Standpoint"
    assert loc.text("gui", "product_name", "fr") == "Standpoint"


def test_a_missing_translation_falls_back_rather_than_breaking(tmp_path: Path) -> None:
    body = "meta:\n  default_locale: fr\n  supported_locales: [fr, en]\ngui:\n  only_fr:\n    fr: Bonjour\n"
    loc = Locales.from_path(_write(tmp_path, body))
    assert loc.text("gui", "only_fr", "en") == "Bonjour"


def test_a_key_with_neither_locale_raises_instead_of_showing_the_key(tmp_path: Path) -> None:
    """A raw identifier reaching a user is worse than a loud failure in testing."""
    body = "meta:\n  default_locale: fr\n  supported_locales: [fr, en]\ngui:\n  odd:\n    de: Hallo\n"
    loc = Locales.from_path(_write(tmp_path, body))
    with pytest.raises(KeyError, match="carries neither"):
        loc.text("gui", "odd", "en")


def test_an_unknown_key_or_section_names_what_exists(tmp_path: Path) -> None:
    loc = Locales.from_path(_write(tmp_path, SOUND))
    with pytest.raises(KeyError, match="no key 'nope'"):
        loc.text("gui", "nope")
    with pytest.raises(KeyError, match="no section named 'nope'"):
        loc.section("nope")


def test_meta_is_not_reachable_as_a_content_section(tmp_path: Path) -> None:
    """`meta` is configuration, not copy; serving it as text would be a category error."""
    loc = Locales.from_path(_write(tmp_path, SOUND))
    with pytest.raises(KeyError, match="no section named 'meta'"):
        loc.section("meta")


# -- interpolation ---------------------------------------------------------


def test_render_fills_placeholders(tmp_path: Path) -> None:
    loc = Locales.from_path(_write(tmp_path, SOUND))
    assert loc.render("gui", "greeting", "en", name="Alice") == "Hello Alice"


def test_render_refuses_a_half_filled_sentence(tmp_path: Path) -> None:
    """Formatting would raise anyway; naming the field up front says what to supply."""
    loc = Locales.from_path(_write(tmp_path, SOUND))
    with pytest.raises(KeyError, match=r"needs placeholder\(s\) \['name'\]"):
        loc.render("gui", "greeting", "en")


def test_render_leaves_escaped_braces_alone(tmp_path: Path) -> None:
    """A template carrying JSON must survive formatting untouched."""
    body = (
        "meta:\n  default_locale: en\n  supported_locales: [en]\n"
        'body:\n  payload:\n    en: \'Return {{"ok": true}} for {who}\'\n'
    )
    loc = Locales.from_path(_write(tmp_path, body))
    assert loc.render("body", "payload", "en", who="us") == 'Return {"ok": true} for us'


def test_placeholders_ignores_escapes_and_indexing() -> None:
    assert _placeholders("{a} and {b.c} and {d[0]}") == {"a", "b", "d"}
    assert _placeholders("{{not a field}}") == set()


# -- validation ------------------------------------------------------------


def test_a_sound_file_has_no_problems(tmp_path: Path) -> None:
    assert Locales.from_path(_write(tmp_path, SOUND)).problems() == []


def test_a_missing_translation_is_reported(tmp_path: Path) -> None:
    body = "meta:\n  default_locale: fr\n  supported_locales: [fr, en]\ngui:\n  only_fr:\n    fr: Bonjour\n"
    problems = Locales.from_path(_write(tmp_path, body)).problems()
    assert any("missing its 'en' translation" in p for p in problems)


def test_an_undeclared_locale_is_reported(tmp_path: Path) -> None:
    body = (
        "meta:\n  default_locale: fr\n  supported_locales: [fr, en]\n"
        "gui:\n  k:\n    fr: a\n    en: b\n    de: c\n"
    )
    problems = Locales.from_path(_write(tmp_path, body)).problems()
    assert any("supported_locales does not declare" in p for p in problems)


def test_a_placeholder_that_differs_between_locales_is_reported(tmp_path: Path) -> None:
    """The failure this catches renders a hole in one language only."""
    body = (
        "meta:\n  default_locale: fr\n  supported_locales: [fr, en]\n"
        "gui:\n  greeting:\n    fr: Bonjour {name}\n    en: Hello\n"
    )
    problems = Locales.from_path(_write(tmp_path, body)).problems()
    assert any("renders a hole in one language" in p for p in problems)
    assert Locales.from_path(_write(tmp_path, body)).problems(require_parity=False) == []


def test_problems_reports_every_fault_not_only_the_first(tmp_path: Path) -> None:
    """A translator fixing a file wants the whole list in one pass."""
    body = (
        "meta:\n  default_locale: fr\n  supported_locales: [fr, en]\n"
        "gui:\n  a:\n    fr: x\n  b:\n    fr: y\n  c:\n    fr: z\n"
    )
    assert len(Locales.from_path(_write(tmp_path, body)).problems()) == 3


# -- sections that are deliberately not localized --------------------------

ONE_LANGUAGE_SECTION = """
meta:
  default_locale: fr
  supported_locales: [fr, en]
  unlocalized_sections: [templates]
gui:
  submit_button:
    fr: Envoyer
    en: Send
templates:
  extract:
    system: You extract fields.
    user: Extract {fields} from the text.
"""


def test_an_unlocalized_section_is_not_read_as_missing_translations(tmp_path: Path) -> None:
    """Its sub-keys are roles, not locale codes.

    A product may keep one section in a single language on purpose. Without
    the declaration, every role name ('system', 'user') reads as an
    undeclared locale and every key reads as missing both translations —
    a wall of findings about translations that were never meant to exist.
    """
    loc = Locales.from_path(_write(tmp_path, ONE_LANGUAGE_SECTION))
    assert loc.unlocalized_sections == ["templates"]
    assert loc.problems() == []


def test_an_unlocalized_section_is_still_checked_when_asked_for(tmp_path: Path) -> None:
    loc = Locales.from_path(_write(tmp_path, ONE_LANGUAGE_SECTION))
    assert loc.problems(sections=["templates"]) != []


def test_raw_reaches_an_entry_no_locale_can_resolve(tmp_path: Path) -> None:
    loc = Locales.from_path(_write(tmp_path, ONE_LANGUAGE_SECTION))
    assert loc.raw("templates", "extract")["system"] == "You extract fields."
    with pytest.raises(KeyError, match="carries neither"):
        loc.text("templates", "extract", "fr")
