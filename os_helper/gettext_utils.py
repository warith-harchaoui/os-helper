"""
Message Catalogues (gettext)

The companion to :mod:`os_helper.i18n_utils`, for packages whose human-facing
text lives in the source rather than behind a semantic key. Where
:class:`~os_helper.i18n_utils.Locales` answers *what is the text for this key*,
:class:`Catalog` answers *what is the French for this English sentence* — the
question gettext was built for.

Why both exist
--------------
``Locales`` keys on meaning (``submit_button``), which survives a rewrite of
the copy. ``Catalog`` keys on the English source string, which does not: edit
the English and the French no longer matches it, so gettext falls back to the
English and the page half-reverts with nothing raised. That is the known cost
of the gettext shape, and it is why :meth:`Catalog.problems` reports a msgid
used by the code but absent from a catalogue. A test that calls it turns the
silent half-revert into a red build, which is the only thing that makes this
shape safe to live with.

What it gives in return is what the suite wanted: one mechanism, the
translator sees a real sentence instead of ``NAV_CONVERT``, and an untranslated
string degrades to readable English rather than to its own key.

No build dependency
-------------------
GNU gettext's ``msgfmt`` would compile the catalogues, and requiring it would
mean a translated interface could only be built where somebody had installed
the gettext tools. The ``.mo`` format is a header, two offset tables and a
blob of strings, so :func:`build_mo` writes it here instead. The thing is
small; the dependency is not.

Layout on disk
--------------
The canonical shape, which :meth:`Catalog.from_package` expects::

    <package>/locales/<lang>/LC_MESSAGES/<domain>.po     # source, committed
    <package>/locales/<lang>/LC_MESSAGES/<domain>.mo      # compiled, committed

English is not a directory: it is the msgid, so it needs no catalogue and
cannot drift from one.

Usage example
-------------
>>> # cat = Catalog.from_package(Path(__file__).parent / "locales", "video_helper")
>>> # cat.gettext("fr", "Convert a document")
>>> # 'Convertir un document'

Author
------
[Warith HARCHAOUI](https://linkedin.com/in/warith-harchaoui/)
"""

from __future__ import annotations

import gettext as _gettext
import re
import struct
from dataclasses import dataclass
from functools import cache
from pathlib import Path

__all__ = [
    "Catalog",
    "build_mo",
    "compile_catalogs",
    "parse_po",
    "untranslated",
    "write_po",
]

#: ``.mo`` magic, little-endian. The byte order is the file's own declaration,
#: so writing little-endian everywhere is portable, not host-dependent.
_MAGIC = 0x950412DE

#: The language every msgid is already written in, so it never gets a
#: catalogue directory and can never fall out of sync with one.
SOURCE_LANGUAGE = "en"

#: One entry line, with the string in C-escaped quotes. ``msgstr[0]`` and
#: ``msgstr[1]`` are the plural forms, which French needs and English mostly
#: does not — hence the optional index.
_ENTRY_RE = re.compile(r'^(msgid|msgid_plural|msgstr)(?:\[(\d+)\])?\s+"(.*)"\s*$')
#: A continuation line: a bare quoted string under the entry it extends.
_CONT_RE = re.compile(r'^\s*"(.*)"\s*$')


def _unescape(text: str) -> str:
    """Turn a ``.po``'s C escapes back into the characters they stand for.

    Parameters
    ----------
    text : str
        The raw contents of one quoted ``.po`` string, without its quotes.

    Returns
    -------
    str
        The same text with ``\\n``, ``\\t``, ``\\"`` and ``\\\\`` resolved.
    """
    return text.replace(r"\n", "\n").replace(r"\t", "\t").replace(r"\"", '"').replace(r"\\", "\\")


def _escape(text: str) -> str:
    """Quote a string for a ``.po`` entry, the inverse of :func:`_unescape`.

    Parameters
    ----------
    text : str
        The literal text to write into a catalogue.

    Returns
    -------
    str
        The text with backslashes, quotes, tabs and newlines C-escaped.
    """
    return text.replace("\\", r"\\").replace('"', r"\"").replace("\t", r"\t").replace("\n", r"\n")


