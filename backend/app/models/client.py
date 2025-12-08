"""
Client model for Windows client connections
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, String, JSON  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Mapped, mapped_column, relationship  # pyright: ignore[reportMissingImports]
from sqlalchemy.sql import func  # pyright: ignore[reportMissingImports]

from app.core.database import Base


class ClientStatus(str, Enum):
    """Client status"""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


class Client(Base):
    """Windows client model"""
    __tablename__ = "clients"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # Machine relationship
    machine_id: Mapped[Optional[int]] = mapped_column(ForeignKey("machines.id"), nullable=True, index=True)
    machine = relationship("Machine", back_populates="clients")
    
    # Client information
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(15), nullable=True, index=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Status
    status: Mapped[ClientStatus] = mapped_column(
        SQLEnum(ClientStatus),
        default=ClientStatus.OFFLINE,
        nullable=False,
        index=True
    )
    
    # Metadata
    client_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Timestamps
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<Client(id={self.id}, client_id='{self.client_id}', status='{self.status}')>"




