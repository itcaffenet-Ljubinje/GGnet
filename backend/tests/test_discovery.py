"""PC identity by MAC, the MAC-derived IQN, and Discovery of unknown PCs."""

from __future__ import annotations

import pytest

from app.services import discovery

MAC = "aa:bb:cc:dd:ee:01"
MAC_IQN = "iqn.2025-05.net.ggnet:pc-aabbccddee01"


def _beat(client, name: str = "desktop-1a2b3c", mac: str | None = "AA-BB-CC-DD-EE-01"):
    body = {"name": name, "agent_version": "0.1.9"}
    if mac:
        body["inventory"] = {"ip_address": "192.168.0.21", "mac_address": mac}
    return client.post("/api/v1/agent/heartbeat", json=body)


def _discovered(client, ignored: bool = False) -> list[dict]:
    r = client.get("/api/v1/discovery", params={"ignored": ignored})
    assert r.status_code == 200, r.text
    return r.json()


# ── IQN from the MAC ─────────────────────────────────────────────────

def test_mac_initiator_iqn(prov):
    iscsi = prov.iscsi
    assert iscsi.mac_initiator_iqn("AA-BB-CC-DD-EE-01") == MAC_IQN
    with pytest.raises(ValueError):
        iscsi.mac_initiator_iqn("aa:bb")


def test_reset_iqn_to_the_default(client):
    m = client.post("/api/v1/machines", json={
        "name": "pc01", "initiator_iqn": "iqn.1991-05.com.microsoft:pc01"}).json()
    # No MAC: the default is the Windows one.
    r = client.patch(f"/api/v1/machines/{m['id']}", json={"initiator_iqn": "", "name": "pc02"})
    assert r.json()["initiator_iqn"] == "iqn.1991-05.com.microsoft:pc02"
    # With a MAC (also one sent in the same request) it is derived from the MAC.
    r = client.patch(f"/api/v1/machines/{m['id']}", json={"initiator_iqn": "", "mac": MAC})
    assert r.json()["initiator_iqn"] == MAC_IQN
    assert client.patch(f"/api/v1/machines/{m['id']}", json={"initiator_iqn": None}).status_code == 422


# ── Heartbeat identity ───────────────────────────────────────────────

def test_heartbeat_finds_the_machine_by_mac_whatever_the_windows_name(client):
    m = client.post("/api/v1/machines", json={"name": "vip-05", "mac": MAC}).json()
    r = _beat(client, name="desktop-1a2b3c")
    assert r.status_code == 200, r.text
    assert r.json()["machine_id"] == m["id"]
    assert r.json()["initiator_iqn"] == MAC_IQN
    assert _discovered(client) == []


def test_heartbeat_by_name_still_works_without_a_mac(client):
    m = client.post("/api/v1/machines", json={"name": "pc01"}).json()
    assert _beat(client, name="PC01", mac=None).json()["machine_id"] == m["id"]
    # A machine without a MAC is found by name whatever MAC the PC reports.
    assert _beat(client, name="PC01").json()["machine_id"] == m["id"]


def test_same_windows_name_on_another_pc_is_refused(client):
    client.post("/api/v1/machines", json={"name": "pc01", "mac": MAC})
    r = _beat(client, name="pc01", mac="aa:bb:cc:dd:ee:99")
    assert r.status_code == 404
    [d] = _discovered(client)
    assert d["mac"] == "aa:bb:cc:dd:ee:99" and d["hostname"] == "pc01"


def test_unknown_agent_is_discovered(client):
    assert _beat(client).status_code == 404
    assert _beat(client).status_code == 404
    [d] = _discovered(client)
    assert d["mac"] == MAC
    assert d["source"] == "agent"
    assert d["hostname"] == "desktop-1a2b3c"
    assert d["ip_address"] == "192.168.0.21"
    assert d["agent_version"] == "0.1.9"
    assert d["seen_count"] == 2


def test_unknown_agent_without_a_mac_is_not_recorded(client):
    assert _beat(client, mac=None).status_code == 404
    assert _discovered(client) == []


