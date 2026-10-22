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
    "extract_sources",
    "language_candidates",
    "parse_po",
    "untranslated",
    "write_po",
]

#: ``.mo`` magic, little-endian. The byte order is the file's own declaration,
#: so writing little-endian everywhere is portable, not host-dependent.
_MAGIC = 0x950412DE

#: What gettext puts between a context and its message inside one key. The
#: format has no separate field for context: ``pgettext`` looks up the two
#: joined by this byte, which is why it needs no change to the file layout.
_CONTEXT_GLUE = "\x04"

#: The language every msgid is already written in, so it never gets a
#: catalogue directory and can never fall out of sync with one.
SOURCE_LANGUAGE = "en"

#: One entry line, with the string in C-escaped quotes. ``msgstr[0]`` and
#: ``msgstr[1]`` are the plural forms, which French needs and English mostly
#: does not — hence the optional index.
_ENTRY_RE = re.compile(r'^(msgctxt|msgid|msgid_plural|msgstr)(?:\[(\d+)\])?\s+"(.*)"\s*$')
#: One ``q``-weighted entry of an ``Accept-Language`` header. The weight is
#: captured loosely (``[^;,\s]+``) rather than as a number on purpose: a
#: browser that sends ``q=high`` should still get its language, and the
#: ``float()`` below is what decides that. Matching digits here instead would
#: discard the whole entry and make that fallback unreachable.
_ACCEPT_RE = re.compile(r"\s*([A-Za-z-]+|\*)\s*(?:;\s*q\s*=\s*([^;,\s]+))?\s*")

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
    are kept the same way, joined to their message by ``\x04`` — the format
    has no separate field for them, which is why :meth:`Catalog.pgettext`
    needs no change to the layout.

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
    context: str | None = None
    # True between reading a `msgctxt` and the `msgid` it qualifies. Without
    # it, a context stays set after its own entry is filed and the NEXT plain
    # msgid both skips its commit and inherits the context — which silently
    # loses one entry and misfiles another.
    context_pending = False
    singular: str | None = None
    plural: str | None = None
    translations: dict[int, str] = {}
    current: tuple[str, int] | None = None
    buffer: list[str] = []

    def commit() -> None:
        """Close the entry being read and file it."""
        nonlocal context, context_pending, singular, plural, translations
        if singular is None:
            return
        # A context is stored by joining it to the msgid, which is how
        # gettext finds a `pgettext` lookup: same file, same table, one key.
        prefix = f"{context}{_CONTEXT_GLUE}" if context else ""
        if plural is None:
            value = translations.get(0, "")
            if value or singular == "":
                entries[prefix + singular] = value
        else:
            forms = [translations.get(i, "") for i in range(max(translations) + 1)]
            if any(forms):
                entries[f"{prefix}{singular}\x00{plural}"] = "\x00".join(forms)
        context, context_pending = None, False
        singular, plural, translations = None, None, {}

    def flush() -> None:
        """Attach the lines gathered so far to the field they belong to."""
        nonlocal context, context_pending, singular, plural
        if current is None:
            return
        field, index = current
        text = "".join(buffer)
        if field == "msgctxt":
            commit()
            context, context_pending = text, True
        elif field == "msgid":
            # Close the previous entry — unless a `msgctxt` line just did it
            # and left the context standing for this very msgid. Committing
            # again here would clear that context before it is ever used.
            if not context_pending:
                commit()
            context_pending = False
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


#: One ``{{_("…")}}`` translation site. The suite's GUIs are one HTML string
#: per module, so the marker lives in the markup rather than in a function
#: call, and this is the form `render_gui` substitutes.
SOURCE_MARKER_RE = re.compile(r'\{\{_\("(.*?)"\)\}\}')


def extract_sources(*texts: str) -> set[str]:
    """Every English source string marked for translation in *texts*.

    The extraction step a gettext workflow normally gets from ``pybabel``,
    scoped to the one marker this suite uses. It exists so that a member's
    test can hand :meth:`Catalog.problems` the strings the code *actually*
    asks for, rather than a hand-maintained list that drifts from the markup
    — which is the only way the reworded-source fault gets caught.

    Before this, eight members each kept their own copy of the same four-line
    regex, which is exactly the duplication a shared loader is for.

    Parameters
    ----------
    *texts : str
        Anything carrying markers — typically a module's HTML template. Pass
        several and the results are unioned.

    Returns
    -------
    set of str
        The msgids found. Empty when nothing is marked, which a caller should
        treat as suspicious rather than as "nothing to translate".

    Examples
    --------
    >>> sorted(extract_sources('<h1>{{_("Run")}}</h1><p>{{_("Done.")}}</p>'))
    ['Done.', 'Run']
    """
    found: set[str] = set()
    for text in texts:
        found |= set(SOURCE_MARKER_RE.findall(text))
    return found


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
        # No hash table. gettext binary-searches the sorted msgid table when
        # the size is zero, which is why the entries must be sorted above. The
        # offset is zero to match: a table that does not exist starts nowhere,
        # and writing the end-of-file offset instead (as md2star's own writer
        # did) is a value no reader uses and no writer should invent.
        0,  # hash table size
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


