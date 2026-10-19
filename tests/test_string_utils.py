"""
Tests for os_helper.string_utils.

Usage Example
-------------
>>> #   pytest tests/test_string_utils.py --cov=os_helper.string_utils

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

from os_helper import string_utils as su


def test_emptystring_catches_none_blank_and_whitespace() -> None:
    assert su.emptystring("") is True
    assert su.emptystring(None) is True
    assert su.emptystring("   ") is True
    assert su.emptystring("Non-empty") is False


def test_asciistring_folds_accents_and_normalizes_case_and_digits() -> None:
    assert su.asciistring("Café-Con-Leche!") == "cafe-con-leche"
    assert su.asciistring("Café-Con-Leche!", replacement_char="_") == "cafe_con_leche"
    assert su.asciistring("Special#File$2024", lower=False) == "Special-File-2024"
    assert su.asciistring("Café@2024.txt") == "cafe-2024-txt"
    assert su.asciistring("MyFile@2024.txt", allow_digits=False) == "myfile-txt"


def test_asciistring_accepts_an_empty_replacement() -> None:
    """Dropping unwanted characters is a legitimate request, not a crash.

    `re.escape("") + "+"` is the pattern `"+"`, which re rejects as "nothing to
    repeat" -- so this used to raise a PatternError from inside re, naming
    neither the function nor the argument that caused it.
    """
    assert su.asciistring("Café-Con-Leche!", replacement_char="") == "cafeconleche"


def test_asciistring_empty_replacement_still_honours_the_other_flags() -> None:
    assert su.asciistring("a1b2", replacement_char="", allow_digits=False) == "ab"
    # NFKD folds "é" to "e" + a combining acute; the base letter survives and
    # only the mark is dropped, which is the whole point of the normalization.
    assert su.asciistring("Café", replacement_char="", lower=False) == "Cafe"
