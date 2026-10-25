"""
The Server page: the ZFS pool (health, space, scrub, TRIM, each disk's
errors), the ZFS RAM cache (ARC), the host's memory and each pool disk's
SMART health. Everything is read-only except starting or stopping a scrub or a TRIM.

Sources (OpenZFS 2.3+ JSON output, smartctl 7.3+ JSON output):
  zpool status -t -j --json-int <pool>   state, scan, vdev tree, TRIM per disk
  zpool scrub [-s] / zpool trim [-s]     start or stop a scrub or a TRIM
  zpool list -j --json-int <pool>        size, allocated, free, fragmentation
  zpool get autotrim <pool>              whether ZFS trims freed blocks by itself
  /proc/spl/kstat/zfs/arcstats           ARC size, target max/min, hits, misses
  /proc/meminfo                          total and available RAM
  smartctl -j -H -A -i <disk>            passed, temperature, wear, power-on hours

SMART is read only when the admin asks (read_smart); the page shows the last
reading with its time. Its values change slowly, and asking every disk on
every page refresh is not free.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

from app.runner import CommandRunner

logger = logging.getLogger("ggnet.server")

_PART_RE = re.compile(r"-part\d+$")


def parse_pool(status_json: str, list_json: str, pool: str) -> dict[str, Any] | None:
    """The pool as the Server page shows it; None when the output is unusable."""
    try:
        status = json.loads(status_json)["pools"][pool]
        props = json.loads(list_json)["pools"][pool]["properties"]
    except (ValueError, KeyError, TypeError):
        return None

    def prop(name: str) -> Any:
        value = (props.get(name) or {}).get("value")
        return value if isinstance(value, int) else None

    root = (status.get("vdevs") or {}).get(pool) or {}
    groups, disks = [], []
    for group in (root.get("vdevs") or {}).values():
        members = list((group.get("vdevs") or {}).values()) or [group]   # a single disk is its own group
        groups.append({"name": group.get("name", "?"), "type": group.get("vdev_type", "?"),
                       "state": group.get("state", "?"),
                       "disks": [m.get("name", "?") for m in members]})
        for d in members:
            disks.append({
                "name": d.get("name", "?"),
                "group": group.get("name", "?"),
                "path": d.get("path"),
                "state": d.get("state", "?"),
                "read_errors": int(d.get("read_errors") or 0),
                "write_errors": int(d.get("write_errors") or 0),
                "checksum_errors": int(d.get("checksum_errors") or 0),
                "trim_state": d.get("trim_state"),
                "trim_percent": round(100 * d["trimmed"] / d["to_trim"], 1)
                if d.get("trim_state") == "ACTIVE" and d.get("to_trim") else None,
                "trim_time": d.get("trim_time") or None,
                "trim_notsup": bool(d.get("trim_notsup")),
            })
    scan = status.get("scan_stats") or {}
    to_examine = int(scan.get("to_examine") or 0)
    examined = int(scan.get("examined") or 0)
    return {
        "name": pool,
        "state": status.get("state", "?"),
        "size": prop("size"),
        "allocated": prop("allocated"),
        "free": prop("free"),
        "fragmentation": prop("fragmentation"),
        "capacity": prop("capacity"),
        "errors": int(status.get("error_count") or 0),
        "scan": {
            "function": (scan.get("function") or "").lower() or None,    # scrub | resilver
            "state": (scan.get("state") or "").lower() or None,          # scanning | finished | canceled
            "start_time": scan.get("start_time") or None,
            "end_time": scan.get("end_time") or None,
            "errors": int(scan.get("errors") or 0),
            "percent": round(100 * examined / to_examine, 1)
                       if to_examine and scan.get("state") == "SCANNING" else None,
            "paused": bool(scan.get("scrub_pause")),
        } if scan else None,
        "groups": groups,
        "disks": disks,
    }


def parse_arcstats(text: str) -> dict[str, int] | None:
    """ARC size, target max/min, hits and misses from /proc/spl/kstat/zfs/arcstats."""
    values: dict[str, int] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[1].isdigit():
            try:
                values[parts[0]] = int(parts[2])
            except ValueError:
                continue
    if "size" not in values or "c_max" not in values:
        return None
    return {k: values.get(k, 0) for k in ("size", "c_max", "c_min", "hits", "misses")}


def parse_meminfo(text: str) -> dict[str, int] | None:
    """Total and available RAM (bytes) from /proc/meminfo."""
    kb = {}
    for line in text.splitlines():
        m = re.match(r"^(\w+):\s+(\d+) kB$", line.strip())
        if m:
            kb[m.group(1)] = int(m.group(2))
    if "MemTotal" not in kb:
        return None
    return {"total": kb["MemTotal"] * 1024, "available": kb.get("MemAvailable", 0) * 1024}


def parse_smart(text: str) -> dict[str, Any]:
    """One disk's SMART summary; unknown values stay None (SAS, SATA and NVMe differ)."""
    try:
        d = json.loads(text)
    except ValueError:
        return {"passed": None}
    passed = (d.get("smart_status") or {}).get("passed")
    wear = (d.get("endurance_used") or {}).get("current_percent")
    if wear is None:
        wear = d.get("scsi_percentage_used_endurance_indicator")
    if wear is None:
        wear = (d.get("nvme_smart_health_information_log") or {}).get("percentage_used")
    return {
        "passed": passed if isinstance(passed, bool) else None,
        "model": d.get("model_name") or d.get("scsi_model_name"),
        "serial": d.get("serial_number"),
        "capacity": (d.get("user_capacity") or {}).get("bytes"),
        "temperature": (d.get("temperature") or {}).get("current"),
        "wear_percent": wear if isinstance(wear, int) else None,
        "power_on_hours": (d.get("power_on_time") or {}).get("hours"),
    }


