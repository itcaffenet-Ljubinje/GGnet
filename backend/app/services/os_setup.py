"""
What a Boot Mode PC's Windows is told about itself at every fresh OS
writeback (app.windows_setup): its computer name, environment variables
the agent and other software on the PC can read instead of being configured
in the image, its boot network card (Add hardware), and the server's agent.
"""

from __future__ import annotations

from app.config import get_config, server_url
from app.db.models import Machine, MachineMode
from app.services.agent_package import AGENT_EXE_NAME, default_package
from app.windows_setup import AgentInstall, OsSetup


def agent_install() -> AgentInstall | None:
    """
    The server's agent for the writebacks: none without a package, or when
    `[boot] inject_agent = false` (the image then carries its own agent).
    """
    if not (get_config().get("boot") or {}).get("inject_agent", True):
        return None
    package = default_package()
    info = package.info()
    exe = package.path(AGENT_EXE_NAME)
    if info is None or exe is None:
        return None
    sha = next(f.sha256 for f in info.files if f.name == AGENT_EXE_NAME)
    return AgentInstall(exe=exe, sha256=sha, server_url=server_url())


def os_setup_for(m: Machine) -> OsSetup | None:
    """None for a Disk Mode PC: its Windows is its own."""
    if m.mode is not MachineMode.BOOT:
        return None
    return OsSetup(m.name, {
        "GGNET_SERVER": server_url(),
        "GGNET_MACHINE_ID": str(m.id),
        "GGNET_MACHINE_NAME": m.name,
    }, boot_nic=m.boot_nic, agent=agent_install())
