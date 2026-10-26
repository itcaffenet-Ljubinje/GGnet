"""
WindowsSetup: makes a Boot Mode OS image ready for every PC (prepare_image,
once per image version) and each PC's OS writeback its own (personalize,
before it boots).

Every Boot Mode PC boots the same Windows image, so on its own every PC would
have the image's computer name. The server edits the PC's fresh OS
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

The fixed address and the letters are the image's, so prepare_image() clears
them once; a writeback only does it when the image still has them (an image
from before prepare_image).

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

prepare_image() makes what is the same on every PC part of the image, once
per version (on Apply Writebacks of an OS image, or "Prepare image" in the
UI): the server's ggnet-agent.exe in C:\\Program Files\\ggnet-agent (where
install.ps1 puts it; only when it differs) with an appsettings.json naming
this server unless the image has one, its service registered as install.ps1
does, Fast Startup off, fixed addresses to DHCP and stale letters forgotten.
It also tunes Windows for a diskless PC (tuning_patch, software_patch):
nothing goes to sleep, PCIe and USB power saving and the network card's
Energy Efficient Ethernet are off (the C: disk runs over that link), a fixed
page file, and no automatic Windows Update, maintenance (defragmentation),
search index or SysMain, which would only fill each writeback for nothing.

The Windows partition of the clone is mounted with ntfs-3g and the hive is
merged with hivexregedit (both ship with Proxmox VE). Only clones are
mounted (a PC's writeback, or the clone that becomes the next image
version); an image's snapshots never are.

Neither method raises: a PC that boots with the image's name is better than
a PC that does not boot, so a failure (an image without Windows yet, a
hibernated Windows that ntfs-3g refuses to mount) is returned as a reason
for the caller to log.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence

from app.runner import CommandRunner

logger = logging.getLogger("ggnet.windows")

DEFAULT_RUN_DIR = Path("/run/ggnet/windows")
HIVE = ("Windows", "System32", "config", "SYSTEM")
SOFTWARE_HIVE = ("Windows", "System32", "config", "SOFTWARE")
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,14}$")
_ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
_CURRENT_RE = re.compile(r'^"Current"=dword:([0-9a-fA-F]{8})\s*$', re.M)
_IFACE_RE = re.compile(r"\\Interfaces\\(\{[0-9A-Fa-f-]{36}\})\]$")
_LETTER_RE = re.compile(r'^"\\\\DosDevices\\\\([A-Za-z]):"=', re.M)
# A PCI device's hardware ID as Windows names its Enum key.
NIC_ID_RE = re.compile(r"^VEN_([0-9A-F]{4})&DEV_([0-9A-F]{4})&SUBSYS_([0-9A-F]{8})&REV_([0-9A-F]{2})$")


AGENT_DIR = ("Program Files", "ggnet-agent")
AGENT_EXE = "ggnet-agent.exe"
AGENT_SERVICE = "ggnet-agent"
AGENT_IMAGE_PATH = '"C:\\Program Files\\ggnet-agent\\ggnet-agent.exe"'
# sc failure: restart after 5 s, 5 s, then 30 s; reset the count after a day
# (SERVICE_FAILURE_ACTIONS as Windows stores it).
AGENT_FAILURE_ACTIONS = bytes.fromhex(
    "80510100" "00000000" "00000000" "03000000" "14000000"
    "01000000" "88130000" "01000000" "88130000" "01000000" "30750000")


@dataclass(frozen=True)
class AgentInstall:
    """The server's agent, put into an OS image by prepare_image()."""

    exe: Path
    sha256: str
    server_url: str


@dataclass(frozen=True)
class OsSetup:
    """What a Boot Mode PC's Windows is told about itself."""

    computer_name: str                        # the machine name, [a-z0-9-], at most 15
    env: Mapping[str, str] = field(default_factory=dict)
    # The boot network card's hardware ID (VEN_10EC&DEV_8168&SUBSYS_E0001458&REV_16), if known.
    boot_nic: str | None = None
    # Its device instance ID on this PC (from the agent), if known.
    boot_nic_instance: str | None = None


@dataclass(frozen=True)
class ImagePrep:
    """What prepare_image() makes part of an OS image (the same for every PC)."""

    agent: AgentInstall | None = None
    # Power, paging and background writes set for a diskless PC (tuning_patch()).
    tuning: bool = True
    # Microsoft Defender's services and drivers off (defender_off_lines()).
    defender_off: bool = False


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


# The instance ID Windows gives a Realtek card that reports a PCI Device Serial
# Number (Gigabyte boards, for example): the 8 serial bytes, then the function.
# Cards without one get an ID from their place on the bus (e.g. 6&95d5d6a&0&...).
REALTEK_DSN_INSTANCE = "01000000684CE00000"
NIC_INSTANCE_RE = re.compile(r"^[A-Za-z0-9&_.-]{1,64}$")