def disk_device(path: str | None) -> str | None:
    """The whole disk behind a pool member (/dev/disk/by-id/x-part1 → /dev/disk/by-id/x)."""
    return _PART_RE.sub("", path) if path else None


GiB = 1024 ** 3
ARC_MAX_PARAM = Path("/sys/module/zfs/parameters/zfs_arc_max")
ZFS_MODPROBE = Path("/etc/modprobe.d/zfs.conf")
_ARC_MAX_RE = re.compile(r"\bzfs_arc_max=\d+")


def arc_limits(total_ram: int, arc_min: int) -> tuple[int, int]:
    """
    The RAM cache's allowed maximum, in bytes: at least 1 GiB and not under
    zfs_arc_min; at most the RAM minus what Proxmox and its VMs keep (16 GiB
    or a quarter of the RAM, whichever is more).
    """
    return max(GiB, arc_min), total_ram - max(16 * GiB, total_ram // 4)


def modprobe_with_arc_max(text: str, nbytes: int) -> str:
    """zfs.conf with zfs_arc_max set: changed on its active line(s), else added; other lines kept."""
    lines = text.splitlines()
    done = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("options zfs") and _ARC_MAX_RE.search(line):
            lines[i] = _ARC_MAX_RE.sub(f"zfs_arc_max={nbytes}", line)
            done = True
    if not done:
        lines.append(f"options zfs zfs_arc_max={nbytes}")
    return "\n".join(lines) + "\n"


class ServerMonitor:
    def __init__(self, pool: str, runner: Optional[CommandRunner] = None, proc: Path = Path("/proc"),
                 clock: Callable[[], float] = time.time, arc_param: Path = ARC_MAX_PARAM,
                 modprobe: Path = ZFS_MODPROBE):
        self.pool_name = pool
        self.runner = runner or CommandRunner(timeout=30)
        self.arc_param = arc_param
        self.modprobe = modprobe
        self.proc = proc
        self.clock = clock
        self._smart: dict[str, dict[str, Any]] = {}
        self.smart_read_at: float | None = None
        self._lock = threading.Lock()

    def pool(self) -> dict[str, Any] | None:
        ok, status, _ = self.runner.run(["zpool", "status", "-t", "-j", "--json-int", self.pool_name])
        if not ok:
            return None
        ok, listing, _ = self.runner.run(["zpool", "list", "-j", "--json-int", self.pool_name])
        if not ok:
            return None
        pool = parse_pool(status, listing, self.pool_name)
        if pool is not None:
            ok, out, _ = self.runner.run(["zpool", "get", "-H", "-o", "value", "autotrim", self.pool_name],
                                         quiet=True)
            pool["autotrim"] = {"on": True, "off": False}.get(out.strip()) if ok else None
        return pool

    def _read(self, *parts: str) -> str | None:
        try:
            return self.proc.joinpath(*parts).read_text()
        except OSError:
            return None

    def arc(self) -> dict[str, int] | None:
        text = self._read("spl", "kstat", "zfs", "arcstats")
        return parse_arcstats(text) if text else None

    def set_arc_max(self, nbytes: int) -> str | None:
        """
        Set the RAM cache's maximum now (the module parameter) and for the next
        boot (zfs.conf; the initramfs too when / is on ZFS). Returns why not,
        or None. The cache shrinks or grows to it over the next minutes.
        """
        try:
            self.arc_param.write_text(f"{nbytes}\n")
        except OSError as e:
            return f"the ZFS module refused the new maximum: {e}"
        try:
            old = self.modprobe.read_text() if self.modprobe.exists() else ""
            self.modprobe.write_text(modprobe_with_arc_max(old, nbytes))
        except OSError as e:
            return f"set for now, but {self.modprobe} could not be saved: {e}"
        ok, fstype, _ = self.runner.run(["findmnt", "-n", "-o", "FSTYPE", "/"], quiet=True)
        if ok and fstype.strip() == "zfs":
            ok, _, err = self.runner.run(["update-initramfs", "-u", "-k", "all"], timeout=600)
            if not ok:
                return f"set and saved, but the initramfs could not be updated: {err}"
        logger.info("RAM cache maximum set to %d bytes", nbytes)
        return None

    def memory(self) -> dict[str, int] | None:
        text = self._read("meminfo")
        return parse_meminfo(text) if text else None

    def smart(self, device: str) -> dict[str, Any]:
        """A disk's last SMART reading; empty until read_smart() ran."""
        with self._lock:
            return self._smart.get(device, {})

    def read_smart(self, devices: list[str]) -> None:
        """Ask every disk for its SMART data now."""
        readings = {}
        for device in devices:
            # smartctl's exit status is a bit mask (bit 3 and up: the disk
            # reports problems), so its JSON is read whatever it returns.
            _, out, _ = self.runner.run(["smartctl", "-j", "-H", "-A", "-i", device], quiet=True)
            readings[device] = parse_smart(out)
        with self._lock:
            self._smart = readings
            self.smart_read_at = self.clock()

    def _zpool(self, verb: str, start: bool) -> bool:
        cmd = ["zpool", verb, self.pool_name] if start else ["zpool", verb, "-s", self.pool_name]
        ok, _, _ = self.runner.run(cmd)
        if ok:
            logger.info("%s of %s %s", verb.capitalize(), self.pool_name, "started" if start else "stopped")
        return ok

    def scrub(self, start: bool) -> bool:
        return self._zpool("scrub", start)

    def trim(self, start: bool) -> bool:
        return self._zpool("trim", start)

    def scrub_pause(self) -> bool:
        """Pause the running scrub; the next `zpool scrub` resumes it where it stopped."""
        ok, _, _ = self.runner.run(["zpool", "scrub", "-p", self.pool_name])
        if ok:
            logger.info("Scrub of %s paused", self.pool_name)
        return ok

    @property
    def last_error(self) -> str:
        return self.runner.last_error
