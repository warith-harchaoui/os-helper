"""
os_helper.api — HTTP surface for the safe, side-effect-free os_helper utilities.

Exposes a deliberately **narrow** slice of the library over FastAPI: OS/
hardware detection, hashing, ASCII normalization, size/time formatting, a URL
reachability check, and config loading. All read-only or purely computational
— nothing here mutates the filesystem (no `mkdir`/`rm`/`cp`/`download`
endpoint). Those stay library/CLI-only: a general-purpose "delete this path
over HTTP" endpoint is a different risk profile than what the rest of the
suite's `[api]` surfaces expose (bucket/sftp mutate a REMOTE store the caller
already has credentials for; a bare filesystem-mutation endpoint here would
let any HTTP caller touch the local disk). Widen deliberately, not by default.

FastAPI is an optional dependency (the ``[api]`` extra) — importing
``os_helper`` itself never requires it; only importing this module does.

Run it
------
``uvicorn os_helper.api:app`` or the console entry point
``os-helper-api`` (docs at ``/docs``).

Author
------
Warith HARCHAOUI, https://linkedin.com/in/warith-harchaoui
"""

from __future__ import annotations

from typing import Any

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except ModuleNotFoundError as exc:  # pragma: no cover - only hit without fastapi
    raise SystemExit(
        "The HTTP surface needs the optional 'api' extra. Install it with\n"
        "  pip install 'os-helper[api]'"
    ) from exc

from . import (
    asciistring,
    format_size,
    get_config,
    hardware_info,
    hash_string,
    is_working_url,
    linux,
    macos,
    now_string,
    windows,
)

try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _pkg_version

    _API_VERSION = _pkg_version("os-helper")
except PackageNotFoundError:  # pragma: no cover — source-tree / uninstalled run
    _API_VERSION = "0"
except Exception:  # pragma: no cover — never fatal on any packaging quirk
    _API_VERSION = "0"


# ---------------------------------------------------------------------------
# Request bodies (POST endpoints only; GET endpoints take query params)
# ---------------------------------------------------------------------------


class HashStringRequest(BaseModel):
    """Body for ``POST /hash/string``."""

    text: str
    size: int = -1


class AsciiRequest(BaseModel):
    """Body for ``POST /str/ascii``."""

    text: str
    replacement_char: str = "-"
    lower: bool = True
    allow_digits: bool = True


class ConfigRequest(BaseModel):
    """Body for ``POST /config``.

    Mirrors :func:`os_helper.get_config`'s fallback order (file/folder ->
    ``.env`` files -> process environment). ``path``/``env_files`` are paths
    on the SERVER's filesystem — this is a local-first tool, not a place to
    read someone else's config over the network.
    """

    keys: list[str]
    config_type: str
    path: str | None = None
    env_files: list[str] | None = None


app = FastAPI(
    title="OS Helper API",
    description=(
        "HTTP surface for the safe, side-effect-free os_helper utilities: "
        "OS/hardware detection, hashing, ASCII normalization, size/time "
        "formatting, URL reachability, config loading. No filesystem "
        "mutation is exposed here — see the CLI/library for that."
    ),
    version=_API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/health", tags=["meta"])
def health() -> dict[str, Any]:
    """Report that the server is up."""
    return {"status": "ok", "version": _API_VERSION}


@app.get("/os", tags=["reads"])
def os_system() -> dict[str, str]:
    """Return the current OS short name (macos / linux / windows / unknown)."""
    if windows():
        name = "windows"
    elif macos():
        name = "macos"
    elif linux():
        name = "linux"
    else:
        name = "unknown"
    return {"os": name}


@app.get("/hardware", tags=["reads"])
def hardware() -> dict[str, Any]:
    """Return this machine's hardware snapshot (CPU, RAM, GPU) as JSON."""
    return hardware_info()


@app.post("/hash/string", tags=["reads"])
def hash_string_endpoint(req: HashStringRequest) -> dict[str, str]:
    """
    Hash a string; ``size`` truncates the digest to that many hex characters.

    Parameters
    ----------
    req : HashStringRequest
        The text to hash and the optional truncation size.

    Returns
    -------
    dict[str, str]
        ``{"hash": <digest>}``.
    """
    return {"hash": hash_string(req.text, size=req.size)}


@app.post("/str/ascii", tags=["reads"])
def ascii_endpoint(req: AsciiRequest) -> dict[str, str]:
    """
    Normalize a string into a filesystem-safe ASCII slug.

    Parameters
    ----------
    req : AsciiRequest
        The text to normalize and the slugging options (replacement
        character, lower-casing, digit handling).

    Returns
    -------
    dict[str, str]
        ``{"result": <slug>}``.
    """
    return {
        "result": asciistring(
            req.text,
            replacement_char=req.replacement_char,
            lower=req.lower,
            allow_digits=req.allow_digits,
        )
    }


@app.get("/misc/format-size", tags=["reads"])
def format_size_endpoint(size: int) -> dict[str, str]:
    """
    Format a byte count as a human-readable string (e.g. '11.8 MB').

    Parameters
    ----------
    size : int
        Byte count to format.

    Returns
    -------
    dict[str, str]
        ``{"formatted": <human-readable size>}``.
    """
    return {"formatted": format_size(size)}


@app.get("/misc/now", tags=["reads"])
def now_endpoint(fmt: str = "log") -> dict[str, str]:
    """
    Return a formatted timestamp.

    Parameters
    ----------
    fmt : str
        Timestamp style: ``'log'`` or ``'filename'``.

    Returns
    -------
    dict[str, str]
        ``{"timestamp": <formatted timestamp>}``.
    """
    return {"timestamp": now_string(fmt)}


@app.get("/misc/url-ok", tags=["reads"])
def url_ok_endpoint(url: str) -> dict[str, bool]:
    """
    Check whether a URL is syntactically valid and reachable.

    Parameters
    ----------
    url : str
        URL to check.

    Returns
    -------
    dict[str, bool]
        ``{"ok": <True if reachable>}``.
    """
    return {"ok": is_working_url(url)}


@app.post("/config", tags=["reads"])
def config_endpoint(req: ConfigRequest) -> dict[str, Any]:
    """
    Load a set of keys via :func:`os_helper.get_config` and return them.

    Parameters
    ----------
    req : ConfigRequest
        The keys to resolve plus the fallback-order inputs (``config_type``,
        ``path``, ``env_files``).

    Returns
    -------
    dict[str, Any]
        Mapping with one entry per requested key.
    """
    return get_config(
        keys=req.keys,
        config_type=req.config_type,
        path=req.path,
        env_files=req.env_files,
    )


def main() -> None:
    """Console entry point (``os-helper-api``): serve the HTTP surface.

    Local-first: binds to loopback by default (override with ``OS_HELPER_HOST``
    / ``OS_HELPER_PORT``).
    """
    import os

    import uvicorn

    host = os.environ.get("OS_HELPER_HOST", "127.0.0.1")
    port = int(os.environ.get("OS_HELPER_PORT", "8010"))
    print(f"OS Helper API -> http://{host}:{port}  (docs at /docs)")
    uvicorn.run(app, host=host, port=port, workers=1)


if __name__ == "__main__":  # pragma: no cover
    main()
