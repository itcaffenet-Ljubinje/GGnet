"""Setting up a Boot Mode PC's OS writeback as that PC (app.windows_setup)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.windows_setup import OsSetup, WindowsSetup, registry_patch, static_interfaces

from .conftest import FakeRunner

SETUP = OsSetup("vip-05", {"GGNET_SERVER": "http://192.168.0.40:8088", "GGNET_MACHINE_ID": "7"})
DEVICE = "/dev/zvol/tank/ggnet/writebacks/vip-05-os"


def _lsblk(*parts: tuple[str, str | None, int]) -> str:
    children = [{"path": p, "type": "part", "fstype": fs, "size": size} for p, fs, size in parts]
    return json.dumps({"blockdevices": [{"path": "/dev/zd16", "type": "disk", "fstype": None,
                                         "size": 100 << 30, "children": children}]})


STANDARD_DISK = _lsblk(
    ("/dev/zd16p1", "vfat", 100 << 20),        # EFI
    ("/dev/zd16p2", None, 16 << 20),           # MSR
    ("/dev/zd16p3", "ntfs", 99 << 30),         # Windows
    ("/dev/zd16p4", "ntfs", 700 << 20),        # Recovery
)


@pytest.fixture
def runner() -> FakeRunner:
    r = FakeRunner()
    r.responses[("lsblk",)] = (True, STANDARD_DISK, "")
    r.responses[("hivexregedit", "--export")] = (
        True, 'Windows Registry Editor Version 5.00\r\n\r\n[\\Select]\r\n"Current"=dword:00000002\r\n', "")
    return r


@pytest.fixture
def windows(runner, tmp_path) -> WindowsSetup:
    return WindowsSetup(runner, run_dir=tmp_path / "run")


def _windows_on(windows: WindowsSetup, name: str = "vip-05") -> Path:
    """What ntfs-3g would show: a Windows tree in the mount directory (names as Windows has them)."""
    config = windows.run_dir / name / "Windows" / "System32" / "config"
    config.mkdir(parents=True)
    (config / "SYSTEM").write_bytes(b"regf")
    return config / "SYSTEM"


def _cmds(runner: FakeRunner) -> list[list[str]]:
    return [c for c in runner.calls if c[0] != "udevadm"]


# ── The registry patch ───────────────────────────────────────────────

def test_registry_patch():
    assert registry_patch(SETUP, 2) == (
        "Windows Registry Editor Version 5.00\n"
        "\n"
        "[\\ControlSet002\\Control\\ComputerName\\ComputerName]\n"
        '"ComputerName"="VIP-05"\n'
        "\n"
        "[\\ControlSet002\\Services\\Tcpip\\Parameters]\n"
        '"Hostname"="vip-05"\n'
        '"NV Hostname"="vip-05"\n'
        "\n"
        "[\\ControlSet002\\Control\\Session Manager\\Environment]\n"
        '"GGNET_SERVER"="http://192.168.0.40:8088"\n'
        '"GGNET_MACHINE_ID"="7"\n'
    )


def test_registry_patch_escapes_and_refuses_bad_input():
    patch = registry_patch(OsSetup("pc01", {"X": 'C:\\Games "x"'}), 1)
    assert '"X"="C:\\\\Games \\"x\\""' in patch
    for bad in (OsSetup("PC 01"), OsSetup("pc01", {"A-B": "1"}), OsSetup("pc01", {"A": "1\n[\\x]"})):
        with pytest.raises(ValueError):
            registry_patch(bad, 1)


# ── personalize() ────────────────────────────────────────────────────

def test_personalize_merges_into_the_windows_partition(windows, runner):
    hive = _windows_on(windows)
    merged = {}

    def merge(cmd):
        merged["reg"] = Path(cmd[3]).read_text(encoding="utf-8")
        return True, "", ""
    runner.responses[("hivexregedit", "--merge")] = merge
    mount = str(windows.run_dir / "vip-05")

    assert windows.personalize(DEVICE, SETUP) is None
    assert _cmds(runner) == [
        ["lsblk", "-J", "-b", "-p", "-o", "PATH,TYPE,FSTYPE,SIZE", DEVICE],
        ["ntfs-3g", "-o", "rw,noatime", "/dev/zd16p3", mount],   # the big NTFS partition
        ["hivexregedit", "--export", str(hive), "\\Select"],
        ["hivexregedit", "--export", str(hive),
         "\\ControlSet002\\Services\\Tcpip\\Parameters\\Interfaces"],
        ["hivexregedit", "--merge", str(hive), str(windows.run_dir / "vip-05.reg")],
        ["umount", mount],
    ]
    assert merged["reg"] == registry_patch(SETUP, 2)   # control set from \Select\Current
    assert not (windows.run_dir / "vip-05.reg").exists()


def test_personalize_finds_the_hive_whatever_its_case(windows, runner):
    config = windows.run_dir / "vip-05" / "WINDOWS" / "system32" / "Config"
    config.mkdir(parents=True)
    (config / "system").write_bytes(b"regf")
    assert windows.personalize(DEVICE, SETUP) is None
    assert ["hivexregedit", "--merge", str(config / "system"),
            str(windows.run_dir / "vip-05.reg")] in runner.calls


def test_control_set_defaults_to_1(windows, runner):
    runner.responses[("hivexregedit", "--export")] = (False, "", "no such key")
    _windows_on(windows)
    merged = {}

    def merge(cmd):
        merged["reg"] = Path(cmd[3]).read_text(encoding="utf-8")
        return True, "", ""
    runner.responses[("hivexregedit", "--merge")] = merge
    assert windows.personalize(DEVICE, SETUP) is None
    assert "[\\ControlSet001\\Control\\ComputerName\\ComputerName]" in merged["reg"]


def test_an_image_without_windows(windows, runner):
    runner.responses[("lsblk",)] = (True, _lsblk(), "")
    assert windows.personalize(DEVICE, SETUP) == f"no Windows partition found on {DEVICE}"
    assert not any(c[0] == "ntfs-3g" for c in runner.calls)


def test_tries_the_next_partition_and_reports_each(windows, runner):
    runner.responses[("ntfs-3g", "-o", "rw,noatime", "/dev/zd16p3")] = (
        False, "", "Windows is hibernated, refused to mount.")
    problem = windows.personalize(DEVICE, SETUP)
    assert problem == ("/dev/zd16p3: Windows is hibernated, refused to mount.; "
                       "/dev/zd16p4: no Windows on it")
    # Only the partition that was mounted is unmounted.
    assert [c for c in runner.calls if c[0] == "umount"] == [["umount", str(windows.run_dir / "vip-05")]]
    assert not any(c[:2] == ["hivexregedit", "--merge"] for c in runner.calls)


def test_a_failed_merge_is_reported_and_unmounted(windows, runner):
    _windows_on(windows)
    runner.responses[("hivexregedit", "--merge")] = (False, "", "hive is corrupt")
    assert windows.personalize(DEVICE, SETUP) == "editing the registry failed: hive is corrupt"
    assert runner.calls[-1] == ["umount", str(windows.run_dir / "vip-05")]


def test_bad_input_never_touches_the_host(windows, runner):
    assert "Invalid computer name" in windows.personalize(DEVICE, OsSetup("Bad Name"))
    assert runner.calls == []


def test_unreadable_lsblk_counts_as_no_windows(windows, runner):
    runner.responses[("lsblk",)] = (True, "not json", "")
    assert windows.personalize(DEVICE, SETUP).startswith("no Windows partition")


def test_an_unexpected_error_is_returned_not_raised(windows, runner):
    def boom(cmd):
        raise RuntimeError("disk vanished")
    runner.responses[("lsblk",)] = boom
    assert windows.personalize(DEVICE, SETUP) == "unexpected error: disk vanished"


def test_partitions_listed_next_to_the_disk(windows, runner):
    """lsblk on PVE 9 lists the partitions of a disk named on its command line flat."""
    runner.responses[("lsblk",)] = (True, json.dumps({"blockdevices": [
        {"path": "/dev/zd64", "type": "disk", "fstype": None, "size": 161061273600},
        {"path": "/dev/zd64p1", "type": "part", "fstype": None, "size": 16759808},
        {"path": "/dev/zd64p2", "type": "part", "fstype": "ntfs", "size": 161042399232},
    ]}), "")
    assert windows.ntfs_partitions(DEVICE) == ["/dev/zd64p2"]


# ── Fixed IPv4 addresses become DHCP ─────────────────────────────────

def _multi_sz(*items: str) -> str:
    raw = ("\0".join(items) + "\0\0").encode("utf-16-le")
    return "hex(7):" + ",".join(f"{b:02x}" for b in raw)


FIXED = "{ce61fd57-992d-4f05-86b6-c4d2b5b7ea91}"
DHCP = "{0b0c1e05-dc82-44aa-ab40-16c8ae66f8a0}"
UNSET = "{11111111-2222-3333-4444-555555555555}"
INTERFACES = (
    "Windows Registry Editor Version 5.00\r\n\r\n"
    "[\\ControlSet002\\Services\\Tcpip\\Parameters\\Interfaces]\r\n\r\n"
    f"[\\ControlSet002\\Services\\Tcpip\\Parameters\\Interfaces\\{DHCP}]\r\n"
    '"EnableDHCP"=dword:00000001\r\n\r\n'
    # vip-05's NIC as Disk2vhd captured it: a fixed address, wrapped like hivexregedit does
    f"[\\ControlSet002\\Services\\Tcpip\\Parameters\\Interfaces\\{FIXED}]\r\n"
    f'"DefaultGateway"={_multi_sz("192.168.0.254")}\r\n'
    '"EnableDHCP"=dword:00000000\r\n'
    f'"IPAddress"={_multi_sz("192.168.0.25")[:40]}\\\r\n  {_multi_sz("192.168.0.25")[40:]}\r\n'
    f'"SubnetMask"={_multi_sz("255.255.255.0")}\r\n\r\n'
    f"[\\ControlSet002\\Services\\Tcpip\\Parameters\\Interfaces\\{FIXED}\\{{aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee}}]\r\n"
    '"EnableDHCP"=dword:00000000\r\n\r\n'
    f"[\\ControlSet002\\Services\\Tcpip\\Parameters\\Interfaces\\{UNSET}]\r\n"
    '"EnableDHCP"=dword:00000000\r\n'
    f'"IPAddress"={_multi_sz("0.0.0.0")}\r\n'
)


def test_static_interfaces_finds_only_fixed_addresses():
    assert static_interfaces(INTERFACES) == [FIXED]
    assert static_interfaces("") == []


def test_registry_patch_switches_interfaces_to_dhcp():
    patch = registry_patch(SETUP, 2, [FIXED])
    assert patch.endswith(
        f"[\\ControlSet002\\Services\\Tcpip\\Parameters\\Interfaces\\{FIXED}]\n"
        '"EnableDHCP"=dword:00000001\n'
        '"IPAddress"=-\n"SubnetMask"=-\n"DefaultGateway"=-\n"DefaultGatewayMetric"=-\n'
    )


def test_personalize_turns_a_fixed_address_into_dhcp(windows, runner):
    _windows_on(windows)
    select = runner.responses[("hivexregedit", "--export")]
    merged = {}

    def export(cmd):
        return (True, INTERFACES, "") if cmd[-1].endswith("\\Interfaces") else select

    def merge(cmd):
        merged["reg"] = Path(cmd[3]).read_text(encoding="utf-8")
        return True, "", ""
    runner.responses[("hivexregedit", "--export")] = export
    runner.responses[("hivexregedit", "--merge")] = merge
    assert windows.personalize(DEVICE, SETUP) is None
    assert merged["reg"] == registry_patch(SETUP, 2, [FIXED])
