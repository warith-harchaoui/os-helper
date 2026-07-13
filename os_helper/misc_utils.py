"""
Miscellaneous Utilities

Grab-bag of helpers that don't warrant a dedicated module:
- timestamp formatting (``now_string``)
- human-readable byte sizes (``format_size``)
- folder content description with optional HTML / JSON dump (``folder_description``)
- URL liveness checks (``is_working_url``)
- folder zipping (``zip_folder``)
- duration <-> string conversion (``time2str``, ``str2time``)
- simple file downloads (``download_file``)
- public IP lookup (``get_user_ip``)

Author:
 - Warith HARCHAOUI, https://linkedin.com/in/warith-harchaoui
"""

import html
import json
import os
import re
import time
import zipfile
from datetime import datetime

import requests
import validators

from .logging_utils import error, info
from .path_utils import dir_exists, join, size_file
from .string_utils import emptystring


def now_string(fmt: str = "log") -> str:
    """
    Get the current timestamp as a formatted string.

    Parameters
    ----------
    fmt : str, optional
        The format of the timestamp.
        "log" (default) => YYYY/MM/DD-HH:MM:SS
        "filename" => YYYY-MM-DD-HH-MM-SS (file-system safe)

    Returns
    -------
    str
        The formatted date-time string.
    """
    result = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
    if fmt == "filename":
        result = result.replace("/", "-").replace(":", "-")
    return result


def format_size(size: int) -> str:
    """
    Convert a byte count into a short human-readable string.

    Picks an appropriate SI-style unit (B, KB, MB, GB, TB) using decimal
    thresholds (1000-based). Useful for log lines and progress reporting.

    Parameters
    ----------
    size : int
        Size in bytes.

    Returns
    -------
    str
        Formatted size, e.g. ``"1.23 MB"``, ``"456.00 KB"``, ``"42 B"``.
    """
    if size > 1e12:
        return f"{size / 1e12:.2f} TB"
    if size > 1e9:
        return f"{size / 1e9:.2f} GB"
    if size > 1e6:
        return f"{size / 1e6:.2f} MB"
    if size > 1e3:
        return f"{size / 1e3:.2f} KB"
    return f"{int(size)} B"


def folder_description(
    path: str,
    recursive: bool = True,
    index_html: bool = True,
    with_size: bool = True,
    description_json: bool = True,
) -> dict[str, int]:
    """
    List a folder's files (with sizes) and optionally emit an HTML / JSON index.

    Walks ``path`` (recursively by default), skips hidden entries (names
    starting with ``"."``), and returns a mapping from each file's path
    relative to ``path`` to its size in bytes. When ``index_html`` is True,
    a Bootstrap-styled ``index.html`` is written into ``path``; when
    ``description_json`` is True, a ``description.json`` companion file is
    written as well.

    Parameters
    ----------
    path : str
        Path to the folder to describe (must exist).
    recursive : bool, optional
        If True, descend into subdirectories. Defaults to True.
    index_html : bool, optional
        If True, write ``path/index.html`` linking each entry. Defaults to True.
    with_size : bool, optional
        If True, include a human-readable size column in the HTML index.
        Defaults to True.
    description_json : bool, optional
        If True, write ``path/description.json`` with the raw mapping.
        Defaults to True.

    Returns
    -------
    dict
        Mapping of ``relative_file_path -> size_in_bytes`` for every
        non-hidden file found.

    Raises
    ------
    AssertionError
        If ``path`` does not exist or is not a directory.
    """
    assert dir_exists(path), f"Folder '{path}' does not exist"

    result: dict[str, int] = {}
    for root, _dirs, files in os.walk(path):
        if not recursive and root != path:
            break
        for file in files:
            if file.startswith("."):
                continue
            fpath = os.path.join(root, file)
            relpath = os.path.relpath(fpath, path)
            result[relpath] = size_file(fpath)

    if index_html:
        index_html_path = join(path, "index.html")
        size_header = "<th>Size</th>" if with_size else ""
        rows = []
        for rel, sz in sorted(result.items()):
            safe_name = html.escape(rel)
            size_cell = f"<td>{format_size(sz)}</td>" if with_size else ""
            rows.append(f'<tr><td><a href="{safe_name}">{safe_name}</a></td>{size_cell}</tr>')
        page = (
            "<!DOCTYPE html>\n<html>\n<head>\n"
            '    <meta charset="UTF-8">\n'
            f"    <title>Folder Index for {html.escape(path)}</title>\n"
            '    <link rel="stylesheet" '
            'href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">\n'
            "</head>\n"
            '<body class="bg-light">\n'
            '    <div class="container mt-4">\n'
            f'        <h1 class="mb-4">Folder: {html.escape(path)}</h1>\n'
            '        <table class="table table-striped">\n'
            f"            <thead><tr><th>File</th>{size_header}</tr></thead>\n"
            "            <tbody>\n"
            + "\n".join("                " + r for r in rows)
            + "\n            </tbody>\n"
            "        </table>\n"
            "    </div>\n"
            "</body>\n</html>\n"
        )
        with open(index_html_path, "w", encoding="utf-8") as fout:
            fout.write(page)
        info(f"HTML index generated at: {index_html_path}")

    if description_json:
        desc_json_path = join(path, "description.json")
        with open(desc_json_path, "w", encoding="utf-8") as jfile:
            json.dump(result, jfile, indent=2)
        info(f"Folder description JSON written to: {desc_json_path}")

    return result


