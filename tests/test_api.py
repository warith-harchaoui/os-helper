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


def test_health(client) -> None:
    res = client.get("/health")
    assert res.status_code == 200 and res.json()["status"] == "ok"


def test_os_endpoint(client) -> None:
    res = client.get("/os")
    assert res.status_code == 200
    assert res.json()["os"] in {"macos", "linux", "windows", "unknown"}


def test_hardware_endpoint(client) -> None:
    res = client.get("/hardware")
    assert res.status_code == 200
    data = res.json()
    assert data["ram_gb"] > 0
    assert data["cpu"]["logical_cores"] >= 1


def test_hash_string_endpoint(client) -> None:
    res = client.post("/hash/string", json={"text": "hello", "size": 8})
    assert res.status_code == 200
    assert len(res.json()["hash"]) == 8


def test_ascii_endpoint(client) -> None:
    res = client.post("/str/ascii", json={"text": "Café-Con-Leche!"})
    assert res.status_code == 200
    assert res.json()["result"] == "cafe-con-leche"


def test_format_size_endpoint(client) -> None:
    res = client.get("/misc/format-size", params={"size": 12345678})
    assert res.status_code == 200
    assert "MB" in res.json()["formatted"]


def test_now_endpoint(client) -> None:
    res = client.get("/misc/now", params={"fmt": "filename"})
    assert res.status_code == 200
    assert res.json()["timestamp"]


def test_config_endpoint(client, tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("MY_KEY=my_value\n")
    res = client.post(
        "/config",
        json={"keys": ["MY_KEY"], "config_type": "test", "env_files": [str(env_file)]},
    )
    assert res.status_code == 200
    assert res.json()["MY_KEY"] == "my_value"
