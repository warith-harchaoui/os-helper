"""
Hardware Utilities

Cross-platform hardware inspection: CPU (core counts + model name), RAM,
GPU (vendor, model name, VRAM), and Apple Silicon chip identification.

This module stays a plain hardware-facts probe. It answers "what does this
machine have" (cores, chip/GPU model strings, memory sizes) and deliberately
does NOT answer AI-inference questions like "how many tokens/s will this
push" or "should this repo use Ollama or vLLM" — those derivations belong to
the consumer (e.g. ``best-engine-ai-helper``), which combines these raw facts
with its own domain tables (memory-bandwidth-per-chip, decode-efficiency-per-
backend, ...). Keeping the split this way lets every helper in the suite
(9+ repos) call the same hardware probe without pulling in AI-specific logic.

Probe order for the accelerator vendor mirrors real-world prevalence: Apple
Silicon first (macOS can otherwise surface stray nvidia-smi output from a VM
or eGPU passthrough), then NVIDIA, then AMD, then an Intel-iGPU check on
Linux, falling back to plain CPU.

Usage example
-------------
>>> import os_helper as osh
>>> info = osh.hardware_info()
>>> info["cpu"]["logical_cores"] > 0
True
>>> info["ram_gb"] > 0
True

Author
------
Warith HARCHAOUI, https://linkedin.com/in/warith-harchaoui
"""

from __future__ import annotations

import platform
import re
import subprocess
import sys
from typing import Any

from .logging_utils import debug, info

# ---------------------------------------------------------------------------
# Internal probe helper
# ---------------------------------------------------------------------------


def _probe(cmd: list[str], **kwargs: Any) -> str:
    """
    Run a subprocess and return its stdout, swallowing any failure.

    Hardware probes (``nvidia-smi``, ``rocm-smi``, ``system_profiler``, ...)
    are optional tools that may simply not exist on a given machine. Every
    caller in this module treats the result as a plain truthiness check, so
    a missing binary or a non-zero exit must never raise — it must just look
    like "nothing detected".

    Parameters
    ----------
    cmd : list[str]
        Command and arguments, as passed to ``subprocess.run``.
    **kwargs
        Forwarded to ``subprocess.run`` (e.g. ``timeout``).

    Returns
    -------
    str
        Decoded stdout, or ``''`` on any error.
    """
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, **kwargs
        )
        return result.stdout
    except (FileNotFoundError, subprocess.CalledProcessError, OSError) as exc:
        # FileNotFoundError: binary not on PATH.
        # CalledProcessError: binary exists but returned non-zero.
        # OSError: platform refused to spawn the process at all.
        debug(f"Hardware probe unavailable/failed: {cmd[0]} ({exc})")
        return ""


def _parse_memory_gb(value_str: str) -> float | None:
    """
    Parse a memory string like ``'96 GB'`` or ``'32768 MiB'`` into GB.

    Parameters
    ----------
    value_str : str
        Raw string from ``system_profiler`` or a similar tool.

    Returns
    -------
    float or None
        Memory in GB, or None if the string could not be parsed.
    """
    s = value_str.strip()
    try:
        if "GB" in s.upper():
            return float(s.upper().replace("GB", "").strip())
        if "GIB" in s.upper():
            return float(s.upper().replace("GIB", "").strip())
        if "MB" in s.upper():
            return float(s.upper().replace("MB", "").strip()) / 1024.0
        if "MIB" in s.upper():
            return float(s.upper().replace("MIB", "").strip()) / 1024.0
        # A bare integer is assumed to be bytes (e.g. some wmic output).
        return float(s) / (1024**3)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Platform
# ---------------------------------------------------------------------------