def nic_patch(export: str, nic: str, instance: str | None = None) -> tuple[str | None, str | None]:
    """
    Add hardware for the boot NIC, from a `hivexregedit --export` of
    <ControlSet>\\Enum\\PCI: (.reg lines to merge, None) when the entry has
    to be added, (None, None) when the image already knows the card, (None,
    why) when it has no driver for the chip.

    Windows starts the boot card from its entry only when the entry has the
    card's own instance ID, which depends on the board (a serial-number ID on
    one board, a bus-location ID on another). `instance` is that ID as the
    PC's agent reported it. The entry is copied from the image's entry for
    the same card, else for the same vendor and device (the same subsystem
    first, as it is the same board family) that has a driver service; its key
    gets the PC's hardware ID and instance, the IDs in its values the PC's
    subsystem and revision. Without a reported instance the copy keeps the
    source's instance, and a Realtek card also gets the serial-number ID.
    """
    want = NIC_ID_RE.match(nic)
    if want is None:
        raise ValueError(f"Invalid PCI hardware ID: {nic!r}")
    if instance is not None and not NIC_INSTANCE_RE.match(instance):
        raise ValueError(f"Invalid device instance ID: {instance!r}")
    ven, dev, sub, rev = want.groups()
    blocks = _reg_blocks(export)
    # upper-case hardware ID -> {upper-case instance: (key path, has a driver service)}
    devices: dict[str, dict[str, tuple[str, bool]]] = {}
    for path, values in blocks:
        head, marker, rest = path.partition("\\Enum\\PCI\\")
        parts = rest.split("\\")
        if not marker or len(parts) < 2:
            continue
        hwid, inst = parts[0].upper(), parts[1].upper()
        key = f"{head}\\Enum\\PCI\\{parts[0]}\\{parts[1]}"
        known = devices.setdefault(hwid, {})
        has_service = any(v.startswith('"Service"=') for v in values) if len(parts) == 2 else False
        old = known.get(inst)
        known[inst] = (key, (old[1] if old else False) or has_service)
    mine = devices.get(nic.upper(), {})
    if instance is None and mine:
        return None, None                      # the card is known; which instance is not checked
    if instance is not None and instance.upper() in mine:
        return None, None
    candidates = [(hwid, inst, key) for hwid, insts in devices.items() for inst, (key, svc) in insts.items()
                  if svc and (m := NIC_ID_RE.match(hwid)) and m.group(1) == ven and m.group(2) == dev]
    if not candidates:
        return None, f"the image has no driver for the boot network card PCI\\{nic}"
    candidates.sort(key=lambda c: (c[0] != nic.upper(), NIC_ID_RE.match(c[0]).group(3) != sub, c[0], c[1]))
    source, source_inst, prefix = candidates[0]
    _, _, old_sub, old_rev = NIC_ID_RE.match(source).groups()
    swaps = [(source, nic), (f"SUBSYS_{old_sub}", f"SUBSYS_{sub}"), (f"REV_{old_rev}", f"REV_{rev}")]
    if instance is not None:
        targets = [instance]
    else:
        targets = [prefix.rsplit("\\", 1)[1]]
        if ven == "10EC" and targets[0].upper() != REALTEK_DSN_INSTANCE:
            targets.append(REALTEK_DSN_INSTANCE)
    base = prefix[: prefix.upper().index("\\ENUM\\PCI\\")] + "\\Enum\\PCI\\" + nic
    # hivexregedit creates a key only under an existing one: the card's key first.
    lines: list[str] = [] if mine else [f"[{base}]"]
    for target in targets:
        for path, values in blocks:
            if path.upper() != prefix.upper() and not path.upper().startswith(prefix.upper() + "\\"):
                continue
            new_path = f"{base}\\{target}{path[len(prefix):]}"
            lines += ["", f"[{new_path}]", *(_swap_ids(v, swaps) for v in values)]
    return "\n".join(lines).lstrip("\n"), None


def _hex(kind: str, data: bytes) -> str:
    return f"{kind}:" + ",".join(f"{b:02x}" for b in data)


def agent_service_patch(control_set: int) -> list[str]:
    """The agent's service as install.ps1 creates it, and Fast Startup off."""
    cs = f"\\ControlSet{control_set:03d}"
    return [
        "", f"[{cs}\\Services\\{AGENT_SERVICE}]",
        '"Type"=dword:00000010',            # own process
        '"Start"=dword:00000002',           # automatic
        '"ErrorControl"=dword:00000001',
        f'"ImagePath"={_hex("hex(2)", (AGENT_IMAGE_PATH + chr(0)).encode("utf-16-le"))}',
        '"ObjectName"="LocalSystem"',
        '"DisplayName"="ggNet agent"',
        '"Description"="Connects the ggNet game disk over iSCSI and reports to the ggNet server."',
        f'"FailureActions"={_hex("hex", AGENT_FAILURE_ACTIONS)}',
        # "Shut down" with Fast Startup is a hibernation: the server would not see a new boot.
        "", f"[{cs}\\Control\\Session Manager\\Power]",
        '"HiberbootEnabled"=dword:00000000',
    ]


