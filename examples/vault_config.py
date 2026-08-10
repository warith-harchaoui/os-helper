"""
Runnable companion to CREDENTIALS_MANAGEMENT.md's "Combining get_config with
a Vault" section.

Implements the two decisions documented there as actual code, not just
prose:

1. Vault secrets are injected into ``os.environ`` (tier 3 of
   :func:`os_helper.get_config`'s fallback), never routed through
   ``get_config(path=...)`` (tier 1) — so they never touch disk.
2. Injection uses ``os.environ.setdefault`` rather than a hard assignment,
   so vault-provided values are a floor, never a ceiling: whatever is
   already in the environment when this runs (a developer's manually
   exported override, a value their own tooling already loaded from a
   local ``.env``, a value the deployment platform injected) wins. This is
   what gives dev/prod parity with zero environment-specific branching.

Run directly: ``python examples/vault_config.py``

Author
------
Warith HARCHAOUI, https://linkedin.com/in/warith-harchaoui
"""

from __future__ import annotations

import os
from collections.abc import Callable

import os_helper as osh


def load_from_vault(fetch_secrets: Callable[[], dict[str, object]]) -> None:
    """
    Inject a vault's secrets into ``os.environ`` — never to disk, never
    clobbering a value the caller already set.

    Parameters
    ----------
    fetch_secrets : Callable[[], dict]
        Zero-argument callable returning ``{key: value}`` from your vault
        client (``hvac`` for HashiCorp Vault, ``boto3`` for AWS Secrets
        Manager, ``google-cloud-secret-manager``, ``azure-keyvault-secrets``,
        ...). Kept generic here so this example carries no vault SDK
        dependency — swap in a real client's fetch call at the call site.
    """
    for key, value in fetch_secrets().items():
        # setdefault, not `=`: an already-set value (however it got there)
        # is left untouched. UPPER_CASE because get_config tries that
        # spelling first.
        os.environ.setdefault(key.upper(), str(value))


def _demo_vault() -> dict[str, str]:
    """Stand-in for a real vault client, so this file runs with zero setup."""
    return {"db_url": "postgres://vault-provided-host/db", "api_key": "vault-provided-key"}


if __name__ == "__main__":
    load_from_vault(_demo_vault)
    # path=None, env_files=[]: skip the file and .env tiers entirely, read
    # straight from the environment just populated above.
    config = osh.get_config(keys=["db_url", "api_key"], config_type="demo", path=None, env_files=[])
    print(config)
