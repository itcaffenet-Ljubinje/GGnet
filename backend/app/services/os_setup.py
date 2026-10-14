"""
What a Boot Mode PC's Windows is told about itself at every fresh OS
writeback (app.windows_setup): its computer name, and environment variables
the agent and other software on the PC can read instead of being configured
in the image.
"""

from __future__ import annotations

from app.config import server_url
from app.db.models import Machine, MachineMode
from app.windows_setup import OsSetup


def os_setup_for(m: Machine) -> OsSetup | None:
    """None for a Disk Mode PC: its Windows is its own."""
    if m.mode is not MachineMode.BOOT:
        return None
    return OsSetup(m.name, {
        "GGNET_SERVER": server_url(),
        "GGNET_MACHINE_ID": str(m.id),
        "GGNET_MACHINE_NAME": m.name,
    })
