"""
WindowsSetup: makes a Boot Mode PC's OS writeback its own before it boots.

Every Boot Mode PC boots the same Windows image, so on its own every PC would
have the image's computer name. Like ggRock (its Rename.PC and
Inject.EnvVariables registry templates), the server edits the PC's fresh OS
clone offline, before iPXE boots it, so Windows comes up as that PC without
an extra reboot:

  SYSTEM hive, current control set (from \\Select\\Current):
    Control\\ComputerName\\ComputerName   ComputerName = PC-07
    Services\\Tcpip\\Parameters           Hostname, NV Hostname = pc-07
    Control\\Session Manager\\Environment  GGNET_SERVER, GGNET_MACHINE_ID, GGNET_MACHINE_NAME
    Services\\Tcpip\\Parameters\\Interfaces\\{...}
                                        a fixed IPv4 address becomes DHCP again
    MountedDevices                      every drive letter but C: is forgotten
    Enum\\PCI\\<boot NIC>               added when the image knows the PC's network
                                        chip only in another revision or board

An image made from a PC with a fixed address would give every PC that
address; the PC that owns it then loses its iSCSI disk whenever another one
is on. Windows takes the boot NIC's address from the iBFT anyway.

The image also remembers the letters of the PC it was made on (vip-05's
local D:, E:, F:). On another PC those volumes do not exist, yet Windows
keeps the letters for them, so the agent could not give the game disk D:
(Set-Partition 42012). Windows gives present volumes letters again at boot.

Add hardware: Windows boots from iSCSI only if its boot network card is
installed before Plug and Play runs, so a PC whose card the image has never
seen stops at 0x7B. The same chip in another revision or on another board
(Realtek 8168 REV_15 on the PC the image was made on, REV_16 on the next
board) only has another hardware ID: its Enum entry is copied from the
known one with the new IDs (iPXE reports them, app.api.v1.boot), so it
binds the same driver. A chip the image has no driver for is reported.

The Windows partition of the clone is mounted with ntfs-3g and the hive is
merged with hivexregedit (both ship with Proxmox VE). Only the PC's clone is
touched; the image and its snapshots are never mounted.

personalize() never raises: a PC that boots with the image's name is better
than a PC that does not boot, so a failure (an image without Windows yet, a
hibernated Windows that ntfs-3g refuses to mount) is returned as a reason
for the caller to log.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional, Sequence

from app.runner import CommandRunner

logger = logging.getLogger("ggnet.windows")

DEFAULT_RUN_DIR = Path("/run/ggnet/windows")
HIVE = ("Windows", "System32", "config", "SYSTEM")
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,14}$")
_ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
_CURRENT_RE = re.compile(r'^"Current"=dword:([0-9a-fA-F]{8})\s*$', re.M)
_IFACE_RE = re.compile(r"\\Interfaces\\(\{[0-9A-Fa-f-]{36}\})\]$")
_LETTER_RE = re.compile(r'^"\\\\DosDevices\\\\([A-Za-z]):"=', re.M)
# A PCI device's hardware ID as Windows names its Enum key.
NIC_ID_RE = re.compile(r"^VEN_([0-9A-F]{4})&DEV_([0-9A-F]{4})&SUBSYS_([0-9A-F]{8})&REV_([0-9A-F]{2})$")


@dataclass(frozen=True)
class OsSetup:
    """What a Boot Mode PC's Windows is told about itself."""

    computer_name: str                        # the machine name, [a-z0-9-], at most 15
    env: Mapping[str, str] = field(default_factory=dict)
    # The boot network card's hardware ID (VEN_10EC&DEV_8168&SUBSYS_E0001458&REV_16), if known.
    boot_nic: str | None = None


