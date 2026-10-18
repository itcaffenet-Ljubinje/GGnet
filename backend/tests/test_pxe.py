"""Settings → Network boot: the boot settings and the PXE service (FakeRunner)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.api.deps import get_pxe_service
from app.db.session import make_engine
from app.main import app
from app.services.pxe import PxeService, effective_config, load_settings

from .conftest import FakeRunner

SHOW = "LoadState=loaded\nActiveState=active\nSubState=running\nActiveEnterTimestamp=@1792297503"


@pytest.fixture
def pxe(client, tmp_path):
    runner = FakeRunner()
    runner.on("systemctl", "show", result=(True, SHOW, ""))
    (tmp_path / "snponly.efi").write_bytes(b"x")
    (tmp_path / "autoexec.ipxe").write_text("#!ipxe\n")
    service = PxeService("ggnet-pxe", tmp_path, runner)
    app.dependency_overrides[get_pxe_service] = lambda: service
    return runner


def test_boot_settings_default_to_config_toml(client):
    r = client.get("/api/v1/settings/boot")
    assert r.status_code == 200
    assert r.json() == {"gateway": "none", "unregistered": "wait", "saved": False}


def test_boot_settings_are_saved(client):
    r = client.put("/api/v1/settings/boot", json={"gateway": " 192.168.0.1 ", "unregistered": "local"})
    assert r.status_code == 200, r.text
    assert r.json() == {"gateway": "192.168.0.1", "unregistered": "local", "saved": True}
    assert client.get("/api/v1/settings/boot").json()["saved"] is True


@pytest.mark.parametrize("body", [
    {"gateway": "router", "unregistered": "wait"},
    {"gateway": "192.168.0.300", "unregistered": "wait"},
    {"gateway": "none", "unregistered": "never"},
])
def test_invalid_boot_settings_are_refused(client, body):
    assert client.put("/api/v1/settings/boot", json=body).status_code == 422
    assert client.get("/api/v1/settings/boot").json()["saved"] is False


def test_effective_config_keeps_config_toml_until_saved(client, db_url):
    cfg = {"boot": {"gateway": "dhcp", "pxe_service": "x"}, "paths": {}}
    engine = make_engine(db_url)
    with Session(engine) as db:
        assert effective_config(db, cfg) is cfg
        s, saved = load_settings(db, cfg)
        assert (s.gateway, s.unregistered, saved) == ("dhcp", "wait", False)
        client.put("/api/v1/settings/boot", json={"gateway": "none", "unregistered": "local"})
        merged = effective_config(db, cfg)
        assert merged["boot"] == {"gateway": "none", "unregistered": "local", "pxe_service": "x"}
    engine.dispose()


def test_pxe_status(client, pxe, tmp_path):
    r = client.get("/api/v1/pxe")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["unit"] == "ggnet-pxe" and body["installed"] is True
    assert (body["state"], body["sub_state"]) == ("active", "running")
    assert datetime.fromisoformat(body["since"]) == datetime.fromtimestamp(1792297503, tz=timezone.utc)
    assert body["tftp_root"] == str(tmp_path)
    assert body["files"] == {"snponly.efi": True, "ipxe.efi": False, "autoexec.ipxe": True}
    assert pxe.calls[0][:3] == ["systemctl", "show", "ggnet-pxe"]


def test_pxe_status_of_a_missing_unit(client, pxe):
    pxe.on("systemctl", "show", result=(
        True, "LoadState=not-found\nActiveState=inactive\nSubState=dead\nActiveEnterTimestamp=", ""))
    body = client.get("/api/v1/pxe").json()
    assert body["installed"] is False and body["state"] == "inactive" and body["since"] is None


def test_pxe_restart(client, pxe):
    r = client.post("/api/v1/pxe/restart")
    assert r.status_code == 200, r.text
    assert ["systemctl", "restart", "ggnet-pxe"] in pxe.calls
    assert r.json()["state"] == "active"


def test_pxe_restart_failure_is_reported(client, pxe):
    pxe.on("systemctl", "restart", result=(False, "", "Job for ggnet-pxe.service failed"))
    r = client.post("/api/v1/pxe/restart")
    assert r.status_code == 502
    assert "Job for ggnet-pxe.service failed" in r.text


def test_pxe_service_from_config():
    s = PxeService.from_config({"paths": {"data_dir": "/var/lib/ggnet"}, "boot": {"pxe_service": "ggnet-dev-dnsmasq"}})
    assert (s.unit, str(s.tftp_root)) == ("ggnet-dev-dnsmasq", "/var/lib/ggnet/tftp")
    s = PxeService.from_config({"paths": {"data_dir": "/x"}, "services": {"tftp_root": "/srv/tftp"}})
    assert (s.unit, str(s.tftp_root)) == ("ggnet-pxe", "/srv/tftp")
