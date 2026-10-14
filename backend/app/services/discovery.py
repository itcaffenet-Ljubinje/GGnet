"""
Discovery: PCs that knock but are not registered (ggRock adds them to the
Machines list on their first PXE boot). Two sources:

  pxe     an unknown MAC asked GET /boot/ipxe (Boot Mode, before Windows)
  agent   a ggnet-agent sent a heartbeat that matches no machine (Disk Mode)

The admin adds one as a machine (claim) or ignores it. Both endpoints are
open to the LAN, so the table is capped: when it is full, new MACs are only
logged until the admin clears some.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.models import DiscoveredMachine, DiscoverySource, Machine

logger = logging.getLogger("ggnet.discovery")

MAX_DISCOVERED = 500


def record(
    db: Session,
    mac: str,
    source: DiscoverySource,
    *,
    hostname: str | None = None,
    ip_address: str | None = None,
    agent_version: str | None = None,
) -> DiscoveredMachine | None:
    """Note a knock from an unregistered MAC (normalized aa:bb:..); commits."""
    if db.scalar(select(Machine.id).where(Machine.mac == mac)) is not None:
        return None
    now = datetime.now(timezone.utc)
    row = db.scalar(select(DiscoveredMachine).where(DiscoveredMachine.mac == mac))
    if row is None:
        if db.scalar(select(func.count()).select_from(DiscoveredMachine)) >= MAX_DISCOVERED:
            logger.warning("Discovery list is full (%d); not recording %s", MAX_DISCOVERED, mac)
            return None
        row = DiscoveredMachine(mac=mac, source=source, first_seen_at=now, seen_count=0)
        db.add(row)
    row.seen_count += 1
    row.last_seen_at = now
    # An agent tells more than iPXE; keep what it said when iPXE knocks later.
    if source is DiscoverySource.AGENT or row.source is DiscoverySource.PXE:
        row.source = source
    if hostname:
        row.hostname = hostname[:64]
    if ip_address:
        row.ip_address = ip_address[:45]
    if agent_version:
        row.agent_version = agent_version[:32]
    db.commit()
    return row


def forget(db: Session, mac: str | None) -> None:
    """Drop the row of a MAC that is now a machine (the caller commits)."""
    if mac:
        db.execute(delete(DiscoveredMachine).where(DiscoveredMachine.mac == mac))
