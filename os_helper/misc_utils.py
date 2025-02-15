"""
Miscellaneous Utilities

This module provides a variety of helper functions that do not fit neatly into
a single category, such as:
 - Generating timestamps
 - Formatting file sizes
 - Describing folders
 - Checking URLs
 - Compressing folders
 - Timing utilities
 - Simple file downloading
 - Converting times

Authors:
 - Warith Harchaoui, https://harchaoui.org/warith
 - Mohamed Chelali, https://mchelali.github.io
 - Bachir Zerroug, https://www.linkedin.com/in/bachirzerroug
"""

import os
import time
import json
from typing import Dict, Optional
import zipfile
import requests
import validators
import re


from datetime import datetime

import logging
from .path_utils import file_exists, dir_exists, size_file, join

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
    Convert a file size in bytes to a human-readable string (B, KB, MB, GB).

    Parameters
    ----------
    size : int
        Size in bytes.

    Returns
    -------
    str
        Formatted size string (e.g. '1.23 MB', '456.00 KB', etc.).
    """
    if size > 1e12:
        return "%.2f TB" % (size / 1e12)
    elif size > 1e9:
        return "%.2f GB" % (size / 1e9)
    elif size > 1e6:
        return "%.2f MB" % (size / 1e6)
    elif size > 1e3:
        return "%.2f KB" % (size / 1e3)
    else:
        return "%d B" % int(size)




# def folder_description(path: str, recursive: bool = True, index_html: bool = True, with_size: bool = True) -> dict:
#     """
#     Describe the contents of a folder, optionally recursively, and generate an HTML index.

#     Parameters
#     ----------
#     path : str
#         Path to the folder.
#     recursive : bool, optional
#         If True, descends into subdirectories. Defaults to True.
#     index_html : bool, optional
#         If True, writes an index.html in the folder. Defaults to True.
#     with_size : bool, optional
#         If True, includes file sizes in the listing. Defaults to True.

#     Returns
#     -------
#     dict
#         A dictionary mapping relative file paths -> file sizes in bytes.
#     """
#     check(dir_exists(path), f"Folder {path} cannot be described because it does not exist")

#     result = {}
#     for root, dirs, files in os.walk(path):
#         if not recursive and root != path:
#             break
#         for file in files:
#             if file.startswith("."):  # skip hidden
#                 continue
#             fpath = os.path.join(root, file)
#             relpath = os.path.relpath(fpath, path)
#             result[relpath] = size_file(fpath)

#     # Optionally generate index.html
#     if index_html:
#         index_html_path = join(path, "index.html")
#         with open(index_html_path, "wt") as fout:
#             fout.write(f"""
# <!DOCTYPE html>
# <html>
# <head>
#     <meta charset="UTF-8">
#     <title>Folder Index for {path}</title>
#     <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
# </head>
# <body class="bg-light">
#     <div class="container mt-4">
#         <h1 class="mb-4">Folder: {path}</h1>
#         <table class="table table-striped">
#             <thead>
#                 <tr>
#                     <th>File</th>
#                     {"<th>Size</th>" if with_size else ""}
#                 </tr>
#             </thead>
#             <tbody>
# """)
#             for rel, sz in sorted(result.items()):
#                 escaped_name = rel.replace("<","&lt;").replace(">","&gt;").replace("&","&amp;")
#                 size_col = f"<td>{format_size(sz)}</td>" if with_size else ""
#                 fout.write(f'<tr><td><a href="{escaped_name}">{escaped_name}</a></td>{size_col}</tr>\n')
#             fout.write("""
#             </tbody>
#         </table>
#     </div>
# </body>
# </html>
# """)
#         info(f"HTML index generated at: {index_html_path}")

#     # Also store a JSON version of the description
#     desc_json_path = join(path, "description.json")
#     with open(desc_json_path, "wt") as jfile:
#         json.dump(result, jfile, indent=2)
#     info(f"Folder description JSON written to: {desc_json_path}")

