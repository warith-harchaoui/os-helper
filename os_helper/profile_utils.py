"""
Profiling Utilities

Context managers for timing code blocks at three different levels:

- ``wall_timer``  — real elapsed wall-clock time (``time.perf_counter``).
- ``cpu_timer``   — CPU time consumed by the current process across all
                    threads (``time.process_time``). Excludes I/O / sleep
                    and subprocesses.
- ``gpu_timer``   — GPU execution time via PyTorch CUDA events (or
                    ``torch.mps.synchronize`` + wall-clock on Apple
                    Silicon, since MPS does not expose timing events).

The three context managers yield a small dict
``{"seconds": float, "milliseconds": float}`` populated when the ``with``
block exits, so the result survives beyond the context.

Plus a pair of MATLAB-flavored convenience functions for the
"sprinkle-a-timer-mid-script" style:

- ``tic`` / ``toc``  — wall-clock stopwatch. ``tic()`` resets the implicit
                       global timer and returns a handle; ``toc()`` reads
                       elapsed seconds since the last ``tic()`` (or since
                       the passed-in handle, for nested timings).

Author:
 - Warith HARCHAOUI, https://linkedin.com/in/warith-harchaoui
"""

from __future__ import annotations

import contextlib
import time
from collections.abc import Generator
from typing import Literal


def _empty_result() -> dict[str, float]:
    """Return a zero-initialized timing result dict.

    Returns
    -------
    dict of str to float
        A fresh ``{"seconds": 0.0, "milliseconds": 0.0}`` mapping. Each timer
        yields its own instance so results never alias between ``with`` blocks.
    """
    # Pre-seed both fields to 0.0 so the dict is valid even if the timed block
    # raises before ``_set_result`` runs.
    return {"seconds": 0.0, "milliseconds": 0.0}


def _set_result(result: dict[str, float], seconds: float) -> None:
    """Populate a timing result dict in place from an elapsed-seconds value.

    Parameters
    ----------
    result : dict of str to float
        The dict yielded to the caller; mutated in place so the value survives
        after the context manager exits.
    seconds : float
        Elapsed time in seconds; the millisecond field is derived from it.
    """
    # Mutate in place (not reassign) because the caller already holds a
    # reference to this exact dict from the ``with ... as`` binding.
    result["seconds"] = seconds
    result["milliseconds"] = seconds * 1000.0


@contextlib.contextmanager
def wall_timer() -> Generator[dict[str, float], None, None]:
    """
    Measure real elapsed wall-clock time using :func:`time.perf_counter`.

    Use this when you want to know "how long did this take to run from
    the user's perspective" — it includes I/O, sleeps, GPU waits, and
    subprocess time.

    Yields
    ------
    dict
        ``{"seconds": float, "milliseconds": float}``, both fields
        populated when the ``with`` block exits.

    Examples
    --------
    >>> with wall_timer() as t:
    ...     time.sleep(0.05)
    >>> assert t["seconds"] >= 0.05
    """
    result = _empty_result()
    # ``perf_counter`` is monotonic and highest-resolution — never affected by
    # wall-clock adjustments (NTP, DST) during the measured block.
    start = time.perf_counter()
    try:
        yield result
    finally:
        # Fill the result on the way out so the elapsed time is recorded even
        # if the body raised.
        _set_result(result, time.perf_counter() - start)


@contextlib.contextmanager
def cpu_timer() -> Generator[dict[str, float], None, None]:
    """
    Measure CPU time consumed by the current process using
    :func:`time.process_time` (sums user + system CPU across all threads).

    Differs from :func:`wall_timer` in two important ways:

    - It excludes time spent blocked on I/O, sleeping, or waiting on the
      GPU — so it isolates "actual computation done by Python+native code".
    - It excludes **subprocesses** (ffmpeg, etc.). For those, use
      :func:`wall_timer` or ``os.times()`` directly.

    On a multi-threaded computation it can report more seconds than
    wall-clock — that's intentional: it counts the CPU work, not the
    elapsed time.

    Yields
    ------
    dict
        ``{"seconds": float, "milliseconds": float}``.

    Examples
    --------
    >>> with cpu_timer() as t:
    ...     total = sum(i * i for i in range(1_000_000))
    >>> assert t["seconds"] > 0
    """
    result = _empty_result()
    # ``process_time`` counts CPU (user+system) time of THIS process only —
    # sleeps and I/O waits do not advance it, unlike ``perf_counter``.
    start = time.process_time()
    try:
        yield result
    finally:
        _set_result(result, time.process_time() - start)


