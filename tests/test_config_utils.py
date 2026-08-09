"""
Tests for os_helper.config_utils.

``get_config`` has a strict fallback order (file/folder -> .env -> process
environment); each test drives one link of that chain for real, using
``tmp_path`` for on-disk fixtures rather than mocking the filesystem.

Usage Example
-------------
>>> #   pytest tests/test_config_utils.py --cov=os_helper.config_utils

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import json

import pytest

from os_helper import config_utils


def test_get_config_loads_from_json_file(tmp_path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"host": "localhost", "port": 5432}))
    config = config_utils.get_config(["host", "port"], "database", path=str(config_path))
    assert config == {"host": "localhost", "port": 5432}


def test_get_config_loads_from_yaml_file(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("host: localhost\nport: 5432\n")
    config = config_utils.get_config(["host", "port"], "database", path=str(config_path))
    assert config == {"host": "localhost", "port": 5432}


def test_get_config_file_missing_a_key_falls_through_to_env(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"host": "localhost"}))  # "port" missing
    monkeypatch.setenv("HOST", "envhost")
    monkeypatch.setenv("PORT", "1234")
    config = config_utils.get_config(
        ["host", "port"], "database", path=str(config_path), env_files=[]
    )
    assert config == {"host": "envhost", "port": "1234"}


def test_get_config_unsupported_extension_falls_through(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "config.txt"
    config_path.write_text("host=localhost")
    monkeypatch.setenv("HOST", "envhost")
    config = config_utils.get_config(["host"], "database", path=str(config_path), env_files=[])
    assert config == {"host": "envhost"}


def test_get_config_scans_directory_for_first_valid_file(tmp_path) -> None:
    # Alphabetically first: valid JSON but missing "port" -> skipped.
    (tmp_path / "a_incomplete.json").write_text(json.dumps({"host": "localhost"}))
    # Second candidate: complete YAML -> picked.
    (tmp_path / "b_complete.yaml").write_text("host: localhost\nport: 5432\n")
    config = config_utils.get_config(["host", "port"], "database", path=str(tmp_path))
    assert config == {"host": "localhost", "port": 5432}


def test_get_config_missing_path_falls_through_without_raising(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOST", "envhost")
    missing = tmp_path / "does-not-exist.json"
    config = config_utils.get_config(
        ["host"], "database", path=str(missing), env_files=[]
    )
    assert config == {"host": "envhost"}


def test_config_from_env_prefers_upper_case_then_exact_case(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("api_key", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("db_url", raising=False)
    monkeypatch.delenv("DB_URL", raising=False)
    # UPPER_CASE is tried first.
    monkeypatch.setenv("API_KEY", "upper-wins")
    # Exact-case-only variable is honored when no UPPER_CASE sibling exists.
    monkeypatch.setenv("db_url", "exact-case-fallback")
    config = config_utils._config_from_env(["api_key", "db_url"])
    assert config == {"api_key": "upper-wins", "db_url": "exact-case-fallback"}


def test_get_config_default_env_files_reads_dotenv_in_cwd(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("TOKEN=from-default-dotenv\n")
    monkeypatch.delenv("TOKEN", raising=False)
    config = config_utils.get_config(["token"], "auth")  # env_files omitted -> defaults to [".env"]
    assert config == {"token": "from-default-dotenv"}


def test_get_config_missing_raises() -> None:
    with pytest.raises(RuntimeError, match="Missing required keys"):
        config_utils.get_config(
            keys=["never_set_anywhere_xyz_123"], config_type="bogus", path=None, env_files=[]
        )
