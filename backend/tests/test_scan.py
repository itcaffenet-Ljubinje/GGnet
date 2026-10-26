"""The hardware scan and automatic Add new hardware at boot (app.services.scan, app.api.v1.boot)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.api import deps
from app.api.v1 import boot
from app.main import app
from app.services import scan
from app.services.toolchain import HardwareAdder
from app.windows_setup import NET_CLASS, ImagePrep

from .test_boot_mode import MAC, FakeWindows, _boot_machine, _get, disks  # noqa: F401 (fixture)

I219 = "VEN_8086&DEV_15BC&SUBSYS_86721043&REV_10"
I219_QUERY = {"pci": "15bc8086", "cls": "020000", "sub": "86721043", "rev": "10"}
INSTANCE = "3&11583659&0&FE"


def _device(nic: str, instance: str, cls: str = NET_CLASS) -> dict:
    return {"instance_id": f"PCI\\{nic}\\{instance}", "hardware_ids": [f"PCI\\{nic}"], "compatible_ids": [],
            "class_guid": cls, "description": "card", "service": None}


# ── Pieces ────────────────────────────────────────────────────────────

def test_choose_card_takes_the_card_ipxe_booted_from():
    devices = [_device("VEN_10EC&DEV_8125&SUBSYS_86771043&REV_05", "01000000684CE00000"),
               _device(I219, INSTANCE),
               _device("VEN_8086&DEV_A3A3&SUBSYS_86941043&REV_00", "3&1&0&A0", cls="{other}")]
    assert scan.choose_card(devices, I219) == scan.ChosenCard(I219, INSTANCE)
    # Another revision of the same chip on this board.
    assert scan.choose_card(devices, I219.replace("REV_10", "REV_11")) == scan.ChosenCard(I219, INSTANCE)
    assert scan.choose_card(devices, None) is None                     # two cards, none named
    assert scan.choose_card(devices[1:], None) == scan.ChosenCard(I219, INSTANCE)
    # In Windows PE without its driver the card has no class, only its class code.
    bare = {**_device(I219, INSTANCE, cls=""), "compatible_ids": ["PCI\\VEN_8086&CC_020000"]}
    assert scan.choose_card([bare], I219) == scan.ChosenCard(I219, INSTANCE)


def test_the_scan_script_boots_windows_pe_with_the_scanner_and_driver():
    script = scan.ipxe_scan_script("http://192.168.0.40:8088/", MAC, "8086-15bc", "intel-pro1000", ["e1d.inf", "e1d.sys"])
    assert "kernel http://192.168.0.40:8088/api/v1/boot/winpe/wimboot index=1" in script
    assert f"initrd -n ggnet-scan.json http://192.168.0.40:8088/api/v1/boot/scan/config?mac={MAC}&chip=8086-15bc" in script
    assert "initrd -n e1d.sys http://192.168.0.40:8088/api/v1/boot/scan/driver/intel-pro1000/e1d.sys" in script
    assert script.index("winpeshl.ini") < script.index("boot.wim")    # boot.wim last, as wimboot wants
    assert script.rstrip().endswith("exit")


def _library(root: Path) -> scan.DriverLibrary:
    """Intel's PRO1000 folder (an ASCII INF naming the I219) and Realtek's WinPE driver (UTF-16 INF)."""
    intel = root / "intel-pro1000"
    intel.mkdir(parents=True)
    (intel / "e1d.inf").write_text("[Version]\nCatalogFile = e1d.cat\n%E15BC% = E15BC.10.0.1, PCI\\VEN_8086&DEV_15BC\n")
    (intel / "e1r68x64.inf").write_text("%E1533% = E1533, PCI\\VEN_8086&DEV_1533\n")
    for name, data in (("e1d.sys", b"MZ"), ("e1d.cat", b"cat"), ("readme.txt", b"hi")):
        (intel / name).write_bytes(data)
    realtek = root / "realtek-pcie"
    realtek.mkdir()
    (realtek / "ws640x64.inf").write_bytes(b"\xff\xfe" + "PCI\\VEN_10EC&DEV_8125&SUBSYS_0000\r\n".encode("utf-16-le"))
    return scan.DriverLibrary(root)


def test_the_driver_library_finds_the_package_for_a_chip(tmp_path):
    library = _library(tmp_path)
    assert library.match("8086-15bc") == ("intel-pro1000", ["e1d.inf"])
    assert library.match("10ec-8125") == ("realtek-pcie", ["ws640x64.inf"])
    assert library.match("10ec-8168") is None
    assert library.match("../x") is None
    assert library.files("intel-pro1000") == ["e1d.cat", "e1d.inf", "e1d.sys", "e1r68x64.inf"]
    assert library.file("intel-pro1000", "readme.txt") is None
    assert library.file("..", "passwd") is None and library.file("intel-pro1000", "../x") is None
    assert scan.DriverLibrary(tmp_path / "missing").match("8086-15bc") is None


# ── At boot ───────────────────────────────────────────────────────────

class NewCardWindows(FakeWindows):
    """An image that starts the I219 only after Add new hardware ran."""

    installed = False

    def nic_support(self, device, nics):
        out = super().nic_support(device, [n for n in nics if n[0] != I219])
        if not isinstance(out, dict):
            return out
        out.update({n: "ready" if self.installed else "missing" for n in nics if n[0] == I219})
        return out

    def start_toolchain(self, device, nics, prep, label="image"):
        self.started = list(nics)

    def toolchain_result(self, device, label="image"):
        self.installed = True
        return {"ok": True, "devices": [{"instance_id": "x", "ok": True, "driver": "Intel"}]}


class FakeVm:
    def run(self, device, label, cancel=None):
        return None


@pytest.fixture
def pc(client, host, prov, disks, tmp_path, monkeypatch):  # noqa: F811
    prov.windows = NewCardWindows(host)
    winpe = tmp_path / "winpe"
    winpe.mkdir()
    for name in ("wimboot", "bcd", "boot.sdi", "boot.wim"):
        (winpe / name).write_bytes(b"pe")
    scanner = tmp_path / "ggnet-scan.exe"
    scanner.write_bytes(b"MZ")
    monkeypatch.setattr(scan, "winpe_dir", lambda cfg: winpe)
    monkeypatch.setattr(boot, "_scanner", lambda: scanner)
    adder = HardwareAdder(prov, FakeVm(), lambda: ImagePrep(), background=False)
    library = _library(tmp_path / "winpe-drivers")
    app.dependency_overrides[deps.get_hardware_adder] = lambda: adder
    app.dependency_overrides[deps.get_driver_library] = lambda: library
    return _boot_machine(client, disks)


def _ipxe(client) -> str:
    r = client.get("/api/v1/boot/ipxe", params={"mac": MAC, **I219_QUERY})
    assert r.status_code == 200, r.text
    return r.text


def test_a_pc_with_a_new_card_is_scanned_then_added_then_booted(client, prov, pc):
    # 1. The image cannot start the card and its instance is unknown: Windows PE with the scanner.
    script = _ipxe(client)
    assert "wimboot" in script and "sanboot" not in script
    assert "/api/v1/boot/scan/driver/intel-pro1000/e1d.sys" in script
    assert f"/api/v1/boot/scan/config?mac={MAC}&chip=8086-15bc" in script
    config = client.get("/api/v1/boot/scan/config", params={"mac": MAC, "chip": "8086-15bc"}).json()
    assert config == {"server": "http://testserver", "mac": MAC, "drivers": ["e1d.inf"]}
    assert client.get("/api/v1/boot/scan/driver/intel-pro1000/e1d.cat").content == b"cat"
    assert client.get("/api/v1/boot/scan/driver/intel-pro1000/readme.txt").status_code == 404
    assert client.get("/api/v1/boot/winpe/BCD").content == b"pe"                # bcd on disk
    assert client.get("/api/v1/boot/winpe/../config.toml").status_code == 404
    assert "ggnet-scan.exe" in client.get("/api/v1/boot/scan/winpeshl.ini").text

    # 2. The scanner reports the card.
    r = client.post("/api/v1/boot/scan", json={"mac": MAC, "scanner_version": "0.1.0", "devices": [
        _device(I219, INSTANCE), _device("VEN_8086&DEV_A3A3&SUBSYS_86941043&REV_00", "3&1&0&A0", "{x}")]})
    assert INSTANCE in r.json()["message"]
    assert _get(client, pc)["nic_instance"] == INSTANCE

    # 3. Next boot: Add new hardware runs (here at once) and the PC waits.
    script = _ipxe(client)
    assert "Adding the network card" in script and "chain --replace" in script
    assert prov.windows.started == [(I219, INSTANCE)]
    assert client.get(f"/api/v1/game-disks/{pc['os_disk_id']}").json()["snapshot"] == "v2"

    # 4. Then it boots the new version.
    assert "sanboot" in _ipxe(client)


def test_new_hardware_can_be_turned_off(client, pc, monkeypatch):
    real = boot.pxe.effective_config

    def off(db, cfg=None):
        out = dict(real(db, cfg))
        out["boot"] = {**(out.get("boot") or {}), "new_hardware": "off"}
        return out
    monkeypatch.setattr(boot.pxe, "effective_config", off)
    assert "sanboot" in _ipxe(client)


def test_without_windows_pe_the_pc_boots_as_before(client, pc, monkeypatch, tmp_path):
    monkeypatch.setattr(scan, "winpe_dir", lambda cfg: tmp_path / "nothing")
    assert "sanboot" in _ipxe(client)


def test_a_scan_from_an_unknown_pc(client, pc):
    r = client.post("/api/v1/boot/scan", json={"mac": "aa:bb:cc:00:00:01", "devices": []})
    assert "not registered" in r.json()["message"]