def is_working_url(url: str) -> bool:
    """
    Return True if ``url`` is syntactically valid and answers 200 to a HEAD.

    Parameters
    ----------
    url : str
        The URL to check.

    Returns
    -------
    bool
        True only when validation succeeds *and* the HEAD request returns
        HTTP 200 within five seconds. Network errors and non-200 responses
        both yield False.
    """
    if not validators.url(url):
        return False
    try:
        resp = requests.head(url, timeout=5)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def zip_folder(folder_path: str, zip_file_path: str = "") -> None:
    """
    Create a deflated ``.zip`` archive of a folder's contents.

    Hidden files (names beginning with ``.``) are skipped. Paths inside the
    archive are stored relative to ``folder_path``.

    Parameters
    ----------
    folder_path : str
        The path to the folder to zip (must exist).
    zip_file_path : str, optional
        Destination archive path. Defaults to ``folder_path + ".zip"``.

    Raises
    ------
    AssertionError
        If ``folder_path`` does not exist.
    """
    assert dir_exists(folder_path), f"Folder '{folder_path}' does not exist"
    if emptystring(zip_file_path):
        zip_file_path = folder_path + ".zip"

    with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(folder_path):
            for file in files:
                if file.startswith("."):
                    continue
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, folder_path)
                zf.write(full_path, arcname)
    info(f"Zipped folder '{folder_path}' into '{zip_file_path}'")

def time2str(seconds: float, no_space: bool = False) -> str:
    """
    Convert a float number of seconds to a readable string, e.g. "1 hr 2 min 5 sec".

    Parameters
    ----------
    seconds : float
        Time in seconds.
    no_space : bool, optional
        If True, removes spaces between number and unit. e.g. "1hr 2min 5sec".

    Returns
    -------
    str
        A human-readable time string.

    Examples
    -------
    >>> time2str(5400.0)
    "1 hr 30 min"
    >>> time2str(120.0)
    "2 min"
    >>> time2str(3661.0)
    "1 hr 1 min 1 sec"

    """
    # Convert seconds to time struct
    time_struct = time.gmtime(seconds)

    parts = []
    hrs = time_struct.tm_hour + (time_struct.tm_mday - 1) * 24
    if hrs:
        parts.append(f"{hrs} hr")
    if time_struct.tm_min:
        parts.append(f"{time_struct.tm_min} min")
    if time_struct.tm_sec or (not hrs and not time_struct.tm_min):
        parts.append(f"{time_struct.tm_sec} sec")

    if no_space:
        parts = [p.replace(" ", "") for p in parts]
    return " ".join(parts)

