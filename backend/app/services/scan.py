"""
Hardware scan: a new PC tells the server its network card itself.

Booting an OS image over iSCSI needs the PC's boot network card installed in
the image under the card's exact instance ID (app.services.toolchain). iPXE
reports the card's hardware ID, but the instance ID only Windows knows. So
when a PC boots an image that cannot start its card and its instance ID is
not known yet, the server answers iPXE with a WinPE boot instead of Windows
(wimboot, the Windows PE files from `[paths] winpe_dir`, with
`ggnet-scan.exe` from the agent folder as its only program):

  1. wimboot injects into WinPE's System32: winpeshl.ini (starts the
     scanner), the scanner, its ggnet-scan.json (this server, the PC's MAC)
     and the image's own driver for the card (WinPE has few network
     drivers), copied once per chip from the image's driver store;
  2. the scanner loads the driver, starts the network and sends the PC's
     PCI devices to POST /api/v1/boot/scan, which keeps the card's instance
     ID; then it restarts the PC;
  3. at the next iPXE request the server starts Add new hardware for the
     card and the PC waits on screen until the new version is active, then
     boots it.

PCs whose card the image already starts (or adds at boot from the same chip,
app.windows_setup.nic_patch) are never scanned.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.windows_setup import NET_CLASS, NIC_ID_RE, NIC_INSTANCE_RE

logger = logging.getLogger("ggnet.scan")

SCANNER_EXE = "ggnet-scan.exe"
# The Windows PE files (from Windows installation media or the ADK) and wimboot.
WINPE_FILES = ("wimboot", "BCD", "boot.sdi", "boot.wim")
WINPESHL_INI = "[LaunchApps]\r\n%SYSTEMROOT%\\System32\\ggnet-scan.exe\r\n"
_DRIVER_FILE = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
_CHIP = re.compile(r"^[0-9a-f]{4}-[0-9a-f]{4}$")


def winpe_dir(cfg: dict[str, Any]) -> Path:
    paths = cfg.get("paths") or {}
    return Path(paths.get("winpe_dir") or Path(paths.get("data_dir", "/var/lib/ggnet")) / "winpe")


def winpe_file(folder: Path, name: str) -> Path | None:
    """One of WINPE_FILES in `folder`, whatever its case (bcd, BCD)."""
    if name not in WINPE_FILES:
        return None
    exact = folder / name
    if exact.is_file():
        return exact
    try:
        return next((p for p in folder.iterdir() if p.name.lower() == name.lower() and p.is_file()), None)
    except OSError:
        return None


def winpe_ready(folder: Path) -> bool:
    return all(winpe_file(folder, n) is not None for n in WINPE_FILES)


def chip_key(nic: str) -> str:
    """'8086-15bc' for VEN_8086&DEV_15BC&...: one driver folder per chip."""
    m = NIC_ID_RE.match(nic)
    if m is None:
        raise ValueError(f"Invalid PCI hardware ID: {nic!r}")
    return f"{m.group(1)}-{m.group(2)}".lower()


def ipxe_scan_script(base: str, mac: str, chip: str | None, drivers: list[str]) -> str:
    """
    The iPXE script that boots WinPE with the scanner. `base` is this server's
    URL with a trailing slash. index=1: Windows PE, not Windows Setup, in a
    boot.wim from installation media.
    """
    boot, scan = f"{base}api/v1/boot/winpe", f"{base}api/v1/boot/scan"
    lines = [
        "#!ipxe",
        f"echo ggNet: this PC's network card is new to its Windows image (MAC {mac}).",
        "echo ggNet: starting the hardware scan (Windows PE); the PC restarts by itself.",
        f"kernel {boot}/wimboot index=1 || goto failed",
        f"initrd -n BCD {boot}/BCD || goto failed",
        f"initrd -n boot.sdi {boot}/boot.sdi || goto failed",
        f"initrd -n winpeshl.ini {scan}/winpeshl.ini || goto failed",
        f"initrd -n {SCANNER_EXE} {scan}/{SCANNER_EXE} || goto failed",
        f"initrd -n ggnet-scan.json {scan}/config?mac={mac}&chip={chip or ''} || goto failed",
    ]
    for name in drivers:
        lines.append(f"initrd -n {name} {scan}/driver/{chip}/{name} || goto failed")
    lines += [
        f"initrd -n boot.wim {boot}/boot.wim || goto failed",
        "boot || goto failed",
        ":failed",
        "echo ggNet: the hardware scan could not start; booting from the local disk in 10 s.",
        "sleep 10",
        "exit",
    ]
    return "\n".join(lines) + "\n"


def scan_config(base: str, mac: str, inf_files: list[str]) -> str:
    return json.dumps({"server": base.rstrip("/"), "mac": mac, "drivers": inf_files})


@dataclass
class ChosenCard:
    nic: str          # PCI hardware ID without PCI\
    instance: str


def choose_card(devices: list[dict], boot_nic: str | None) -> ChosenCard | None:
    """
    The PC's boot network card among the PCI devices the scanner sent: the
    one with the hardware ID iPXE reported, else the only network card with
    that chip, else the only network card.
    """
    cards = []
    for d in devices:
        if str(d.get("class_guid") or "").lower() != NET_CLASS:
            continue
        parts = str(d.get("instance_id") or "").split("\\")
        if len(parts) != 3 or parts[0].upper() != "PCI":
            continue
        nic, instance = parts[1].upper(), parts[2].upper()
        if NIC_ID_RE.match(nic) and NIC_INSTANCE_RE.match(instance):
            cards.append(ChosenCard(nic, instance))
    if boot_nic:
        exact = [c for c in cards if c.nic == boot_nic.upper()]
        if exact:
            return exact[0]
        chip = boot_nic.upper().split("&SUBSYS_")[0]
        same = [c for c in cards if c.nic.startswith(chip + "&")]
        if len(same) == 1:
            return same[0]
    return cards[0] if len(cards) == 1 else None


class DriverCache:
    """
    Network card drivers for WinPE, one folder per chip under `root`, copied
    from an OS image's driver store the first time a PC with that chip is
    scanned. `copy(dest)` fills a folder and returns its INF names or why not.
    """

    def __init__(self, root: Path):
        self.root = root
        self._lock = threading.Lock()

    def folder(self, chip: str) -> Path | None:
        return self.root / chip if _CHIP.match(chip) else None

    def file(self, chip: str, name: str) -> Path | None:
        folder = self.folder(chip)
        if folder is None or not _DRIVER_FILE.match(name):
            return None
        path = folder / name
        return path if path.is_file() else None

    def infs(self, nic: str, copy: Callable[[Path], list[str] | str]) -> list[str]:
        """The INF files for this chip, copied first when missing; [] when there is none."""
        folder = self.folder(chip_key(nic))
        assert folder is not None
        with self._lock:
            if not folder.is_dir():
                tmp = folder.with_name(folder.name + ".new")
                shutil.rmtree(tmp, ignore_errors=True)
                result = copy(tmp)
                if isinstance(result, str):
                    logger.warning("No WinPE driver for PCI\\%s: %s", nic, result)
                    shutil.rmtree(tmp, ignore_errors=True)
                    return []
                tmp.rename(folder)
            return sorted(p.name for p in folder.iterdir() if p.suffix.lower() == ".inf")

    def files(self, chip: str) -> list[str]:
        folder = self.folder(chip)
        if folder is None or not folder.is_dir():
            return []
        return sorted(p.name for p in folder.iterdir() if p.is_file() and _DRIVER_FILE.match(p.name))


# ── Which cards a version of an image starts (cached; a version never changes) ──

_STATUS: dict[tuple[str, str], dict[tuple[str, str | None], str]] = {}
_STATUS_LOCK = threading.Lock()


def nic_status(prov, master: str, snapshot: str, cards: list[tuple[str, str | None]]
               ) -> dict[tuple[str, str | None], str] | str:
    """
    Provisioner.check_hardware() for the cards not checked on this version
    yet; one check at a time, so PCs that boot together share it.
    """
    with _STATUS_LOCK:
        known = _STATUS.setdefault((master, snapshot), {})
        todo = sorted({c for c in cards if c not in known}, key=lambda c: (c[0], c[1] or ""))
        if todo:
            found = prov.check_hardware(master, snapshot, todo)
            if isinstance(found, str):
                return found
            known.update(found)
        return {c: known.get(c, "unknown") for c in cards}