HIGH_PERFORMANCE = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
BALANCED = "381b4222-f694-41f0-9685-ff5bb260df2e"
# (subgroup, setting) of the power plan, all set to 0 on AC and DC, as
# `powercfg /setacvalueindex` stores them.
POWER_SETTINGS = (
    ("238c9fa8-0aad-41ed-83f4-97be242c8f20", "29f6c1db-86da-48c5-9fdb-f2b67b1f44da"),  # sleep after: never
    ("238c9fa8-0aad-41ed-83f4-97be242c8f20", "9d7815a6-7ee4-497e-8888-515a05f02364"),  # hibernate after: never
    ("238c9fa8-0aad-41ed-83f4-97be242c8f20", "94ac6d29-73ce-41a6-809f-6363ba21b47e"),  # hybrid sleep: off
    ("7516b95f-f776-4464-8c53-06167f40cc99", "3c0bc021-c8a8-4e07-a973-6b14cbcb2b7e"),  # display off after: never
    ("0012ee47-9041-4b5d-9b77-535fba8b1442", "6738e2c4-e8a5-4a42-b16a-e040e769756e"),  # disk off after: never
    ("501a4d13-42af-4429-9fd1-a8218c268e20", "ee12f906-d277-404b-b6da-e5fa1a576df5"),  # PCIe ASPM: off
    ("2a737441-1930-4402-8d77-b2bebba308a3", "48e6b7a6-50f5-4782-a5d4-53bb8f07e226"),  # USB selective suspend: off
)
PAGE_FILE_MB = 4096
# Services that write to the disk all day for nothing: the writeback is
# discarded at every restart (search index, prefetch training).
IDLE_WRITERS = ("WSearch", "SysMain")
NET_CLASS = "{4d36e972-e325-11ce-bfc1-08002be10318}"
# Network card power saving that drops or slows the link the C: disk runs
# over (Realtek and Intel keywords); set to "0" where the driver has them.
# Wake-on-LAN is left alone.
NIC_POWER_SAVING = ("*EEE", "AdvancedEEE", "EEELinkAdvertisement", "EnableGreenEthernet",
                    "GigaLite", "PowerSavingMode", "*SelectiveSuspend")
_NET_ADAPTER_RE = re.compile(r"\\Control\\Class\\" + re.escape(NET_CLASS) + r"\\(\d{4})$", re.I)


def _nic_lines(cs: str, export: str) -> list[str]:
    """Power saving keywords off on every network adapter that has them."""
    lines: list[str] = []
    for path, values in _reg_blocks(export):
        m = _NET_ADAPTER_RE.search(path)
        if not m:
            continue
        names = [n for n in NIC_POWER_SAVING if any(v.partition("=")[0].strip('"') == n for v in values)]
        if names:
            lines += ["", f"[{cs}\\Control\\Class\\{NET_CLASS}\\{m.group(1)}]",
                      *(f'"{n}"="0"' for n in names)]
    return lines


# The iSCSI initiator's own load-order group. For an iSCSI boot the network
# groups load before the storage drivers, and the initiator right after them.
ISCSI_GROUP = "ggNet iSCSI"
NETWORK_GROUPS = ("NDIS Wrapper", "NDIS", "Base", "PNP_TDI")
_STORAGE_GROUP = "SCSI miniport"


def group_order_lines(cs: str, export: str) -> list[str]:
    """
    Load the network stack, then the iSCSI initiator, before the storage
    drivers. Windows loads the initiator with the storage drivers, before
    NDIS and TCP/IP, so on an iSCSI boot it retries setting up its portal
    (iScsiPrt event 5, 0xC0000207) ten times, 3 s apart, before its iBF
    bootstrap: 30 s of every boot. With NETWORK_GROUPS moved ahead of
    "SCSI miniport" and the initiator in its own group right after them, it
    finds TCP/IP ready and logs in at once (measured: 30 s -> 4 s).
    `export` is a `hivexregedit --export` of Control\\ServiceGroupOrder;
    nothing is changed when it cannot be read or lacks a group.
    """
    raw = next((v.partition("=")[2] for _, values in _reg_blocks(export) for v in values
                if v.startswith('"List"=hex(7):')), None)
    if raw is None:
        return []
    try:
        groups = bytes(int(x, 16) for x in raw[7:].split(",") if x).decode("utf-16-le").split("\0")
    except ValueError:
        return []
    groups = [g for g in groups if g]
    if _STORAGE_GROUP not in groups or any(g not in groups for g in NETWORK_GROUPS):
        return []
    moved = (*NETWORK_GROUPS, ISCSI_GROUP)
    groups = [g for g in groups if g not in moved]
    at = groups.index(_STORAGE_GROUP)
    groups[at:at] = moved
    data = ("\0".join(groups) + "\0\0").encode("utf-16-le")
    return [
        "", f"[{cs}\\Control\\ServiceGroupOrder]", f'"List"={_hex("hex(7)", data)}',
        "", f"[{cs}\\Services\\iScsiPrt]", f'"Group"={_reg_string(ISCSI_GROUP)}',
    ]


