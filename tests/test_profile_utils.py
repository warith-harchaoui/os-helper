"""
Tests for os_helper.profile_utils.

``wall_timer``/``cpu_timer``/``tic``/``toc`` have no PyTorch dependency and
always run. The ``gpu_timer``/``_resolve_gpu_backend`` tests need torch —
which os-helper itself does NOT depend on (lazy import) — so those are
individually skipped, not gated at module level (a module-level
``importorskip`` would have silently skipped the torch-independent tests
above too in any torch-less environment, including this project's own CI).
This machine has PyTorch with MPS but no CUDA, so the MPS path is driven for
real; the CUDA path (unavailable hardware) is driven by substituting a fake
``torch.cuda.Event`` at the same boundary PyTorch itself would occupy — the
timer's own logic (synchronize/record/elapsed_time plumbing) still runs for
real.

Usage Example
-------------
>>> #   pytest tests/test_profile_utils.py --cov=os_helper.profile_utils

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import sys
import time

import pytest

from os_helper import profile_utils

try:
    import torch
except ImportError:
    torch = None

requires_torch = pytest.mark.skipif(torch is None, reason="torch not installed")


class _FakeCudaEvent:
    """Stands in for ``torch.cuda.Event`` where no CUDA device is present."""

    def __init__(self, enable_timing: bool = True) -> None:
        self.enable_timing = enable_timing

    def record(self) -> None:
        pass

    def elapsed_time(self, other: "_FakeCudaEvent") -> float:
        return 12.5  # milliseconds


# ---------------------------------------------------------------------------
# wall_timer / cpu_timer / tic / toc — no torch involved
# ---------------------------------------------------------------------------


def test_wall_and_cpu_timers_measure_real_vs_cpu_time() -> None:
    with profile_utils.wall_timer() as t:
        time.sleep(0.05)
    assert t["seconds"] >= 0.04  # tolerate timer jitter
    assert abs(t["milliseconds"] - t["seconds"] * 1000) < 1e-6

    # cpu_timer must NOT count time spent sleeping (no CPU work).
    with profile_utils.cpu_timer() as t:
        time.sleep(0.1)
    assert t["seconds"] < 0.05

    # ...but it does count real CPU-bound work.
    with profile_utils.cpu_timer() as t:
        s = sum(i * i for i in range(500_000))
    assert s > 0
    assert t["seconds"] > 0


def test_tic_toc_basic_nested_and_missing_tic() -> None:
    profile_utils.tic()
    time.sleep(0.02)
    assert profile_utils.toc() >= 0.015

    # Explicit handle survives a subsequent tic() (nested timings).
    outer = profile_utils.tic()
    time.sleep(0.02)
    inner = profile_utils.tic()
    time.sleep(0.02)
    inner_elapsed = profile_utils.toc(inner)
    outer_elapsed = profile_utils.toc(outer)
    assert outer_elapsed > inner_elapsed
    # Implicit toc() reads the most recent tic() (inner).
    assert abs(profile_utils.toc() - inner_elapsed) < 0.02

    # No prior tic() at all -> RuntimeError.
    profile_utils._LAST_TIC = None
    with pytest.raises(RuntimeError, match="toc"):
        profile_utils.toc()


def test_toc_with_logging_enabled() -> None:
    profile_utils.tic()
    assert profile_utils.toc(log=True) >= 0


# ---------------------------------------------------------------------------
# gpu_timer / _resolve_gpu_backend — needs real or faked torch
# ---------------------------------------------------------------------------


def test_resolve_gpu_backend_without_torch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "torch", None)  # forces `import torch` -> ImportError
    with pytest.raises(RuntimeError, match="requires PyTorch"):
        profile_utils._resolve_gpu_backend("auto")


@requires_torch
def test_gpu_timer_rejects_unknown_backend() -> None:
    with pytest.raises(ValueError, match="Unknown gpu_timer backend"):
        with profile_utils.gpu_timer(backend="bogus"):
            pass


@requires_torch
def test_resolve_gpu_backend_explicit_cuda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    with pytest.raises(RuntimeError, match="CUDA is unavailable"):
        profile_utils._resolve_gpu_backend("cuda")
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    assert profile_utils._resolve_gpu_backend("cuda") == "cuda"


@requires_torch
def test_resolve_gpu_backend_explicit_mps(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: False)
    with pytest.raises(RuntimeError, match="MPS is unavailable"):
        profile_utils._resolve_gpu_backend("mps")
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: True)
    assert profile_utils._resolve_gpu_backend("mps") == "mps"


@requires_torch
def test_resolve_gpu_backend_auto_prefers_cuda_then_mps_then_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    assert profile_utils._resolve_gpu_backend("auto") == "cuda"

    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: True)
    assert profile_utils._resolve_gpu_backend("auto") == "mps"

    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: False)
    with pytest.raises(RuntimeError, match="neither CUDA nor MPS"):
        profile_utils._resolve_gpu_backend("auto")


@requires_torch
def test_gpu_timer_mps_measures_real_elapsed_time() -> None:
    if not (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
        pytest.skip("MPS not available on this machine")
    with profile_utils.gpu_timer(backend="mps") as t:
        x = torch.randn(64, 64, device="mps")
        _ = x @ x
    assert t["seconds"] >= 0
    assert t["milliseconds"] == pytest.approx(t["seconds"] * 1000.0)


@requires_torch
def test_gpu_timer_cuda_path_with_fake_events(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "synchronize", lambda: None)
    monkeypatch.setattr(torch.cuda, "Event", _FakeCudaEvent)
    with profile_utils.gpu_timer(backend="cuda") as t:
        pass
    assert t["milliseconds"] == pytest.approx(12.5)
    assert t["seconds"] == pytest.approx(0.0125)
