"""Tests for the ``os-helper-gui`` launcher's argument parsing.

The launcher moved from argparse to click on 2026-10-27, finishing the
suite-wide conversion. Two properties had to survive that move, and neither
is obvious from reading the diff:

* **``-h`` still works.** argparse supplies the short form for free; click
  does not, so a plain conversion silently takes the flag away from anyone
  who had been using it.
* **``import os_helper.gui`` stays cheap.** The module's lean-import
  contract says so, which is why click is imported *inside* ``_cli_main``
  and the command is built there instead of with module-level decorators.

These tests need click but *not* FastAPI, so they live here rather than in
``test_gui.py`` — that module skips wholesale without the web stack, which
would have taken the launcher's own coverage with it.

Usage Example
-------------
>>> #   pytest tests/test_gui_launcher.py

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import builtins
import importlib
import sys

import pytest

pytest.importorskip("click")

from os_helper import gui  # noqa: E402


@pytest.fixture
def captured_run(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """Replace :func:`gui.run` so the flags can be read without serving."""
    seen: dict[str, object] = {}

    def fake_run(root: str | None = None, host: str = "", port: int = 0) -> None:
        seen.update(root=root, host=host, port=port)

    monkeypatch.setattr(gui, "run", fake_run)
    return seen


@pytest.mark.parametrize("flag", ["-h", "--help"])
def test_both_help_flags_answer(flag: str, capsys: pytest.CaptureFixture[str]) -> None:
    """``-h`` as well as ``--help``: the short form argparse gave for free."""
    assert gui._cli_main([flag]) == 0
    out = capsys.readouterr().out
    for option in ("--root", "--host", "--port"):
        assert option in out, f"{flag} should document {option}"


def test_the_flags_reach_run(captured_run: dict[str, object], tmp_path) -> None:
    """Parsing is not the point; handing the values to :func:`run` is."""
    assert gui._cli_main(["--root", str(tmp_path), "--host", "0.0.0.0", "--port", "9100"]) == 0
    assert captured_run == {"root": str(tmp_path), "host": "0.0.0.0", "port": 9100}


def test_defaults_bind_to_localhost_only(captured_run: dict[str, object]) -> None:
    """No argument means the dashboard is not exposed to the network."""
    assert gui._cli_main([]) == 0
    assert captured_run["host"] == "127.0.0.1"
    assert captured_run["port"] == 8017
    assert captured_run["root"] is None


def test_an_impossible_port_is_refused(captured_run: dict[str, object]) -> None:
    """A gain over the argparse version, which took 99999 and let bind fail.

    ``type=int`` validated the *shape* and nothing else, so the error arrived
    from the socket layer, far from the flag that caused it.
    """
    assert gui._cli_main(["--port", "99999"]) == 2
    assert captured_run == {}, "run() must not be reached on a usage error"


def test_an_unknown_option_is_refused(captured_run: dict[str, object]) -> None:
    """Exit 2 on a typo, not a silent launch with default settings."""
    assert gui._cli_main(["--prot", "9000"]) == 2
    assert captured_run == {}


def test_the_module_still_imports_without_click(monkeypatch: pytest.MonkeyPatch) -> None:
    """The lean-import contract: click is a launcher cost, not an import cost.

    Proved by making click unimportable and importing the module anyway. A
    ``@click.command`` decorator at module level would fail this.
    """
    real_import = builtins.__import__

    def blocked(name: str, *args: object, **kwargs: object) -> object:
        if name == "click" or name.startswith("click."):
            raise ModuleNotFoundError("No module named 'click'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    for name in [m for m in sys.modules if m == "click" or m.startswith("click.")]:
        monkeypatch.delitem(sys.modules, name)

    fresh = importlib.reload(gui)
    assert fresh.create_app is not None  # the module is usable, click or not

    # And the launcher names the extra instead of leaking ModuleNotFoundError:
    # the console script is installed even when the extra is not.
    with pytest.raises(ImportError, match=r"os-helper\[gui\]"):
        fresh._cli_main(["-h"])


def test_reload_left_the_module_intact() -> None:
    """Guards the test above: a failed reload must not poison the rest."""
    importlib.reload(gui)
    assert callable(gui._cli_main)