def _reg_string(value: str) -> str:
    """A .reg string literal."""
    if any(c in value for c in "\r\n\0"):
        raise ValueError("registry strings must not contain line breaks or NUL")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def static_interfaces(export: str) -> list[str]:
    """
    The TCP/IP interfaces in a `hivexregedit --export` of
    Services\\Tcpip\\Parameters\\Interfaces that have a fixed IPv4 address
    (EnableDHCP 0 and an IPAddress other than 0.0.0.0).
    """
    found = []
    for block in export.replace("\\\r\n  ", "").replace("\\\n  ", "").split("\n["):
        lines = block.strip().splitlines()
        m = _IFACE_RE.search(lines[0].rstrip("\r")) if lines else None
        if not m:
            continue
        values = dict(line.rstrip("\r").split("=", 1) for line in lines[1:] if "=" in line)
        if values.get('"EnableDHCP"') != "dword:00000000":
            continue
        raw = values.get('"IPAddress"', "")
        if not raw.startswith("hex(7):"):
            continue
        try:
            text = bytes(int(x, 16) for x in raw[7:].split(",") if x).decode("utf-16-le")
        except ValueError:
            continue
        if any(a and a != "0.0.0.0" for a in text.split("\0")):
            found.append(m.group(1))
    return found


def reserved_letters(export: str) -> list[str]:
    """Drive letters other than C: in a `hivexregedit --export` of MountedDevices."""
    letters = {m.group(1).upper() for m in _LETTER_RE.finditer(export)}
    return sorted(letters - {"C"})


def _reg_blocks(export: str) -> list[tuple[str, list[str]]]:
    """The keys of a `hivexregedit --export` with their value lines, in order."""
    text = export.replace("\\\r\n  ", "").replace("\\\n  ", "").replace("\r\n", "\n")
    blocks: list[tuple[str, list[str]]] = []
    for line in text.split("\n"):
        if line.startswith("[") and line.endswith("]"):
            blocks.append((line[1:-1], []))
        elif blocks and line.strip():
            blocks[-1][1].append(line)
    return blocks


def _swap_ids(line: str, swaps: Sequence[tuple[str, str]]) -> str:
    """A .reg value line with each old ID replaced, in text and in UTF-16 hex data."""
    name, sep, data = line.partition("=")
    if not sep:
        return line
    m = re.match(r"^(hex(?:\([0-9a-fA-F]+\))?:)([0-9a-fA-F,]*)$", data)
    if m:
        raw = bytes(int(x, 16) for x in m.group(2).split(",") if x)
        for old, new in swaps:
            raw = raw.replace(old.encode("utf-16-le"), new.encode("utf-16-le"))
        data = m.group(1) + ",".join(f"{b:02x}" for b in raw)
    else:
        for old, new in swaps:
            data = data.replace(old, new)
    return f"{name}={data}"


def nic_patch(export: str, nic: str) -> tuple[str | None, str | None]:
    """
    Add hardware for the boot NIC, from a `hivexregedit --export` of
    <ControlSet>\\Enum\\PCI: (.reg lines to merge, None) when the image knows
    the chip under another hardware ID, (None, None) when it knows this one,
    (None, why) when it has no driver for the chip.

    The entry is copied from the image's entry for the same vendor and device
    (the same subsystem first, as it is the same board family) that has a
    driver service; its key and the IDs in its values get the PC's subsystem
    and revision.
    """
    want = NIC_ID_RE.match(nic)
    if want is None:
        raise ValueError(f"Invalid PCI hardware ID: {nic!r}")
    ven, dev, sub, rev = want.groups()
    blocks = _reg_blocks(export)
    devices: dict[str, str] = {}            # upper-case device key name -> key path prefix
    services: set[str] = set()
    for path, values in blocks:
        head, marker, rest = path.partition("\\Enum\\PCI\\")
        if not marker or not rest:
            continue
        name = rest.split("\\", 1)[0]
        devices.setdefault(name.upper(), f"{head}\\Enum\\PCI\\{name}")
        if any(v.startswith('"Service"=') for v in values):
            services.add(name.upper())
    if nic in devices:
        return None, None
    siblings = sorted(n for n in services
                      if (m := NIC_ID_RE.match(n)) and m.group(1) == ven and m.group(2) == dev)
    if not siblings:
        return None, f"the image has no driver for the boot network card PCI\\{nic}"
    source = next((n for n in siblings if NIC_ID_RE.match(n).group(3) == sub), siblings[0])
    _, _, old_sub, old_rev = NIC_ID_RE.match(source).groups()
    swaps = [(source, nic), (f"SUBSYS_{old_sub}", f"SUBSYS_{sub}"), (f"REV_{old_rev}", f"REV_{rev}")]
    prefix = devices[source]
    lines: list[str] = []
    for path, values in blocks:
        if path.upper() != prefix.upper() and not path.upper().startswith(prefix.upper() + "\\"):
            continue
        new_path = prefix[: -len(source)] + nic + path[len(prefix):]
        lines += ["", f"[{new_path}]", *(_swap_ids(v, swaps) for v in values)]
    return "\n".join(lines).lstrip("\n"), None


