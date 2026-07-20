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

# Postpone annotation evaluation so union syntax like ``str | None`` is legal
# on the oldest supported interpreter (Python 3.10).
from __future__ import annotations

import html
import json
import os
import re
import time
import zipfile
from datetime import datetime
from typing import Any

# ``requests`` powers the URL/download helpers; ``validators`` gives us a
# quick, dependency-light URL syntax check before we ever touch the network.
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
    # Default "log" layout keeps ``/`` and ``:`` for human readability.
    result = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
    # The "filename" variant swaps those characters out because ``/`` and ``:``
    # are illegal (or awkward) in file names on common filesystems.
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
    # Walk from the largest unit down; the first threshold the size clears wins,
    # so we always report in the most compact sensible unit. We use decimal
    # (1000-based) thresholds — matching how disk vendors quote sizes — rather
    # than binary (1024-based) ones.
    if size > 1e12:
        return f"{size / 1e12:.2f} TB"
    if size > 1e9:
        return f"{size / 1e9:.2f} GB"
    if size > 1e6:
        return f"{size / 1e6:.2f} MB"
    if size > 1e3:
        return f"{size / 1e3:.2f} KB"
    # Below a kilobyte we show whole bytes — no fractional byte makes sense.
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
    # Walk the tree, collecting every visible file's size keyed by its path
    # relative to ``path`` (so the mapping is portable, not tied to absolutes).
    for root, _dirs, files in os.walk(path):
        # In non-recursive mode, stop as soon as ``os.walk`` steps below the top
        # level (the first yielded ``root`` is ``path`` itself).
        if not recursive and root != path:
            break
        for file in files:
            # Skip dotfiles: they are usually editor/OS metadata, not content.
            if file.startswith("."):
                continue
            fpath = os.path.join(root, file)
            relpath = os.path.relpath(fpath, path)
            result[relpath] = size_file(fpath)

    # Optionally render a browsable HTML index of everything we found.
    if index_html:
        index_html_path = join(path, "index.html")
        size_header = "<th>Size</th>" if with_size else ""
        rows = []
        # Sort for deterministic output; ``html.escape`` guards against file
        # names containing characters that would otherwise break the markup.
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
        # UTF-8 so non-ASCII file names survive the round-trip to disk.
        with open(index_html_path, "w", encoding="utf-8") as fout:
            fout.write(page)
        info(f"HTML index generated at: {index_html_path}")

    # Optionally also dump the raw mapping as machine-readable JSON.
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
    # Cheap syntactic gate first: reject obviously malformed URLs before we
    # spend a network round-trip on them.
    if not validators.url(url):
        return False
    try:
        # HEAD (not GET) so we probe liveness without downloading the body;
        # a short timeout keeps callers from hanging on dead hosts.
        resp = requests.head(url, timeout=5)
        return resp.status_code == 200
    except requests.RequestException:
        # Any transport-level failure means "not reachable" for our purposes.
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
    # Default the archive name to ``<folder>.zip`` sitting next to the folder.
    if emptystring(zip_file_path):
        zip_file_path = folder_path + ".zip"

    # ``ZIP_DEFLATED`` actually compresses (vs ``ZIP_STORED`` which just packs).
    with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(folder_path):
            for file in files:
                # Exclude dotfiles for the same reason as folder_description.
                if file.startswith("."):
                    continue
                full_path = os.path.join(root, file)
                # Store paths relative to the folder so the archive extracts
                # cleanly without leaking the source machine's directory layout.
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
    # Reuse ``gmtime`` as a cheap seconds -> (h, m, s) decomposer; UTC/gmtime
    # avoids any local-timezone offset creeping into a pure duration.
    time_struct = time.gmtime(seconds)

    parts = []
    # ``gmtime`` caps hours at 23 and rolls the rest into the day-of-month, so
    # fold those extra days back into the hour count to support long durations.
    hrs = time_struct.tm_hour + (time_struct.tm_mday - 1) * 24
    if hrs:
        parts.append(f"{hrs} hr")
    if time_struct.tm_min:
        parts.append(f"{time_struct.tm_min} min")
    # Always emit a seconds component when everything else is zero, so a tiny
    # duration renders as "0 sec" rather than an empty string.
    if time_struct.tm_sec or (not hrs and not time_struct.tm_min):
        parts.append(f"{time_struct.tm_sec} sec")

    # Compact form drops the space between number and unit ("1hr" vs "1 hr").
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
    # An empty/blank input has no duration — return zero rather than raising.
    if emptystring(input_string):
        return 0.0

    # Normalize case and surrounding whitespace so the matchers below are simple.
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
        ("seconds", "second", "secs", "sec", "s"): 1,
    }

    total_seconds = 0.0
    remaining = input_string
    found_unit = False

    # Scan for every "<number> <unit>" occurrence and accumulate its
    # contribution. We consume each match from ``remaining`` so a unit cannot
    # be double-counted (e.g. the "h" in "hours" won't also match on its own).
    for units, multiplier in time_units.items():
        for unit in units:
            pattern = rf"(\d+(?:\.\d+)?)\s*{unit}\b"
            match = re.search(pattern, remaining)
            if match:
                try:
                    value = float(match.group(1))
                    total_seconds += value * multiplier
                    # Strip the matched span so overlapping units don't re-fire.
                    remaining = re.sub(pattern, "", remaining, count=1).strip()
                    found_unit = True
                except ValueError:
                    error(f"Invalid numeric value in: {input_string}")
                    continue

    # If any unit token matched, trust the accumulated total.
    if found_unit:
        return total_seconds

    # Otherwise fall back to interpreting the whole string as bare seconds.
    try:
        return float(input_string)
    except ValueError:
        error(f"Cannot parse time from: {input_string}")
        return 0.0


