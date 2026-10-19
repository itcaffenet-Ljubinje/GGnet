"""What a Boot Mode PC's Windows gets from the server (app.services.os_setup)."""

from __future__ import annotations

import hashlib

from app.services import os_setup
from app.services.agent_package import AgentPackage


def _package(tmp_path) -> AgentPackage:
    for name, data in (("ggnet-agent.exe", b"MZ agent"), ("install.ps1", b"#"), ("uninstall.ps1", b"#")):
        (tmp_path / name).write_bytes(data)
    return AgentPackage(tmp_path)


def test_the_servers_agent_goes_into_the_writebacks(tmp_path, monkeypatch):
    monkeypatch.setattr(os_setup, "default_package", lambda: _package(tmp_path))
    agent = os_setup.agent_install()
    assert agent.exe == tmp_path / "ggnet-agent.exe"
    assert agent.sha256 == hashlib.sha256(b"MZ agent").hexdigest()
    assert agent.server_url == "http://127.0.0.1:8088"


def test_no_agent_without_a_package_or_when_turned_off(tmp_path, monkeypatch):
    monkeypatch.setattr(os_setup, "default_package", lambda: AgentPackage(tmp_path / "empty"))
    assert os_setup.agent_install() is None
    monkeypatch.setattr(os_setup, "default_package", lambda: _package(tmp_path))
    cfg = dict(os_setup.get_config())
    monkeypatch.setattr(os_setup, "get_config", lambda: {**cfg, "boot": {"inject_agent": False}})
    assert os_setup.agent_install() is None
