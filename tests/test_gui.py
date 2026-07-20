"""
Tests for the optional Tree Radar treemap GUI (``os_helper.gui``).

These tests exercise the FastAPI surface: the ``GET /gui`` HTML page and
the ``GET /api/tree`` JSON data endpoint, against a temporary directory.

Design note
-----------
The GUI lives behind the optional ``os-helper[gui]`` extra so the core
``import os_helper`` stays FastAPI-free. Accordingly, this whole module
calls ``pytest.importorskip("fastapi")``: when the extra is not
installed, every test here is skipped cleanly, keeping CI green regardless of whether the web
stack is present. (Project CI installs ``.[dev]``, which now includes the
gui stack, so these tests actually run there.)

Usage Example
-------------
>>> #   pytest tests/test_gui.py

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import os

import pytest

# The GUI needs FastAPI (the [gui] extra). If it is absent, skip the whole
# module rather than fail — this is what keeps CI green without the extra.
pytest.importorskip("fastapi")
# TestClient needs httpx as its transport; skip too if that is missing.
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from os_helper.gui import (  # noqa: E402
    _type_family,
    build_tree_payload,
    create_app,
)


@pytest.fixture()
def sample_tree(tmp_path):
    """Create a small on-disk tree with a known duplicate pair.

    Layout
    ------
    - ``a.txt`` and ``sub/b.txt`` share identical content (a duplicate pair).
    - ``sub/c.py`` is a unique code file.

    Parameters
    ----------
    tmp_path : pathlib.Path
        pytest's per-test temporary directory fixture.

    Returns
    -------
    str
        Absolute path of the created root directory.
    """
    # Two identical files so the dedupe pass has a real cluster to find.
    (tmp_path / "a.txt").write_text("identical payload")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.txt").write_text("identical payload")  # duplicate of a.txt
    # A distinct code file so the "type family" classification is exercised.
    (sub / "c.py").write_text("print('hello')\n")
    return str(tmp_path)


def test_type_family_classification():
    """``_type_family`` buckets extensions into coarse families."""
    # Case-insensitive extension match and the archive/final-ext behavior.
    assert _type_family("main.PY") == "code"
    assert _type_family("data.CSV") == "data"
    assert _type_family("clip.mp4") == "media"
    assert _type_family("bundle.tar.gz") == "archive"
    assert _type_family("noext") == "other"


def test_build_tree_payload_sizes_and_dedupe(sample_tree):
    """The tree payload rolls sizes up and finds the duplicate cluster."""
    payload = build_tree_payload(sample_tree, dedupe=True)

    # Root is absolute and points at the scanned directory.
    assert payload["root"] == os.path.abspath(sample_tree)
    tree = payload["tree"]
    assert tree["is_dir"] is True
    # The root's rolled-up size must be positive (it summed its children).
    assert tree["size"] > 0
    # Human-readable size string is precomputed server-side.
    assert isinstance(tree["size_h"], str) and tree["size_h"]

    # Exactly one duplicate cluster (a.txt + sub/b.txt) should be reported.
    dedupe = payload["dedupe"]
    assert len(dedupe) == 1
    (paths,) = dedupe.values()
    assert len(paths) == 2
    assert {os.path.basename(p) for p in paths} == {"a.txt", "b.txt"}


def test_build_tree_payload_rejects_non_directory(tmp_path):
    """Scanning a non-directory raises ``NotADirectoryError``."""
    missing = str(tmp_path / "does-not-exist")
    with pytest.raises(NotADirectoryError):
        build_tree_payload(missing)


def test_gui_route_returns_html(sample_tree):
    """``GET /gui`` returns a 200 HTML page containing the app markup."""
    client = TestClient(create_app(default_root=sample_tree))
    resp = client.get("/gui")

    assert resp.status_code == 200
    # FastAPI's HTMLResponse sets an HTML content type.
    assert resp.headers["content-type"].startswith("text/html")
    body = resp.text
    # Sanity-check that it is really our page, not an error page.
    assert "<title>OS Helper — Tree Radar</title>" in body
    # The launch root must be injected so the page auto-scans it.
    assert os.path.abspath(sample_tree) in body


def test_api_tree_route_returns_valid_json(sample_tree):
    """``GET /api/tree`` returns a valid, well-shaped JSON tree."""
    client = TestClient(create_app(default_root=sample_tree))
    resp = client.get("/api/tree", params={"root": sample_tree})

    assert resp.status_code == 200
    data = resp.json()  # raises if the body is not valid JSON
    # Contract keys are present and the tree root is a directory node.
    assert set(data.keys()) == {"root", "tree", "dedupe"}
    assert data["tree"]["is_dir"] is True
    assert data["tree"]["size"] > 0


def test_api_tree_route_bad_root_is_400(sample_tree):
    """A non-directory root yields a clean HTTP 400, not a 500."""
    client = TestClient(create_app(default_root=sample_tree))
    resp = client.get("/api/tree", params={"root": os.path.join(sample_tree, "nope")})
    assert resp.status_code == 400