def progress_bar(
    total: int | None = None,
    *,
    desc: str = "",
    disable: bool | None = None,
    unit: str = "B",
) -> Any:
    """Create a :mod:`tqdm` progress bar configured for file transfers.

    The suite-wide byte-transfer bar, so every helper that moves bytes (HTTP
    download, S3 up / download, SFTP put / get) shows the *same* progress UI:
    byte-scaled units (KiB / MiB / GiB), a known total when available (for a
    percentage + ETA), and — crucially — **auto-suppression when ``stderr`` is
    not a TTY**, so CI logs and piped output are never flooded with control
    characters. Each caller simply wraps its transfer library's progress hook
    (``requests`` chunks, boto3 ``Callback``, paramiko ``callback``) around one
    of these bars.

    Parameters
    ----------
    total : int or None, optional
        Total number of bytes when known (enables percentage + ETA); ``None``
        leaves the bar open-ended.
    desc : str, optional
        Short label shown at the left of the bar (e.g. the file / key name).
    disable : bool or None, optional
        Force the bar on / off. ``None`` (default) auto-disables when ``stderr``
        is not an interactive terminal.
    unit : str, optional
        Progress unit (default ``"B"``; ``unit_scale`` renders raw byte counts as
        KiB / MiB / GiB).

    Returns
    -------
    tqdm.tqdm
        A ready progress bar; call ``.update(n)`` per transferred chunk and
        ``.close()`` when done.

    Examples
    --------
    >>> bar = progress_bar(total=10, desc="demo", disable=True)
    >>> bar.total
    10
    >>> bar.disable
    True
    >>> bar.close()
    """
    import sys

    from tqdm import tqdm

    # Auto-suppress on a non-TTY (CI / piped logs) unless the caller forces it.
    if disable is None:
        disable = not sys.stderr.isatty()
    return tqdm(
        total=total,
        desc=desc,
        unit=unit,
        unit_scale=True,
        unit_divisor=1024,
        disable=disable,
    )