def registry_patch(setup: OsSetup, control_set: int, dhcp_interfaces: Sequence[str] = (),
                   forget_letters: Sequence[str] = (), extra: str | None = None) -> str:
    """The .reg text hivexregedit merges into the SYSTEM hive."""
    if not _NAME_RE.match(setup.computer_name):
        raise ValueError(f"Invalid computer name: {setup.computer_name!r}")
    cs = f"\\ControlSet{control_set:03d}"
    lines = [
        "Windows Registry Editor Version 5.00",
        "",
        f"[{cs}\\Control\\ComputerName\\ComputerName]",
        f'"ComputerName"={_reg_string(setup.computer_name.upper())}',
        "",
        f"[{cs}\\Services\\Tcpip\\Parameters]",
        f'"Hostname"={_reg_string(setup.computer_name)}',
        f'"NV Hostname"={_reg_string(setup.computer_name)}',
    ]
    if setup.env:
        lines += ["", f"[{cs}\\Control\\Session Manager\\Environment]"]
        for key, value in setup.env.items():
            if not _ENV_KEY_RE.match(key):
                raise ValueError(f"Invalid environment variable name: {key!r}")
            lines.append(f"{_reg_string(key)}={_reg_string(value)}")
    for iface in dhcp_interfaces:
        lines += [
            "", f"[{cs}\\Services\\Tcpip\\Parameters\\Interfaces\\{iface}]",
            '"EnableDHCP"=dword:00000001',
            '"IPAddress"=-', '"SubnetMask"=-', '"DefaultGateway"=-', '"DefaultGatewayMetric"=-',
        ]
    if forget_letters:
        lines += ["", "[\\MountedDevices]"]
        for letter in forget_letters:
            if len(letter) != 1 or not letter.isalpha() or letter.upper() == "C":
                raise ValueError(f"Invalid drive letter to forget: {letter!r}")
            lines.append(f'"\\\\DosDevices\\\\{letter.upper()}:"=-')
    if extra:
        lines += ["", extra]
    return "\n".join(lines) + "\n"


