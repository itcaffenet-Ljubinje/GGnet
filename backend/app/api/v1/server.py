"""
API for the Server page: the ZFS pool, its disks, the RAM cache and the
writebacks' total (app.services.server_status). Read-only, except starting
or stopping a scrub.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.api.deps import get_provisioner, get_server_monitor
from app.api.v1.errors import host_failed
from app.api.v1.schemas import (
    ArcOut,
    MemoryOut,
    PoolDiskOut,
    PoolGroupOut,
    PoolOut,
    PoolScanOut,
    ScrubIn,
    ServerOut,
)
from app.services.provisioning import Provisioner
from app.services.server_status import ServerMonitor, disk_device

router = APIRouter(prefix="/server", tags=["server"])


def _time(ts: int | None) -> datetime | None:
    return datetime.fromtimestamp(ts, timezone.utc) if ts else None


def _pool(mon: ServerMonitor) -> PoolOut | None:
    p = mon.pool()
    if p is None:
        return None
    disks = []
    for d in p["disks"]:
        device = disk_device(d["path"])
        s = mon.smart(device) if device else {}
        disks.append(PoolDiskOut(
            name=d["name"], group=d["group"], state=d["state"],
            read_errors=d["read_errors"], write_errors=d["write_errors"],
            checksum_errors=d["checksum_errors"],
            trim_state=d["trim_state"], trim_time=_time(d["trim_time"]),
            trim_supported=not d["trim_notsup"],
            smart_passed=s.get("passed"), model=s.get("model"), serial=s.get("serial"),
            capacity_bytes=s.get("capacity"), temperature=s.get("temperature"),
            wear_percent=s.get("wear_percent"), power_on_hours=s.get("power_on_hours"),
        ))
    trims = [d.trim_time for d in disks if d.trim_supported]
    scan = p["scan"]
    return PoolOut(
        name=p["name"], state=p["state"], size_bytes=p["size"], allocated_bytes=p["allocated"],
        free_bytes=p["free"], fragmentation=p["fragmentation"], capacity=p["capacity"],
        errors=p["errors"],
        scan=PoolScanOut(**{**scan, "start_time": _time(scan["start_time"]),
                            "end_time": _time(scan["end_time"])}) if scan else None,
        # The pool counts as trimmed when its least recently trimmed disk was.
        last_trim=None if not trims or None in trims else min(trims),
        groups=[PoolGroupOut(**g) for g in p["groups"]],
        disks=disks,
    )


@router.get("", response_model=ServerOut)
def get_server(
    mon: ServerMonitor = Depends(get_server_monitor),
    prov: Provisioner = Depends(get_provisioner),
):
    arc = mon.arc()
    mem = mon.memory()
    clones = prov.writebacks()
    lookups = arc["hits"] + arc["misses"] if arc else 0
    return ServerOut(
        pool=_pool(mon),
        arc=ArcOut(size_bytes=arc["size"], max_bytes=arc["c_max"], min_bytes=arc["c_min"],
                   hit_percent=round(100 * arc["hits"] / lookups, 1) if lookups else None) if arc else None,
        memory=MemoryOut(total_bytes=mem["total"], available_bytes=mem["available"]) if mem else None,
        writebacks_bytes=sum(c["used"] for c in clones),
        writebacks_count=len(clones),
    )


@router.post("/scrub", response_model=ServerOut)
def scrub(
    body: ScrubIn,
    mon: ServerMonitor = Depends(get_server_monitor),
    prov: Provisioner = Depends(get_provisioner),
):
    """Start or stop a scrub of the pool. A scrub reads every block: PCs are slower meanwhile."""
    if not mon.scrub(body.action == "start"):
        host_failed(f"{'Starting' if body.action == 'start' else 'Stopping'} the scrub failed: {mon.last_error}")
    return get_server(mon, prov)
