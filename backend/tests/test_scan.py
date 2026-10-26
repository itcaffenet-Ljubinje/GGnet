"""The hardware scan and automatic Add new hardware at boot (app.services.scan, app.api.v1.boot)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.api import deps
from app.api.v1 import boot
from app.main import app
from app.services import scan
from app.services.toolchain import HardwareAdder
from app.windows_setup import NET_CLASS, ImagePrep, WindowsSetup, active_package, best_inf, driver_ids

from .conftest import FakeRunner
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
    script = scan.ipxe_scan_script("http://192.168.0.40:8088/", MAC, "8086-15bc", ["net1ic64.inf", "e1i.sys"])
    assert "kernel http://192.168.0.40:8088/api/v1/boot/winpe/wimboot index=1" in script
    assert f"initrd -n ggnet-scan.json http://192.168.0.40:8088/api/v1/boot/scan/config?mac={MAC}&chip=8086-15bc" in script
    assert "initrd -n e1i.sys http://192.168.0.40:8088/api/v1/boot/scan/driver/8086-15bc/e1i.sys" in script
    assert script.index("winpeshl.ini") < script.index("boot.wim")    # boot.wim last, as wimboot wants
    assert script.rstrip().endswith("exit")


def test_driver_lookup_in_the_drivers_hive():
    assert driver_ids(I219)[-1] == "VEN_8086&DEV_15BC"
    export = ('[\\DriverDatabase\\DeviceIds\\PCI\\VEN_10EC&DEV_8168]\n'
              '"oem10.inf"=hex(3):01,ff,00,00\n"rt640x64.inf"=hex(3):02,ff,00,00\n')
    assert best_inf(export) == "oem10.inf"
    name = "rt640x64.inf_amd64_7364471142ff6778"
    utf16 = ",".join(f"{b:02x}" for b in (name + "\0").encode("utf-16-le"))
    assert active_package(f'[\\DriverDatabase\\DriverInfFiles\\oem10.inf]\n"Active"=hex(1):{utf16}\n') == name
    assert active_package('[\\DriverDatabase\\DriverInfFiles\\x.inf]\n"Active"="..\\\\evil"\n') is None


def test_copy_nic_driver_takes_the_package_from_the_driver_store(tmp_path):
    runner = FakeRunner()
    runner.on("lsblk", result=(True, '{"blockdevices": [{"path": "/dev/zd16p3", "type": "part", '
                                     '"fstype": "ntfs", "size": 1}]}', ""))
    package = "net1ic64.inf_amd64_93678a2d694d4579"
    utf16 = ",".join(f"{b:02x}" for b in (package + "\0").encode("utf-16-le"))

    def export(cmd):
        if cmd[-1].endswith("\\VEN_8086&DEV_15BC"):
            return True, '[\\DriverDatabase\\DeviceIds\\PCI\\VEN_8086&DEV_15BC]\n"net1ic64.inf"=hex(3):02,ff,00,00\n', ""
        if cmd[-1].endswith("\\net1ic64.inf"):
            return True, f'[\\DriverDatabase\\DriverInfFiles\\net1ic64.inf]\n"Active"=hex(1):{utf16}\n', ""
        return False, "", "no such key"
    runner.on("hivexregedit", "--export", result=export)
    windows = WindowsSetup(runner, run_dir=tmp_path / "run")
    root = windows.run_dir / "nic-driver"
    (root / "Windows" / "System32" / "config").mkdir(parents=True)
    for hive in ("SYSTEM", "DRIVERS"):
        (root / "Windows" / "System32" / "config" / hive).write_bytes(b"regf")
    store = root / "Windows" / "System32" / "DriverStore" / "FileRepository" / package
    store.mkdir(parents=True)
    for f in ("net1ic64.inf", "e1i68x64.sys", "net1ic64.cat"):
        (store / f).write_text(f)

    dest = tmp_path / "out"
    assert windows.copy_nic_driver("/dev/zvol/x", I219, dest) == ["net1ic64.inf"]
    assert sorted(p.name for p in dest.iterdir()) == ["e1i68x64.sys", "net1ic64.cat", "net1ic64.inf"]
    assert ["ntfs-3g", "-o", "ro", "/dev/zd16p3", str(root)] in runner.calls
    assert "no driver" in windows.copy_nic_driver("/dev/zvol/x", "VEN_1234&DEV_5678&SUBSYS_00000000&REV_01",
                                                  tmp_path / "none")


def test_driver_cache_copies_once_per_chip(tmp_path):
    cache = scan.DriverCache(tmp_path)
    copies = []

    def copy(dest: Path):
        copies.append(dest)
        dest.mkdir(parents=True)
        (dest / "net1ic64.inf").write_text("x")
        (dest / "e1i.sys").write_text("x")
        return ["net1ic64.inf"]
    assert cache.infs(I219, copy) == ["net1ic64.inf"]
    assert cache.infs(I219.replace("REV_10", "REV_11"), copy) == ["net1ic64.inf"]
    assert len(copies) == 1
    assert cache.files("8086-15bc") == ["e1i.sys", "net1ic64.inf"]
    assert cache.file("8086-15bc", "../x") is None and cache.file("../../etc", "passwd") is None
    cat = "Microsoft-Windows-Ethernet-Client-Intel-E1i68x64-FOD-Package~31bf3856ad364e35~amd64~~10.0.28000.1.cat"
    (tmp_path / "8086-15bc" / cat).write_text("x")             # catalogs' names have ~
    assert cache.file("8086-15bc", cat) is not None and cat in cache.files("8086-15bc")
    assert cache.infs("VEN_1234&DEV_5678&SUBSYS_00000000&REV_01", lambda dest: "no driver") == []


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

    def copy_nic_driver(self, device, nic, dest):
        dest.mkdir(parents=True)
        (dest / "net1ic64.inf").write_text("x")
        return ["net1ic64.inf"]


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
    cache = scan.DriverCache(tmp_path / "drivers")
    app.dependency_overrides[deps.get_hardware_adder] = lambda: adder
    app.dependency_overrides[deps.get_driver_cache] = lambda: cache
    return _boot_machine(client, disks)


def _ipxe(client) -> str:
    r = client.get("/api/v1/boot/ipxe", params={"mac": MAC, **I219_QUERY})
    assert r.status_code == 200, r.text
    return r.text


def test_a_pc_with_a_new_card_is_scanned_then_added_then_booted(client, prov, pc):
    # 1. The image cannot start the card and its instance is unknown: Windows PE with the scanner.
    script = _ipxe(client)
    assert "wimboot" in script and "sanboot" not in script
    assert "/api/v1/boot/scan/driver/8086-15bc/net1ic64.inf" in script
    assert f"/api/v1/boot/scan/config?mac={MAC}&chip=8086-15bc" in script
    config = client.get("/api/v1/boot/scan/config", params={"mac": MAC, "chip": "8086-15bc"}).json()
    assert config == {"server": "http://testserver", "mac": MAC, "drivers": ["net1ic64.inf"], "catalogs": []}
    assert client.get("/api/v1/boot/scan/driver/8086-15bc/net1ic64.inf").content == b"x"
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


# ── Windows' compressed files (app.wof) ──────────────────────────────

def test_wof_reparse_data_names_the_algorithm():
    from app import wof

    lzx = bytes.fromhex("170000801000000001000000020000000100000001000000")
    assert wof.wof_algorithm(lzx) == 1
    assert wof.wof_algorithm(lzx[:4] + lzx[4:20] + (7).to_bytes(4, "little")) is None
    assert wof.wof_algorithm(b"\x0c\x00\x00\xa0" + bytes(20)) is None          # a symlink


def test_wof_chunks_and_stored_data():
    import struct

    from app import wof

    data = bytes(range(256)) * 40                        # 10240 bytes: chunks of 4096, 4096, 2048
    stream = struct.pack("<II", 4096, 8192) + data       # all stored: offsets after the table
    assert [n for _, n in wof.chunks(stream, len(data), 4096)] == [4096, 4096, 2048]
    assert wof.decompress(stream, len(data), 0) == data
    with pytest.raises(wof.WofError):
        wof.chunks(struct.pack("<II", 9000, 100) + data, len(data), 4096)


def test_wof_file_size_from_ntfsinfo():
    from app import wof

    out = ("Dumping attribute $FILE_NAME (0x30)\n\tData Size:\t 5 (0x5)\n"
           "Dumping attribute $DATA (0x80)\n\tData size:\t\t 262854 (0x402c6)\n"
           "Dumping attribute $DATA (0x80)\n\tAttribute name:\t 'WofCompressedData'\n\tData size:\t 13998\n")
    assert wof.data_size(out) == 262854


def test_read_file_reads_a_wof_file_past_ntfs3g():
    import struct

    from app import wof

    data = b"x" * 5000
    reparse = bytes.fromhex("170000801000000001000000020000000100000000000000")   # XPRESS4K
    answers = {"0xc0": reparse, "WofCompressedData": struct.pack("<I", 4096) + data}

    def run(cmd):
        if cmd[0] == "ntfsinfo":
            return True, b"Dumping attribute $DATA (0x80)\n\tData size:\t 5000 (0x1388)\n"
        key = "WofCompressedData" if "WofCompressedData" in cmd else cmd[3]
        return True, answers[key]
    assert wof.read_file("/dev/zd16p3", "Windows/x.sys", run) == data


def test_pe_hashes_skip_checksum_and_signature():
    import struct

    from app import wof

    pe = bytearray(512)
    pe[:2] = b"MZ"
    struct.pack_into("<I", pe, 0x3C, 64)
    pe[64:68] = b"PE\0\0"
    struct.pack_into("<H", pe, 64 + 24, 0x20B)
    other = bytearray(pe)
    struct.pack_into("<I", other, 64 + 24 + 64, 0x1234)  # another checksum: same hash
    assert wof.pe_hashes(bytes(pe)) == wof.pe_hashes(bytes(other)) and len(wof.pe_hashes(bytes(pe))) == 2
    assert not wof.embedded_signature(bytes(pe))
    assert wof.pe_hashes(b"not a PE") == []


def test_copy_nic_driver_adds_the_catalog_of_an_inbox_driver(tmp_path):
    import struct

    from app import wof

    runner = FakeRunner()
    runner.on("lsblk", result=(True, '{"blockdevices": [{"path": "/dev/zd16p3", "type": "part", '
                                     '"fstype": "ntfs", "size": 1}]}', ""))
    package = "net1ic64.inf_amd64_93678a2d694d4579"
    utf16 = ",".join(f"{b:02x}" for b in (package + "\0").encode("utf-16-le"))

    def export(cmd):
        if cmd[-1].endswith("\\VEN_8086&DEV_15BC"):
            return True, '[\\DriverDatabase\\DeviceIds\\PCI\\VEN_8086&DEV_15BC]\n"net1ic64.inf"=hex(3):02,ff,00,00\n', ""
        return True, f'[\\DriverDatabase\\DriverInfFiles\\net1ic64.inf]\n"Active"=hex(1):{utf16}\n', ""
    runner.on("hivexregedit", "--export", result=export)
    windows = WindowsSetup(runner, run_dir=tmp_path / "run")
    root = windows.run_dir / "nic-driver"
    (root / "Windows" / "System32" / "config").mkdir(parents=True)
    for hive in ("SYSTEM", "DRIVERS"):
        (root / "Windows" / "System32" / "config" / hive).write_bytes(b"regf")
    store = root / "Windows" / "System32" / "DriverStore" / "FileRepository" / package
    store.mkdir(parents=True)
    (store / "net1ic64.inf").write_text("[Version]")
    sys_file = bytearray(512)
    sys_file[:2] = b"MZ"
    struct.pack_into("<I", sys_file, 0x3C, 64)
    sys_file[64:68] = b"PE\0\0"
    struct.pack_into("<H", sys_file, 64 + 24, 0x20B)
    (store / "e1i68x64.sys").write_bytes(bytes(sys_file))
    catroot = root / "Windows" / "System32" / "CatRoot" / "{F750E6C3-38EE-11D1-85E5-00C04FC295EE}"
    catroot.mkdir(parents=True)
    (catroot / "Other-Package.cat").write_bytes(b"nothing")
    signing = "Microsoft-Windows-Ethernet-Client-Intel-E1i68x64-FOD-Package.cat"
    (catroot / signing).write_bytes(b"..." + wof.pe_hashes(bytes(sys_file))[0] + b"...")

    dest = tmp_path / "out"
    assert windows.copy_nic_driver("/dev/zvol/x", I219, dest) == ["net1ic64.inf"]
    assert sorted(p.name for p in dest.iterdir()) == sorted(["e1i68x64.sys", signing, "net1ic64.inf"])
    assert scan.scan_config("http://s/", MAC, sorted(p.name for p in dest.iterdir())).count(signing) == 1
