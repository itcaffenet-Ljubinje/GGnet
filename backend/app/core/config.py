"""
Application configuration using Pydantic Settings
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "sqlite:///./ggnet.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # File Storage
    UPLOAD_DIR: Path = Path("./uploads")
    IMAGES_DIR: Path = Path("./images")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024 * 1024  # 10GB
    ALLOWED_IMAGE_FORMATS: str = "vhd,vhdx,raw,qcow2"  # Comma-separated string from env
    
    # iSCSI Configuration
    ISCSI_TARGET_PREFIX: str = "iqn.2025.ggnet"
    ISCSI_PORTAL_IP: str = "0.0.0.0"
    ISCSI_PORTAL_PORT: int = 3260
    TARGETCLI_PATH: str = "/usr/bin/targetcli"
    QEMU_IMG_PATH: str = "/usr/bin/qemu-img"
    
    # Network Boot
    TFTP_ROOT: Path = Path("/var/lib/tftpboot")
    IPXE_SCRIPT_PATH: Path = Path("/var/lib/tftpboot/boot.ipxe")
    UEFI_BOOT_PATH: Path = Path("/var/lib/tftpboot/bootx64.efi")
    
    # Security Settings
    RATE_LIMIT_UPLOADS: str = "5/minute"
    ENABLE_ANTIVIRUS_SCAN: bool = False
    ANTIVIRUS_COMMAND: str = "clamdscan"
    
    # Monitoring & Logging
    AUDIT_LOG_FILE: Path = Path("./logs/audit.log")
    ERROR_LOG_FILE: Path = Path("./logs/error.log")
    SENTRY_DSN: Optional[str] = None
    
    # Email Notifications
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@ggnet.local"
    
    # Backup Configuration
    BACKUP_DIR: Path = Path("./backups")
    BACKUP_RETENTION_DAYS: int = 30
    AUTO_BACKUP_ENABLED: bool = True
    AUTO_BACKUP_SCHEDULE: str = "0 2 * * *"  # Daily at 2 AM
    
    @field_validator("UPLOAD_DIR", "IMAGES_DIR", "BACKUP_DIR", mode="before")
    @classmethod
    def create_directories(cls, v):
        """Create directories if they don't exist"""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @field_validator("AUDIT_LOG_FILE", "ERROR_LOG_FILE", mode="before")
    @classmethod
    def create_log_directories(cls, v):
        """Create log directories if they don't exist"""
        path = Path(v)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    
    @field_validator("ALLOWED_IMAGE_FORMATS", mode="before")
    @classmethod
    def validate_image_formats(cls, v):
        """Validate image formats"""
        # Handle list input (default value)
        if isinstance(v, list):
            allowed = {"vhd", "vhdx", "raw", "qcow2", "vmdk", "vdi"}
            for fmt in v:
                if fmt.lower() not in allowed:
                    raise ValueError(f"Unsupported image format: {fmt}")
            return ",".join([fmt.lower() for fmt in v])
        
        # Handle string input (comma-separated values from env)
        if isinstance(v, str):
            if not v.strip():
                return "vhd,vhdx,raw,qcow2"  # Default values
            # Validate the formats
            formats = [fmt.strip() for fmt in v.split(",") if fmt.strip()]
            allowed = {"vhd", "vhdx", "raw", "qcow2", "vmdk", "vdi"}
            for fmt in formats:
                if fmt.lower() not in allowed:
                    raise ValueError(f"Unsupported image format: {fmt}")
            return ",".join([fmt.lower() for fmt in formats])
        
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def allowed_image_formats_list(self) -> List[str]:
        """Get allowed image formats as a list"""
        if not self.ALLOWED_IMAGE_FORMATS.strip():
            return ["vhd", "vhdx", "raw", "qcow2"]
        return [fmt.strip() for fmt in self.ALLOWED_IMAGE_FORMATS.split(",") if fmt.strip()]
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL"""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
        return self.DATABASE_URL
    
    @property
    def database_url_async(self) -> str:
        """Get asynchronous database URL"""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        elif self.DATABASE_URL.startswith("sqlite://"):
            return self.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
        return self.DATABASE_URL
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

