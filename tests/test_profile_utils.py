"""
Tests for os_helper.profile_utils — the ``gpu_timer`` backend-resolution
matrix and ``toc(log=True)``.

``wall_timer`` / ``cpu_timer`` / ``tic`` / ``toc`` (no logging) already have
solid coverage in ``test_os_helpers.py``; this file closes the remaining gaps
in ``_resolve_gpu_backend`` (all backend x availability combinations) and
``gpu_timer`` itself. This machine has PyTorch with MPS but no CUDA, so the
MPS path is driven for real; the CUDA path (unavailable hardware) is driven
by substituting a fake ``torch.cuda.Event`` at the same boundary PyTorch
itself would occupy — the timer's own logic (synchronize/record/elapsed_time
plumbing) still runs for real.

Usage Example
-------------
>>> #   pytest tests/test_profile_utils.py --cov=os_helper.profile_utils

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import sys

import pytest

torch = pytest.importorskip("torch")

from os_helper import profile_utils  # noqa: E402


class _FakeCudaEvent:
    """Stands in for ``torch.cuda.Event`` where no CUDA device is present."""

    def __init__(self, enable_timing: bool = True) -> None:
        self.enable_timing = enable_timing

    def record(self) -> None:
        pass

    def elapsed_time(self, other: "_FakeCudaEvent") -> float:
        return 12.5  # milliseconds


def test_resolve_gpu_backend_without_torch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "torch", None)  # forces `import torch` -> ImportError
    with pytest.raises(RuntimeError, match="requires PyTorch"):
        profile_utils._resolve_gpu_backend("auto")


def test_resolve_gpu_backend_explicit_cuda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    with pytest.raises(RuntimeError, match="CUDA is unavailable"):
        profile_utils._resolve_gpu_backend("cuda")
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    assert profile_utils._resolve_gpu_backend("cuda") == "cuda"


def test_resolve_gpu_backend_explicit_mps(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: False)
    with pytest.raises(RuntimeError, match="MPS is unavailable"):
        profile_utils._resolve_gpu_backend("mps")
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: True)
    assert profile_utils._resolve_gpu_backend("mps") == "mps"


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


def test_gpu_timer_mps_measures_real_elapsed_time() -> None:
    if not (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
        pytest.skip("MPS not available on this machine")
    with profile_utils.gpu_timer(backend="mps") as t:
        x = torch.randn(64, 64, device="mps")
        _ = x @ x
    assert t["seconds"] >= 0
    assert t["milliseconds"] == pytest.approx(t["seconds"] * 1000.0)


def test_gpu_timer_cuda_path_with_fake_events(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "synchronize", lambda: None)
    monkeypatch.setattr(torch.cuda, "Event", _FakeCudaEvent)
    with profile_utils.gpu_timer(backend="cuda") as t:
        pass
    assert t["milliseconds"] == pytest.approx(12.5)
    assert t["seconds"] == pytest.approx(0.0125)


def test_toc_with_logging_enabled() -> None:
    profile_utils.tic()
    elapsed = profile_utils.toc(log=True)
    assert elapsed >= 0