# ── iPXE ─────────────────────────────────────────────────────────────

def test_unknown_pxe_mac_is_discovered(client):
    r = client.get("/api/v1/boot/ipxe", params={"mac": "AA-BB-CC-DD-EE-01"})
    assert "exit" in r.text
    [d] = _discovered(client)
    assert d["source"] == "pxe" and d["mac"] == MAC and d["hostname"] is None
    # Its agent later tells more; a later PXE knock keeps that.
    _beat(client)
    client.get("/api/v1/boot/ipxe", params={"mac": MAC})
    [d] = _discovered(client)
    assert d["source"] == "agent" and d["hostname"] == "desktop-1a2b3c" and d["seen_count"] == 3


def test_registered_mac_is_not_discovered(client):
    client.post("/api/v1/machines", json={"name": "pc01", "mac": MAC})
    client.get("/api/v1/boot/ipxe", params={"mac": MAC})
    assert _discovered(client) == []


# ── Claim, ignore, remove ────────────────────────────────────────────

def test_claim_adds_the_machine_with_its_mac_and_mac_iqn(client):
    _beat(client)
    [d] = _discovered(client)
    r = client.post(f"/api/v1/discovery/{d['id']}/claim", json={"name": "VIP-05"})
    assert r.status_code == 201, r.text
    m = r.json()
    assert (m["name"], m["mac"], m["initiator_iqn"]) == ("vip-05", MAC, MAC_IQN)
    assert _discovered(client) == []
    # The PC is now known: its next heartbeat gets its config.
    assert _beat(client).json()["machine_id"] == m["id"]


def test_claim_checks_like_create(client):
    client.post("/api/v1/machines", json={"name": "vip-05"})
    _beat(client)
    [d] = _discovered(client)
    r = client.post(f"/api/v1/discovery/{d['id']}/claim", json={"name": "vip-05"})
    assert r.status_code == 409
    assert len(_discovered(client)) == 1   # still listed
    r = client.post(f"/api/v1/discovery/{d['id']}/claim", json={"name": "bad name!"})
    assert r.status_code == 422
    assert client.post("/api/v1/discovery/999/claim", json={"name": "pc09"}).status_code == 404


def test_adding_a_machine_by_hand_drops_its_discovery(client):
    _beat(client)
    client.post("/api/v1/machines", json={"name": "pc01", "mac": MAC})
    assert _discovered(client) == []


def test_setting_a_mac_drops_its_discovery(client):
    m = client.post("/api/v1/machines", json={"name": "pc01"}).json()
    _beat(client)
    assert client.patch(f"/api/v1/machines/{m['id']}", json={"mac": MAC}).status_code == 200
    assert _discovered(client) == []


def test_ignore_hides_it_also_when_it_knocks_again(client):
    _beat(client)
    [d] = _discovered(client)
    assert client.post(f"/api/v1/discovery/{d['id']}/ignore").json()["ignored"] is True
    _beat(client)
    assert _discovered(client) == []
    [d] = _discovered(client, ignored=True)
    assert d["ignored"] is True and d["seen_count"] == 2


def test_remove_lets_it_come_back(client):
    _beat(client)
    [d] = _discovered(client)
    assert client.delete(f"/api/v1/discovery/{d['id']}").status_code == 204
    assert _discovered(client) == []
    _beat(client)
    assert len(_discovered(client)) == 1
    assert client.delete("/api/v1/discovery/999").status_code == 404


def test_the_list_is_capped(client, monkeypatch):
    monkeypatch.setattr(discovery, "MAX_DISCOVERED", 2)
    for i in range(3):
        client.get("/api/v1/boot/ipxe", params={"mac": f"aa:bb:cc:dd:ee:0{i}"})
    assert len(_discovered(client)) == 2
    # Known rows still update when the list is full.
    client.get("/api/v1/boot/ipxe", params={"mac": "aa:bb:cc:dd:ee:00"})
    assert sorted(d["seen_count"] for d in _discovered(client)) == [1, 2]