def _adaptive_chunk_size(
    total: int | None,
    *,
    target: int = 512,
    lo: int = 64 * 1024,
    hi: int = 4 * 1024 * 1024,
    default: int = 1 << 20,
) -> int:
    """Choose a streaming block size proportional to the total download size.

    Sizing the read/write block by the payload keeps two things stable across a
    2 KB config file and a multi-gigabyte model: the number of progress-bar
    redraws and the per-iteration Python / syscall overhead. Rather than
    hand-tuned size buckets, aim for a fixed ``target`` number of chunks and
    clamp the result to a sane ``[lo, hi]`` window. When the size is unknown (no
    ``Content-Length`` header), fall back to ``default``. Note the block size is
    a local buffering knob only — it does not change the bytes on the wire.

    Parameters
    ----------
    total : int or None
        Total download size in bytes, or ``None`` when the server sent no
        ``Content-Length``.
    target : int, optional
        Desired number of chunks over the whole download (default 512).
    lo, hi : int, optional
        Lower / upper clamp on the returned block size in bytes (default 64 KiB /
        4 MiB).
    default : int, optional
        Block size used when ``total`` is unknown (default 1 MiB).

    Returns
    -------
    int
        Block size in bytes to pass to ``iter_content`` and the file writes.

    Examples
    --------
    >>> _adaptive_chunk_size(750 * 1024 * 1024)  # ~750 MB → ~1.5 MiB
    1536000
    >>> _adaptive_chunk_size(None)               # unknown size → 1 MiB default
    1048576
    >>> _adaptive_chunk_size(5 * 1024 ** 3) == 4 * 1024 * 1024  # 5 GB → hi clamp
    True
    >>> _adaptive_chunk_size(10 * 1024) == 64 * 1024             # 10 KB → lo clamp
    True
    """
    # No size advertised → we cannot scale; use the fixed fallback.
    if not total:
        return default
    # Aim for ``target`` chunks, but never below ``lo`` (so tiny files still
    # stream) nor above ``hi`` (bounded memory + a bar that keeps moving on huge
    # files).
    return max(lo, min(hi, total // target))


def download_file(
    url: str,
    file_path: str = "",
    *,
    chunk_size: int | None = None,
    progress: bool = True,
    check_url: bool = True,
) -> dict[str, object]:
    """
    Download a URL to a local file, streaming with a progress bar.

    The response is streamed block-by-block and written as it arrives, so the
    whole payload is **never** held in memory — a multi-hundred-megabyte archive
    downloads with a flat memory footprint. A :mod:`tqdm` progress bar is shown
    on an interactive terminal (auto-suppressed when ``stderr`` is not a TTY,
    e.g. CI / log files). Start and completion are logged via :func:`info`; a
    failed request is logged via :func:`error` and re-raised.

    The block size adapts to the payload by default (via
    :func:`_adaptive_chunk_size`): the server's ``Content-Length`` — already read
    for the progress total, so no extra request — is turned into a block sized to
    give ~500 updates, clamped to ``[64 KiB, 4 MiB]``. That keeps a 2 KB config
    and a multi-GB model both sensible. Pass an explicit ``chunk_size`` to
    override.

    If ``file_path`` is empty, the destination name is derived from the last
    path segment of the URL (query string stripped).

    Parameters
    ----------
    url : str
        The URL to download from.
    file_path : str, optional
        Destination path. Defaults to the URL's last segment.
    chunk_size : int or None, optional
        Streaming block size in bytes. ``None`` (default) picks a size adaptively
        from the download's ``Content-Length``; an explicit int overrides it.
    progress : bool, optional
        Show a progress bar on an interactive terminal (default ``True``). The
        bar is auto-suppressed when ``stderr`` is not a TTY.
    check_url : bool, optional
        Pre-validate the URL with a HEAD request (default ``True``). Set to
        ``False`` when the server rejects HEAD (405/403) or you simply want to
        skip the extra round-trip and let the GET's ``raise_for_status`` be the
        only gate.

    Returns
    -------
    dict of str to object
        Lightweight metadata about the completed download:
        ``{"path": <destination>, "content_type": <server MIME or "">,
        "bytes": <size on disk>}``. Callers that only want the side effect
        (the file on disk) can ignore it.

    Raises
    ------
    AssertionError
        If the URL fails the :func:`is_working_url` precondition.
    requests.RequestException
        If the GET request fails or returns a non-2xx status.
    """
    # Refuse to start a download we already know will fail (bad or dead URL).
    # The precheck is a HEAD request, which some servers/CDNs reject (405/403)
    # even though a GET succeeds; pass ``check_url=False`` to skip it and rely on
    # ``raise_for_status`` below instead.
    if check_url:
        assert is_working_url(url), f"URL '{url}' is not working"

    if emptystring(file_path):
        # Derive a destination name from the URL: strip the scheme, drop the
        # query string, and take the last path segment.
        stripped_url = url.replace("https://", "").replace("http://", "")
        stripped_url = stripped_url.split("?")[0]
        file_path = stripped_url.split("/")[-1]

    info(f"Downloading '{url}' → '{file_path}'")
    try:
        # ``stream=True`` + iter_content keeps memory flat regardless of size;
        # a (connect, read) timeout avoids hanging forever on a stalled server.
        with requests.get(url, stream=True, timeout=(10, 60)) as resp:
            # Turn any 4xx/5xx into an exception so we never write an error page
            # to disk as if it were the requested file.
            resp.raise_for_status()
            # Capture the server's declared type so the caller can, e.g., pick a
            # file extension from it without issuing a second request.
            content_type = resp.headers.get("Content-Type", "")
            # Content-Length gives the bar a total + ETA; absent → open-ended.
            total = int(resp.headers.get("Content-Length", 0)) or None
            # Adapt the block size to the payload unless the caller pinned one.
            block = chunk_size if chunk_size is not None else _adaptive_chunk_size(total)
            # Shared suite bar: auto-quiet on a non-TTY, forced off when progress=False.
            bar = progress_bar(
                total=total,
                desc=os.path.basename(file_path) or "download",
                disable=None if progress else True,
            )
            # Binary mode: the payload may be an image, archive, etc., not text.
            with open(file_path, "wb") as fout:
                for chunk in resp.iter_content(chunk_size=block):
                    if not chunk:
                        continue  # keep-alive chunk carries no data
                    fout.write(chunk)
                    bar.update(len(chunk))
            bar.close()
    except requests.RequestException as e:
        error(f"Failed to download from '{url}': {e}")
        raise

    size = size_file(file_path)
    info(f"File downloaded from '{url}' and saved to '{file_path}' ({size} bytes)")
    # Return lightweight metadata so callers that need the MIME type / final path
    # (e.g. to choose a file extension) don't have to re-request. Historically
    # this returned None; existing callers that ignore the return are unaffected.
    return {"path": file_path, "content_type": content_type, "bytes": size}


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

    # Query the v4-only and v4/v6 ipify endpoints independently so a failure of
    # one family still lets the other succeed.
    for family, endpoint in (
        ("ipv4", "https://api.ipify.org?format=json"),
        ("ipv6", "https://api64.ipify.org?format=json"),
    ):
        try:
            ip_address[family] = requests.get(endpoint, timeout=5).json().get("ip")
        except (requests.RequestException, ValueError, KeyError):
            # Network error, non-JSON body, or missing key all mean "unknown".
            ip_address[family] = None

    # Only fail hard when BOTH lookups came back empty — a single address is
    # still a useful result for the caller.
    assert any(ip_address.values()), "Failed to retrieve IP address (no IPv4 / IPv6 address found)"
    return ip_address