def str2time(input_string: str) -> float:
    """
    Parse a time string into seconds.

    Parameters
    ----------
    input_string : str
        A string representing time.

    Returns
    -------
    float
        Number of seconds parsed from the string.

    Examples
    --------
    >>> str2time("1:30:00")
    5400.0
    >>> str2time("1 hr 30 min")
    5400.0
    >>> str2time("120 s")
    120.0
    >>> str2time("1.5 hours")
    5400.0
    >>> str2time("1.5 days")
    129600.0
    """
    if emptystring(input_string):
        return 0.0

    input_string = input_string.strip().lower()

    # Handle HH:MM:SS format
    if ":" in input_string:
        try:
            parts = [float(p) for p in input_string.split(":")]
            if len(parts) == 3:  # HH:MM:SS
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            elif len(parts) == 2:  # MM:SS
                return parts[0] * 60 + parts[1]
            else:
                error(f"Invalid time format: {input_string} - expected 2 or 3 parts")
                return 0.0
        except ValueError:
            error(f"Invalid time format: {input_string}")
            return 0.0

    # Handle text formats like "1 hour 30 minutes"
    time_units = {
        ("days", "day", "d"): 24 * 3600,
        ("hours", "hour", "hrs", "hr", "h"): 3600,
        ("minutes", "minute", "mins", "min", "m"): 60,
        ("seconds", "second", "secs", "sec", "s"): 1
    }

    total_seconds = 0.0
    remaining = input_string
    found_unit = False

    for units, multiplier in time_units.items():
        for unit in units:
            pattern = fr"(\d+(?:\.\d+)?)\s*{unit}\b"
            match = re.search(pattern, remaining)
            if match:
                try:
                    value = float(match.group(1))
                    total_seconds += value * multiplier
                    remaining = re.sub(pattern, "", remaining, count=1).strip()
                    found_unit = True
                except ValueError:
                    error(f"Invalid numeric value in: {input_string}")
                    continue

    if found_unit:
        return total_seconds

    # Try parsing as raw seconds
    try:
        return float(input_string)
    except ValueError:
        error(f"Cannot parse time from: {input_string}")
        return 0.0


def download_file(url: str, file_path: str = "") -> None:
    """
    Download a URL to a local file.

    If ``file_path`` is empty, the destination name is derived from the last
    path segment of the URL (query string stripped).

    Parameters
    ----------
    url : str
        The URL to download from.
    file_path : str, optional
        Destination path. Defaults to the URL's last segment.

    Raises
    ------
    AssertionError
        If the URL fails the :func:`is_working_url` precondition.
    requests.RequestException
        If the GET request fails or returns a non-2xx status.
    """
    assert is_working_url(url), f"URL '{url}' is not working"

    if emptystring(file_path):
        # Derive a destination name from the URL: strip the scheme, drop the
        # query string, and take the last path segment.
        stripped_url = url.replace("https://", "").replace("http://", "")
        stripped_url = stripped_url.split("?")[0]
        file_path = stripped_url.split("/")[-1]

    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except requests.RequestException as e:
        error(f"Failed to download from '{url}': {e}")
        raise

    with open(file_path, "wb") as fout:
        fout.write(resp.content)

    info(f"File downloaded from '{url}' and saved to '{file_path}'")


def get_user_ip() -> dict[str, str | None]:
    """
    Fetch the caller's public IPv4 and IPv6 addresses via the ipify API.

    Returns
    -------
    dict
        ``{"ipv4": <str or None>, "ipv6": <str or None>}``. An individual
        entry is None when its endpoint fails or returns no address.

    Raises
    ------
    AssertionError
        If both endpoints fail and no address could be retrieved.
    """
    ip_address: dict[str, str | None] = {"ipv4": None, "ipv6": None}

    for family, endpoint in (
        ("ipv4", "https://api.ipify.org?format=json"),
        ("ipv6", "https://api64.ipify.org?format=json"),
    ):
        try:
            ip_address[family] = requests.get(endpoint, timeout=5).json().get("ip")
        except (requests.RequestException, ValueError, KeyError):
            ip_address[family] = None

    assert any(ip_address.values()), "Failed to retrieve IP address (no IPv4 / IPv6 address found)"
    return ip_address
