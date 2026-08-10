"""
Proves the two "Combining get_config with a Vault" decisions from
CREDENTIALS_MANAGEMENT.md actually hold, by exercising the runnable example
at ``examples/vault_config.py`` end to end against the real ``get_config``.

Usage Example
-------------
>>> #   pytest tests/test_vault_config_example.py

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

import os_helper as osh

_EXAMPLE_PATH = Path(__file__).resolve().parent.parent / "examples" / "vault_config.py"
_spec = importlib.util.spec_from_file_location("vault_config_example", _EXAMPLE_PATH)
assert _spec is not None and _spec.loader is not None
vault_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vault_config)


def test_vault_injection_never_touches_disk(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.delenv("DB_URL", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)  # any accidental file write would land here

    vault_config.load_from_vault(
        lambda: {"db_url": "postgres://vault/db", "api_key": "vault-key"}
    )

    assert list(tmp_path.iterdir()) == []  # decision 1: nothing written to disk
    config = osh.get_config(
        keys=["db_url", "api_key"], config_type="test", path=None, env_files=[]
    )
    assert config == {"db_url": "postgres://vault/db", "api_key": "vault-key"}


def test_vault_values_are_a_floor_not_a_ceiling(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DB_URL", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)
    # Simulate a developer's local override already present in the
    # environment (their own .env loaded earlier, a manual export, CI) —
    # this must survive vault injection untouched.
    monkeypatch.setenv("DB_URL", "postgres://dev-local/db")

    vault_config.load_from_vault(
        lambda: {"db_url": "postgres://vault/db", "api_key": "vault-key"}
    )

    config = osh.get_config(
        keys=["db_url", "api_key"], config_type="test", path=None, env_files=[]
    )
    assert config["db_url"] == "postgres://dev-local/db"  # decision 2: dev override wins
    assert config["api_key"] == "vault-key"  # vault fills the gap it didn't set
