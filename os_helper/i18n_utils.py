"""
Localization Utilities

A package that shows text to a person in more than one language needs one
place where that text lives, and one rule for which version comes out. Spread
the strings through the source and you get the two failures this module
exists to prevent: a sentence that exists in French and not in English, found
by a user rather than by a test, and a sentence edited in one language whose
twin silently keeps the old wording.

:class:`Locales` loads a ``locales/i18n.yaml`` file — the suite's canonical
shape, described in ``CODING.md`` section 21.3 — and answers two questions:
what is the text for this key in this language, and is this file complete.

The file is organised in **sections** of **semantic keys**, each key carrying
one string per locale::

    meta:
      default_locale: fr
      supported_locales: [fr, en]
    gui:
      submit_button:
        fr: Envoyer
        en: Send

Sections are named by the caller and carry no meaning here: this module
parses, resolves and validates, and never knows what any one section is for.
That is deliberate — it is what lets a single loader serve every member of
the suite whatever each one keeps in its file.

Keys are semantic, not the English text (section 21.3.1): wording changes
more often than meaning, so ``submit_button`` keeps the code untouched when
the copy is rewritten.

Resolution is deterministic (section 21.3.4). A key missing in the requested
locale falls back to ``meta.default_locale``; a key missing there too raises,
because a raw key reaching a user is worse than a loud failure in testing.

Usage example
-------------
>>> import os_helper as osh
>>> loc = osh.Locales.from_path("locales/i18n.yaml")  # doctest: +SKIP
>>> loc.text("gui", "submit_button", "en")            # doctest: +SKIP
'Send'
>>> loc.render("gui", "greeting", "fr", name="Alice")  # doctest: +SKIP
'Bonjour Alice'

Author
------
Warith HARCHAOUI, https://linkedin.com/in/warith-harchaoui
"""

# Postpone annotation evaluation for consistent modern typing on Python 3.10.
from __future__ import annotations

import string
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .logging_utils import warning
from .path_utils import file_exists

#: The section every file must carry: it declares which locales exist and
#: which one answers when the asked-for locale has nothing.
META_SECTION = "meta"


def _placeholders(template: str) -> set[str]:
    """Return the named ``{placeholder}`` fields of a ``str.format`` template.

    Parameters
    ----------
    template : str
        A template string.

    Returns
    -------
    set of str
        Field names. Positional (``{}``) and index (``{0}``) fields are not
        named and are left out; ``{{`` escapes are not fields at all.

    Examples
    --------
    >>> sorted(_placeholders("Hi {name}, you have {count} messages"))
    ['count', 'name']
    >>> _placeholders("JSON stays put: {{\\"a\\": 1}}")
    set()
    """
    names: set[str] = set()
    for _, field, _, _ in string.Formatter().parse(template):
        if field:
            # "a.b" / "a[0]" address into a value; the placeholder is "a".
            names.add(field.split(".")[0].split("[")[0])
    return names