class WindowsSetup:
    def __init__(self, runner: Optional[CommandRunner] = None, run_dir: Path = DEFAULT_RUN_DIR):
        self.runner = runner or CommandRunner()
        self.run_dir = run_dir

    def _run(self, cmd: list[str], quiet: bool = False) -> tuple[bool, str, str]:
        return self.runner.run(cmd, quiet=quiet)

    def ntfs_partitions(self, device: str) -> list[str]:
        """The NTFS partitions of a disk, largest first (Windows is the big one)."""
        # A clone made a moment ago: wait for udev to create its partition devices.
        self._run(["udevadm", "settle", "--timeout=10"], quiet=True)
        ok, out, _ = self._run(["lsblk", "-J", "-b", "-p", "-o", "PATH,TYPE,FSTYPE,SIZE", device])
        if not ok:
            return []
        try:
            devices = json.loads(out).get("blockdevices") or []
        except ValueError:
            return []
        # lsblk nests partitions under their disk, or (for a disk named on the
        # command line, as on PVE 9) lists them next to it: take both.
        flat, todo = [], list(devices)
        while todo:
            d = todo.pop()
            flat.append(d)
            todo.extend(d.get("children") or [])
        parts = [d for d in flat if d.get("type") == "part" and d.get("fstype") == "ntfs"]
        parts.sort(key=lambda c: int(c.get("size") or 0), reverse=True)
        return [c["path"] for c in parts]

    def control_set(self, hive: Path) -> int:
        """The control set Windows boots with (SYSTEM\\Select\\Current); 1 when unreadable."""
        ok, out, _ = self._run(["hivexregedit", "--export", str(hive), "\\Select"], quiet=True)
        m = _CURRENT_RE.search(out) if ok else None
        return int(m.group(1), 16) if m and int(m.group(1), 16) > 0 else 1

    def static_interfaces(self, hive: Path, control_set: int) -> list[str]:
        """Interfaces with a fixed IPv4 address in the hive; none when unreadable."""
        key = f"\\ControlSet{control_set:03d}\\Services\\Tcpip\\Parameters\\Interfaces"
        ok, out, _ = self._run(["hivexregedit", "--export", str(hive), key], quiet=True)
        return static_interfaces(out) if ok else []

    def reserved_letters(self, hive: Path) -> list[str]:
        """Drive letters other than C: the hive remembers; none when unreadable."""
        ok, out, _ = self._run(["hivexregedit", "--export", str(hive), "\\MountedDevices"], quiet=True)
        return reserved_letters(out) if ok else []

    def enum_pci(self, hive: Path, control_set: int) -> str | None:
        """The hive's PCI device entries as .reg text; None when unreadable."""
        key = f"\\ControlSet{control_set:03d}\\Enum\\PCI"
        ok, out, _ = self._run(["hivexregedit", "--export", str(hive), key], quiet=True)
        return out if ok else None

    def personalize(self, device: str, setup: OsSetup) -> str | None:
        """Write the PC's identity into its OS clone. None when done, else why not."""
        try:
            registry_patch(setup, 1)   # validate before touching the host
            if setup.boot_nic and not NIC_ID_RE.match(setup.boot_nic):
                raise ValueError(f"Invalid PCI hardware ID: {setup.boot_nic!r}")
        except ValueError as e:
            return str(e)
        try:
            return self._personalize(device, setup)
        except Exception as e:     # never fail the provisioning it is part of
            logger.exception("Setting up Windows on %s failed", device)
            return f"unexpected error: {e}"

    def _personalize(self, device: str, setup: OsSetup) -> str | None:
        parts = self.ntfs_partitions(device)
        if not parts:
            return f"no Windows partition found on {device}"
        mount = self.run_dir / setup.computer_name
        reasons = []
        for part in parts:
            try:
                mount.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                return f"cannot create {mount}: {e}"
            ok, _, err = self._run(["ntfs-3g", "-o", "rw,noatime", part, str(mount)])
            if not ok:
                reasons.append(f"{part}: {err.strip() or 'mount failed'}")
                continue
            try:
                hive = _find(mount, HIVE)
                if hive is None:
                    reasons.append(f"{part}: no Windows on it")
                    continue
                return self._merge(hive, setup)
            finally:
                if not self._run(["umount", str(mount)])[0]:
                    logger.error("Could not unmount %s", mount)
                try:
                    mount.rmdir()
                except OSError:
                    pass
        return "; ".join(reasons)

    def _merge(self, hive: Path, setup: OsSetup) -> str | None:
        control_set = self.control_set(hive)
        fixed = self.static_interfaces(hive, control_set)
        letters = self.reserved_letters(hive)
        nic_reg, nic_problem = None, None
        if setup.boot_nic:
            export = self.enum_pci(hive, control_set)
            if export is None:
                nic_problem = "cannot read the image's PCI devices"
            else:
                nic_reg, nic_problem = nic_patch(export, setup.boot_nic)
        patch = registry_patch(setup, control_set, fixed, letters, nic_reg)
        reg = self.run_dir / f"{setup.computer_name}.reg"
        try:
            reg.write_text(patch, encoding="utf-8")
            ok, _, err = self._run(["hivexregedit", "--merge", str(hive), str(reg)])
        finally:
            reg.unlink(missing_ok=True)
        if not ok:
            return f"editing the registry failed: {err.strip()}"
        logger.info("Windows on %s set up as %s", hive, setup.computer_name)
        if fixed:
            logger.info("Fixed IPv4 addresses switched to DHCP on %s: %s", setup.computer_name,
                        ", ".join(fixed))
        if letters:
            logger.info("Drive letters forgotten on %s: %s", setup.computer_name, ", ".join(letters))
        if nic_reg:
            logger.info("Boot network card PCI\\%s added for %s", setup.boot_nic, setup.computer_name)
        if nic_problem:
            logger.warning("%s: %s", setup.computer_name, nic_problem)
        return nic_problem


def _find(root: Path, parts: tuple[str, ...]) -> Path | None:
    """root/parts, matching each name without regard to case (as Windows does)."""
    path = root
    for name in parts:
        exact = path / name
        if exact.exists():
            path = exact
            continue
        try:
            match = next((p for p in path.iterdir() if p.name.lower() == name.lower()), None)
        except OSError:
            return None
        if match is None:
            return None
        path = match
    return path if path.is_file() else None