# Drivers and services of other diskless systems. In an image made for one of
# them they sit in the way of the disk and the network card (a CCBoot image
# has its cache driver above every volume and its own filter on every network
# card) and stop Windows booting over plain iSCSI (0x7B). Prepare image turns
# them off and takes them out of the device classes' filter lists.
FOREIGN_DISKLESS = (
    "CCacheX", "CCBootPNPX", "CCBootPNP", "CCopyFile", "CCBootClient",     # CCBoot
)
_CLASS_KEY = re.compile(r"\\Control\\Class\\(\{[0-9A-Fa-f-]{36}\})$")


def _multi_sz(line: str) -> list[str] | None:
    """The strings of a .reg REG_MULTI_SZ line (hex(7)), or None."""
    raw = line.partition("=")[2]
    if not raw.startswith("hex(7):"):
        return None
    try:
        return [s for s in bytes(int(x, 16) for x in raw[7:].split(",") if x).decode("utf-16-le").split("\0") if s]
    except ValueError:
        return None


def foreign_filter_lines(cs: str, class_export: str, foreign: Sequence[str]) -> list[str]:
    """
    The device classes' UpperFilters/LowerFilters without the `foreign`
    drivers; `class_export` is a `hivexregedit --export` of Control\\Class.
    A list left empty is deleted.
    """
    gone = {f.lower() for f in foreign}
    lines: list[str] = []
    for path, values in _reg_blocks(class_export):
        m = _CLASS_KEY.search(path)
        if not m:
            continue
        changed = []
        for v in values:
            name = v.partition("=")[0]
            if name not in ('"UpperFilters"', '"LowerFilters"'):
                continue
            items = _multi_sz(v)
            if items is None or not any(i.lower() in gone for i in items):
                continue
            kept = [i for i in items if i.lower() not in gone]
            data = ("\0".join(kept) + "\0\0").encode("utf-16-le")
            changed.append(f"{name}={_hex('hex(7)', data)}" if kept else f"{name}=-")
        if changed:
            lines += ["", f"[{cs}\\Control\\Class\\{m.group(1)}]", *changed]
    return lines


def nic_services(enum_pci_export: str) -> list[str]:
    """The drivers of the image's PCI network cards (the services of Net class devices)."""
    found: list[str] = []
    for _, values in _reg_blocks(enum_pci_export):
        text = {v.partition("=")[0].strip('"'): v.partition("=")[2] for v in values}
        cls = _reg_text(text.get("ClassGUID", ""))
        service = _reg_text(text.get("Service", ""))
        if cls.lower() == NET_CLASS and service and service not in found:
            found.append(service)
    return found


def _reg_text(data: str) -> str:
    """A .reg string value (quoted, or hex(1)/hex(2) UTF-16) as text; "" when unreadable."""
    if data.startswith('"') and data.endswith('"'):
        return data[1:-1].replace("\\\\", "\\")
    m = re.match(r"^hex\((?:1|2)\):([0-9a-fA-F,]*)$", data)
    if not m:
        return ""
    try:
        return bytes(int(x, 16) for x in m.group(1).split(",") if x).decode("utf-16-le").rstrip("\0")
    except ValueError:
        return ""


def diskless_boot_lines(control_set: int, class_export: str, enum_pci_export: str,
                        foreign: Sequence[str]) -> list[str]:
    """
    SYSTEM hive lines so the image boots over plain iSCSI: other diskless
    systems' drivers off and out of the filter lists, and the network cards'
    drivers marked for a network boot (BootFlags 1, as Windows marks the card
    it was installed to boot from), so Windows loads the PC's card early.
    """
    cs = f"\\ControlSet{control_set:03d}"
    lines = foreign_filter_lines(cs, class_export, foreign)
    for name in foreign:
        lines += ["", f"[{cs}\\Services\\{name}]", '"Start"=dword:00000004']
    for service in nic_services(enum_pci_export):
        lines += ["", f"[{cs}\\Services\\{service}]", '"BootFlags"=dword:00000001']
    return lines


