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
from typing import Mapping, Optional

from app.runner import CommandRunner

logger = logging.getLogger("ggnet.windows")

DEFAULT_RUN_DIR = Path("/run/ggnet/windows")
HIVE = ("Windows", "System32", "config", "SYSTEM")
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,14}$")
_ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
_CURRENT_RE = re.compile(r'^"Current"=dword:([0-9a-fA-F]{8})\s*$', re.M)


@dataclass(frozen=True)
class OsSetup:
    """What a Boot Mode PC's Windows is told about itself."""

    computer_name: str                        # the machine name, [a-z0-9-], at most 15
    env: Mapping[str, str] = field(default_factory=dict)


def _reg_string(value: str) -> str:
    """A .reg string literal."""
    if any(c in value for c in "\r\n\0"):
        raise ValueError("registry strings must not contain line breaks or NUL")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def registry_patch(setup: OsSetup, control_set: int) -> str:
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

    def personalize(self, device: str, setup: OsSetup) -> str | None:
        """Write the PC's identity into its OS clone. None when done, else why not."""
        try:
            registry_patch(setup, 1)   # validate before touching the host
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
        patch = registry_patch(setup, self.control_set(hive))
        reg = self.run_dir / f"{setup.computer_name}.reg"
        try:
            reg.write_text(patch, encoding="utf-8")
            ok, _, err = self._run(["hivexregedit", "--merge", str(hive), str(reg)])
        finally:
            reg.unlink(missing_ok=True)
        if not ok:
            return f"editing the registry failed: {err.strip()}"
        logger.info("Windows on %s set up as %s", hive, setup.computer_name)
        return None


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
