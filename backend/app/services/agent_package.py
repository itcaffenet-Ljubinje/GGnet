"""
The ggnet-agent package the web UI offers for download (Settings → Client
app): ggnet-agent.exe, install.ps1, uninstall.ps1 and an optional VERSION
file in `[paths] agent_dir` (default `<data_dir>/agent`), as unpacked from the
release's ggnet-agent-win-x64.zip.

Besides the single files and a zip of them, the server makes a bootstrap
script for a one-line install on a PC: it downloads the files, checks their
SHA-256 against the values the server computed, and runs install.ps1 with
this server's URL. The checksums catch a broken download; they do not
protect against a forged server (that comes with TLS).
"""

from __future__ import annotations

import hashlib
import os
import threading
import zipfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.config import get_config

AGENT_EXE_NAME = "ggnet-agent.exe"
FILES = (AGENT_EXE_NAME, "install.ps1", "uninstall.ps1")
VERSION_FILE = "VERSION"


@dataclass(frozen=True)
class PackageFile:
    name: str
    size: int
    sha256: str


@dataclass(frozen=True)
class Package:
    version: str | None
    files: tuple[PackageFile, ...]


class AgentPackage:
    def __init__(self, directory: Path):
        self.directory = directory
        self._lock = threading.Lock()
        self._cache: tuple[tuple, Package] | None = None

    def _stamp(self) -> tuple | None:
        """Size and mtime of every file; None when one is missing."""
        stamp = []
        for name in FILES:
            try:
                st = (self.directory / name).stat()
            except OSError:
                return None
            stamp.append((name, st.st_size, st.st_mtime_ns))
        return tuple(stamp)

    def info(self) -> Package | None:
        """The package with checksums (computed once per change), or None if incomplete."""
        stamp = self._stamp()
        if stamp is None:
            return None
        with self._lock:
            if self._cache and self._cache[0] == stamp:
                return self._cache[1]
            files = tuple(PackageFile(name, size, _sha256(self.directory / name)) for name, size, _ in stamp)
            package = Package(_read_version(self.directory / VERSION_FILE), files)
            self._cache = (stamp, package)
            return package

    def path(self, name: str) -> Path | None:
        """A package file by name; only the known names, never a path from the request."""
        if name not in FILES:
            return None
        p = self.directory / name
        return p if p.is_file() else None

    def zip(self) -> Path | None:
        """A zip of the package, rebuilt when a file changed."""
        package = self.info()
        if package is None:
            return None
        key = "-".join(f.sha256[:12] for f in package.files)
        cache = self.directory / ".cache"
        target = cache / f"ggnet-agent-{key}.zip"
        with self._lock:
            if target.is_file():
                return target
            cache.mkdir(exist_ok=True)
            for old in cache.glob("ggnet-agent-*.zip"):
                old.unlink(missing_ok=True)
            tmp = target.with_suffix(".tmp")
            with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as z:
                for f in package.files:
                    z.write(self.directory / f.name, f"ggnet-agent/{f.name}")
                if package.version:
                    z.writestr(f"ggnet-agent/{VERSION_FILE}", package.version + "\n")
            os.replace(tmp, target)
            return target


@lru_cache(maxsize=1)
def default_package() -> AgentPackage:
    """The package in [paths] agent_dir (default <data_dir>/agent), one per process."""
    paths = get_config()["paths"]
    return AgentPackage(Path(paths.get("agent_dir") or Path(paths["data_dir"]) / "agent"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_version(path: Path) -> str | None:
    try:
        v = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    # A version string only: it is shown in the UI and the zip name.
    return v[:64] if v and all(c.isalnum() or c in ".+-" for c in v) else None


def bootstrap_script(server_url: str, package: Package) -> str:
    """PowerShell for `irm <server>/api/v1/agent/bootstrap.ps1 | iex` in an admin PowerShell."""
    hashes = "\n".join(f"    '{f.name}' = '{f.sha256}'" for f in package.files)
    return f"""# ggNet agent installer, made by the ggNet server for {server_url}
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) {{ throw 'Run PowerShell as Administrator' }}

$server = '{server_url}'
$dir = Join-Path $env:ProgramData 'ggnet-agent-setup'
New-Item -ItemType Directory -Force $dir | Out-Null
$files = @{{
{hashes}
}}
foreach ($name in $files.Keys) {{
    $out = Join-Path $dir $name
    Write-Host "Downloading $name..."
    Invoke-WebRequest -UseBasicParsing "$server/api/v1/agent/download/$name" -OutFile $out
    if ((Get-FileHash $out -Algorithm SHA256).Hash.ToLower() -ne $files[$name]) {{
        throw "Checksum mismatch for $name; download it again"
    }}
}}
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $dir 'install.ps1') -ServerUrl $server
if ($LASTEXITCODE -ne 0) {{ throw "install.ps1 failed with exit code $LASTEXITCODE" }}
"""