def tuning_patch(control_set: int, net_class_export: str = "", group_order_export: str = "") -> list[str]:
    """
    SYSTEM hive lines for a diskless PC: High performance with nothing ever
    going to sleep (the display included; shutting idle PCs down is the cafe
    software's), no hibernation or Fast Startup, a fixed 4 GB page file that
    is not wiped at shutdown, no crash dumps (the dump driver cannot write
    over iSCSI), no search index or SysMain, the network cards' power saving
    off, and the iSCSI boot without its 30 s wait (group_order_lines;
    WaitForNetworkAtBoot 0, no duplicate address check on the boot address,
    no DHCP media sense).
    """
    cs = f"\\ControlSet{control_set:03d}"
    schemes = f"{cs}\\Control\\Power\\User\\PowerSchemes"
    lines = ["", f"[{schemes}]", f'"ActivePowerScheme"="{HIGH_PERFORMANCE}"']
    for scheme in (HIGH_PERFORMANCE, BALANCED):
        lines += ["", f"[{schemes}\\{scheme}]"]
        # hivexregedit creates a key only under an existing one: parents first.
        for subgroup in dict.fromkeys(s for s, _ in POWER_SETTINGS):
            lines += ["", f"[{schemes}\\{scheme}\\{subgroup}]"]
            for setting in (t for s, t in POWER_SETTINGS if s == subgroup):
                lines += ["", f"[{schemes}\\{scheme}\\{subgroup}\\{setting}]",
                          '"ACSettingIndex"=dword:00000000', '"DCSettingIndex"=dword:00000000']
    page_files = f"c:\\pagefile.sys {PAGE_FILE_MB} {PAGE_FILE_MB}\0\0".encode("utf-16-le")
    lines += [
        "", f"[{cs}\\Control\\Power]",
        '"HibernateEnabled"=dword:00000000',
        '"HibernateEnabledDefault"=dword:00000000',
        "", f"[{cs}\\Control\\Session Manager\\Power]",
        '"HiberbootEnabled"=dword:00000000',
        "", f"[{cs}\\Control\\Session Manager\\Memory Management]",
        f'"PagingFiles"={_hex("hex(7)", page_files)}',
        '"ClearPageFileAtShutdown"=dword:00000000',
        "", f"[{cs}\\Control\\CrashControl]",
        '"CrashDumpEnabled"=dword:00000000',
        "", f"[{cs}\\Services\\iScsiPrt\\Parameters]",
        '"WaitForNetworkAtBoot"=dword:00000000',
        '"DelayForNetworkAtBoot"=dword:00000001',
        "", f"[{cs}\\Services\\Tcpip\\Parameters]",
        '"ArpRetryCount"=dword:00000000',
        '"DisableDhcpMediaSense"=dword:00000001',
    ]
    lines += group_order_lines(cs, group_order_export)
    for service in IDLE_WRITERS:
        lines += ["", f"[{cs}\\Services\\{service}]", '"Start"=dword:00000004']
    return lines + _nic_lines(cs, net_class_export)


def software_patch() -> str:
    """
    SOFTWARE hive .reg for a diskless PC: no automatic Windows Update (the
    image is updated on a PC with Keep writeback, then applied; drivers from
    Windows Update could replace the boot network card's), no automatic Store
    app updates, and no automatic maintenance (defragmentation and the like).
    """
    # A fresh Windows has no WindowsUpdate or WindowsStore policy keys yet:
    # each key's parent comes first (hivexregedit creates only one level).
    return "\n".join([
        "Windows Registry Editor Version 5.00",
        "", "[\\Policies\\Microsoft]",
        "", "[\\Policies\\Microsoft\\Windows]",
        "", "[\\Policies\\Microsoft\\Windows\\WindowsUpdate]",
        '"ExcludeWUDriversInQualityUpdate"=dword:00000001',
        "", "[\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU]",
        '"NoAutoUpdate"=dword:00000001',
        "", "[\\Policies\\Microsoft\\WindowsStore]",
        '"AutoDownload"=dword:00000002',
        "", "[\\Microsoft\\Windows NT\\CurrentVersion\\Schedule]",
        "", "[\\Microsoft\\Windows NT\\CurrentVersion\\Schedule\\Maintenance]",
        '"MaintenanceDisabled"=dword:00000001',
    ]) + "\n"


# Microsoft Defender's services and drivers: the engine, network inspection,
# its file system filter, its early-launch driver, Defender for Endpoint and
# the newer core service. Only those in the image are touched.
DEFENDER_SERVICES = ("WinDefend", "WdNisSvc", "WdNisDrv", "WdFilter", "WdBoot", "Sense", "MDCoreSvc")


def defender_off_lines(control_set: int, present: Sequence[str]) -> str:
    """
    SYSTEM hive .reg that keeps Defender from starting: its services and
    drivers disabled. Written offline, so Tamper Protection (which guards
    these keys while Windows runs) cannot undo it. A diskless PC loses
    everything at restart anyway; nothing scans or rebuilds its cache at boot.
    """
    cs = f"\\ControlSet{control_set:03d}"
    lines = ["Windows Registry Editor Version 5.00"]
    for name in present:
        if name not in DEFENDER_SERVICES:
            raise ValueError(f"Not a Defender service: {name!r}")
        lines += ["", f"[{cs}\\Services\\{name}]", '"Start"=dword:00000004']
    return "\n".join(lines) + "\n"


