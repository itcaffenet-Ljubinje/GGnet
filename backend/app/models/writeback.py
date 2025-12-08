"""
Writeback model for machine writeback files
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Mapped, mapped_column, relationship  # pyright: ignore[reportMissingImports]
from sqlalchemy.sql import func  # pyright: ignore[reportMissingImports]

from app.core.database import Base


class Writeback(Base):
    """Writeback file model"""
    __tablename__ = "writebacks"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Relationships
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), nullable=False, index=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("images.id"), nullable=False, index=True)
    
    # File information
    path: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True, index=True)
    size: Mapped[int] = mapped_column(BigInteger, default=0)
    
    # Status
    is_permanent: Mapped[bool] = mapped_column(default=False)  # If True, don't delete on reset
    
    # Timestamps
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
    
    # Relationships
    machine = relationship("Machine", back_populates="writebacks")
    image = relationship("Image", back_populates="writebacks")
    
    def __repr__(self) -> str:
        return f"<Writeback(id={self.id}, machine_id={self.machine_id}, path='{self.path}')>"




