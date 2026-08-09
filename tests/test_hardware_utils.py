"""
Tests for os_helper.hardware_utils.

The hardware probes shell out to system_profiler / nvidia-smi / rocm-smi /
lspci / sysctl. Rather than depend on which tools a CI box happens to have,
most tests patch ``hardware_utils._probe`` to feed canned tool output, so
every vendor branch runs deterministically. A few tests keep the real
machine's public contract (return shapes, positivity) honest.

Usage Example
-------------
>>> #   pytest tests/test_hardware_utils.py

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

from __future__ import annotations

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
# A representative rocm-smi VRAM listing (bytes as the last colon field).
_AMD_VRAM = "GPU[0]        : VRAM Total Memory (B): 25757220864\n"


def _fake_probe(mapping: dict[str, str]):
    """Return a ``_probe`` replacement yielding ``mapping[cmd[0]]`` (default '')."""

    def probe(cmd: list[str], **kw: object) -> str:
        return mapping.get(cmd[0], "")

    return probe


def test_platform_name_matches_known_values() -> None:
    result = hardware_utils.platform_name()
    assert result in ("darwin", "linux", "windows")


def test_parse_memory_gb_units_and_garbage() -> None:
    assert hardware_utils._parse_memory_gb("96 GB") == 96.0
    assert hardware_utils._parse_memory_gb("  8 GB ") == 8.0
    assert hardware_utils._parse_memory_gb("32768 MiB") == pytest.approx(32.0)
    assert hardware_utils._parse_memory_gb("16 GiB") == pytest.approx(16.0)
    assert hardware_utils._parse_memory_gb(str(16 * 1024**3)) == pytest.approx(16.0)
    assert hardware_utils._parse_memory_gb("not a number") is None


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


def test_nvidia_gpus_parses_csv_and_skips_bad_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    # Two GPUs, one with a non-numeric memory field that must be skipped.
    csv = "NVIDIA GeForce RTX 4090, 24564\nNVIDIA GeForce RTX 3090, N/A\n"
    monkeypatch.setattr(hardware_utils, "_probe", _fake_probe({"nvidia-smi": csv}))
    gpus = hardware_utils.nvidia_gpus()
    assert gpus == [
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
    gpus = hardware_utils.amd_gpus()
    assert gpus == [
        {"vendor": "amd", "name": "Radeon RX 7900 XTX", "vram_gb": 24.0}
    ]
    # A VRAM line with a non-numeric byte field is skipped -> empty list.
    monkeypatch.setattr(
        hardware_utils,
        "_probe",
        _fake_probe({"rocm-smi": "GPU[0] : VRAM Total Memory (B): N/A"}),
    )
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


def test_probe_returns_empty_on_missing_binary() -> None:
    # A binary that isn't on PATH must yield '' so probes are simple truthiness
    # checks with no try/except at every call site.
    assert hardware_utils._probe(["definitely-not-a-real-binary-zzz"]) == ""


def test_hardware_info_public_contract_on_this_machine() -> None:
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


def test_cpu_model_and_ram_gb_are_sane_on_this_machine() -> None:
    # These call the real platform probes (sysctl / /proc/cpuinfo / psutil);
    # only assert the loose public contract, not an exact value.
    model = hardware_utils.cpu_model()
    assert model is None or isinstance(model, str)
    assert hardware_utils.ram_gb() > 0
    assert hardware_utils.cpu_count_logical() >= 1


def test_cpu_percent_is_a_valid_percentage() -> None:
    assert 0.0 <= hardware_utils.cpu_percent() <= 100.0


def test_available_ram_gb_is_bounded_by_total_ram() -> None:
    assert 0 <= hardware_utils.available_ram_gb() <= hardware_utils.ram_gb()


def test_disk_usage_gb_public_contract() -> None:
    usage = hardware_utils.disk_usage_gb()
    assert set(usage) == {"free_gb", "used_gb", "total_gb", "percent_used"}
    assert 0.0 <= usage["percent_used"] <= 100.0
    assert usage["free_gb"] + usage["used_gb"] == pytest.approx(usage["total_gb"], rel=0.01)
    # An explicit path is honored (same filesystem as the default here).
    here = hardware_utils.disk_usage_gb(".")
    assert set(here) == {"free_gb", "used_gb", "total_gb", "percent_used"}


def test_apple_gpu_utilization_percent_parses_ioreg_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ioreg_output = (
        '"PerformanceStatistics" = {"Device Utilization %"=42,"In use system memory'
        '"=1234567}\n'
    )
    monkeypatch.setattr(
        hardware_utils, "_probe", _fake_probe({"ioreg": ioreg_output})
    )
    assert hardware_utils._apple_gpu_utilization_percent() == 42.0
    # No ioreg output (non-macOS, or unexpected driver shape) -> None.
    monkeypatch.setattr(hardware_utils, "_probe", _fake_probe({}))
    assert hardware_utils._apple_gpu_utilization_percent() is None


def test_gpu_utilization_percent_dispatches_by_vendor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        hardware_utils, "_apple_gpu_utilization_percent", lambda: 55.0
    )
    assert hardware_utils.gpu_utilization_percent("apple") == 55.0

    monkeypatch.setattr(
        hardware_utils, "_probe", _fake_probe({"nvidia-smi": "37\n"})
    )
    assert hardware_utils.gpu_utilization_percent("nvidia") == 37.0
    monkeypatch.setattr(hardware_utils, "_probe", _fake_probe({}))
    assert hardware_utils.gpu_utilization_percent("nvidia") is None

    monkeypatch.setattr(
        hardware_utils,
        "_probe",
        _fake_probe({"rocm-smi": "GPU[0]  : GPU use (%): 12\n"}),
    )
    assert hardware_utils.gpu_utilization_percent("amd") == 12.0
    monkeypatch.setattr(hardware_utils, "_probe", _fake_probe({}))
    assert hardware_utils.gpu_utilization_percent("amd") is None

    # Intel / CPU have no known live-utilization source.
    assert hardware_utils.gpu_utilization_percent("intel") is None
    assert hardware_utils.gpu_utilization_percent("cpu") is None