def language_candidates(tag: str | None) -> list[str]:
    """A language tag plus its base, so ``fr-CA`` can find the ``fr`` catalogue.

    Normalised the way gettext names its directories (``fr_CA``, not
    ``fr-CA``) and stripped of any ``.UTF-8`` / ``@euro`` suffix a POSIX locale
    string carries. One normalisation here means an HTTP header and an
    environment variable can both be passed in.

    Parameters
    ----------
    tag : str or None
        A BCP 47 tag (``fr-CA``), a POSIX locale (``fr_CA.UTF-8``), or None.

    Returns
    -------
    list of str
        Most specific first, then the bare language: a Québécois browser gets
        the French catalogue rather than nothing when ``fr_CA`` does not exist.
        Empty when *tag* is empty.
    """
    if not tag:
        return []
    cleaned = tag.strip().replace("-", "_").split(".")[0].split("@")[0]
    if not cleaned:
        return []
    base = cleaned.split("_")[0]
    return [cleaned, base] if base != cleaned else [cleaned]


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
            its base language when only that has one (``fr-CA`` → ``fr``),
            otherwise :attr:`default_language`.
        """
        available = self.languages
        for candidate in language_candidates(language):
            if candidate in available:
                return candidate
        return self.default_language

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

    def pgettext(self, language: str | None, context: str, message: str) -> str:
        """Translate one source string **in a given context**.

        The answer to a word that is one word in English and two in French:
        ``pgettext("month name", "May")`` and ``pgettext("verb", "May")`` are
        separate entries, because a translator cannot disambiguate them from
        the msgid alone.

        Parameters
        ----------
        language : str or None
            Requested language, resolved through :meth:`resolve` first.
        context : str
            The disambiguating label, as written in the catalogue's
            ``msgctxt``.
        message : str
            The English source string.

        Returns
        -------
        str
            The translation, or *message* itself when this context has no
            entry — never the ``context\x04message`` key, which would put a
            control character in front of a reader.
        """
        key = f"{context}{_CONTEXT_GLUE}{message}"
        found = self._translator(self.resolve(language)).gettext(key)
        return message if found == key else found

    def ngettext(self, language: str | None, singular: str, plural: str, n: int) -> str:
        """Translate a message whose wording depends on a count.

        Parameters
        ----------
        language : str or None
            Requested language, resolved through :meth:`resolve` first.
        singular, plural : str
            The two English source forms. The pair is the msgid: gettext
            stores it NUL-joined, which is what :func:`build_mo` writes.
        n : int
            The count that picks the form. Which form that is comes from the
            catalogue's own plural rule, not from ``n == 1`` — the point of
            asking gettext rather than branching at the call site.

        Returns
        -------
        str
            The translated form, or the matching English source when the
            catalogue has no entry.
        """
        return self._translator(self.resolve(language)).ngettext(singular, plural, n)

    def negotiate(self, header: str | None) -> str | None:
        """Best language from an HTTP ``Accept-Language`` header, or ``None``.

        Honours ``q`` weights and falls back to a base language, so a browser
        asking for ``fr-CA;q=0.9, en;q=0.8`` gets the ``fr`` catalogue.

        Parsed here rather than with a header library: this is one header, the
        grammar is a list of tags with optional weights, and the suite does not
        take a dependency for forty lines of standard parsing.

        Parameters
        ----------
        header : str or None
            The raw header value.

        Returns
        -------
        str or None
            The language to serve, or ``None`` when the best match is the
            source language or when nothing offered has a catalogue — both of
            which mean "leave the source text alone". Returning ``None`` rather
            than ``"en"`` lets a caller distinguish "the visitor asked for
            English" from "the visitor asked for nothing we have".

        Notes
        -----
        The source language counts as **offered** even though it has no
        catalogue, and that is not a technicality: without it, a visitor who
        asked for English first and French second would be served French,
        because the language they actually wanted was the one the loop could
        not see.
        """
        if not header:
            return None
        offered = set(self.languages)
        if offered <= {SOURCE_LANGUAGE}:
            return None

        ranked: list[tuple[float, int, str]] = []
        for order, part in enumerate(header.split(",")):
            match = _ACCEPT_RE.fullmatch(part)
            if not match or match.group(1) == "*":
                continue
            try:
                quality = float(match.group(2)) if match.group(2) else 1.0
            except ValueError:
                # A malformed q value is the browser's problem, not a reason to
                # refuse the language: treat it as the default weight.
                quality = 1.0
            # `order` breaks ties the way the header's own sequence intends, and
            # negating quality sorts strongest-first with a plain ascending sort.
            ranked.append((-quality, order, match.group(1)))

        for _quality, _order, tag in sorted(ranked):
            for candidate in language_candidates(tag):
                if candidate in offered:
                    return None if candidate.split("_")[0] == SOURCE_LANGUAGE else candidate
        return None

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
