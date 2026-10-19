"""
Boot Mode: the iPXE script for one PC, by its MAC address.

iPXE (with the script embedded at build time, docs/architecture.md section 4)
asks `GET /api/v1/boot/ipxe?mac=aa-bb-cc-dd-ee-ff` right after DHCP. The
answer is always a script, never an HTTP error, so a PC that ggNet does not
boot falls through to its next boot device instead of stopping in iPXE:

  Boot Mode PC with its disks   sanboot from the shared target, LUN 0 (OS);
                                Windows sees LUN 1 (game disk) on the same session
  Boot Mode PC without disks    message, then exit
  Disk Mode PC                  exit (boot from the local disk)
  unknown MAC                   listed in Discovery (Machines → New PCs) and,
                                like ggRock, waits on screen until the admin
                                registers it, asking iPXE again every 10 s; a
                                key press boots the local disk instead.
                                `[boot] unregistered = "local"` exits at once
                                (also set in the web UI: Settings → Network boot).

autoexec.ipxe (scripts/install_ggnet.sh) also sends the boot NIC's PCI IDs
(pci, cls, sub, rev); the server keeps them as the PC's `boot_nic` and adds
that card to its OS writeback when the image knows the chip only in another
revision or board (Add hardware, app.windows_setup).

Before it answers a provisioned PC, the server discards its writebacks like
the watcher does after a disconnect (app.services.writebacks), unless the PC
keeps its writeback. No authentication yet (planned with JWT); the script
only names the PC's own initiator IQN, which the ACL is bound to.
"""

from __future__ import annotations

import ipaddress
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_provisioner, get_writeback_settings
from app.config import get_config
from app.api.v1.schemas import _mac
from app.db.models import DiscoverySource, Machine, MachineMode, MachineStatus
from app.db.session import get_db
from app.services import discovery, pxe
from app.services.provisioning import Provisioner
from app.services.writebacks import WritebackSettings, on_ipxe

logger = logging.getLogger("ggnet.api.boot")

router = APIRouter(prefix="/boot", tags=["boot"])


def _script(*lines: str) -> PlainTextResponse:
    return PlainTextResponse("#!ipxe\n" + "\n".join(lines) + "\n")


def exit_script(message: str) -> PlainTextResponse:
    """Leave iPXE: the firmware goes on with its next boot device."""
    return _script(f"echo {message}", "sleep 5", "exit")


WAIT_SECONDS = 10


def wait_script(mac: str, again_url: str) -> PlainTextResponse:
    """
    An unregistered PC waits until it is registered: every WAIT_SECONDS it
    asks for its script again (the same URL), so it boots as soon as the admin
    adds it, with no reboot. Any key leaves iPXE for the local disk.
    """
    return _script(
        f"echo ggNet: this PC is not registered (MAC {mac}).",
        "echo Register it in the ggNet web UI: Machines -> New PCs. It boots as soon as it is registered.",
        ":wait",
        f"prompt --timeout {WAIT_SECONDS * 1000} Waiting for registration. Press any key to boot from the local disk. "
        "&& goto local || goto again",
        ":again",
        f"chain --replace --autofree {again_url} || goto wait",
        ":local",
        "echo Booting from the local disk.",
        "exit",
    )


def unregistered_mode(cfg: dict | None = None) -> str:
    """`[boot] unregistered`: "wait" (the default, as ggRock) or "local"."""
    value = str(((cfg if cfg is not None else get_config()).get("boot") or {}).get("unregistered") or "wait")
    if value not in ("wait", "local"):
        logger.error("Ignoring invalid [boot] unregistered %r; using wait", value)
        return "wait"
    return value


NO_GATEWAY = "0.0.0.0"


def boot_gateway(cfg: dict | None = None) -> str | None:
    """
    The gateway iPXE puts into the iBFT for Windows; None keeps the DHCP one.

    By default 0.0.0.0. With the router's gateway in the iBFT, Windows lost
    its iSCSI disk as it took over from iPXE (INACCESSIBLE_BOOT_DEVICE;
    vip-05, 2026-10-16, A/B on the same image); with 0.0.0.0 it boots, and
    Windows still gets its default route and internet afterwards.
    `[boot] gateway` in config.toml: "none" (the default), "dhcp" (the
    router's gateway), or an IP (e.g. the ggNet server with IP forwarding,
    as ggRock does). An invalid value falls back to the default.
    """
    value = str(((cfg if cfg is not None else get_config()).get("boot") or {}).get("gateway") or "").strip()
    if value in ("", "none"):
        return NO_GATEWAY
    if value == "dhcp":
        return None
    try:
        return str(ipaddress.IPv4Address(value))
    except ValueError:
        logger.error("Ignoring invalid [boot] gateway %r; using %s", value, NO_GATEWAY)
        return NO_GATEWAY


