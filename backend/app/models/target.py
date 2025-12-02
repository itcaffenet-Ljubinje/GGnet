"""
Target model for iSCSI target management
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.database import Base


class TargetStatus(str, Enum):
    """iSCSI target status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class Target(Base):
    """iSCSI target model"""
    
    __tablename__ = "targets"
    
    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(String(100), unique=True, index=True, nullable=False)
    iqn = Column(String(255), unique=True, index=True, nullable=False)
    
    # Foreign keys
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Target configuration
    image_path = Column(String(500), nullable=False)
    initiator_iqn = Column(String(255), nullable=False)
    lun_id = Column(Integer, default=0, nullable=False)
    status = Column(SQLEnum(TargetStatus), default=TargetStatus.PENDING, nullable=False)
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    machine = relationship("Machine", back_populates="targets")
    image = relationship("Image", back_populates="targets")
    creator = relationship("User", back_populates="created_targets")
    sessions = relationship("Session", back_populates="target")
    
    def __repr__(self):
        return f"<Target(id={self.id}, target_id='{self.target_id}', iqn='{self.iqn}')>"