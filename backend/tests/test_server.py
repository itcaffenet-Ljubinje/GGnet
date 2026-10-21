"""The Server page: pool, disks, SMART, RAM cache (app.services.server_status, /api/v1/server)."""

from __future__ import annotations

import json

import pytest

from app.api.deps import get_server_monitor
from app.main import app
from app.services.server_status import (
    ServerMonitor,
    disk_device,
    parse_arcstats,
    parse_meminfo,
    parse_pool,
    parse_smart,
)

from .conftest import FakeRunner

POOL = "tank"


def _disk(name: str, **extra) -> dict:
    return {"name": name, "vdev_type": "disk", "state": "ONLINE",
            "path": f"/dev/disk/by-id/scsi-{name}-part1",
            "read_errors": 0, "write_errors": 0, "checksum_errors": 0,
            "trim_state": "COMPLETE", "trim_time": 1782609164, "trim_notsup": 0, **extra}


# As `zpool status -t -j --json-int` prints it (OpenZFS 2.4), cut down to two mirrors.
STATUS = json.dumps({"output_version": {"command": "zpool status"}, "pools": {POOL: {
    "name": POOL, "state": "DEGRADED", "error_count": 0,
    "scan_stats": {"function": "SCRUB", "state": "SCANNING", "start_time": 1791671041, "end_time": 0,
                   "to_examine": 4000, "examined": 1000, "errors": 0, "scrub_pause": 0},
    "vdevs": {POOL: {"name": POOL, "vdev_type": "root", "state": "DEGRADED", "vdevs": {
        "mirror-0": {"name": "mirror-0", "vdev_type": "mirror", "state": "ONLINE", "vdevs": {
            "a1": _disk("a1"), "a2": _disk("a2")}},
        "mirror-1": {"name": "mirror-1", "vdev_type": "mirror", "state": "DEGRADED", "vdevs": {
            "b1": _disk("b1", checksum_errors=3),
            "b2": _disk("b2", state="FAULTED", trim_time=0, trim_state="UNTRIMMED")}},
    }}},
}}})
LIST = json.dumps({"pools": {POOL: {"properties": {
    "size": {"value": 10857677324288}, "allocated": {"value": 3790479101952},
    "free": {"value": 7067198222336}, "fragmentation": {"value": 22}, "capacity": {"value": 34},
    "health": {"value": "DEGRADED"}}}}})
ARCSTATS = """13 1 0x01 147 39984 4040563419 4302486183421061
name                            type data
hits                            4    95
misses                          4    5
c_min                           4    6333509632
c_max                           4    68719476736
size                            4    68708277664
"""
MEMINFO = "MemTotal:       197573400 kB\nMemFree:        72000000 kB\nMemAvailable:   87000000 kB\n"
SMART_SAS = json.dumps({
    "model_name": "TOSHIBA 5SRB384C EMC3840", "serial_number": "37P0A0GFT3EE",
    "user_capacity": {"bytes": 3840774504448}, "smart_status": {"passed": True},
    "temperature": {"current": 32}, "power_on_time": {"hours": 72361},
    "endurance_used": {"current_percent": 35},
})


def test_parse_pool_reads_the_tree_scan_and_space():
    p = parse_pool(STATUS, LIST, POOL)
    assert (p["state"], p["size"], p["free"], p["fragmentation"], p["capacity"]) == (
        "DEGRADED", 10857677324288, 7067198222336, 22, 34)
    assert p["scan"] == {"function": "scrub", "state": "scanning", "start_time": 1791671041,
                         "end_time": None, "errors": 0, "percent": 25.0, "paused": False}
    assert [(g["name"], g["state"], g["disks"]) for g in p["groups"]] == [
        ("mirror-0", "ONLINE", ["a1", "a2"]), ("mirror-1", "DEGRADED", ["b1", "b2"])]
    b1, b2 = p["disks"][2:]
    assert (b1["group"], b1["checksum_errors"]) == ("mirror-1", 3)
    assert (b2["state"], b2["trim_time"]) == ("FAULTED", None)


def test_parse_pool_refuses_garbage():
    assert parse_pool("not json", LIST, POOL) is None
    finished = STATUS.replace('"SCANNING"', '"FINISHED"')
    assert parse_pool(finished, LIST, POOL)["scan"]["percent"] is None     # only while it runs
    assert parse_pool(STATUS, LIST, "other") is None


