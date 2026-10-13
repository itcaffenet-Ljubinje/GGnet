"""
Boot Mode: the iPXE script for one PC, by its MAC address.

iPXE (with the script embedded at build time, docs/architecture.md section 4)
asks `GET /api/v1/boot/ipxe?mac=aa-bb-cc-dd-ee-ff` right after DHCP. The
answer is always a script, never an HTTP error, so a PC that ggNet does not
boot falls through to its next boot device instead of stopping in iPXE:

  Boot Mode PC with its disks   sanboot from the shared target, LUN 0 (OS);
                                Windows sees LUN 1 (game disk) on the same session
  Boot Mode PC without disks    message, then exit
  Disk Mode PC, unknown MAC     exit (boot from the local disk)

Before it answers a provisioned PC, the server discards its writebacks like
the watcher does after a disconnect (app.services.writebacks), unless the PC
keeps its writeback. No authentication yet (planned with JWT); the script
only names the PC's own initiator IQN, which the ACL is bound to.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_provisioner, get_writeback_settings
from app.api.v1.schemas import _mac
from app.db.models import Machine, MachineMode, MachineStatus
from app.db.session import get_db
from app.services.provisioning import Provisioner
from app.services.writebacks import WritebackSettings, on_ipxe

logger = logging.getLogger("ggnet.api.boot")

router = APIRouter(prefix="/boot", tags=["boot"])


def _script(*lines: str) -> PlainTextResponse:
    return PlainTextResponse("#!ipxe\n" + "\n".join(lines) + "\n")


def exit_script(message: str) -> PlainTextResponse:
    """Leave iPXE: the firmware goes on with its next boot device."""
    return _script(f"echo {message}", "sleep 5", "exit")


def sanboot_script(m: Machine, portal_ip: str, portal_port: int, target_iqn: str) -> PlainTextResponse:
    """
    No `--no-describe`: Windows needs the iBFT table iPXE writes to keep
    booting from iSCSI. `initiator-iqn` must be the PC's ACL, or LIO refuses
    the login.
    """
    host = f"[{portal_ip}]" if ":" in portal_ip else portal_ip
    os_disk, game = m.os_disk, m.game_disk
    os_version = (m.os_clone_snapshot or "").partition("@")[2]
    game_version = (m.clone_snapshot or "").partition("@")[2]
    return _script(
        f"set initiator-iqn {m.initiator_iqn}",
        f"set root-path iscsi:{host}::{portal_port}:0:{target_iqn}",
        f"echo ggNet: booting {m.name} ({os_disk.name} {os_version}, {game.name} {game_version})",
        "sanboot ${root-path} || goto failed",
        ":failed",
        "echo Boot failed, retrying in 10 s",
        "sleep 10",
        "reboot",
    )


def _find(db: Session, mac: str) -> Machine | None:
    """The machine with this MAC set by the admin, else the one whose agent reported it."""
    return (db.scalar(select(Machine).where(Machine.mac == mac))
            or db.scalar(select(Machine).where(Machine.reported_mac == mac).order_by(Machine.id)))


@router.get("/ipxe", response_class=PlainTextResponse)
def ipxe_script(
    mac: str = "",
    db: Session = Depends(get_db),
    prov: Provisioner = Depends(get_provisioner),
    settings: WritebackSettings = Depends(get_writeback_settings),
):
    try:
        mac = _mac(mac)
    except ValueError:
        mac = None
    if mac is None:
        return exit_script("ggNet: no valid MAC address in the request. Booting from local disk.")

    m = _find(db, mac)
    if m is None:
        logger.info("iPXE request from unregistered MAC %s", mac)
        return exit_script(f"This PC is not registered in ggNet ({mac}). Booting from local disk.")
    if m.mode is not MachineMode.BOOT:
        return exit_script(f"ggNet: {m.name} is in Disk Mode. Booting from local disk.")
    if m.status is not MachineStatus.PROVISIONED or m.os_clone_zvol is None:
        reason = m.last_error if m.status is MachineStatus.ERROR else "it has no OS image and game disk"
        logger.warning("iPXE request from %s, which cannot boot: %s", m.name, reason)
        return exit_script(f"ggNet: {m.name} cannot boot from the network: {reason}")

    if not on_ipxe(db, prov, m, settings):
        logger.error("iPXE request from %s: %s", m.name, m.last_error)
        return exit_script(f"ggNet: {m.name} cannot boot from the network: {m.last_error}")
    logger.info("iPXE: %s boots %s + %s", m.name, m.os_clone_snapshot, m.clone_snapshot)
    return sanboot_script(m, prov.iscsi.portal_ip, prov.iscsi.portal_port, m.iscsi_target_iqn)
