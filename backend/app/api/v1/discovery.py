"""
API for Discovery: PCs that knocked (iPXE or agent) but are not registered
(app.services.discovery). The admin adds one as a machine with a name of
their choice (its MAC comes from the discovery, so its IQN is derived from
the MAC), ignores it, or removes it from the list.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_provisioner
from app.api.v1.errors import not_found
from app.api.v1.machines import create_machine
from app.api.v1.schemas import DiscoveredOut, DiscoveryClaim, MachineCreate, MachineOut
from app.db.models import DiscoveredMachine
from app.db.session import get_db
from app.services.provisioning import Provisioner

router = APIRouter(prefix="/discovery", tags=["discovery"])


def _get(db: Session, discovered_id: int) -> DiscoveredMachine:
    row = db.get(DiscoveredMachine, discovered_id)
    if row is None:
        not_found("Discovered PC", discovered_id)
    return row


@router.get("", response_model=list[DiscoveredOut])
def list_discovered(ignored: bool = False, db: Session = Depends(get_db)):
    """Newest first; ignored PCs only with `?ignored=true`."""
    query = select(DiscoveredMachine).order_by(DiscoveredMachine.last_seen_at.desc())
    if not ignored:
        query = query.where(DiscoveredMachine.ignored.is_(False))
    return db.scalars(query).all()


@router.post("/{discovered_id}/claim", response_model=MachineOut, status_code=status.HTTP_201_CREATED)
def claim(
    discovered_id: int,
    body: DiscoveryClaim,
    db: Session = Depends(get_db),
    prov: Provisioner = Depends(get_provisioner),
):
    """Add the PC as a machine, exactly like POST /machines with its MAC."""
    row = _get(db, discovered_id)
    create = MachineCreate(mac=row.mac, **body.model_dump())
    return create_machine(create, db, prov)   # also drops the discovery row


@router.post("/{discovered_id}/ignore", response_model=DiscoveredOut)
def ignore(discovered_id: int, db: Session = Depends(get_db)):
    """Hide the PC from the list; it stays hidden when it knocks again."""
    row = _get(db, discovered_id)
    row.ignored = True
    db.commit()
    return row


@router.delete("/{discovered_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove(discovered_id: int, db: Session = Depends(get_db)):
    """Remove the PC from the list; it comes back if it knocks again."""
    db.delete(_get(db, discovered_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
