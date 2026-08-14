"""
Tests for os_helper.api (the FastAPI HTTP surface).

Gated on the ``api`` extra (FastAPI). Uses Starlette's TestClient — no real
server or network. Skips cleanly when the extra isn't installed, so the
default suite is unaffected.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
starlette_testclient = pytest.importorskip("starlette.testclient")

from os_helper.api import app  # noqa: E402

TestClient = starlette_testclient.TestClient


@pytest.fixture()
def client() -> "starlette_testclient.TestClient":
    return TestClient(app)


def test_get_endpoints(client) -> None:
    res = client.get("/health")
    assert res.status_code == 200 and res.json()["status"] == "ok"

    res = client.get("/os")
    assert res.status_code == 200
    assert res.json()["os"] in {"macos", "linux", "windows", "unknown"}

    res = client.get("/hardware")
    assert res.status_code == 200
    data = res.json()
    assert data["ram_gb"] > 0 and data["cpu"]["logical_cores"] >= 1

    res = client.get("/misc/format-size", params={"size": 12345678})
    assert res.status_code == 200 and "MB" in res.json()["formatted"]

    res = client.get("/misc/now", params={"fmt": "filename"})
    assert res.status_code == 200 and res.json()["timestamp"]


def test_post_endpoints(client, tmp_path) -> None:
    res = client.post("/hash/string", json={"text": "hello", "size": 8})
    assert res.status_code == 200 and len(res.json()["hash"]) == 8

    res = client.post("/str/ascii", json={"text": "Café-Con-Leche!"})
    assert res.status_code == 200 and res.json()["result"] == "cafe-con-leche"

    env_file = tmp_path / ".env"
    env_file.write_text("MY_KEY=my_value\n")
    res = client.post(
        "/config",
        json={"keys": ["MY_KEY"], "config_type": "test", "env_files": [str(env_file)]},
    )
    assert res.status_code == 200 and res.json()["MY_KEY"] == "my_value"


def test_config_unresolvable_keys_returns_400_not_500(client) -> None:
    # get_config's documented failure mode (no source satisfies the request)
    # used to fall through to FastAPI's generic 500 handler, indistinguishable
    # from an actual server bug. It is a client-input problem: 400.
    res = client.post(
        "/config",
        json={"keys": ["nonexistent_key_xyz"], "config_type": "test", "env_files": []},
    )
    assert res.status_code == 400
    assert "Missing required keys" in res.json()["detail"]