def _resolve_gpu_backend(backend: str) -> Literal["cuda", "mps"]:
    """Pick a concrete GPU backend or raise a clear RuntimeError.

    Parameters
    ----------
    backend : str
        Requested backend: ``"auto"``, ``"cuda"``, or ``"mps"``.

    Returns
    -------
    {"cuda", "mps"}
        The concrete backend to use.

    Raises
    ------
    RuntimeError
        If PyTorch is missing or the requested/derived backend is unavailable.
    ValueError
        If ``backend`` is not a recognized value.
    """
    # Import lazily: PyTorch is an optional, heavy dependency and most callers
    # of the wall/cpu timers never need it.
    try:
        import torch  # type: ignore
    except ImportError as exc:
        raise RuntimeError("gpu_timer requires PyTorch. Install with: pip install torch") from exc

    # Explicit CUDA request: honour it only if a CUDA device is actually present.
    if backend == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("gpu_timer(backend='cuda') called but CUDA is unavailable")
        return "cuda"
    # Explicit MPS (Apple Silicon) request, guarded the same way.
    if backend == "mps":
        if not (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
            raise RuntimeError("gpu_timer(backend='mps') called but MPS is unavailable")
        return "mps"
    # Auto: prefer CUDA (faster, has real timing events), fall back to MPS.
    if backend == "auto":
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        raise RuntimeError("gpu_timer(backend='auto') called but neither CUDA nor MPS is available")
    # Anything else is a programming error on the caller's side.
    raise ValueError(f"Unknown gpu_timer backend {backend!r}; expected 'auto', 'cuda', or 'mps'")


@contextlib.contextmanager
def gpu_timer(backend: str = "auto") -> Generator[dict[str, float], None, None]:
    """
    Measure GPU execution time, synchronizing before and after the block.

    Backends
    --------
    - ``"cuda"`` — uses ``torch.cuda.Event(enable_timing=True)`` pairs,
      which give microsecond-level GPU-side timing.
    - ``"mps"`` — Apple Silicon. PyTorch's MPS backend does not expose
      timing events, so this falls back to ``torch.mps.synchronize()`` +
      :func:`time.perf_counter` around the block. Accuracy ~1 ms.
    - ``"auto"`` — pick CUDA if available, else MPS, else raise.

    Both paths synchronize **before and after** the block so the measured
    duration corresponds to actual GPU work, not just kernel-queue
    submission. Without synchronization, GPU ops are asynchronous and the
    timer would understate the cost dramatically.

    Parameters
    ----------
    backend : str, optional
        ``"auto"`` (default), ``"cuda"``, or ``"mps"``.

    Yields
    ------
    dict
        ``{"seconds": float, "milliseconds": float}``.

    Raises
    ------
    RuntimeError
        If PyTorch is not installed, or if the requested backend is
        unavailable on this machine.
    ValueError
        If ``backend`` is not one of ``"auto"``, ``"cuda"``, ``"mps"``.

    Examples
    --------
    >>> import torch
    >>> if torch.cuda.is_available():
    ...     x = torch.randn(2048, 2048, device="cuda")
    ...     with gpu_timer() as t:
    ...         y = x @ x
    ...     print(t["milliseconds"])
    """
    chosen = _resolve_gpu_backend(backend)
    result = _empty_result()

    import torch  # already known to be importable thanks to _resolve_gpu_backend

    if chosen == "cuda":
        # Drain any queued work first so the start event marks a clean baseline.
        torch.cuda.synchronize()
        # CUDA events timestamp on the GPU itself — far more accurate than
        # wrapping wall-clock around asynchronous kernel launches.
        start_event = torch.cuda.Event(enable_timing=True)
        end_event = torch.cuda.Event(enable_timing=True)
        start_event.record()
        try:
            yield result
        finally:
            end_event.record()
            # Block until the GPU actually finishes before reading the delta.
            torch.cuda.synchronize()
            elapsed_ms = start_event.elapsed_time(end_event)
            _set_result(result, elapsed_ms / 1000.0)
        return

    # MPS path — no timing events, so synchronize and measure wall-clock
    # around the synchronized block. Accuracy ~1ms.
    torch.mps.synchronize()
    start = time.perf_counter()
    try:
        yield result
    finally:
        torch.mps.synchronize()
        _set_result(result, time.perf_counter() - start)


# ---------------------------------------------------------------------------
#  MATLAB-style tic / toc
# ---------------------------------------------------------------------------

# Single implicit "last tic" timestamp. Each tic() overwrites it, matching
# MATLAB's semantics. For nested timings, capture the handle returned by
# tic() and pass it to toc().
_LAST_TIC: float | None = None


def tic() -> float:
    """
    Start (or restart) the implicit global stopwatch.

    Returns the start timestamp so callers can pin a handle for nested or
    interleaved measurements:

    >>> t_outer = tic()
    >>> # ... work ...
    >>> t_inner = tic()      # implicit global now points at t_inner
    >>> # ... more work ...
    >>> toc(t_inner)         # explicit handle works regardless of which tic() was last
    >>> toc(t_outer)

    Returns
    -------
    float
        ``time.perf_counter()`` snapshot, usable as a handle for :func:`toc`.
    """
    global _LAST_TIC
    _LAST_TIC = time.perf_counter()
    return _LAST_TIC


def toc(handle: float | None = None, *, log: bool = False) -> float:
    """
    Return seconds elapsed since the matching :func:`tic` call.

    Parameters
    ----------
    handle : float, optional
        Handle returned by :func:`tic`. If None, the implicit "last tic"
        timestamp is used.
    log : bool, optional
        If True, log the elapsed time at INFO level via the root logger.

    Returns
    -------
    float
        Seconds elapsed (does **not** reset the timer — call ``tic()`` again
        to restart).

    Raises
    ------
    RuntimeError
        If called with no handle and no prior ``tic()``.

    Examples
    --------
    >>> tic()
    >>> # ... work ...
    >>> elapsed = toc()
    """
    now = time.perf_counter()
    # No explicit handle: fall back to the implicit global set by the last tic().
    if handle is None:
        if _LAST_TIC is None:
            raise RuntimeError("toc() called before tic()")
        handle = _LAST_TIC
    elapsed = now - handle
    if log:
        # Import lazily to avoid a hard module-load dependency on logging_utils
        # for the common (non-logging) toc() call.
        from .logging_utils import info

        info(f"toc: {elapsed:.3f}s")
    return elapsed
