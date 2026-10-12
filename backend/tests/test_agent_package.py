"""Settings → Client app: agent package info, downloads and the bootstrap script."""

from __future__ import annotations

import hashlib
import io
import zipfile

import pytest

from app.api.deps import get_agent_package, get_server_url
from app.main import app
from app.services.agent_package import AgentPackage

SERVER = "http://192.168.0.40:8088"
CONTENT = {"ggnet-agent.exe": b"MZ" + b"\x00" * 1000, "install.ps1": b"param()\n", "uninstall.ps1": b"# remove\n"}


@pytest.fixture
def package_dir(tmp_path, client):
    d = tmp_path / "agent"
    d.mkdir()
    pkg = AgentPackage(d)
    app.dependency_overrides[get_agent_package] = lambda: pkg
    app.dependency_overrides[get_server_url] = lambda: SERVER
    yield d
    app.dependency_overrides.pop(get_agent_package, None)
    app.dependency_overrides.pop(get_server_url, None)


def _fill(d, version="0.1.9"):
    for name, data in CONTENT.items():
        (d / name).write_bytes(data)
    if version is not None:
        (d / "VERSION").write_text(version + "\n")


def test_missing_package_is_reported_not_an_error(client, package_dir):
    r = client.get("/api/v1/agent/package")
    assert r.status_code == 200
    got = r.json()
    assert (got["available"], got["files"], got["directory"]) == (False, [], str(package_dir))
    assert client.get("/api/v1/agent/download.zip").status_code == 404
    assert client.get("/api/v1/agent/bootstrap.ps1").status_code == 404


def test_package_info_with_checksums_and_install_command(client, package_dir):
    _fill(package_dir)
    got = client.get("/api/v1/agent/package").json()
    assert (got["available"], got["version"], got["server_url"]) == (True, "0.1.9", SERVER)
    assert got["install_command"] == f"irm {SERVER}/api/v1/agent/bootstrap.ps1 | iex"
    assert got["files"] == [
        {"name": n, "size_bytes": len(d), "sha256": hashlib.sha256(d).hexdigest()} for n, d in CONTENT.items()
    ]


def test_downloads_only_known_files(client, package_dir):
    _fill(package_dir)
    (package_dir / "secret.txt").write_text("no")
    r = client.get("/api/v1/agent/download/install.ps1")
    assert r.status_code == 200 and r.content == CONTENT["install.ps1"]
    for bad in ("secret.txt", "..%2Fconfig.toml", "VERSION"):
        assert client.get(f"/api/v1/agent/download/{bad}").status_code == 404


def test_zip_has_the_package_and_is_rebuilt_after_a_change(client, package_dir):
    _fill(package_dir)
    r = client.get("/api/v1/agent/download.zip")
    assert r.status_code == 200
    assert 'filename="ggnet-agent-0.1.9.zip"' in r.headers["content-disposition"]
    z = zipfile.ZipFile(io.BytesIO(r.content))
    assert sorted(z.namelist()) == sorted(f"ggnet-agent/{n}" for n in [*CONTENT, "VERSION"])
    assert z.read("ggnet-agent/ggnet-agent.exe") == CONTENT["ggnet-agent.exe"]

    (package_dir / "install.ps1").write_bytes(b"param($ServerUrl)\n")
    z = zipfile.ZipFile(io.BytesIO(client.get("/api/v1/agent/download.zip").content))
    assert z.read("ggnet-agent/install.ps1") == b"param($ServerUrl)\n"
    assert len(list((package_dir / ".cache").glob("*.zip"))) == 1    # the old zip is gone


def test_bootstrap_checks_every_file_and_runs_install(client, package_dir):
    _fill(package_dir)
    r = client.get("/api/v1/agent/bootstrap.ps1")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/plain")
    script = r.text
    for name, data in CONTENT.items():
        assert f"'{name}' = '{hashlib.sha256(data).hexdigest()}'" in script
    assert f"$server = '{SERVER}'" in script
    assert "Checksum mismatch" in script and "IsInRole" in script
    assert "-ExecutionPolicy Bypass -File (Join-Path $dir 'install.ps1') -ServerUrl $server" in script


def test_a_bad_version_file_is_ignored(client, package_dir):
    _fill(package_dir, version="0.1.9'; whoami")
    assert client.get("/api/v1/agent/package").json()["version"] is None
