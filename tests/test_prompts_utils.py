"""
Tests for the model-facing prompt templates.

Two properties matter here and neither is shared with `Catalog`.

First, **shape detection on real data**. A prompt section is keyed either
``key -> language -> text`` or ``key -> field -> language -> text``, and the
two are hard to tell apart by nesting alone: a first implementation guessed
from it and was wrong on standpoint, whose prompt section also carries a whole
``gui`` sub-tree shaped ``{en: {...}, fr: {...}}`` — values that *are*
mappings under keys that are plainly languages. The discriminator is the
file's own declared locales, and the fixtures below include that exact trap.

Second, **the placeholder check across languages**. A translated prompt that
drops a ``{field}`` the code fills raises at render time, in production, for
whoever first asks for that language — there is no earlier signal. That is
what `problems()` exists to turn into a red build.

Author
------
[Warith HARCHAOUI](https://linkedin.com/in/warith-harchaoui/)
"""

from __future__ import annotations

from pathlib import Path

import pytest

import os_helper as osh

_SOUND = """
meta:
  default_locale: en
  supported_locales: [en, fr, es]

prompts:
  axis_prompt:
    en: You are naming the four poles of {count} axes.
    fr: Vous nommez les quatre pôles de {count} axes.
    es: Estás nombrando los cuatro polos de {count} ejes.
  verdict:
    en: Layout checks passed.
    fr: Vérifications de mise en page réussies.
    es: Verificaciones de disposición superadas.
  critique:
    system:
      en: You are a strict reviewer.
      fr: Vous êtes un relecteur strict.
      es: Eres un revisor estricto.
    user:
      en: Examine {subject}.
      fr: Examinez {subject}.
      es: Examina {subject}.
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "i18n.yaml"
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def prompts(tmp_path: Path) -> osh.Prompts:
    """A sound three-language section with both shapes in it."""
    return osh.Prompts.from_path(_write(tmp_path, _SOUND))


def test_a_simple_prompt_reads_in_each_language(prompts: osh.Prompts) -> None:
    """The ordinary case: key plus language in, template out."""
    assert prompts.text("verdict", "fr") == "Vérifications de mise en page réussies."
    assert prompts.text("verdict", "es") == "Verificaciones de disposición superadas."
    assert prompts.text("verdict", "en") == "Layout checks passed."


def test_a_fielded_prompt_reads_one_part_at_a_time(prompts: osh.Prompts) -> None:
    """`system` and `user` are parts of one prompt, not two prompts."""
    assert prompts.text("critique", "fr", field="system") == "Vous êtes un relecteur strict."
    assert prompts.text("critique", "es", field="user") == "Examina {subject}."


def test_asking_a_fielded_prompt_without_a_field_says_so(prompts: osh.Prompts) -> None:
    """Returning the `system` part by default would be a silent wrong answer."""
    with pytest.raises(KeyError, match="comes in parts"):
        prompts.text("critique", "fr")


def test_an_unknown_key_names_what_is_available(prompts: osh.Prompts) -> None:
    """A prompt that silently became its own key would reach a model."""
    with pytest.raises(KeyError, match="no prompt 'nope'"):
        prompts.text("nope", "fr")


def test_languages_are_taken_from_the_prompts_themselves(prompts: osh.Prompts) -> None:
    """A package may be bilingual in its GUI and trilingual in its prompts."""
    assert prompts.languages == ("en", "es", "fr")


def test_a_regional_tag_resolves_to_its_base_language(prompts: osh.Prompts) -> None:
    """`fr-CA` should get the French prompt, not the English default."""
    assert prompts.resolve("fr-CA") == "fr"
    assert prompts.text("verdict", "fr_CA.UTF-8") == "Vérifications de mise en page réussies."


def test_an_unknown_language_falls_back_to_the_default(prompts: osh.Prompts) -> None:
    """A model must be given *some* instruction, deterministically."""
    assert prompts.resolve("de") == "en"
    assert prompts.text("verdict", "de") == "Layout checks passed."


def test_render_fills_the_placeholders(prompts: osh.Prompts) -> None:
    """Templates are data: this formats, it never evaluates."""
    assert prompts.render("axis_prompt", "fr", count=2) == "Vous nommez les quatre pôles de 2 axes."


def test_render_says_what_it_was_not_given(prompts: osh.Prompts) -> None:
    """A half-filled instruction does not fail — the model answers the wrong
    question, which is far worse than an exception."""
    with pytest.raises(KeyError, match="needs \\['count'\\]"):
        prompts.render("axis_prompt", "fr")


def test_bundle_returns_every_prompt_for_one_language(prompts: osh.Prompts) -> None:
    """How prompts are really consumed: resolve the language once, read many.

    Asking key by key re-resolves the language each time, which is slower and
    an invitation to resolve it inconsistently across one request.
    """
    spanish = prompts.bundle("es")
    assert spanish["verdict"] == "Verificaciones de disposición superadas."
    assert spanish["critique"]["system"] == "Eres un revisor estricto."
    assert set(spanish) == {"axis_prompt", "verdict", "critique"}


def test_a_language_subtree_is_not_mistaken_for_fields(tmp_path: Path) -> None:
    """The trap that broke the first implementation, from real data.

    standpoint keeps a whole `gui` sub-tree inside its prompt section, shaped
    `{en: {...}, fr: {...}}`: its values are mappings, so a "values are dicts
    means fields" heuristic reads `en` and `fr` as field names and then reports
    every GUI key as a language. The declared locales settle it.
    """
    source = _SOUND + """
  gui:
    en:
      run_button: Run
    fr:
      run_button: Lancer
    es:
      run_button: Ejecutar
