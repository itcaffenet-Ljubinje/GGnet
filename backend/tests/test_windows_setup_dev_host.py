"""
WindowsSetup against a real zvol on the host: udev, lsblk, ntfs-3g, umount
and hivexregedit as they really behave.

Runs real zfs and disk commands, so it is skipped unless both are set:
  GGNET_ALLOW_DESTRUCTIVE_TESTS=yes
  GGNET_CONFIG=<config whose storage.root_dataset ends in "-dev">

It creates a 1G zvol under storage.writebacks with a GPT (EFI + NTFS
partition), and removes it. With GGNET_TEST_HIVE=<an empty regf hive file,
e.g. hivex's images/minimal> it also merges into a real hive.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from app.config import get_config
from app.windows_setup import OsSetup, WindowsSetup
from app.zfs_manager import ZFSManager

pytestmark = pytest.mark.destructive

ZVOL_NAME = "pytest-win-os"
SETUP = OsSetup("pytest-pc", {"GGNET_SERVER": "http://192.0.2.1:8088"})
# The keys a real SYSTEM hive has, for an empty test hive.
BASE_KEYS = """Windows Registry Editor Version 5.00

[\\Select]
"Current"=dword:00000001

[\\ControlSet001]

[\\ControlSet001\\Control]

[\\ControlSet001\\Control\\ComputerName]

[\\ControlSet001\\Control\\ComputerName\\ComputerName]
"ComputerName"="IMAGE"

[\\ControlSet001\\Control\\Session Manager]

[\\ControlSet001\\Control\\Session Manager\\Environment]
"Path"="C:\\\\Windows"

[\\ControlSet001\\Services]

[\\ControlSet001\\Services\\Tcpip]

[\\ControlSet001\\Services\\Tcpip\\Parameters]
"""


def sh(*cmd: str) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


@pytest.fixture
def dev_zfs() -> ZFSManager:
    if not os.environ.get("GGNET_CONFIG"):
        pytest.fail("GGNET_CONFIG must point to the dev config")
    get_config.cache_clear()
    zfs = ZFSManager()
    if not zfs.layout.root_dataset.endswith("-dev"):
        pytest.fail(f"Refusing to run: {zfs.layout.root_dataset!r} is not a -dev dataset")
    return zfs


@pytest.fixture
def ntfs_zvol(dev_zfs):
    """A 1G zvol with an EFI partition and an empty NTFS partition; its device and NTFS partition."""
    zvol = f"{dev_zfs.layout.writebacks}/{ZVOL_NAME}"
    assert not dev_zfs.dataset_exists(zvol), f"{zvol} left over from an earlier run"
    assert dev_zfs.create_zvol(zvol, 1)
    device = dev_zfs.zvol_device_path(zvol)
    try:
        sh("udevadm", "settle", "--timeout=10")
        sh("sgdisk", "-n", "1:0:+100M", "-t", "1:ef00", "-n", "2:0:0", "-t", "2:0700", device)
        sh("udevadm", "settle", "--timeout=10")
        part = f"{device}-part2"
        sh("mkntfs", "-Q", "-F", "-L", "Windows", part)
        sh("udevadm", "settle", "--timeout=10")
        yield device, part
    finally:
        dev_zfs.destroy(zvol, recursive=True)
    assert not dev_zfs.dataset_exists(zvol)


def _put_hive(part: str, hive: bytes, tmp_path: Path) -> None:
    mnt = tmp_path / "mnt"
    mnt.mkdir()
    sh("ntfs-3g", part, str(mnt))
    try:
        config = mnt / "Windows" / "System32" / "config"
        config.mkdir(parents=True)
        (config / "SYSTEM").write_bytes(hive)
    finally:
        sh("umount", str(mnt))


def _mounted(path: Path) -> bool:
    return subprocess.run(["findmnt", str(path)], capture_output=True).returncode == 0


def test_empty_ntfs_has_no_windows(ntfs_zvol, tmp_path):
    device, part = ntfs_zvol
    windows = WindowsSetup(run_dir=tmp_path / "run")
    assert windows.ntfs_partitions(device)[0].endswith(("p2", "-part2"))
    problem = windows.personalize(device, SETUP)
    assert problem is not None and problem.endswith("no Windows on it")
    assert not _mounted(windows.run_dir / SETUP.computer_name)


def test_a_broken_hive_is_reported_and_unmounted(ntfs_zvol, tmp_path):
    device, part = ntfs_zvol
    _put_hive(part, b"not a hive", tmp_path)
    windows = WindowsSetup(run_dir=tmp_path / "run")
    problem = windows.personalize(device, SETUP)
    assert problem is not None and problem.startswith("editing the registry failed")
    assert not _mounted(windows.run_dir / SETUP.computer_name)


@pytest.mark.skipif(not os.environ.get("GGNET_TEST_HIVE"), reason="set GGNET_TEST_HIVE to an empty hive")
def test_merges_into_a_real_hive(ntfs_zvol, tmp_path):
    device, part = ntfs_zvol
    hive = tmp_path / "SYSTEM"
    shutil.copy(os.environ["GGNET_TEST_HIVE"], hive)
    (tmp_path / "base.reg").write_text(BASE_KEYS)
    sh("hivexregedit", "--merge", str(hive), str(tmp_path / "base.reg"))
    _put_hive(part, hive.read_bytes(), tmp_path)

    windows = WindowsSetup(run_dir=tmp_path / "run")
    assert windows.personalize(device, SETUP) is None

    mnt = tmp_path / "check"
    mnt.mkdir()
    sh("ntfs-3g", "-o", "ro", part, str(mnt))
    try:
        out = sh("hivexregedit", "--export", str(mnt / "Windows/System32/config/SYSTEM"), "\\ControlSet001")
    finally:
        sh("umount", str(mnt))
    utf16 = lambda s: ",".join(f"{b:02x}" for b in (s + "\0").encode("utf-16-le"))   # noqa: E731
    assert f'"ComputerName"=hex(1):{utf16("PYTEST-PC")}' in out
    assert f'"Hostname"=hex(1):{utf16("pytest-pc")}' in out
    assert f'"GGNET_SERVER"=hex(1):{utf16("http://192.0.2.1:8088")}' in out
    assert '"Path"=' in out   # what was there stays
