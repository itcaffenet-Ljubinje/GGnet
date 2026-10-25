"""
Grow the data partition of a disk image after its zvol got bigger, offline on
the server, so Windows sees the new space without Disk Management:

  sgdisk -e <dev>                           backup GPT to the new end of the disk
  sfdisk --json <dev>                       partitions, read back
  sgdisk -d N -n N:<start>:0 -t -u -c <dev> the last partition, same start, type,
                                            GUID and name, up to the end
  blockdev --rereadpt <dev>; udevadm settle
  ntfsresize --no-action --force <part>     check, then the real run
  ntfsresize --force <part>

Only a last partition that is a Windows data partition (Microsoft basic data,
NTFS, no attributes) is grown. An OS image ends with its Recovery partition
behind C:, so it is left as it is and C: is extended in Windows instead.
The disk must not be in use: the caller grows a fresh clone.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass

logger = logging.getLogger("ggnet.grow")

BASIC_DATA = "EBD0A0A2-B9E5-4433-87C0-68B6B72699C7"
# Less free space than this behind the last partition is not worth a resize (1 MiB).
MIN_FREE_SECTORS = 2048
_PART_NODE = re.compile(r"p(\d+)$")


def _real_device(path: str) -> str:
    return os.path.realpath(path)


@dataclass
class GrowResult:
    extended: bool
    note: str        # what was done, or why the partition was left as it is


class PartitionGrower:
    def __init__(self, runner):
        self.runner = runner

    def _run(self, cmd: list[str], timeout: int | None = None) -> tuple[bool, str, str]:
        return self.runner.run(cmd, timeout=timeout)

    def extend_last(self, device: str) -> GrowResult:
        """Grow the last partition of `device` and its NTFS to the end of the disk."""
        # /dev/zvol/<pool>/... is a link to /dev/zdN, whose partitions are /dev/zdNpK.
        device = _real_device(device)
        ok, _, err = self._run(["sgdisk", "-e", device])
        if not ok:
            return GrowResult(False, f"the partition table could not be moved to the new end: {err}")
        ok, out, err = self._run(["sfdisk", "--json", device])
        if not ok:
            return GrowResult(False, f"the partition table could not be read: {err}")
        try:
            table = json.loads(out)["partitiontable"]
            parts = table["partitions"]
            last_lba = int(table["lastlba"])
        except (ValueError, KeyError, TypeError) as e:
            return GrowResult(False, f"the partition table could not be read: {e}")
        if table.get("label") != "gpt" or not parts:
            return GrowResult(False, "the disk has no GPT partitions")

        last = max(parts, key=lambda p: int(p["start"]))
        m = _PART_NODE.search(str(last.get("node", "")))
        if m is None:
            return GrowResult(False, f"unexpected partition name {last.get('node')!r}")
        number = int(m.group(1))
        start, size = int(last["start"]), int(last["size"])
        if str(last.get("type", "")).upper() != BASIC_DATA:
            return GrowResult(False, "the last partition is not a data partition (an OS image ends with "
                                     "its Recovery partition): extend the volume in Windows instead")
        if last.get("attrs"):
            return GrowResult(False, f"the last partition has attributes ({last['attrs']}); extend it in Windows")
        if last_lba - (start + size - 1) < MIN_FREE_SECTORS:
            return GrowResult(False, "there is no new space behind the last partition")

        cmd = ["sgdisk", "-d", str(number), "-n", f"{number}:{start}:0",
               "-t", f"{number}:{BASIC_DATA}", "-u", f"{number}:{last['uuid']}"]
        if last.get("name"):
            cmd += ["-c", f"{number}:{last['name']}"]
        ok, _, err = self._run(cmd + [device])
        if not ok:
            return GrowResult(False, f"the partition could not be grown: {err}")
        self._run(["blockdev", "--rereadpt", device])
        self._run(["udevadm", "settle"])

        part = f"{device}p{number}"
        ok, _, err = self._run(["ntfsresize", "--no-action", "--force", part], timeout=600)
        if not ok:
            return GrowResult(False, f"the partition is bigger, but NTFS refused the check: {err}")
        ok, _, err = self._run(["ntfsresize", "--force", part], timeout=3600)
        if not ok:
            return GrowResult(False, f"the partition is bigger, but NTFS could not be grown: {err}")
        logger.info("Partition %s of %s and its NTFS grown to the end of the disk", number, device)
        return GrowResult(True, "the data partition was extended to the new size")