def parse_po(path: str | Path) -> dict[str, str]:
    """Read a ``.po`` into the ``{msgid: msgstr}`` mapping a ``.mo`` stores.

    Plural entries are kept: gettext stores them by NUL-joining the two
    ``msgid`` forms into one key and the ``msgstr[n]`` forms into one value,
    which is exactly what :func:`build_mo` then writes. Contexts (``msgctxt``)
    are not handled — no member of the suite uses them, and a parser that
    half-read them would be worse than one that says it does not.

    An entry with an empty translation is **dropped**, which is what makes an
    unfinished catalogue fall back to its English source rather than serve
    emptiness. Use :func:`untranslated` to see those instead of losing them.

    Parameters
    ----------
    path : str or pathlib.Path
        The ``.po`` file to read.

    Returns
    -------
    dict of str to str
        Every translated entry, ready for :func:`build_mo`.
    """
    entries: dict[str, str] = {}
    singular: str | None = None
    plural: str | None = None
    translations: dict[int, str] = {}
    current: tuple[str, int] | None = None
    buffer: list[str] = []

    def commit() -> None:
        """Close the entry being read and file it."""
        nonlocal singular, plural, translations
        if singular is None:
            return
        if plural is None:
            value = translations.get(0, "")
            if value or singular == "":
                entries[singular] = value
        else:
            forms = [translations.get(i, "") for i in range(max(translations) + 1)]
            if any(forms):
                entries[f"{singular}\x00{plural}"] = "\x00".join(forms)
        singular, plural, translations = None, None, {}

    def flush() -> None:
        """Attach the lines gathered so far to the field they belong to."""
        nonlocal singular, plural
        if current is None:
            return
        field, index = current
        text = "".join(buffer)
        if field == "msgid":
            commit()
            singular = text
        elif field == "msgid_plural":
            plural = text
        else:
            translations[index] = text

    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line or line.startswith("#"):
            continue
        match = _ENTRY_RE.match(line)
        if match:
            flush()
            current = (match.group(1), int(match.group(2) or 0))
            buffer = [_unescape(match.group(3))]
            continue
        cont = _CONT_RE.match(line)
        if cont and current is not None:
            buffer.append(_unescape(cont.group(1)))
    flush()
    commit()
    return entries


def untranslated(path: str | Path) -> list[str]:
    """Every msgid in a ``.po`` whose translation is empty.

    :func:`parse_po` drops these on purpose, so that an unfinished catalogue
    degrades to English. This reports them, which is what a test needs in
    order to fail on a half-finished translation instead of shipping one.

    Parameters
    ----------
    path : str or pathlib.Path
        The ``.po`` file to inspect.

    Returns
    -------
    list of str
        The untranslated msgids, in file order. The header entry (``msgid ""``)
        is not included — it legitimately carries metadata, not a translation.
    """
    missing: list[str] = []
    singular: str | None = None
    has_text = False
    current: str | None = None
    buffer: list[str] = []

    def close() -> None:
        """File the entry just read if it turned out to be untranslated."""
        nonlocal singular, has_text
        # The empty msgid is the header entry, which carries metadata rather
        # than a translation, so an empty msgstr there is correct.
        if singular and not has_text:
            missing.append(singular)
        singular, has_text = None, False

    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line or line.startswith("#"):
            continue
        match = _ENTRY_RE.match(line)
        if match:
            field, text = match.group(1), _unescape(match.group(3))
            if field == "msgid":
                close()
                singular = text
                buffer = [text]
            elif field == "msgstr":
                has_text = has_text or bool(text)
                buffer = [text]
            current = field
            continue
        cont = _CONT_RE.match(line)
        if cont and current is not None:
            piece = _unescape(cont.group(1))
            if current == "msgid" and singular is not None:
                singular += piece
            elif current == "msgstr":
                has_text = has_text or bool(piece)
            buffer.append(piece)
    close()
    return missing


