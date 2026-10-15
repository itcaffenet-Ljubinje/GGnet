"""Boot Mode: OS images, OS + game writebacks per PC, and the iPXE script (FakeHost)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_writeback_settings
from app.db.session import make_engine
from app.main import app
from app.services import writebacks
from app.services.writebacks import WritebackSettings

SETTINGS = WritebackSettings(auto_discard=True, grace=timedelta(seconds=30))
T0 = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
IQN = "iqn.2025-05.net.ggnet:pc-aabbccddee05"   # derived from MAC
MAC = "aa:bb:cc:dd:ee:05"
OS_CLONE = "tank/ggnet/writebacks/vip-05-os"
GAME_CLONE = "tank/ggnet/writebacks/vip-05"
TARGET = "iqn.2025-05.net.ggnet:storage"


def _disk(client, name: str, kind: str = "game") -> dict:
    r = client.post("/api/v1/game-disks", json={"name": name, "size_gb": 10, "kind": kind})
    assert r.status_code == 201, r.text
    r = client.post(f"/api/v1/game-disks/{r.json()['id']}/publish")
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture
def disks(client) -> tuple[dict, dict]:
    return _disk(client, "win11", "os"), _disk(client, "cs2")


def _boot_machine(client, disks, **body) -> dict:
    os_disk, game = disks
    r = client.post("/api/v1/machines", json={
        "name": "vip-05", "mode": "boot", "mac": MAC,
        "game_disk_id": game["id"], "os_disk_id": os_disk["id"], **body,
    })
    assert r.status_code == 201, r.text
    return r.json()


def _get(client, m) -> dict:
    return client.get(f"/api/v1/machines/{m['id']}").json()


def _ipxe(client, mac: str = "aa-bb-cc-dd-ee-05") -> str:
    r = client.get("/api/v1/boot/ipxe", params={"mac": mac})
    assert r.status_code == 200, r.text
    assert r.text.startswith("#!ipxe\n")
    return r.text


def _mark_dirty(db_url) -> None:
    """The PC wrote to its writebacks (the watcher saw it connected)."""
    engine = make_engine(db_url)
    with engine.begin() as conn:
        conn.execute(text("UPDATE machines SET writeback_dirty = 1"))
    engine.dispose()


def _clones_made(host) -> list[str]:
    return [c[-1] for c in host.calls if c[:2] == ["zfs", "clone"]]


@pytest.fixture
def auto(client):
    app.dependency_overrides[get_writeback_settings] = lambda: SETTINGS


# ── OS images ─────────────────────────────────────────────────────────

def test_os_image_is_created_for_windows_io(client, host):
    r = client.post("/api/v1/game-disks", json={"name": "win11", "size_gb": 80, "kind": "os"})
    assert r.status_code == 201, r.text
    assert r.json()["kind"] == "os"
    create = next(c for c in host.calls if c[:2] == ["zfs", "create"])
    assert {"volblocksize=16k", "compression=lz4", "sync=standard"} <= set(create)


def test_game_disk_is_the_default_kind(client, host):
    assert _disk(client, "cs2")["kind"] == "game"
    create = next(c for c in host.calls if c[:2] == ["zfs", "create"])
    assert "volblocksize=64k" in create


def test_os_image_cannot_be_edited_on_a_pc(client):
    r = client.post("/api/v1/game-disks", json={"name": "win11", "size_gb": 80, "kind": "os"})
    m = client.post("/api/v1/machines", json={"name": "pc01"}).json()
    r = client.post(f"/api/v1/game-disks/{r.json()['id']}/edit", json={"machine_id": m["id"]})
    assert r.status_code == 409


def test_os_image_in_use_cannot_be_deleted(client, disks):
    _boot_machine(client, disks)
    r = client.delete(f"/api/v1/game-disks/{disks[0]['id']}")
    assert r.status_code == 409


# ── Provisioning ──────────────────────────────────────────────────────

def test_boot_machine_gets_os_lun0_and_game_lun1(client, host, disks):
    m = _boot_machine(client, disks)
    assert m["status"] == "provisioned"
    assert (m["os_disk_id"], m["os_clone_zvol"], m["os_clone_snapshot"]) == (
        disks[0]["id"], OS_CLONE, "tank/ggnet/images/win11@base")
    assert (m["clone_zvol"], m["clone_snapshot"]) == (GAME_CLONE, "tank/ggnet/images/cs2@base")
    assert host.visible(IQN) == [f"/dev/zvol/{OS_CLONE}", f"/dev/zvol/{GAME_CLONE}"]


def test_boot_machine_needs_an_os_image(client, host, disks):
    r = client.post("/api/v1/machines", json={
        "name": "vip-05", "mode": "boot", "game_disk_id": disks[1]["id"]})
    assert r.status_code == 409
    assert "OS image" in r.json()["detail"]["error"]


def test_disks_must_be_of_the_right_kind(client, disks):
    os_disk, game = disks
    r = client.post("/api/v1/machines", json={
        "name": "vip-05", "mode": "boot", "game_disk_id": os_disk["id"], "os_disk_id": game["id"]})
    assert r.status_code == 409


def test_disk_mode_machine_gets_no_os_image(client, disks):
    os_disk, game = disks
    r = client.post("/api/v1/machines", json={
        "name": "pc01", "game_disk_id": game["id"], "os_disk_id": os_disk["id"]})
    assert r.status_code == 409


def test_machine_name_must_not_end_in_os(client):
    r = client.post("/api/v1/machines", json={"name": "vip-05-os"})
    assert r.status_code == 422


def test_assign_keeps_the_os_image_when_not_sent(client, host, disks):
    m = _boot_machine(client, disks)
    other = _disk(client, "valorant")
    r = client.post(f"/api/v1/machines/{m['id']}/assign", json={"game_disk_id": other["id"]})
    assert r.status_code == 200, r.text
    assert r.json()["os_disk_id"] == disks[0]["id"]
    assert host.visible(IQN) == [f"/dev/zvol/{OS_CLONE}", f"/dev/zvol/{GAME_CLONE}"]
    assert host.datasets[GAME_CLONE]["origin"] == "tank/ggnet/images/valorant@base"


def test_remove_disks_deletes_both_writebacks(client, host, disks):
    m = _boot_machine(client, disks)
    r = client.post(f"/api/v1/machines/{m['id']}/assign", json={"game_disk_id": None})
    assert r.status_code == 200, r.text
    out = r.json()
    assert (out["status"], out["os_disk_id"], out["os_clone_zvol"]) == ("idle", None, None)
    assert not host.exists(OS_CLONE) and not host.exists(GAME_CLONE)
    assert host.visible(IQN) == []


def test_failed_os_clone_rolls_back_the_game_clone(client, host, disks):
    host.fail_on[("zfs", "clone", "-o", "sync=disabled", "tank/ggnet/images/win11@base")] = "out of space"
    r = client.post("/api/v1/machines", json={
        "name": "vip-05", "mode": "boot",
        "game_disk_id": disks[1]["id"], "os_disk_id": disks[0]["id"]})
    assert r.status_code == 502
    assert not host.exists(GAME_CLONE)
    m = client.get("/api/v1/machines").json()[0]
    assert m["status"] == "error"
    # The leftovers are recorded, so removing the disks cleans up.
    del host.fail_on[("zfs", "clone", "-o", "sync=disabled", "tank/ggnet/images/win11@base")]
    r = client.post(f"/api/v1/machines/{m['id']}/assign", json={"game_disk_id": None})
    assert r.status_code == 200, r.text


def test_keep_writeback_keeps_both(client, host, disks):
    m = _boot_machine(client, disks)
    r = client.put(f"/api/v1/machines/{m['id']}/keep-writeback", json={"enabled": True})
    assert r.status_code == 200, r.text
    synced = {c[-1] for c in host.calls if c[:3] == ["zfs", "set", "sync=standard"]}
    assert synced == {OS_CLONE, GAME_CLONE}


# ── Apply Writebacks ──────────────────────────────────────────────────

def _boot_keeper(client, disks) -> dict:
    m = _boot_machine(client, disks)
    r = client.put(f"/api/v1/machines/{m['id']}/keep-writeback", json={"enabled": True})
    assert r.status_code == 200, r.text
    return m


def test_apply_writebacks_makes_both_next_versions(client, host, disks, windows):
    m = _boot_keeper(client, disks)
    windows.done.clear()
    r = client.post(f"/api/v1/machines/{m['id']}/apply-writebacks")
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["os_clone_snapshot"] == "tank/ggnet/images/win11@v2"
    assert out["clone_snapshot"] == "tank/ggnet/images/cs2@v2"
    assert client.get(f"/api/v1/game-disks/{disks[0]['id']}").json()["snapshot"] == "v2"
    assert client.get(f"/api/v1/game-disks/{disks[1]['id']}").json()["snapshot"] == "v2"
    assert host.datasets[OS_CLONE]["origin"] == "tank/ggnet/images/win11@v2"
    assert host.datasets[GAME_CLONE]["origin"] == "tank/ggnet/images/cs2@v2"
    # Both writebacks are still kept, and the fresh OS one is this PC again.
    assert {host.datasets[c]["props"]["sync"] for c in (OS_CLONE, GAME_CLONE)} == {"standard"}
    assert [d for d, _, _ in windows.done] == [f"/dev/zvol/{OS_CLONE}"]
    assert host.visible(IQN) == [f"/dev/zvol/{OS_CLONE}", f"/dev/zvol/{GAME_CLONE}"]


def test_apply_only_the_os_writeback_keeps_the_game_one(client, host, disks, windows):
    m = _boot_keeper(client, disks)
    windows.done.clear()
    r = client.post(f"/api/v1/machines/{m['id']}/apply-writebacks", json={"game": False})
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["os_clone_snapshot"] == "tank/ggnet/images/win11@v2"
    assert out["clone_snapshot"] == "tank/ggnet/images/cs2@base"
    assert client.get(f"/api/v1/game-disks/{disks[1]['id']}").json()["snapshot"] == "base"
    # The game writeback was mapped again as it was, not re-cloned.
    assert ["zfs", "destroy", "-r", GAME_CLONE] not in host.calls
    assert host.datasets[GAME_CLONE]["origin"] == "tank/ggnet/images/cs2@base"
    assert [d for d, _, _ in windows.done] == [f"/dev/zvol/{OS_CLONE}"]
    assert host.visible(IQN) == [f"/dev/zvol/{OS_CLONE}", f"/dev/zvol/{GAME_CLONE}"]


def test_apply_only_the_game_writeback_keeps_the_os_one(client, host, disks, windows):
    m = _boot_keeper(client, disks)
    windows.done.clear()
    r = client.post(f"/api/v1/machines/{m['id']}/apply-writebacks", json={"os": False})
    assert r.status_code == 200, r.text
    assert r.json()["os_clone_snapshot"] == "tank/ggnet/images/win11@base"
    assert r.json()["clone_snapshot"] == "tank/ggnet/images/cs2@v2"
    assert ["zfs", "destroy", "-r", OS_CLONE] not in host.calls
    assert windows.done == []          # the kept OS writeback is already this PC


def test_apply_nothing_is_refused(client, host, disks):
    m = _boot_keeper(client, disks)
    r = client.post(f"/api/v1/machines/{m['id']}/apply-writebacks", json={"os": False, "game": False})
    assert r.status_code == 409
    assert "tank/ggnet/images/win11@v2" not in host.snapshots


def test_apply_os_refused_when_the_image_moved_on(client, host, disks):
    m = _boot_keeper(client, disks)
    host.snapshots["tank/ggnet/images/win11@manual"] = set()
    r = client.post(f"/api/v1/machines/{m['id']}/apply-writebacks", json={"game": False})
    assert r.status_code == 502 and "not the newest version" in r.json()["detail"]["error"]
    # Nothing was applied, so the PC gets its writebacks back.
    assert host.visible(IQN) == [f"/dev/zvol/{OS_CLONE}", f"/dev/zvol/{GAME_CLONE}"]


def test_apply_failing_on_the_second_disk_records_the_first(client, host, disks):
    m = _boot_keeper(client, disks)
    host.snapshots["tank/ggnet/images/win11@manual"] = set()   # the OS apply fails
    r = client.post(f"/api/v1/machines/{m['id']}/apply-writebacks")
    assert r.status_code == 502 and "Reset the machine" in r.json()["detail"]["error"]
    assert client.get(f"/api/v1/game-disks/{disks[1]['id']}").json()["snapshot"] == "v2"
    assert _get(client, m)["status"] == "error"


# ── Writeback discard ─────────────────────────────────────────────────

def test_watcher_discards_both_writebacks(client, host, prov, disks, db_url):
    m = _boot_machine(client, disks)
    engine = make_engine(db_url)
    make_session = sessionmaker(bind=engine, expire_on_commit=False)
    host.sessions.add(IQN)
    writebacks.tick(make_session, prov, SETTINGS, now=T0)
    host.sessions.discard(IQN)
    writebacks.tick(make_session, prov, SETTINGS, now=T0 + timedelta(seconds=1))
    host.calls.clear()
    writebacks.tick(make_session, prov, SETTINGS, now=T0 + timedelta(seconds=40))
    engine.dispose()
    assert sorted(_clones_made(host)) == [GAME_CLONE, OS_CLONE]
    assert host.visible(IQN) == [f"/dev/zvol/{OS_CLONE}", f"/dev/zvol/{GAME_CLONE}"]
    assert _get(client, m)["writeback_dirty"] is False


# ── iPXE script ───────────────────────────────────────────────────────

def test_ipxe_sanboots_a_boot_machine(client, disks):
    _boot_machine(client, disks)
    script = _ipxe(client)
    assert f"set initiator-iqn {IQN}" in script
    assert f"set root-path iscsi:192.168.10.1::3260:0:{TARGET}" in script
    assert "sanboot ${root-path} || goto failed" in script
    assert "--no-describe" not in script


def test_ipxe_finds_the_mac_the_agent_reported(client, disks):
    m = _boot_machine(client, disks, mac=None)
    r = client.post("/api/v1/agent/heartbeat", json={
        "name": "vip-05", "agent_version": "0.2.0", "initiator_iqn": IQN,
        "iscsi_connected": True, "inventory": {"mac_address": MAC}})
    assert r.status_code == 200, r.text
    assert _get(client, m)["reported_mac"] == MAC
    assert "sanboot" in _ipxe(client)


@pytest.mark.parametrize("mac", ["aa-bb-cc-dd-ee-99", "not-a-mac", ""])
def test_ipxe_unknown_pc_boots_locally(client, disks, mac):
    _boot_machine(client, disks)
    script = _ipxe(client, mac)
    assert script.rstrip().endswith("exit")
    assert "sanboot" not in script


def test_ipxe_disk_mode_pc_boots_locally(client, disks):
    client.post("/api/v1/machines", json={"name": "pc01", "mac": MAC})
    script = _ipxe(client)
    assert "Disk Mode" in script and "sanboot" not in script


def test_ipxe_boot_machine_without_disks_boots_locally(client):
    client.post("/api/v1/machines", json={"name": "vip-05", "mode": "boot", "mac": MAC})
    script = _ipxe(client)
    assert "cannot boot" in script and "sanboot" not in script


def test_ipxe_discards_a_dirty_writeback_before_boot(client, host, disks, auto, db_url):
    m = _boot_machine(client, disks)
    _mark_dirty(db_url)
    host.calls.clear()
    assert "sanboot" in _ipxe(client)
    assert sorted(_clones_made(host)) == [GAME_CLONE, OS_CLONE]
    assert _get(client, m)["writeback_dirty"] is False


def test_ipxe_does_not_discard_while_a_session_is_live(client, host, disks, auto, db_url):
    _boot_machine(client, disks)
    _mark_dirty(db_url)
    host.sessions.add(IQN)
    host.calls.clear()
    assert "sanboot" in _ipxe(client)
    assert _clones_made(host) == []


def test_ipxe_discard_failure_boots_locally(client, host, disks, auto, db_url):
    m = _boot_machine(client, disks)
    _mark_dirty(db_url)
    host.fail_on[("zfs", "clone")] = "pool is full"
    script = _ipxe(client)
    assert "sanboot" not in script and "pool is full" in script
    assert _get(client, m)["status"] == "error"


def test_boot_traffic_sums_both_luns(client, host, disks):
    m = _boot_machine(client, disks)
    host.traffic[IQN] = (100, 7)
    out = client.get("/api/v1/machines/traffic").json()
    row = next(t for t in out if t["machine_id"] == m["id"])
    assert (row["received_bytes"], row["sent_bytes"]) in {(14 << 20, 200 << 20), (200 << 20, 14 << 20)}


# ── The PC's identity in its OS writeback (app.windows_setup) ─────────

class FakeWindows:
    """Records each personalize() and what was on the target at that moment."""

    def __init__(self, host, problem: str | None = None):
        self.host = host
        self.problem = problem
        self.done: list[tuple[str, object, bool]] = []

    def personalize(self, device, setup):
        mapped = any(c[0] == "targetcli" and OS_CLONE.split("/")[-1] in " ".join(c)
                     for c in self.host.calls)
        self.done.append((device, setup, mapped))
        return self.problem


@pytest.fixture
def windows(prov, host):
    prov.windows = FakeWindows(host)
    return prov.windows


def test_a_new_os_writeback_gets_the_pc_identity_before_it_is_mapped(client, host, disks, windows):
    host.calls.clear()
    m = _boot_machine(client, disks)
    [(device, setup, mapped)] = windows.done
    assert device == f"/dev/zvol/{OS_CLONE}"
    assert mapped is False
    assert setup.computer_name == "vip-05"
    assert setup.env == {"GGNET_SERVER": "http://127.0.0.1:8088",
                         "GGNET_MACHINE_ID": str(m["id"]), "GGNET_MACHINE_NAME": "vip-05"}


def test_every_discard_sets_it_up_again(client, host, disks, auto, db_url, windows):
    _boot_machine(client, disks)
    _mark_dirty(db_url)
    windows.done.clear()
    assert "sanboot" in _ipxe(client)
    assert [d for d, _, _ in windows.done] == [f"/dev/zvol/{OS_CLONE}"]


def test_a_setup_problem_does_not_stop_the_boot(client, host, disks, windows):
    windows.problem = "no Windows partition found"
    m = _boot_machine(client, disks)
    assert m["status"] == "provisioned"
    assert "sanboot" in _ipxe(client)


def test_disk_mode_pcs_are_never_set_up(client, disks, windows):
    _, game = disks
    r = client.post("/api/v1/machines", json={"name": "pc01", "game_disk_id": game["id"]})
    assert r.status_code == 201
    assert windows.done == []


# ── [boot] gateway ───────────────────────────────────────────────────

@pytest.mark.parametrize("value, line", [
    (None, None),
    ("", None),
    ("none", "set netX/gateway 0.0.0.0"),
    ("192.168.10.1", "set netX/gateway 192.168.10.1"),
    ("not-an-ip", None),
])
def test_boot_gateway(value, line):
    from app.api.v1.boot import boot_gateway
    cfg = {} if value is None else {"boot": {"gateway": value}}
    assert boot_gateway(cfg) == (line.split()[-1] if line else None)


def test_the_gateway_goes_before_the_sanboot(client, disks, monkeypatch):
    from app.api.v1 import boot
    monkeypatch.setattr(boot, "boot_gateway", lambda: "0.0.0.0")
    _boot_machine(client, disks)
    lines = _ipxe(client).splitlines()
    assert lines[1] == "set netX/gateway 0.0.0.0"
    assert lines.index("set netX/gateway 0.0.0.0") < next(i for i, l in enumerate(lines) if l.startswith("sanboot"))