"""
    prompts = osh.Prompts.from_path(_write(tmp_path, source))
    assert prompts.languages == ("en", "es", "fr"), (
        "a language-keyed sub-tree was read as fields"
    )
    assert prompts.bundle("fr")["gui"] == {"run_button": "Lancer"}


def test_problems_is_quiet_on_a_sound_section(prompts: osh.Prompts) -> None:
    """The guard must not cry wolf, or nobody keeps it green."""
    assert prompts.problems() == []


def test_problems_catches_a_dropped_placeholder(tmp_path: Path) -> None:
    """The failure specific to this shape, and the reason `problems` exists.

    A French prompt missing the `{count}` the code fills does not fail when it
    is written, nor when the file is loaded, nor for anyone reading English.
    It raises inside `format()` on the first request that asks for French.
    """
    broken = _SOUND.replace(
        "fr: Vous nommez les quatre pôles de {count} axes.",
        "fr: Vous nommez les quatre pôles des axes.",
    )
    faults = osh.Prompts.from_path(_write(tmp_path, broken)).problems()
    assert any("placeholders" in f and "'fr'" in f for f in faults), faults


def test_problems_catches_an_extra_placeholder(tmp_path: Path) -> None:
    """A placeholder the English does not have is just as fatal.

    It reaches `format()` with no value and raises there, so the asymmetry is
    reported in both directions rather than only for what is missing.
    """
    broken = _SOUND.replace(
        "es: Estás nombrando los cuatro polos de {count} ejes.",
        "es: Estás nombrando los cuatro polos de {count} ejes sobre {topic}.",
    )
    faults = osh.Prompts.from_path(_write(tmp_path, broken)).problems()
    assert any("placeholders" in f and "'es'" in f for f in faults), faults


def test_problems_catches_a_language_a_prompt_forgot(tmp_path: Path) -> None:
    """One prompt missing Spanish while its neighbours have it.

    The caller asked for Spanish and gets English, which for a model means a
    different answer — not a cosmetic fallback.
    """
    broken = _SOUND.replace("    es: Verificaciones de disposición superadas.\n", "")
    faults = osh.Prompts.from_path(_write(tmp_path, broken)).problems()
    assert any("no 'es' text" in f for f in faults), faults


def test_problems_catches_an_empty_prompt(tmp_path: Path) -> None:
    """An empty instruction is worse than a missing one: it reaches the model."""
    broken = _SOUND.replace("    fr: Vérifications de mise en page réussies.", '    fr: ""')
    faults = osh.Prompts.from_path(_write(tmp_path, broken)).problems()
    assert any("empty" in f for f in faults), faults


def test_a_bare_string_prompt_is_language_invariant(tmp_path: Path) -> None:
    """Some templates are the same everywhere and should not be duplicated."""
    source = _SOUND + """
  separator: "---"
"""
    prompts = osh.Prompts.from_path(_write(tmp_path, source))
    assert prompts.text("separator", "fr") == "---"
    assert prompts.text("separator", "es") == "---"
    assert prompts.problems() == []