def sanboot_script(m: Machine, portal_ip: str, portal_port: int, target_iqn: str,
                   gateway: str | None = None) -> PlainTextResponse:
    """
    No `--no-describe`: Windows needs the iBFT table iPXE writes to keep
    booting from iSCSI. `initiator-iqn` must be the PC's ACL, or LIO refuses
    the login. `gateway` (boot_gateway()) replaces the DHCP gateway in it.
    """
    host = f"[{portal_ip}]" if ":" in portal_ip else portal_ip
    os_disk, game = m.os_disk, m.game_disk
    os_version = (m.os_clone_snapshot or "").partition("@")[2]
    game_version = (m.clone_snapshot or "").partition("@")[2]
    return _script(
        *([f"set netX/gateway {gateway}"] if gateway else []),
        f"set initiator-iqn {m.initiator_iqn}",
        f"set root-path iscsi:{host}::{portal_port}:0:{target_iqn}",
        f"echo ggNet: booting {m.name} ({os_disk.name} {os_version}, {game.name} {game_version})",
        "sanboot ${root-path} || goto failed",
        ":failed",
        "echo Boot failed, retrying in 10 s",
        "sleep 10",
        "reboot",
    )


def boot_nic_id(pci: str, cls: str, sub: str, rev: str) -> str | None:
    """
    The boot NIC's hardware ID as Windows names it, from PCI config space as
    iPXE reads it (hexraw, highest byte first): `pci` offset 0, 4 bytes
    (device, vendor), `cls` offset 9, 3 bytes (class, subclass, interface),
    `sub` offset 0x2c, 4 bytes (subsystem, subsystem vendor), `rev` offset 8.
    None unless it is a network controller (class 02), so a misread device
    never gets a network card's driver.
    """
    parts = [v.strip().lower().replace(":", "") for v in (pci, cls, sub, rev)]
    if [len(v) for v in parts] != [8, 6, 8, 2] or not all(
            all(c in "0123456789abcdef" for c in v) for v in parts):
        return None
    pci, cls, sub, rev = (v.upper() for v in parts)
    if not cls.startswith("02") or pci[4:] in ("FFFF", "0000"):
        return None
    return f"VEN_{pci[4:]}&DEV_{pci[:4]}&SUBSYS_{sub}&REV_{rev}"


def _find(db: Session, mac: str) -> Machine | None:
    """The machine with this MAC set by the admin, else the one whose agent reported it."""
    return (db.scalar(select(Machine).where(Machine.mac == mac))
            or db.scalar(select(Machine).where(Machine.reported_mac == mac).order_by(Machine.id)))


# What autoexec.ipxe (scripts/install_ggnet.sh) reads from the boot NIC's PCI
# config space before it asks for the script; empty when it could not.
NIC_QUERY = "&pci=${ggnet_pci}&cls=${ggnet_cls}&sub=${ggnet_sub}&rev=${ggnet_rev}"


@router.get("/ipxe", response_class=PlainTextResponse)
def ipxe_script(
    request: Request,
    mac: str = "",
    pci: str = "",
    cls: str = "",
    sub: str = "",
    rev: str = "",
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

    # [boot] settings: config.toml's, or the ones saved in the web UI.
    cfg = pxe.effective_config(db)
    nic = boot_nic_id(pci, cls, sub, rev)
    m = _find(db, mac)
    if m is None:
        logger.info("iPXE request from unregistered MAC %s", mac)
        discovery.record(db, mac, DiscoverySource.PXE,
                         ip_address=request.client.host if request.client else None, boot_nic=nic)
        if unregistered_mode(cfg) == "local":
            return exit_script(f"This PC is not registered in ggNet ({mac}). Booting from local disk.")
        # ${net0/mac} is iPXE's, so the PC asks with its own MAC like the first time.
        return wait_script(mac, f"{request.base_url}api/v1/boot/ipxe?mac=${{net0/mac}}{NIC_QUERY}")
    if m.mode is not MachineMode.BOOT:
        return exit_script(f"ggNet: {m.name} is in Disk Mode. Booting from local disk.")
    if m.status is not MachineStatus.PROVISIONED or m.os_clone_zvol is None:
        reason = m.last_error if m.status is MachineStatus.ERROR else "it has no OS image and game disk"
        logger.warning("iPXE request from %s, which cannot boot: %s", m.name, reason)
        return exit_script(f"ggNet: {m.name} cannot boot from the network: {reason}")

    if not on_ipxe(db, prov, m, settings, boot_nic=nic):
        logger.error("iPXE request from %s: %s", m.name, m.last_error)
        return exit_script(f"ggNet: {m.name} cannot boot from the network: {m.last_error}")
    logger.info("iPXE: %s boots %s + %s", m.name, m.os_clone_snapshot, m.clone_snapshot)
    return sanboot_script(m, prov.iscsi.portal_ip, prov.iscsi.portal_port, m.iscsi_target_iqn,
                          boot_gateway(cfg))