def defender_policy_patch() -> str:
    """SOFTWARE hive .reg: Defender's policies off, and no "protection is off" notifications."""
    return "\n".join([
        "Windows Registry Editor Version 5.00",
        "", "[\\Policies\\Microsoft]",
        "", "[\\Policies\\Microsoft\\Windows Defender]",
        '"DisableAntiSpyware"=dword:00000001',
        "", "[\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection]",
        '"DisableRealtimeMonitoring"=dword:00000001',
        '"DisableOnAccessProtection"=dword:00000001',
        '"DisableScanOnRealtimeEnable"=dword:00000001',
        "", "[\\Policies\\Microsoft\\Windows Defender\\Spynet]",
        '"SpynetReporting"=dword:00000000',
        '"SubmitSamplesConsent"=dword:00000002',
        "", "[\\Policies\\Microsoft\\Windows Defender Security Center]",
        "", "[\\Policies\\Microsoft\\Windows Defender Security Center\\Notifications]",
        '"DisableNotifications"=dword:00000001',
    ]) + "\n"


def _cleanup_lines(cs: str, dhcp_interfaces: Sequence[str], forget_letters: Sequence[str]) -> list[str]:
    """Fixed addresses to DHCP, and every letter but C: forgotten."""
    lines: list[str] = []
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
    return lines