#     return result


def is_working_url(url: str) -> bool:
    """
    Check if a URL is valid and reachable.

    This function validates a URL (syntax) and sends a HEAD request to see if it's reachable.

    Parameters
    ----------
    url : str
        The URL to check.

    Returns
    -------
    bool
        True if URL is valid and returns status_code=200, else False.
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
    Zip the contents of a folder into a .zip file.

    Parameters
    ----------
    folder_path : str
        The path to the folder to zip.
    zip_file_path : str, optional
        The path/name of the resulting .zip file. If empty,
        defaults to folder_path.zip
    """
    assert dir_exists(folder_path), f"Folder '{folder_path}' does not exist"
    if not zip_file_path:
        zip_file_path = folder_path + ".zip"

    with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # skip hidden
                if file.startswith("."):
                    continue
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, folder_path)
                zf.write(full_path, arcname)
    logging.info(f"Zipped folder '{folder_path}' into '{zip_file_path}'")

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
    if not input_string:
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
                logging.error(f"Invalid time format: {input_string} - expected 2 or 3 parts")
                return 0.0
        except ValueError:
            logging.error(f"Invalid time format: {input_string}")
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
                    logging.error(f"Invalid numeric value in: {input_string}")
                    continue

    if found_unit:
        return total_seconds

    # Try parsing as raw seconds
    try:
        return float(input_string)
    except ValueError:
        logging.error(f"Cannot parse time from: {input_string}")
        return 0.0


def download_file(url: str, file_path: str = "") -> None:
    """
    Download a file from a URL, optionally specifying output file path.

    Parameters
    ----------
    url : str
        The URL to download from.
    file_path : str, optional
        The path/filename to save to. If empty, uses last part of URL.

    Raises
    ------
    SystemExit
        If the URL is invalid or unreachable.
    """
    assert is_working_url(url), f"URL '{url}' is not working"

    if not file_path:
        # Attempt to guess filename from last part of the URL
        stripped_url = url.replace("https://", "").replace("http://", "")
        # Remove query params
        stripped_url = stripped_url.split("?")[0]
        segments = stripped_url.split("/")
        file_path = segments[-1] 

    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to download from '{url}': {e}")

    with open(file_path, "wb") as fout:
        fout.write(resp.content)

    logging.info(f"File downloaded from '{url}' and saved to '{file_path}'")

def get_user_ip() -> Dict[str, Optional[str]]:
    """
    Fetches the user's public IP addresses in both IPv4 and IPv6 formats, if available.

    This function attempts to retrieve the user's IP addresses using the `ipify` API.
    It tries separate endpoints for IPv4 and IPv6 and returns a dictionary containing
    both addresses, or `None` if an address could not be retrieved.

    Returns
    -------
    dict of {str: Optional[str]}
        A dictionary with the keys "ipv4" and "ipv6". The values are either the IP addresses
        as strings or `None` if the address could not be fetched.
        
    """
    
    # Initialize a dictionary to store both IPv4 and IPv6 addresses
    ip_address = {"ipv4": None, "ipv6": None}
    
    some_ip = False

    # Try to get the IPv4 address
    try:
        response_v4 = requests.get("https://api.ipify.org?format=json")
        ip = response_v4.json().get("ip")
        if not( ip is None):
            ip_address["ipv4"] = ip
            some_ip = True
    except (requests.RequestException, KeyError):
        ip_address["ipv4"] = None  # Set to None if the request or dict access fails

    # Try to get the IPv6 address
    try:
        response_v6 = requests.get("https://api64.ipify.org?format=json")
        ip = response_v6.json().get("ip")
        if not( ip is None):
            ip_address["ipv6"] = ip
            some_ip = True
    except (requests.RequestException, KeyError):
        ip_address["ipv6"] = None  # Set to None if the request or dict access fails
        
    assert some_ip, "Failed to retrieve IP address (no IPv4 / IPv6 address found)"

    return ip_address