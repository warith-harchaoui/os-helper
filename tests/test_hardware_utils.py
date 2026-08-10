"""
Tests for os_helper.hardware_utils.

The hardware probes shell out to system_profiler / nvidia-smi / rocm-smi /
lspci / sysctl, or read platform-specific files (/proc/cpuinfo). Tests drive
the real functions end to end and only replace the subprocess/filesystem
boundary (``_probe``, ``builtins.open``, ``platform.processor``) so every
platform/vendor branch runs deterministically regardless of which tools the
CI box actually has. A few tests keep the real machine's public contract
(return shapes, positivity) honest.

Usage Example
-------------
>>> #   pytest tests/test_hardware_utils.py --cov=os_helper.hardware_utils

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

import io

import pytest

from os_helper import hardware_utils

# A representative macOS ``system_profiler SPHardwareDataType`` excerpt.
_MAC_HW = (
    "Hardware:\n"
    "    Hardware Overview:\n"
    "      Model Name: MacBook Pro\n"
    "      Chip: Apple M2 Max\n"
    "      Memory: 96 GB\n"
)

# A representative rocm-smi product-name listing.
_AMD_NAMES = "GPU[0]\t\t: Card series: \tRadeon RX 7900 XTX\n"
# A representative rocm-smi VRAM listing: a valid row, a row that doesn't
# match the "VRAM Total Memory (B)" shape at all, and a row that matches but
# carries an unparseable byte count — all three must be tolerated silently.
_AMD_VRAM = (
    "GPU[0]        : VRAM Total Memory (B): 25757220864\n"
    "GPU[0]        : VRAM Total Used Memory (B): 512\n"
    "GPU[1]        : VRAM Total Memory (B): N/A\n"
)


def _fake_probe(mapping: dict[str, str]):
    """Return a ``_probe`` replacement yielding ``mapping[cmd[0]]`` (default '')."""

    def probe(cmd: list[str], **kw: object) -> str:
        return mapping.get(cmd[0], "")

    return probe


def test_probe_returns_empty_on_missing_binary() -> None:
    # A binary that isn't on PATH must yield '' so probes are simple truthiness
    # checks with no try/except at every call site.
    assert hardware_utils._probe(["definitely-not-a-real-binary-zzz"]) == ""


def test_parse_memory_gb_units_and_garbage() -> None:
    assert hardware_utils._parse_memory_gb("96 GB") == 96.0
    assert hardware_utils._parse_memory_gb("  8 GB ") == 8.0
    assert hardware_utils._parse_memory_gb("32768 MiB") == pytest.approx(32.0)
    assert hardware_utils._parse_memory_gb("16 GiB") == pytest.approx(16.0)
    assert hardware_utils._parse_memory_gb(str(16 * 1024**3)) == pytest.approx(16.0)
    assert hardware_utils._parse_memory_gb("not a number") is None


def test_platform_name_maps_sys_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    cases = [
        ("darwin", "darwin"),
        ("win32", "windows"),
        ("linux", "linux"),
        ("freebsd13", "linux"),  # every other POSIX platform folds into "linux"
    ]
    for sys_platform, expected in cases:
        monkeypatch.setattr(hardware_utils.sys, "platform", sys_platform)
        assert hardware_utils.platform_name() == expected, sys_platform


def test_gpu_vendor_detects_each_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    # Each vendor is selected by the first probe that returns non-empty output.
    cases = [
        ("darwin", {"system_profiler": _MAC_HW}, "apple"),
        ("linux", {"nvidia-smi": "GPU 0: NVIDIA RTX 4090 (UUID: ...)"}, "nvidia"),
        ("linux", {"rocm-smi": "GPU[0]: 1002"}, "amd"),
        ("linux", {"lspci": "01:00.0 VGA compatible controller: Intel Arc"}, "intel"),
        ("linux", {}, "cpu"),
    ]
    for plat, mapping, expected in cases:
        monkeypatch.setattr(hardware_utils, "platform_name", lambda p=plat: p)
        monkeypatch.setattr(hardware_utils, "_probe", _fake_probe(mapping))
        assert hardware_utils.gpu_vendor() == expected, f"{plat} / {mapping}"


def test_apple_chip_and_unified_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(hardware_utils, "platform_name", lambda: "darwin")
    monkeypatch.setattr(hardware_utils, "_probe", _fake_probe({"system_profiler": _MAC_HW}))
    assert hardware_utils.apple_chip_name() == "Apple M2 Max"
    assert hardware_utils.apple_unified_memory_gb() == 96.0
    # Off macOS, both probes short-circuit to None without shelling out.
    monkeypatch.setattr(hardware_utils, "platform_name", lambda: "linux")
    assert hardware_utils.apple_chip_name() is None
    assert hardware_utils.apple_unified_memory_gb() is None
    # On macOS with nothing usable in system_profiler's output, still None.
    monkeypatch.setattr(hardware_utils, "platform_name", lambda: "darwin")
    monkeypatch.setattr(hardware_utils, "_probe", _fake_probe({}))
    assert hardware_utils.apple_chip_name() is None
    assert hardware_utils.apple_unified_memory_gb() is None


def test_cpu_model_per_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    # macOS: sysctl's machdep.cpu.brand_string.
    monkeypatch.setattr(hardware_utils, "platform_name", lambda: "darwin")
    monkeypatch.setattr(hardware_utils, "_probe", _fake_probe({"sysctl": "Apple M3 Pro\n"}))
    assert hardware_utils.cpu_model() == "Apple M3 Pro"
    monkeypatch.setattr(hardware_utils, "_probe", _fake_probe({}))
    assert hardware_utils.cpu_model() is None

    # Linux: first "model name" line of /proc/cpuinfo.
    monkeypatch.setattr(hardware_utils, "platform_name", lambda: "linux")
    cpuinfo = "processor\t: 0\nmodel name\t: AMD Ryzen 9 7950X\n"
    monkeypatch.setattr("builtins.open", lambda *a, **k: io.StringIO(cpuinfo))
    assert hardware_utils.cpu_model() == "AMD Ryzen 9 7950X"
    # Sandboxed/unreadable /proc/cpuinfo -> None, not a crash.
    monkeypatch.setattr(
        "builtins.open", lambda *a, **k: (_ for _ in ()).throw(OSError("no such file"))
    )
    assert hardware_utils.cpu_model() is None

    # Windows: platform.processor() reads the registry-backed identifier.
    monkeypatch.setattr(hardware_utils, "platform_name", lambda: "windows")
    monkeypatch.setattr(hardware_utils.platform, "processor", lambda: "Intel64 Family 6 ")
    assert hardware_utils.cpu_model() == "Intel64 Family 6"
    monkeypatch.setattr(hardware_utils.platform, "processor", lambda: "")
    assert hardware_utils.cpu_model() is None


def test_nvidia_gpus_parses_csv_and_skips_bad_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    csv = (
        "NVIDIA GeForce RTX 4090, 24564\n"  # valid
        "NVIDIA GeForce RTX 3090, N/A\n"  # non-numeric memory -> skipped
        "a driver warning with no comma\n"  # wrong field count -> skipped
    )
    monkeypatch.setattr(hardware_utils, "_probe", _fake_probe({"nvidia-smi": csv}))
    assert hardware_utils.nvidia_gpus() == [
        {"vendor": "nvidia", "name": "NVIDIA GeForce RTX 4090", "vram_gb": 24.0}
    ]
    # No nvidia-smi on PATH -> empty list, not an error.
    monkeypatch.setattr(hardware_utils, "_probe", _fake_probe({}))
    assert hardware_utils.nvidia_gpus() == []


def test_amd_gpus_pairs_name_and_vram_by_index(monkeypatch: pytest.MonkeyPatch) -> None:
    def probe(cmd: list[str], **kw: object) -> str:
        if cmd[:2] == ["rocm-smi", "--showproductname"]:
            return _AMD_NAMES
        if cmd[:2] == ["rocm-smi", "--showmeminfo"]:
            return _AMD_VRAM
        return ""

    monkeypatch.setattr(hardware_utils, "_probe", probe)
    # GPU[0]: name + valid VRAM row. A same-index "Used Memory" row (doesn't
    # match "Total Memory (B)") and a GPU[1] row with a garbage byte count are
    # both silently skipped.
    assert hardware_utils.amd_gpus() == [
        {"vendor": "amd", "name": "Radeon RX 7900 XTX", "vram_gb": 24.0}
    ]
    # rocm-smi entirely unavailable -> empty list, not an error.
    monkeypatch.setattr(hardware_utils, "_probe", _fake_probe({}))
    assert hardware_utils.amd_gpus() == []


def test_gpus_dispatches_by_vendor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(hardware_utils, "gpu_vendor", lambda: "nvidia")
    monkeypatch.setattr(hardware_utils, "nvidia_gpus", lambda: [{"vendor": "nvidia"}])
    assert hardware_utils.gpus() == [{"vendor": "nvidia"}]
    monkeypatch.setattr(hardware_utils, "gpu_vendor", lambda: "amd")
    monkeypatch.setattr(hardware_utils, "amd_gpus", lambda: [{"vendor": "amd"}])
    assert hardware_utils.gpus() == [{"vendor": "amd"}]
    # Apple / Intel / CPU have no discrete GPU list to enumerate.
    for vendor in ("apple", "intel", "cpu"):
        monkeypatch.setattr(hardware_utils, "gpu_vendor", lambda v=vendor: v)
        assert hardware_utils.gpus() == []


def test_gpu_utilization_percent_dispatches_by_vendor(monkeypatch: pytest.MonkeyPatch) -> None:
    # Apple: delegates to the IOKit/ioreg probe (no sudo/powermetrics).
    ioreg_output = '"PerformanceStatistics" = {"Device Utilization %"=42,"foo"=1}\n'
    monkeypatch.setattr(hardware_utils, "_probe", _fake_probe({"ioreg": ioreg_output}))
    assert hardware_utils.gpu_utilization_percent("apple") == 42.0
    monkeypatch.setattr(hardware_utils, "_probe", _fake_probe({}))
    assert hardware_utils.gpu_utilization_percent("apple") is None

    # NVIDIA: single CSV percentage.
    monkeypatch.setattr(hardware_utils, "_probe", _fake_probe({"nvidia-smi": "37\n"}))
    assert hardware_utils.gpu_utilization_percent("nvidia") == 37.0
    monkeypatch.setattr(hardware_utils, "_probe", _fake_probe({}))
    assert hardware_utils.gpu_utilization_percent("nvidia") is None

    # AMD: a malformed "GPU use" line is skipped in favor of a later valid one;
    # no valid line at all falls through to None.
    monkeypatch.setattr(
        hardware_utils,
        "_probe",
        _fake_probe({"rocm-smi": "GPU[0]  : GPU use (%): N/A\nGPU[1]  : GPU use (%): 12\n"}),
    )
    assert hardware_utils.gpu_utilization_percent("amd") == 12.0
    monkeypatch.setattr(
        hardware_utils, "_probe", _fake_probe({"rocm-smi": "GPU[0]  : GPU use (%): N/A\n"})
    )
    assert hardware_utils.gpu_utilization_percent("amd") is None

    # Intel / CPU have no known live-utilization source.
    assert hardware_utils.gpu_utilization_percent("intel") is None
    assert hardware_utils.gpu_utilization_percent("cpu") is None


def test_hardware_info_and_live_metrics_are_sane_on_this_machine() -> None:
    info = hardware_utils.hardware_info()
    assert set(info) == {
        "platform", "cpu", "ram_gb", "available_ram_gb", "disk",
        "gpu_vendor", "gpus", "gpu_utilization_percent",
        "apple_chip", "apple_unified_gb",
    }
    assert info["ram_gb"] > 0
    assert info["cpu"]["logical_cores"] >= 1
    assert 0.0 <= info["cpu"]["percent"] <= 100.0
    assert 0 <= info["available_ram_gb"] <= info["ram_gb"]
    assert set(info["disk"]) == {"free_gb", "used_gb", "total_gb", "percent_used"}
    assert isinstance(info["gpus"], list)
    # These call the real platform probes (sysctl / /proc/cpuinfo / psutil /
    # shutil.disk_usage); only the loose public contract is asserted, not an
    # exact value, since the CI box's actual load/free-space is unknown.
    model = hardware_utils.cpu_model()
    assert model is None or isinstance(model, str)
    assert hardware_utils.cpu_count_logical() >= 1
    assert hardware_utils.ram_gb() > 0
    assert 0.0 <= hardware_utils.cpu_percent() <= 100.0
    assert 0 <= hardware_utils.available_ram_gb() <= hardware_utils.ram_gb()

    usage = hardware_utils.disk_usage_gb()
    assert set(usage) == {"free_gb", "used_gb", "total_gb", "percent_used"}
    assert 0.0 <= usage["percent_used"] <= 100.0
    assert usage["free_gb"] + usage["used_gb"] == pytest.approx(usage["total_gb"], rel=0.01)
    # An explicit path is honored (same filesystem as the default here).
    assert set(hardware_utils.disk_usage_gb(".")) == set(usage)