def image_patch(control_set: int, dhcp_interfaces: Sequence[str] = (), forget_letters: Sequence[str] = (),
                agent_service: bool = False, tuning: bool = False, net_class_export: str = "",
                group_order_export: str = "") -> str:
    """The .reg text prepare_image() merges into an image's SYSTEM hive."""
    cs = f"\\ControlSet{control_set:03d}"
    lines = ["Windows Registry Editor Version 5.00"]
    lines += _cleanup_lines(cs, dhcp_interfaces, forget_letters)
    if agent_service:
        lines += agent_service_patch(control_set)
    if tuning:
        lines += tuning_patch(control_set, net_class_export, group_order_export)
    return "\n".join(lines) + "\n"


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
    lines += _cleanup_lines(cs, dhcp_interfaces, forget_letters)
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

    def personalize(self, device: str, setup: OsSetup, label: str | None = None) -> str | None:
        """
        Write the PC's identity into its OS clone. None when done, else why
        not. `label` names the mount and .reg file (default: the computer
        name); a PC's spare writeback is set up under its own label, so it
        never shares them with a reset of the PC's writeback.
        """
        try:
            registry_patch(setup, 1)   # validate before touching the host
            if setup.boot_nic and not NIC_ID_RE.match(setup.boot_nic):
                raise ValueError(f"Invalid PCI hardware ID: {setup.boot_nic!r}")
            if setup.boot_nic_instance and not NIC_INSTANCE_RE.match(setup.boot_nic_instance):
                raise ValueError(f"Invalid device instance ID: {setup.boot_nic_instance!r}")
        except ValueError as e:
            return str(e)
        try:
            name = label or setup.computer_name
            return self._on_windows(device, name, lambda root, hive: self._merge(hive, setup, name))
        except Exception as e:     # never fail the provisioning it is part of
            logger.exception("Setting up Windows on %s failed", device)
            return f"unexpected error: {e}"

    def prepare_image(self, device: str, prep: ImagePrep, label: str = "image") -> str | None:
        """
        Make an OS clone that is about to become an image version ready for
        every PC (see the module doc). None when done, else why not.
        """
        try:
            return self._on_windows(device, f"prepare-{label}", lambda root, hive: self._prepare(root, hive, prep))
        except Exception as e:     # never fail the apply it is part of
            logger.exception("Preparing the image on %s failed", device)
            return f"unexpected error: {e}"

    def nic_support(self, device: str, nics: Sequence[tuple[str, str | None]]
                    ) -> dict[tuple[str, str | None], str] | str:
        """
        Whether the Windows on `device` can boot PCs with these boot network
        cards, each a (PCI hardware ID, instance ID or None): "ready" when it
        knows the card (under that instance, when known), "added" when it
        knows the chip under another revision, board or instance (personalize
        adds the card at every boot), "missing" when it has no driver for it.
        A string says why it could not be read. Mounted read-only.
        """
        result: dict[tuple[str, str | None], str] = {}

        def work(root: Path, hive: Path) -> str | None:
            export = self.enum_pci(hive, self.control_set(hive))
            if export is None:
                return "the image's PCI devices cannot be read"
            for nic, instance in nics:
                lines, missing = nic_patch(export, nic, instance)
                result[(nic, instance)] = "missing" if missing else "added" if lines else "ready"
            return None

        for nic, instance in nics:
            if not NIC_ID_RE.match(nic) or (instance is not None and not NIC_INSTANCE_RE.match(instance)):
                return f"Invalid network card: {nic!r} {instance!r}"
        try:
            problem = self._on_windows(device, "hardware-check", work, readonly=True)
        except Exception as e:
            logger.exception("Checking the hardware of %s failed", device)
            return f"unexpected error: {e}"
        return problem or result

    def _on_windows(self, device: str, name: str, work: Callable[[Path, Path], str | None],
                    readonly: bool = False) -> str | None:
        """Mount the disk's Windows partition and run `work(root, SYSTEM hive)` on it."""
        parts = self.ntfs_partitions(device)
        if not parts:
            return f"no Windows partition found on {device}"
        mount = self.run_dir / name
        reasons = []
        for part in parts:
            try:
                mount.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                return f"cannot create {mount}: {e}"
            ok, _, err = self._run(["ntfs-3g", "-o", "ro" if readonly else "rw,noatime", part, str(mount)])
            if not ok:
                reasons.append(f"{part}: {err.strip() or 'mount failed'}")
                continue
            try:
                hive = _find(mount, HIVE)
                if hive is None:
                    reasons.append(f"{part}: no Windows on it")
                    continue
                return work(mount, hive)
            finally:
                if not self._run(["umount", str(mount)])[0]:
                    logger.error("Could not unmount %s", mount)
                try:
                    mount.rmdir()
                except OSError:
                    pass
        return "; ".join(reasons)

    def _install_agent(self, root: Path, agent: AgentInstall) -> tuple[bool, str | None]:
        """
        The server's agent into the mounted Windows: (whether the service can
        be registered, why not). The file is written only when it differs.
        """
        program_files = _find_dir(root, AGENT_DIR[:1])
        if program_files is None:
            return False, "no Program Files folder in the image"
        folder = _find_dir(program_files, AGENT_DIR[1:]) or program_files / AGENT_DIR[1]
        exe = folder / AGENT_EXE
        try:
            folder.mkdir(exist_ok=True)
            if not _same_file(exe, agent.exe, agent.sha256):
                tmp = folder / f"{AGENT_EXE}.new"
                shutil.copyfile(agent.exe, tmp)
                os.replace(tmp, exe)
                logger.info("Agent copied into the image")
            settings = folder / "appsettings.json"
            if not settings.exists():
                settings.write_text(json.dumps(agent_settings(agent.server_url), indent=2), encoding="utf-8")
        except OSError as e:
            return exe.is_file(), f"copying the agent failed: {e}"
        return True, None

    def _merge_reg(self, hive: Path, name: str, patch: str) -> str | None:
        reg = self.run_dir / f"{name}.reg"
        try:
            reg.write_text(patch, encoding="utf-8")
            ok, _, err = self._run(["hivexregedit", "--merge", str(hive), str(reg)])
        finally:
            reg.unlink(missing_ok=True)
        return None if ok else f"editing the registry failed: {err.strip()}"

    def net_class(self, hive: Path, control_set: int) -> str:
        """The network adapters' class key as .reg text; empty when unreadable."""
        key = f"\\ControlSet{control_set:03d}\\Control\\Class\\{NET_CLASS}"
        ok, out, _ = self._run(["hivexregedit", "--export", str(hive), key], quiet=True)
        return out if ok else ""

    def group_order(self, hive: Path, control_set: int) -> str:
        """The driver load-order groups as .reg text; empty when unreadable."""
        key = f"\\ControlSet{control_set:03d}\\Control\\ServiceGroupOrder"
        ok, out, _ = self._run(["hivexregedit", "--export", str(hive), key], quiet=True)
        return out if ok else ""

    def _prepare(self, root: Path, hive: Path, prep: ImagePrep) -> str | None:
        agent_ok, agent_problem = self._install_agent(root, prep.agent) if prep.agent else (False, None)
        control_set = self.control_set(hive)
        fixed = self.static_interfaces(hive, control_set)
        letters = self.reserved_letters(hive)
        nics = self.net_class(hive, control_set) if prep.tuning else ""
        order = self.group_order(hive, control_set) if prep.tuning else ""
        problem = self._merge_reg(hive, "prepare", image_patch(control_set, fixed, letters, agent_ok,
                                                               prep.tuning, nics, order))
        tuning_problem = self._tune_software(root) if prep.tuning and problem is None else None
        diskless_problem = self._diskless_boot(hive, control_set) if prep.tuning and problem is None else None
        defender_problem = self._defender_off(root, hive, control_set) \
            if prep.defender_off and problem is None else None
        if problem is None:
            logger.info("Image prepared (agent: %s, diskless tuning: %s, Defender off: %s, DHCP: %s, "
                        "letters forgotten: %s)",
                        "yes" if agent_ok else "no", "yes" if prep.tuning and not tuning_problem else "no",
                        "yes" if prep.defender_off and not defender_problem else "no",
                        ", ".join(fixed) or "-", ", ".join(letters) or "-")
        return "; ".join(p for p in (problem, agent_problem, tuning_problem, diskless_problem, defender_problem)
                         if p) or None

    def _has_key(self, hive: Path, key: str) -> bool:
        ok, out, _ = self._run(["hivexregedit", "--export", str(hive), key], quiet=True)
        return ok and f"[{key}]".lower() in out.lower()

    def _diskless_boot(self, hive: Path, control_set: int) -> str | None:
        """Other diskless systems' drivers off and out of the way; network card drivers marked for a network boot."""
        cs = f"\\ControlSet{control_set:03d}"
        foreign = [name for name in FOREIGN_DISKLESS if self._has_key(hive, f"{cs}\\Services\\{name}")]
        ok, classes, _ = self._run(["hivexregedit", "--export", str(hive), f"{cs}\\Control\\Class"], quiet=True)
        enum = self.enum_pci(hive, control_set) or ""
        lines = diskless_boot_lines(control_set, classes if ok else "", enum, foreign)
        if not lines:
            return None
        problem = self._merge_reg(hive, "prepare-diskless", "\n".join(["Windows Registry Editor Version 5.00", *lines]) + "\n")
        if problem:
            return f"diskless boot: {problem}"
        if foreign:
            logger.info("Other diskless systems' drivers turned off in the image: %s", ", ".join(foreign))
        return None

    def _defender_off(self, root: Path, hive: Path, control_set: int) -> str | None:
        """Defender's services and drivers disabled (SYSTEM), its policies off (SOFTWARE)."""
        present = [name for name in DEFENDER_SERVICES
                   if self._run(["hivexregedit", "--export", str(hive),
                                 f"\\ControlSet{control_set:03d}\\Services\\{name}"], quiet=True)[0]]
        problem = self._merge_reg(hive, "prepare-defender", defender_off_lines(control_set, present))
        if problem:
            return f"Defender: {problem}"
        software = _find(root, SOFTWARE_HIVE)
        if software is None:
            return "Defender: no SOFTWARE hive in the image"
        problem = self._merge_reg(software, "prepare-defender-policy", defender_policy_patch())
        logger.info("Defender turned off in the image (%s)", ", ".join(present) or "no services found")
        return f"Defender: {problem}" if problem else None

    def _tune_software(self, root: Path) -> str | None:
        """The SOFTWARE hive's part of the tuning, and the hibernation file gone."""
        hiberfil = _find(root, ("hiberfil.sys",))
        if hiberfil is not None and hiberfil.is_file():
            try:
                hiberfil.unlink()
            except OSError as e:
                logger.warning("Could not delete %s: %s", hiberfil, e)
        software = _find(root, SOFTWARE_HIVE)
        if software is None:
            return "no SOFTWARE hive in the image"
        return self._merge_reg(software, "prepare-software", software_patch())

    def _merge(self, hive: Path, setup: OsSetup, name: str | None = None) -> str | None:
        control_set = self.control_set(hive)
        fixed = self.static_interfaces(hive, control_set)
        letters = self.reserved_letters(hive)
        nic_reg, nic_problem = None, None
        if setup.boot_nic:
            export = self.enum_pci(hive, control_set)
            if export is None:
                nic_problem = "cannot read the image's PCI devices"
            else:
                nic_reg, nic_problem = nic_patch(export, setup.boot_nic, setup.boot_nic_instance)
        patch = registry_patch(setup, control_set, fixed, letters, nic_reg)
        problem = self._merge_reg(hive, name or setup.computer_name, patch)
        if problem:
            return problem
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


