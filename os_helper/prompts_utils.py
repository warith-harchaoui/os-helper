"""
Model-Facing Prompt Templates, in Several Languages

The third localization shape the suite needs, and the one that is **not**
translation. :class:`~os_helper.Catalog` serves interface copy keyed on its
English source; :class:`~os_helper.i18n_utils.Locales` serves any text keyed
on meaning; :class:`Prompts` serves the text a *model* reads, which looks like
the second but is consumed like neither.

Why prompts are not gettext
---------------------------
A prompt's language versions are **independently authored, not translated**.
Measured in standpoint on 2026-10-22, one prompt ran 1345 characters in
English, 1532 in French and 1479 in Spanish: nobody translated that: somebody
wrote the instruction three times, because what makes a model behave in French
is not the French words of the English sentence.

Two consequences follow, and they are the whole reason this module exists
rather than a second catalogue:

* **The key is the stable thing.** Prompt engineering reworks the wording
  constantly. Key on the English text, as gettext does, and every tweak to the
  English orphans the other languages — which then fall back to English
  silently, exactly where a wrong language is hardest to notice. Key on
  ``axis_prompt`` and the wording is free to move.
* **A 1300-character msgid is not a catalogue entry.** It is unreadable in a
  ``.po``, unusable in a translation tool, and meaningless to a translator who
  is not a prompt engineer.

So prompts stay keyed on meaning, in YAML, read through :class:`Locales` —
which already parses, validates and falls back. What this class adds is the
four things every caller was otherwise writing by hand:

1. the **whole-language view** (a caller wants every prompt for one language,
   not one prompt at a time), cached;
2. the **field shape** ``key.system`` / ``key.user``, for prompts that come in
   parts;
3. **language resolution** for a requested tag, so ``fr-CA`` finds ``fr``;
4. a **placeholder check across languages** — the failure specific to this
   shape, where a translated prompt drops a ``{field}`` the code fills and the
   render raises in production rather than in a test.

Layout
------
::

    prompts:
      axis_prompt:                  # simple: key -> language -> text
        en: You are naming the four poles…
        fr: Vous nommez les quatre pôles…
      eyeball_critique:             # fielded: key -> field -> language -> text
        system:
          en: You are a strict visual-quality reviewer…
        user:
          en: Examine the image and write…

Usage example
-------------
>>> # p = Prompts.from_path("standpoint/locales/i18n.yaml", section="bundle")
>>> # p.text("axis_prompt", "fr")
>>> # p.render("title_template", "fr", domain="LLM")
>>> # p.bundle("fr")["axis_prompt"]

Author
------
[Warith HARCHAOUI](https://linkedin.com/in/warith-harchaoui/)
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .i18n_utils import Locales, _placeholders

__all__ = ["Prompts"]


@dataclass(frozen=True, eq=False)
class Prompts:
    """One section of a locale file, read as model-facing templates.

    Build one with :meth:`from_path`; the constructor takes an already-parsed
    :class:`Locales` for callers that have one.

    Attributes
    ----------
    locales : os_helper.Locales
        The parsed file. Reused rather than re-read, so a package that also
        has a ``gui`` section pays for one parse.
    section : str
        Which section holds the prompts. Named by the caller because os-helper
        has no business knowing that prompts are a thing — it is the member
        that decides, and members differ (``prompts`` here, ``bundle`` there).
    """

    locales: Locales
    section: str

    # -- construction ----------------------------------------------------

    @classmethod
    def from_path(cls, path: str | Path, section: str = "prompts") -> Prompts:
        """Read a locale file and take one section of it as prompts.

        Parameters
        ----------
        path : str or pathlib.Path
            The ``locales/i18n.yaml`` to read. Must live **inside** the
            importable package directory, or it is not package data and never
            reaches the wheel.
        section : str
            The section holding the templates.

        Returns
        -------
        Prompts
            A handle. The file is parsed and validated now, by `Locales`.
        """
        return cls(Locales.from_path(path), section)

    # -- interrogation ---------------------------------------------------

    @property
    def keys(self) -> tuple[str, ...]:
        """Every prompt key in this section, sorted."""
        return tuple(sorted(self.locales.section(self.section)))

    @property
    def languages(self) -> tuple[str, ...]:
        """Every language any prompt in this section is written in, sorted.

        Taken from the prompts themselves rather than from ``meta``: a package
        whose interface is bilingual may well have prompts in three languages,
        or in one, and the file should not have to lie about either.
        """
        declared = set(self.locales.supported_locales)
        found: set[str] = set()
        for value in self.locales.section(self.section).values():
            found |= _languages_of(value, declared)
        return tuple(sorted(found))

    @property
    def default_language(self) -> str:
        """The language served when the request names one we do not have."""
        return self.locales.default_locale

    def resolve(self, language: str | None) -> str:
        """The language that will actually be served for a request.

        Parameters
        ----------
        language : str or None
            A language code, possibly regional (``fr-CA``) or absent.

        Returns
        -------
        str
            *language* when prompts exist in it, its base language when only
            that has them, otherwise :attr:`default_language`.
        """
        from .gettext_utils import language_candidates

        available = self.languages
        for candidate in language_candidates(language):
            if candidate in available:
                return candidate
        return self.default_language

    # -- lookup ----------------------------------------------------------

    def text(self, key: str, language: str | None = None, *, field: str | None = None) -> str:
        """One prompt, in the best available language.

        Parameters
        ----------
        key : str
            The semantic key, e.g. ``axis_prompt``.
        language : str or None
            Wanted language; resolved through :meth:`resolve` first, so a
            regional tag or an unknown one never reaches the file.
        field : str, optional
            For prompts that come in parts, which part — typically
            ``"system"`` or ``"user"``. Omit for a single-text prompt.

        Returns
        -------
        str
            The template, unformatted. Use :meth:`render` to fill it.

        Raises
        ------
        KeyError
            If the key (or the field) does not exist, or carries neither the
            wanted language nor the default one. Raising beats returning the
            key: a prompt that is silently the string ``axis_prompt`` would
            reach a model and produce confident nonsense.
        """
        entry = self._entry(key, field)
        if isinstance(entry, str):
            return entry

        wanted = self.resolve(language)
        for candidate in (wanted, self.default_language):
            if candidate in entry:
                found = entry[candidate]
                if not isinstance(found, str):
                    # A locale file may hold a whole structure under a
                    # language — standpoint keeps its GUI strings that way.
                    # That is legitimate data, but it is not a template, and
                    # `str()`-ing a dict into a prompt would send a model the
                    # repr of a mapping. Point the caller at the view that
                    # returns it intact.
                    where = f"{self.section}.{key}" + (f".{field}" if field else "")
                    raise KeyError(
                        f"{self.locales.path}: {where} holds a "
                        f"{type(found).__name__} in {candidate!r}, not a template; "
                        f"read it with bundle({candidate!r}) instead"
                    )
                return found
        fallback = self.default_language
        where = f"{self.section}.{key}" + (f".{field}" if field else "")
        raise KeyError(
            f"{self.locales.path}: {where} carries neither {wanted!r} nor the default "
            f"{fallback!r}; it has {sorted(entry)}"
        )

    def render(
        self,
        key: str,
        language: str | None = None,
        *,
        field: str | None = None,
        **values: Any,
    ) -> str:
        """One prompt with its ``{placeholder}`` fields filled in.

        Templates are data, never code: this formats, it never evaluates. The
        placeholder names are checked first, so a caller learns what it forgot
        instead of sending a half-filled instruction to a model — which would
        not fail, it would just answer the wrong question.

        Parameters
        ----------
        key : str
            The semantic key.
        language : str or None
            Wanted language, resolved through :meth:`resolve`.
        field : str, optional
            Which part, for a fielded prompt.
        **values
            One value per placeholder in the template.

        Returns
        -------
        str
            The formatted prompt.

        Raises
        ------
        KeyError
            If the template needs a placeholder no value was given for.
        """
        template = self.text(key, language, field=field)
        missing = _placeholders(template) - set(values)
        if missing:
            where = f"{self.section}.{key}" + (f".{field}" if field else "")
            raise KeyError(
                f"{self.locales.path}: {where} needs {sorted(missing)}, "
                f"which render() was not given"
            )
        return template.format(**values)

    @lru_cache(maxsize=16)  # noqa: B019
    def bundle(self, language: str | None = None) -> dict[str, Any]:
        """Every prompt for one language at once.

        This is how prompts are actually consumed: a caller resolves the
        language once, then reads several templates. Asking key by key means
        resolving the language again for each, which is both slower and an
        invitation to resolve it inconsistently.

        Parameters
        ----------
        language : str or None
            Wanted language, resolved through :meth:`resolve`.

        Returns
        -------
        dict
            ``{key: text}`` for simple prompts, ``{key: {field: text}}`` for
            fielded ones. Values come back **as stored**, so a key holding a
            structure for that language (a nested sub-tree, not a template)
            survives intact. A key with nothing for this language and nothing
            for the default is omitted rather than raising: a bundle is a
            view, and a caller that needs one key should ask for it by name
            and get the error.
        """
        wanted = self.resolve(language)
        declared = set(self.locales.supported_locales)
        out: dict[str, Any] = {}
        for key, value in self.locales.section(self.section).items():
            if _is_fielded(value, declared):
                fields = {}
                for field, inner in value.items():
                    leaf = _leaf(inner, wanted, self.default_language)
                    if leaf is not _ABSENT:
                        fields[field] = leaf
                if fields:
                    out[key] = fields
            else:
                leaf = _leaf(value, wanted, self.default_language)
                if leaf is not _ABSENT:
                    out[key] = leaf
        return out

    # -- validation ------------------------------------------------------

    def problems(self) -> list[str]:
        """Everything wrong with this section, as sentences.

        Checks, in order:

        * a prompt missing a language that the others have — the reader gets
          a different language than the one they asked for, which for a model
          means a different answer;
        * a prompt whose text is empty;
        * **a language whose template does not carry the same placeholders as
          the default** — the failure specific to this shape. A French prompt
          that drops the ``{criteria}`` the English one has will raise at
          render time, in production, on whichever request first asked for
          French. An *extra* placeholder is just as bad: it reaches
          ``format()`` with no value and raises there instead.

        Returns
        -------
        list of str
            One sentence per fault, empty when the section is sound.
        """
        faults: list[str] = []
        entries = self.locales.section(self.section)
        declared = set(self.locales.supported_locales)
        everywhere = set(self.languages)
        default = self.default_language

        for key in sorted(entries):
            value = entries[key]
            parts = value if _is_fielded(value, declared) else {None: value}
            for field, texts in parts.items():
                where = f"{self.section}.{key}" + (f".{field}" if field else "")
                if isinstance(texts, str):
                    # One text for every language, deliberately. Nothing to
                    # compare, and nothing to be missing.
                    if not texts.strip():
                        faults.append(f"{where} is empty")
                    continue
                if not isinstance(texts, dict):
                    faults.append(
                        f"{where} must be a string or a mapping of languages, "
                        f"got {type(texts).__name__}"
                    )
                    continue

                for absent in sorted(everywhere - set(texts)):
                    faults.append(
                        f"{where} has no {absent!r} text, though other prompts here do — "
                        f"a caller asking for {absent!r} silently gets {default!r}"
                    )
                for language, text in sorted(texts.items()):
                    if not str(text).strip():
                        faults.append(f"{where} is empty in {language!r}")

                if default in texts:
                    expected = _placeholders(str(texts[default]))
                    for language, text in sorted(texts.items()):
                        if language == default:
                            continue
                        got = _placeholders(str(text))
                        if got != expected:
                            faults.append(
                                f"{where} in {language!r} has placeholders {sorted(got)} "
                                f"but {default!r} has {sorted(expected)} — render() will "
                                f"raise for whoever asks for {language!r}"
                            )
        return faults

    # -- internals -------------------------------------------------------

    def _entry(self, key: str, field: str | None) -> Any:
        """The raw node for a key (and field), with a message naming the file."""
        entries = self.locales.section(self.section)
        if key not in entries:
            raise KeyError(
                f"{self.locales.path}: section {self.section!r} has no prompt {key!r}; "
                f"it has {sorted(entries)}"
            )
        value = entries[key]
        declared = set(self.locales.supported_locales)
        if field is None:
            if _is_fielded(value, declared):
                raise KeyError(
                    f"{self.locales.path}: {self.section}.{key} comes in parts "
                    f"{sorted(value)}; ask for one with field="
                )
            return value
        if not isinstance(value, dict) or field not in value:
            raise KeyError(
                f"{self.locales.path}: {self.section}.{key} has no field {field!r}; "
                f"it has {sorted(value) if isinstance(value, dict) else type(value).__name__}"
            )
        return value[field]


#: Sentinel for "this node carries nothing for that language", distinct from a
#: node that legitimately carries ``None`` or an empty string.
_ABSENT = object()


def _leaf(node: Any, wanted: str, default: str) -> Any:
    """The value a node holds for *wanted*, else for *default*, else absent.

    Returned **as it is stored**: a template comes back a string, and a
    structure comes back a structure. `bundle` is a view of the file, so it
    must not reshape what it finds.
    """
    if not isinstance(node, dict):
        return node
    for candidate in (wanted, default):
        if candidate in node:
            return node[candidate]
    return _ABSENT


def _is_fielded(value: Any, locales: set[str]) -> bool:
    """Whether a prompt node is ``{field: {language: text}}`` rather than flat.

    Decided by asking the file which codes are locales, not by looking at the
    nesting. Guessing from nesting is what a first attempt did, and it was
    wrong on real data: standpoint keeps a whole ``gui`` sub-tree inside its
    prompt section as ``{en: {...}, fr: {...}}``, whose values *are* mappings
    while its keys are plainly languages. The declared locales settle it —
    outer keys that are locales mean language-first, anything else means
    fields.
    """
    if not isinstance(value, dict) or not value:
        return False
    return not (set(value) & locales)


def _languages_of(value: Any, locales: set[str]) -> set[str]:
    """Every language code appearing under one prompt node."""
    if not isinstance(value, dict):
        return set()
    if _is_fielded(value, locales):
        found: set[str] = set()
        for inner in value.values():
            if isinstance(inner, dict):
                found |= set(inner) & locales
        return found
    return set(value) & locales