def write_po(
    path: str | Path,
    entries: dict[str, str],
    *,
    language: str,
    project: str,
) -> Path:
    """Write a ``.po`` catalogue, sorted by msgid so diffs stay readable.

    The header carries the charset, because a catalogue without one is read as
    ASCII by some tools and French is not ASCII.

    Parameters
    ----------
    path : str or pathlib.Path
        Destination ``.po`` file; parent directories are created.
    entries : dict of str to str
        ``{english_source: translation}``. An empty translation is written as
        an empty ``msgstr``, which marks the entry as still to do rather than
        dropping it.
    language : str
        The catalogue's language code, recorded in the header.
    project : str
        The package the catalogue belongs to, recorded in the header.

    Returns
    -------
    pathlib.Path
        The file written.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {language} catalogue for {project}.",
        "#",
        "# msgid is the English source string as it appears in the code, so a",
        "# reworded source needs its entry reworded too — os_helper.Catalog.problems",
        "# reports the mismatch rather than letting the page half-revert to English.",
        'msgid ""',
        'msgstr ""',
        f'"Project-Id-Version: {project}\\n"',
        f'"Language: {language}\\n"',
        '"MIME-Version: 1.0\\n"',
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        '"Content-Transfer-Encoding: 8bit\\n"',
        "",
    ]
    for source in sorted(entries):
        lines.append(f'msgid "{_escape(source)}"')
        lines.append(f'msgstr "{_escape(entries[source])}"')
        lines.append("")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def build_mo(entries: dict[str, str]) -> bytes:
    """Serialise ``{msgid: msgstr}`` into the binary gettext reads.

    Layout, in order: a 28-byte header, the originals' ``(length, offset)``
    table, the translations' table, then the two blobs. Entries must be sorted
    by msgid — gettext binary-searches them. A plural entry arrives here
    already NUL-joined on both sides, which is how the format carries it.

    Parameters
    ----------
    entries : dict of str to str
        The catalogue, typically from :func:`parse_po`.

    Returns
    -------
    bytes
        A complete ``.mo`` file.
    """
    items = sorted(entries.items())
    ids = b"\x00".join(key.encode("utf-8") for key, _ in items) + b"\x00"
    strs = b"\x00".join(value.encode("utf-8") for _, value in items) + b"\x00"
    count = len(items)
    # Header is 7 unsigned ints; the two tables are 2 ints per entry each.
    key_table = 7 * 4
    value_table = key_table + count * 8
    ids_start = value_table + count * 8
    strs_start = ids_start + len(ids)

    key_offsets: list[int] = []
    position = 0
    for key, _value in items:
        encoded = len(key.encode("utf-8"))
        key_offsets += [encoded, ids_start + position]
        position += encoded + 1

    value_offsets: list[int] = []
    position = 0
    for _key, value in items:
        encoded = len(value.encode("utf-8"))
        value_offsets += [encoded, strs_start + position]
        position += encoded + 1

    header = struct.pack(
        "<7I",
        _MAGIC,
        0,  # format revision
        count,
        key_table,
        value_table,
        0,  # hash table size: unused, gettext falls back to binary search
        0,  # hash table offset
    )
    tables = struct.pack(f"<{len(key_offsets)}I", *key_offsets) + struct.pack(
        f"<{len(value_offsets)}I", *value_offsets
    )
    return header + tables + ids + strs


def compile_catalogs(locales_dir: str | Path, *, check: bool = False) -> list[Path]:
    """Compile every ``.po`` under *locales_dir* to the ``.mo`` beside it.

    Parameters
    ----------
    locales_dir : str or pathlib.Path
        The ``locales/`` root holding ``<lang>/LC_MESSAGES/<domain>.po``.
    check : bool, keyword-only
        Recompile in memory and compare instead of writing. This is what CI
        wants: a translation edited without recompiling cannot then reach a
        release looking live.

    Returns
    -------
    list of pathlib.Path
        With ``check=False``, the ``.mo`` files written. With ``check=True``,
        the ``.mo`` files that are **stale or missing** — empty means in sync.
    """
    root = Path(locales_dir)
    touched: list[Path] = []
    for po_path in sorted(root.glob("*/LC_MESSAGES/*.po")):
        mo_path = po_path.with_suffix(".mo")
        data = build_mo(parse_po(po_path))
        if check:
            current = mo_path.read_bytes() if mo_path.exists() else b""
            if current != data:
                touched.append(mo_path)
        else:
            mo_path.write_bytes(data)
            touched.append(mo_path)
    return touched


@dataclass(frozen=True)
class Catalog:
    """Compiled message catalogues for one package, read through gettext.

    Build one with :meth:`from_package` rather than calling the constructor,
    so the directory layout is resolved once and in one place.

    Attributes
    ----------
    locales_dir : pathlib.Path
        The ``locales/`` root. Used in error messages, so a failure names the
        directory to fix.
    domain : str
        The gettext domain, and therefore each ``.mo`` file's stem.
    default_language : str
        The language served when the caller asks for one that has no
        catalogue. The suite's GUIs default to French; English needs no
        catalogue because it is the msgid.
    """

    locales_dir: Path
    domain: str
    default_language: str

    # -- construction ----------------------------------------------------

    @classmethod
    def from_package(
        cls,
        locales_dir: str | Path,
        domain: str,
        *,
        default_language: str = "fr",
    ) -> Catalog:
        """Resolve the catalogue directory for a package.

        Parameters
        ----------
        locales_dir : str or pathlib.Path
            Conventionally ``<package>/locales``, i.e. **inside** the importable
            package directory. Outside it, the catalogues do not travel in the
            wheel and every string raises at run time on an installed copy.
        domain : str
            The gettext domain; by convention the package's import name.
        default_language : str, keyword-only
            Language for an unknown or absent request.

        Returns
        -------
        Catalog
            A catalogue handle. Nothing is read from disk until a lookup.
        """
        return cls(Path(locales_dir), domain, default_language)

    # -- interrogation ---------------------------------------------------

    @property
    def languages(self) -> tuple[str, ...]:
        """Every language this package can render, sorted.

        The source language is always present — it is the msgid — followed by
        each ``<lang>/LC_MESSAGES/<domain>.mo`` actually on disk. A ``.po``
        with no compiled ``.mo`` is deliberately **not** listed: it cannot be
        served, and claiming it would offer a language that renders English.
        """
        found = {
            path.parent.parent.name
            for path in self.locales_dir.glob(f"*/LC_MESSAGES/{self.domain}.mo")
        }
        return tuple(sorted(found | {SOURCE_LANGUAGE}))

    def resolve(self, language: str | None) -> str:
        """The language that will actually be served for a request.

        Parameters
        ----------
        language : str or None
            The requested code, typically straight off a ``?lang=`` parameter.

        Returns
        -------
        str
            *language* when it has a catalogue (or is the source language),
            otherwise :attr:`default_language`.
        """
        return language if language in self.languages else self.default_language

    # -- lookup ----------------------------------------------------------

    @cache  # noqa: B019
    def _translator(self, language: str) -> _gettext.NullTranslations:
        """The gettext translator for one language, read once.

        A missing catalogue yields :class:`gettext.NullTranslations`, whose
        ``gettext`` returns the msgid — which is the English source, so a
        language with no catalogue renders readable English rather than
        raising or emitting a key.
        """
        return _gettext.translation(
            self.domain,
            localedir=str(self.locales_dir),
            languages=[language],
            fallback=True,
        )

    def gettext(self, language: str | None, message: str) -> str:
        """Translate one English source string.

        Parameters
        ----------
        language : str or None
            Requested language; resolved through :meth:`resolve` first, so an
            unknown code never reaches the catalogues.
        message : str
            The English source string, i.e. the msgid.

        Returns
        -------
        str
            The translation, or *message* itself when the catalogue has no
            entry for it.
        """
        return self._translator(self.resolve(language)).gettext(message)

    def translator_for(self, language: str | None) -> _gettext.NullTranslations:
        """The raw translator, for a caller that wants to bind its own ``_``.

        Parameters
        ----------
        language : str or None
            Requested language, resolved through :meth:`resolve`.

        Returns
        -------
        gettext.NullTranslations
            The translator whose ``gettext`` method does the lookup.
        """
        return self._translator(self.resolve(language))

    # -- validation ------------------------------------------------------

    def problems(self, *, used: set[str] | None = None) -> list[str]:
        """Everything wrong with this package's catalogues, as sentences.

        Checks, in order:

        * a ``.po`` with no compiled ``.mo``, or a ``.mo`` that no longer
          matches its ``.po`` — a translation edited and not recompiled;
        * an entry whose translation is empty, which would quietly serve
          English from a language that claims to be translated;
        * when *used* is given, a string the code asks for that no catalogue
          carries, and a catalogue entry nothing asks for.

        That third check is the one that matters most under this shape.
        Because the msgid **is** the English copy, rewording a sentence in the
        template orphans its translation, gettext falls back to English, and
        the page half-reverts with nothing raised. Passing the set of strings
        the code actually uses turns that into a failure a test can see.

        Parameters
        ----------
        used : set of str, optional
            Every msgid the code looks up. When omitted, the two
            code-versus-catalogue checks are skipped.

        Returns
        -------
        list of str
            One sentence per fault, empty when the catalogues are sound.
        """
        faults: list[str] = []

        stale = compile_catalogs(self.locales_dir, check=True)
        for mo_path in stale:
            verb = "is missing" if not mo_path.exists() else "is stale"
            faults.append(
                f"{mo_path} {verb}: recompile with os_helper.compile_catalogs({self.locales_dir!s})"
            )

        for po_path in sorted(self.locales_dir.glob(f"*/LC_MESSAGES/{self.domain}.po")):
            language = po_path.parent.parent.name
            for msgid in untranslated(po_path):
                faults.append(f"{language}: no translation for {msgid!r} ({po_path})")

        if used is not None:
            for language in self.languages:
                if language == SOURCE_LANGUAGE:
                    continue
                po_path = self.locales_dir / language / "LC_MESSAGES" / f"{self.domain}.po"
                if not po_path.exists():
                    continue
                catalogue = set(parse_po(po_path)) | set(untranslated(po_path))
                for msgid in sorted(used - catalogue):
                    faults.append(
                        f"{language}: the code uses {msgid!r}, which the catalogue "
                        f"does not carry — it will render as English ({po_path})"
                    )
                for msgid in sorted(catalogue - used - {""}):
                    faults.append(
                        f"{language}: the catalogue carries {msgid!r}, which no code "
                        f"uses — dead entry, or the source string was reworded ({po_path})"
                    )
        return faults