@dataclass(frozen=True)
class Locales:
    """A parsed ``locales/i18n.yaml``: sections of keys, each with one text per locale.

    Build one with :meth:`from_path` rather than calling the constructor, so
    the file is validated as it is read.

    Attributes
    ----------
    document : dict
        The whole parsed file, sections included.
    path : pathlib.Path
        Where it was read from. Used in error messages, so a failure names
        the file to fix.
    """

    document: dict[str, Any]
    path: Path

    # -- construction ----------------------------------------------------

    @classmethod
    def from_path(cls, path: str | Path) -> Locales:
        """Parse a locale file, failing loudly if it cannot serve its purpose.

        Parameters
        ----------
        path : str or pathlib.Path
            Path to the YAML file, conventionally ``locales/i18n.yaml`` at
            the package root.

        Returns
        -------
        Locales
            The parsed file.

        Raises
        ------
        FileNotFoundError
            If the file is absent.
        RuntimeError
            If it does not parse as a YAML mapping, or lacks a usable
            ``meta`` section. A malformed locale file must fail at load
            rather than surface later as a puzzling ``KeyError`` deep in a
            caller.
        """
        target = Path(path)
        if not file_exists(str(target)):
            raise FileNotFoundError(f"locale file not found: {target}")

        raw = yaml.safe_load(target.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise RuntimeError(f"{target} must parse as a YAML mapping, got {type(raw).__name__}")

        meta = raw.get(META_SECTION)
        if not isinstance(meta, dict):
            raise RuntimeError(f"{target} is missing its '{META_SECTION}' section")

        default = meta.get("default_locale")
        if not isinstance(default, str) or not default:
            raise RuntimeError(
                f"{target}: {META_SECTION}.default_locale must be a non-empty string"
            )

        supported = meta.get("supported_locales")
        if not isinstance(supported, list) or not supported:
            raise RuntimeError(
                f"{target}: {META_SECTION}.supported_locales must be a non-empty list"
            )

        if default not in supported:
            raise RuntimeError(
                f"{target}: default_locale {default!r} is not among supported_locales {supported!r}; "
                "the fallback locale has to be one the file actually carries"
            )
        return cls(document=raw, path=target)

    # -- metadata --------------------------------------------------------

    @property
    def default_locale(self) -> str:
        """The locale that answers when the asked-for one has nothing."""
        return str(self.document[META_SECTION]["default_locale"])

    @property
    def supported_locales(self) -> list[str]:
        """Every locale this file declares, in declaration order."""
        return [str(code) for code in self.document[META_SECTION]["supported_locales"]]

    def sections(self) -> list[str]:
        """Section names, ``meta`` excluded — the content sections."""
        return [name for name in self.document if name != META_SECTION]

    @property
    def unlocalized_sections(self) -> list[str]:
        """Sections whose keys are deliberately **not** indexed by locale.

        A product may keep one section in a single language on purpose, and
        then its sub-keys mean something else entirely — a role, a variant, a
        field name. Declaring them here is what stops :meth:`problems` from
        reading those sub-keys as locale codes and reporting a wall of
        translations that were never meant to exist.

        Declared in the file, so the loader stays ignorant of what any
        section is for::

            meta:
              unlocalized_sections: [templates]
        """
        declared = self.document[META_SECTION].get("unlocalized_sections") or []
        return [str(name) for name in declared]

    def raw(self, section: str, key: str) -> Any:
        """Return one entry exactly as written, with no locale resolution.

        The accessor for an unlocalized section, whose sub-keys are not
        locales and so cannot be resolved by :meth:`text`.

        Parameters
        ----------
        section : str
            Section name.
        key : str
            Key within that section.

        Returns
        -------
        Any
            Whatever the file holds there — usually a string or a mapping.

        Raises
        ------
        KeyError
            If the section or the key is absent.
        """
        entries = self.section(section)
        if key not in entries:
            raise KeyError(f"{self.path}: section {section!r} has no key {key!r}")
        return entries[key]

    def section(self, name: str) -> dict[str, Any]:
        """Return one whole section: semantic key -> ``{locale: text}``.

        Parameters
        ----------
        name : str
            Section name, as spelled in the file.

        Returns
        -------
        dict
            The section's entries.

        Raises
        ------
        KeyError
            If the section is absent.
        """
        if name not in self.document or name == META_SECTION:
            raise KeyError(f"{self.path}: no section named {name!r}; it has {self.sections()}")
        entry: dict[str, Any] = self.document[name]
        return entry

    # -- resolution ------------------------------------------------------

    def text(self, section: str, key: str, locale: str | None = None) -> str:
        """Return the text for one key, falling back to the default locale.

        Parameters
        ----------
        section : str
            Section name.
        key : str
            Semantic key within that section.
        locale : str, optional
            Wanted locale. Defaults to :attr:`default_locale`.

        Returns
        -------
        str
            The text in *locale*, or in the default locale when *locale* has
            no entry for this key.

        Raises
        ------
        KeyError
            If the key is absent, or carries neither the wanted locale nor
            the default one. Returning the raw key instead would push a
            developer's identifier in front of a user (section 21.3.4).
        """
        entries = self.section(section)
        if key not in entries:
            raise KeyError(f"{self.path}: section {section!r} has no key {key!r}")

        value = entries[key]
        # A key may hold a bare string when the text is the same everywhere —
        # a product name, a symbol — rather than a mapping of locales.
        if isinstance(value, str):
            return value
        if not isinstance(value, dict):
            raise KeyError(
                f"{self.path}: {section}.{key} must be a string or a mapping of locales, "
                f"got {type(value).__name__}"
            )

        wanted = locale or self.default_locale
        if wanted in value:
            return str(value[wanted])

        fallback = self.default_locale
        if fallback in value:
            # Loud enough to be fixed, quiet enough not to break a release:
            # the user still reads a real sentence, in the wrong language.
            warning(
                f"{self.path}: {section}.{key} has no {wanted!r} entry; "
                f"falling back to {fallback!r}"
            )
            return str(value[fallback])

        raise KeyError(
            f"{self.path}: {section}.{key} carries neither {wanted!r} nor the default "
            f"{fallback!r}; it has {sorted(value)}"
        )

    def render(self, section: str, key: str, locale: str | None = None, **values: Any) -> str:
        """Return a key's text with its ``{placeholder}`` fields filled in.

        Templates are data, never code (section 21.3.5): this formats, it
        never evaluates, and it checks the placeholder names first so a
        caller learns what it forgot instead of shipping a half-filled
        sentence.

        Parameters
        ----------
        section : str
            Section name.
        key : str
            Semantic key within that section.
        locale : str, optional
            Wanted locale. Defaults to :attr:`default_locale`.
        **values
            One argument per placeholder in the template.

        Returns
        -------
        str
            The filled text.

        Raises
        ------
        KeyError
            If the template needs a placeholder that *values* does not carry.
        """
        template = self.text(section, key, locale)
        needed = _placeholders(template)
        missing = sorted(needed - set(values))
        if missing:
            raise KeyError(
                f"{self.path}: {section}.{key} needs placeholder(s) {missing} "
                f"that were not supplied"
            )
        return template.format(**values)

    # -- validation ------------------------------------------------------

    def problems(
        self,
        *,
        require_parity: bool = True,
        sections: list[str] | None = None,
    ) -> list[str]:
        """Return everything wrong with this file, as sentences, worst first.

        Built for a test to assert on (section 21.3.7). It reports *all* the
        problems rather than raising on the first, because a translator
        fixing a file wants the whole list in one pass.

        Parameters
        ----------
        require_parity : bool, optional
            When true (the default), a key whose translations do not all take
            the same ``{placeholder}`` fields is reported. Parity matters
            because a template missing a field renders a sentence with a hole
            in it, in that language only.
        sections : list of str, optional
            Which sections to check. Defaults to every content section except
            those listed in :attr:`unlocalized_sections`, since a section
            that is deliberately single-language has no translations to miss.

        Returns
        -------
        list of str
            One sentence per problem. Empty when the file is sound.

        Examples
        --------
        >>> import os_helper as osh
        >>> osh.Locales.from_path("locales/i18n.yaml").problems()  # doctest: +SKIP
        []
        """
        found: list[str] = []
        declared = self.supported_locales
        default = self.default_locale
        skipped = set(self.unlocalized_sections)
        wanted = (
            sections if sections is not None else [s for s in self.sections() if s not in skipped]
        )

        for name in wanted:
            entries = self.document[name]
            if not isinstance(entries, dict):
                found.append(
                    f"section {name!r} must be a mapping of keys, got {type(entries).__name__}"
                )
                continue

            for key, value in entries.items():
                if isinstance(value, str):
                    # A deliberate single-language entry; nothing to compare.
                    continue
                if not isinstance(value, dict):
                    found.append(f"{name}.{key} must be a string or a mapping of locales")
                    continue

                if default not in value:
                    found.append(f"{name}.{key} has no {default!r} entry, the declared default")

                for code in sorted(set(value) - set(declared)):
                    found.append(
                        f"{name}.{key} carries locale {code!r}, which "
                        f"{META_SECTION}.supported_locales does not declare"
                    )

                for code in declared:
                    if code not in value:
                        found.append(f"{name}.{key} is missing its {code!r} translation")

                if require_parity:
                    fields = {
                        code: _placeholders(str(text))
                        for code, text in value.items()
                        if isinstance(text, str)
                    }
                    reference = fields.get(default)
                    if reference is not None:
                        for code, names in sorted(fields.items()):
                            if code != default and names != reference:
                                found.append(
                                    f"{name}.{key}: {code!r} takes {sorted(names)} but "
                                    f"{default!r} takes {sorted(reference)} — "
                                    "a placeholder that differs renders a hole in one language"
                                )
        return found