def platform_name() -> str:
    """
    Return the current OS as a short lowercase string.

    Returns
    -------
    str
        One of: ``'darwin'``, ``'linux'``, ``'windows'``.

    Examples
    --------
    >>> platform_name() in ('darwin', 'linux', 'windows')
    True
    """
    if sys.platform.startswith("darwin"):
        return "darwin"
    if sys.platform.startswith("win"):
        return "windows"
    # Every other POSIX platform (BSD variants, etc.) is treated as Linux for
    # the purposes of this suite, which only ships Linux-specific probes.
    return "linux"


# ---------------------------------------------------------------------------
# CPU
# ---------------------------------------------------------------------------


def cpu_count_logical() -> int:
    """
    Return the number of logical CPUs (including hyperthreads/SMT).

    Returns
    -------
    int
        ``os.cpu_count()``, or 1 if the platform refuses to report it.

    Examples
    --------
    >>> cpu_count_logical() >= 1
    True
    """
    import os

    # os.cpu_count() can return None on exotic sandboxes; never surface that.
    return os.cpu_count() or 1


def cpu_count_physical() -> int | None:
    """
    Return the number of physical CPU cores (excluding hyperthreads/SMT).

    Delegates to ``psutil``, which already normalizes this across platforms
    (it reads ``/proc/cpuinfo`` core ids on Linux, ``sysctl`` on macOS, and
    the WMI processor table on Windows).

    Returns
    -------
    int or None
        Physical core count, or None when psutil cannot determine it (rare,
        e.g. some container sandboxes).
    """
    import psutil  # mandatory runtime dependency; always importable

    return psutil.cpu_count(logical=False)


def cpu_model() -> str | None:
    """
    Return a human-readable CPU model string for the current machine.

    Parameters
    ----------
    None

    Returns
    -------
    str or None
        e.g. ``'Apple M2 Max'``, ``'AMD Ryzen 9 7950X'``,
        ``'Intel(R) Xeon(R) Platinum 8358 CPU @ 2.60GHz'``. None if no probe
        on this platform yielded a usable string.

    Examples
    --------
    >>> cpu_model() is None or isinstance(cpu_model(), str)
    True
    """
    plat = platform_name()

    if plat == "darwin":
        # sysctl's machdep.cpu.brand_string is the canonical CPU name on both
        # Intel and Apple Silicon Macs.
        out = _probe(["sysctl", "-n", "machdep.cpu.brand_string"]).strip()
        return out or None

    if plat == "linux":
        # /proc/cpuinfo repeats "model name" once per logical core; the
        # first occurrence is enough to name the chip.
        try:
            with open("/proc/cpuinfo", encoding="utf-8") as fh:
                for line in fh:
                    if line.lower().startswith("model name"):
                        return line.split(":", 1)[1].strip() or None
        except OSError:
            debug("Could not read /proc/cpuinfo for CPU model detection.")
        return None

    # Windows: platform.processor() reads the registry-backed
    # PROCESSOR_IDENTIFIER, which is a reasonable (if verbose) model string
    # without needing to shell out to wmic (deprecated on modern Windows).
    out = platform.processor().strip()
    return out or None


# ---------------------------------------------------------------------------
# RAM
# ---------------------------------------------------------------------------


def ram_gb() -> float:
    """
    Return total system RAM in GB.

    Returns
    -------
    float
        Total RAM in GB. Always a positive float — ``psutil`` is a mandatory
        runtime dependency, so this never raises ``ImportError``.

    Examples
    --------
    >>> ram_gb() > 0
    True
    """
    import psutil  # mandatory runtime dependency; always importable

    return float(psutil.virtual_memory().total) / (1024**3)


# ---------------------------------------------------------------------------
# Accelerator vendor
# ---------------------------------------------------------------------------


