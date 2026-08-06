"""Smoke test for the MCP surface (`os_helper.mcp`).

Gated on the ``mcp`` extra (FastAPI + fastapi-mcp). Importing `os_helper.mcp`
mounts an MCP endpoint onto the FastAPI app; we check the endpoint is wired
and that the HTTP API keeps serving alongside it. Skips cleanly when the
extra isn't installed, so the default suite is unaffected.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("fastapi_mcp")
starlette_testclient = pytest.importorskip("starlette.testclient")

from os_helper import mcp as mcp_module  # noqa: E402  (import mounts MCP on the app)


def test_mcp_endpoint_is_mounted() -> None:
    """Importing the module publishes an `/mcp` endpoint named 'os-helper'."""
    paths = {r.path for r in mcp_module.app.routes}
    assert any("/mcp" in p for p in paths), paths
    assert mcp_module.mcp.name == "os-helper"


def test_api_still_served_next_to_mcp() -> None:
    """The FastAPI routes still work once the MCP endpoint is mounted."""
    client = starlette_testclient.TestClient(mcp_module.app)
    res = client.get("/health")
    assert res.status_code == 200 and res.json()["status"] == "ok"
    res = client.get("/hardware")
    assert res.status_code == 200 and res.json()["ram_gb"] > 0