def test_arc_memory_and_smart_parsers():
    assert parse_arcstats(ARCSTATS) == {"size": 68708277664, "c_max": 68719476736,
                                        "c_min": 6333509632, "hits": 95, "misses": 5}
    assert parse_arcstats("nothing here") is None
    assert parse_meminfo(MEMINFO) == {"total": 197573400 * 1024, "available": 87000000 * 1024}
    assert parse_smart(SMART_SAS) == {"passed": True, "model": "TOSHIBA 5SRB384C EMC3840",
                                      "serial": "37P0A0GFT3EE", "capacity": 3840774504448,
                                      "temperature": 32, "wear_percent": 35, "power_on_hours": 72361}
    nvme = json.dumps({"smart_status": {"passed": False},
                       "nvme_smart_health_information_log": {"percentage_used": 7}})
    assert parse_smart(nvme)["wear_percent"] == 7 and parse_smart(nvme)["passed"] is False
    assert parse_smart("")["passed"] is None
    assert disk_device("/dev/disk/by-id/scsi-350000397ac9008d9-part1") == "/dev/disk/by-id/scsi-350000397ac9008d9"


@pytest.fixture
def monitor(tmp_path) -> tuple[ServerMonitor, FakeRunner]:
    runner = FakeRunner()
    runner.responses[("zpool", "status")] = (True, STATUS, "")
    runner.responses[("zpool", "list")] = (True, LIST, "")
    runner.responses[("smartctl",)] = (True, SMART_SAS, "")
    (tmp_path / "spl" / "kstat" / "zfs").mkdir(parents=True)
    (tmp_path / "spl" / "kstat" / "zfs" / "arcstats").write_text(ARCSTATS)
    (tmp_path / "meminfo").write_text(MEMINFO)
    clock = iter(range(0, 10_000, 100))
    return ServerMonitor(POOL, runner, proc=tmp_path, clock=lambda: next(clock)), runner


def test_smart_is_read_again_only_after_a_while(monitor):
    mon, runner = monitor
    for _ in range(3):                                  # t = 0, 100, 200 s
        mon.smart("/dev/disk/by-id/scsi-a1")
    assert sum(c[0] == "smartctl" for c in runner.calls) == 1
    mon.smart("/dev/disk/by-id/scsi-a1")                # t = 300 s: stale
    assert sum(c[0] == "smartctl" for c in runner.calls) == 2


def test_server_api(client, monitor, prov, monkeypatch):
    mon, runner = monitor
    app.dependency_overrides[get_server_monitor] = lambda: mon
    monkeypatch.setattr(prov, "writebacks", lambda: [{"zvol": "w/pc01", "used": 3 << 30},
                                                      {"zvol": "w/pc01-os", "used": 1 << 30}])
    r = client.get("/api/v1/server")
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["arc"] == {"size_bytes": 68708277664, "max_bytes": 68719476736,
                        "min_bytes": 6333509632, "hit_percent": 95.0}
    assert s["memory"]["total_bytes"] == 197573400 * 1024
    assert (s["writebacks_bytes"], s["writebacks_count"]) == (4 << 30, 2)
    pool = s["pool"]
    assert (pool["state"], pool["scan"]["percent"]) == ("DEGRADED", 25.0)
    assert pool["last_trim"] is None                     # one disk was never trimmed
    a1 = pool["disks"][0]
    assert (a1["smart_passed"], a1["temperature"], a1["wear_percent"]) == (True, 32, 35)
    assert ["smartctl", "-j", "-H", "-A", "-i", "/dev/disk/by-id/scsi-a1"] in runner.calls

    r = client.post("/api/v1/server/scrub", json={"action": "stop"})
    assert r.status_code == 200
    assert ["zpool", "scrub", "-s", POOL] in runner.calls
    runner.responses[("zpool", "scrub")] = (False, "", "no active scrub")
    r = client.post("/api/v1/server/scrub", json={"action": "start"})
    assert r.status_code == 502
    assert "no active scrub" in r.text


def test_unreadable_pool_still_shows_the_rest(client, monitor, prov, monkeypatch):
    mon, runner = monitor
    runner.responses[("zpool", "status")] = (False, "", "no such pool")
    app.dependency_overrides[get_server_monitor] = lambda: mon
    monkeypatch.setattr(prov, "writebacks", lambda: [])
    s = client.get("/api/v1/server").json()
    assert s["pool"] is None and s["arc"]["hit_percent"] == 95.0

