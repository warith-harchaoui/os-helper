"""os_helper: Model Context Protocol (MCP) surface.

A thin adapter that exposes the FastAPI app from :mod:`os_helper.api` as MCP
tools, so any MCP-aware host (an agent runtime, an IDE integration, a custom
shell) can call the safe os_helper utilities (hardware info, hashing, ASCII
normalization, size/time formatting, URL check, config loading) as first-class
tools. Uses `fastapi-mcp` (https://github.com/tadata-org/fastapi_mcp): one
wrapper publishes the whole existing HTTP surface, so the routes are never
duplicated.

Install the extra to pull in ``fastapi-mcp``::

    pip install "os-helper[mcp]"

Then run the server (HTTP API + MCP endpoint at ``/mcp``)::

    os-helper-mcp                 # console entry point
    python -m os_helper.mcp       # equivalent

Author
------
Warith HARCHAOUI, https://linkedin.com/in/warith-harchaoui
"""

from __future__ import annotations

try:
    from fastapi_mcp import FastApiMCP
except ImportError as exc:  # pragma: no cover - exercised only without the extra
    raise ImportError(
        'The MCP surface needs the [mcp] extra: pip install "os-helper[mcp]"'
    ) from exc

# Reuse the exact same FastAPI app: MCP is a thin wrapper on top, no new routes.
from os_helper.api import app

# Publish the HTTP endpoints (hardware / hash / ascii / misc / config) as MCP tools.
mcp = FastApiMCP(
    app,
    name="os-helper",
    description=(
        "os-helper MCP tools: OS/hardware detection, hashing, ASCII "
        "normalization, size/time formatting, URL reachability, and config "
        "loading — the safe, side-effect-free subset of os_helper, entirely "
        "on the local machine."
    ),
)
# Newer fastapi-mcp splits mount() into transport-specific mount_http(); fall back to
# the legacy mount() so a range of fastapi-mcp versions keeps working.
if hasattr(mcp, "mount_http"):
    mcp.mount_http()
else:  # pragma: no cover - legacy fastapi-mcp
    mcp.mount()


def main() -> None:
    """Console entry point (``os-helper-mcp``): serve the API + MCP endpoint.

    Boots the FastAPI app (now serving both the plain HTTP routes and the
    ``/mcp`` MCP endpoint) with uvicorn in a single worker. Local-first: binds
    to loopback by default (override with ``OS_HELPER_HOST`` / ``OS_HELPER_PORT``).
    """
    import os

    import uvicorn

    host = os.environ.get("OS_HELPER_HOST", "127.0.0.1")
    port = int(os.environ.get("OS_HELPER_PORT", "8010"))
    print(f"OS Helper API + MCP -> http://{host}:{port}  (MCP at /mcp)")
    uvicorn.run(app, host=host, port=port, workers=1)


if __name__ == "__main__":  # pragma: no cover
    main()