def gpu_vendor() -> str:
    """
    Identify the primary compute accelerator vendor on this machine.

    Checks, in order: Apple Silicon, NVIDIA (``nvidia-smi``), AMD
    (``rocm-smi``), Intel integrated graphics (Linux ``lspci`` only), then
    falls back to ``'cpu'``.

    Returns
    -------
    str
        One of: ``'apple'``, ``'nvidia'``, ``'amd'``, ``'intel'``, ``'cpu'``.

    Examples
    --------
    >>> gpu_vendor() in ('apple', 'nvidia', 'amd', 'intel', 'cpu')
    True
    """
    plat = platform_name()

    if plat == "darwin":
        # system_profiler reliably reports the Apple Silicon chip name; older
        # Intel Macs report neither "Apple M" nor "Apple A" and fall through.
        out = _probe(["system_profiler", "SPHardwareDataType"])
        if "Apple M" in out or "Apple A" in out:
            info("Detected accelerator vendor: apple")
            return "apple"

    # NVIDIA works the same way on Linux and Windows.
    if _probe(["nvidia-smi", "-L"]):
        info("Detected accelerator vendor: nvidia")
        return "nvidia"

    # AMD's ROCm stack (Linux only, in practice).
    if _probe(["rocm-smi", "--showid"]):
        info("Detected accelerator vendor: amd")
        return "amd"

    # Intel Arc / integrated graphics — Linux-only probe via lspci.
    if plat == "linux":
        lspci = _probe(["lspci"])
        if "Intel" in lspci and "VGA" in lspci:
            info("Detected accelerator vendor: intel")
            return "intel"

    info("No accelerator detected; falling back to cpu")
    return "cpu"


# ---------------------------------------------------------------------------
# Apple Silicon
# ---------------------------------------------------------------------------


def apple_chip_name() -> str | None:
    """
    Return the Apple Silicon chip name (e.g. ``'Apple M2 Max'``).

    Returns
    -------
    str or None
        The chip name, or None on non-macOS platforms or when the
        ``system_profiler`` "Chip:" line is absent (older Intel Macs).
    """
    if platform_name() != "darwin":
        return None
    out = _probe(["system_profiler", "SPHardwareDataType"])
    for line in out.splitlines():
        if "Chip:" in line:
            return line.partition("Chip:")[2].strip() or None
    return None


def apple_unified_memory_gb() -> float | None:
    """
    Return the Apple Silicon unified-memory pool size in GB.

    Returns
    -------
    float or None
        Memory in GB, or None off macOS or when the value could not be
        parsed from ``system_profiler``.
    """
    if platform_name() != "darwin":
        return None
    out = _probe(["system_profiler", "SPHardwareDataType"])
    for line in out.splitlines():
        # The relevant line looks like: "  Memory: 96 GB".
        if "Memory:" in line and ("GB" in line or "MB" in line):
            _, _, value = line.partition("Memory:")
            parsed = _parse_memory_gb(value)
            if parsed is not None:
                return parsed
    return None


# ---------------------------------------------------------------------------
# Discrete GPUs (NVIDIA / AMD)
# ---------------------------------------------------------------------------


def nvidia_gpus() -> list[dict[str, Any]]:
    """
    List every NVIDIA GPU visible to ``nvidia-smi`` with its name and VRAM.

    Returns
    -------
    list of dict
        One entry per GPU: ``{"vendor": "nvidia", "name": str, "vram_gb":
        float}``. Empty list when ``nvidia-smi`` is unavailable or reports
        nothing.

    Examples
    --------
    >>> all('vram_gb' in g for g in nvidia_gpus())
    True
    """
    # CSV output, one line per GPU: "NVIDIA GeForce RTX 4090, 24564".
    out = _probe(
        ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"]
    )
    gpus: list[dict[str, Any]] = []
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 2:
            continue
        name, mib_str = parts
        try:
            vram_gb = float(mib_str) / 1024.0
        except ValueError:
            # A non-numeric memory field (rare driver hiccup) — skip this row
            # rather than fabricate a VRAM figure.
            continue
        gpus.append({"vendor": "nvidia", "name": name, "vram_gb": round(vram_gb, 1)})
    return gpus


