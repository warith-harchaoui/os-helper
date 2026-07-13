"""
String Utilities

This module provides helper functions for handling and manipulating strings,
including checks for empty strings, converting strings to ASCII-safe formats,
and converting between string representations and numerical time values.

Author:
 - Warith HARCHAOUI, https://linkedin.com/in/warith-harchaoui
"""

import re
import string
import unicodedata


def emptystring(s: str | None) -> bool:
    """
    Return True if ``s`` is None, not a string, or only whitespace.

    Convenient for input validation where ``""``, ``None`` and
    ``"   "`` should all be treated the same way.

    Parameters
    ----------
    s : Optional[str]
        The value to check.

    Returns
    -------
    bool
        True when ``s`` is None or contains only whitespace; False otherwise.

    Examples
    --------
    >>> emptystring("")
    True
    >>> emptystring("   ")
    True
    >>> emptystring(None)
    True
    >>> emptystring("hello")
    False
    """
    if s is None:
        return True
    return bool(isinstance(s, str) and len(s.strip()) == 0)



def asciistring(
    input_string: str,
    replacement_char: str = "-",
    lower: bool = True,
    allow_digits: bool = True
) -> str:
    """
    Convert a given string into a "safe" ASCII string by replacing accented and non-ASCII characters.

    Non-ASCII characters that cannot be converted will be replaced with a specified character.

    Parameters
    ----------
    input_string : str
        The input string to be converted.
    replacement_char : str, optional
        The character to replace non-ASCII or unwanted characters with. Defaults to '-'.
    lower : bool, optional
        Whether to convert the string to lowercase. Defaults to True.
    allow_digits : bool, optional
        Whether to allow digits in the resulting string. Defaults to True.

    Returns
    -------
    str
        A "safe" ASCII string with unwanted characters replaced and case adjusted.

    Examples
    --------
    >>> asciistring("MyFile@2024.txt")
    'myfile-2024-txt'

    >>> asciistring("Café-Con-Leche!", replacement_char="_")
    'cafe_con_leche'

    >>> asciistring("Special#File$2024", lower=False)
    'Special-File-2024'
    """
    # Normalize Unicode characters to decompose accents (e.g., é -> e + ´)
    normalized_string = unicodedata.normalize('NFKD', input_string)

    # Define the set of allowed characters
    allowed_chars = string.ascii_letters
    if allow_digits:
        allowed_chars += string.digits

    # Optionally convert to lowercase
    if lower:
        normalized_string = normalized_string.lower()

    # Replace disallowed characters with the replacement_char
    result = ''.join(
        c if c in allowed_chars and ord(c) < 128 else replacement_char
        for c in normalized_string
    )

    # Use regex to replace multiple consecutive replacement characters with a single one
    result = re.sub(f'{re.escape(replacement_char)}+', replacement_char, result)

    # Strip any leading or trailing replacement characters
    return result.strip(replacement_char)