def agent_settings(server_url: str) -> dict:
    """appsettings.json as install.ps1 writes it (Boot Mode: the game disk is D:)."""
    return {
        "Agent": {
            "ServerUrl": server_url.rstrip("/"),
            "DriveLetter": "D",
            "HeartbeatSeconds": 30,
            "ManageInitiatorName": True,
            "HideLocalDisks": True,
        },
        "Logging": {"EventLog": {"LogLevel": {
            "Default": "Information", "Microsoft": "Warning", "System.Net.Http.HttpClient": "Warning"}}},
    }


def _same_file(path: Path, source: Path, sha256: str) -> bool:
    """Whether `path` already holds the source (size first, then the checksum)."""
    try:
        if not path.is_file() or path.stat().st_size != source.stat().st_size:
            return False
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest() == sha256
    except OSError:
        return False


def _find_dir(root: Path, parts: tuple[str, ...]) -> Path | None:
    """root/parts as directories, without regard to case (as Windows does)."""
    path = root
    for name in parts:
        exact = path / name
        if exact.is_dir():
            path = exact
            continue
        try:
            match = next((p for p in path.iterdir() if p.name.lower() == name.lower() and p.is_dir()), None)
        except OSError:
            return None
        if match is None:
            return None
        path = match
    return path


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