def amd_gpus() -> list[dict[str, Any]]:
    """
    List every AMD GPU visible to ``rocm-smi`` with its name and VRAM.

    ROCm's text output format has drifted across releases, so this is a
    best-effort parse: it pairs up ``--showproductname`` names with
    ``--showmeminfo vram`` totals by GPU index. When the two calls disagree
    on GPU count (or either returns nothing usable), it degrades to VRAM-only
    entries rather than guessing a mismatched name.

    Returns
    -------
    list of dict
        One entry per GPU: ``{"vendor": "amd", "name": str | None,
        "vram_gb": float}``. Empty list when ``rocm-smi`` is unavailable.
    """
    # "GPU[0]  : Card series: 	Radeon RX 7900 XTX" (indentation/whitespace
    # varies by ROCm version, hence the loose "Card series" substring match).
    name_out = _probe(["rocm-smi", "--showproductname"])
    names: dict[int, str] = {}
    for line in name_out.splitlines():
        match = re.match(r"GPU\[(\d+)\]", line)
        if match and "Card series" in line:
            idx = int(match.group(1))
            _, _, val = line.rpartition(":")
            name = val.strip()
            if name:
                names[idx] = name

    # "GPU[0]  : VRAM Total Memory (B): 17163091968" — the byte count is the
    # LAST colon-separated field, so rpartition (not partition) is required.
    mem_out = _probe(["rocm-smi", "--showmeminfo", "vram"])
    gpus: list[dict[str, Any]] = []
    for line in mem_out.splitlines():
        match = re.match(r"GPU\[(\d+)\]", line)
        if not (match and "VRAM Total Memory" in line and "B)" in line):
            continue
        idx = int(match.group(1))
        _, _, val = line.rpartition(":")
        try:
            vram_gb = float(val.strip()) / (1024**3)
        except ValueError:
            continue
        gpus.append(
            {"vendor": "amd", "name": names.get(idx), "vram_gb": round(vram_gb, 1)}
        )
    return gpus


def gpus() -> list[dict[str, Any]]:
    """
    List every discrete GPU on this machine, dispatched by detected vendor.

    Apple Silicon is intentionally excluded: it has no discrete VRAM pool to
    enumerate (see :func:`apple_unified_memory_gb` instead).

    Returns
    -------
    list of dict
        See :func:`nvidia_gpus` / :func:`amd_gpus` for the entry shape.
        Empty list on Apple Silicon, Intel iGPU, or CPU-only machines.
    """
    vendor = gpu_vendor()
    if vendor == "nvidia":
        return nvidia_gpus()
    if vendor == "amd":
        return amd_gpus()
    return []


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------


def hardware_info() -> dict[str, Any]:
    """
    Return a single snapshot of every hardware fact this module can detect.

    Convenience aggregate over every other function in this module, useful
    for a one-call "what is this machine" report (CLI ``detect`` commands,
    diagnostics, bug reports).

    Returns
    -------
    dict
        ``{"platform": str, "cpu": {"physical_cores": int | None,
        "logical_cores": int, "model": str | None}, "ram_gb": float,
        "gpu_vendor": str, "gpus": list[dict], "apple_chip": str | None,
        "apple_unified_gb": float | None}``.

    Examples
    --------
    >>> info = hardware_info()
    >>> set(info) == {
    ...     "platform", "cpu", "ram_gb", "gpu_vendor", "gpus",
    ...     "apple_chip", "apple_unified_gb",
    ... }
    True
    """
    vendor = gpu_vendor()
    return {
        "platform": platform_name(),
        "cpu": {
            "physical_cores": cpu_count_physical(),
            "logical_cores": cpu_count_logical(),
            "model": cpu_model(),
        },
        "ram_gb": round(ram_gb(), 1),
        "gpu_vendor": vendor,
        "gpus": gpus(),
        # Apple's memory pool is unified (shared with the CPU), so it is
        # reported separately rather than folded into the "gpus" VRAM list.
        "apple_chip": apple_chip_name() if vendor == "apple" else None,
        "apple_unified_gb": apple_unified_memory_gb() if vendor == "apple" else None,
    }
