"""
iPXE Binary Management API
Manages iPXE boot binaries including SecureBoot support
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
from pydantic import BaseModel, ConfigDict
from datetime import datetime
import structlog
import shutil
import hashlib

from app.core.dependencies import get_db, get_current_user, require_operator
from app.core.config import get_settings
from app.models.user import User

router = APIRouter(prefix="/ipxe-binaries", tags=["ipxe-binaries"])
logger = structlog.get_logger()
settings = get_settings()


class IPXEBinaryInfo(BaseModel):
    """iPXE binary information"""
    filename: str
    binary_type: str  # "snponly", "ipxe", "undionly", "ipxe32", "ipxe64"
    architecture: str  # "x86", "x64", "arm64"
    secureboot: bool
    version: Optional[str] = None
    size_bytes: int
    sha256_hash: str
    file_path: str
    uploaded_at: datetime
    description: Optional[str] = None


class IPXEBinaryResponse(BaseModel):
    """Response model for iPXE binary"""
    filename: str
    binary_type: str
    architecture: str
    secureboot: bool
    version: Optional[str]
    size_bytes: int
    sha256_hash: str
    download_url: str
    uploaded_at: datetime
    description: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


def get_tftp_directory() -> Path:
    """Get TFTP root directory"""
    tftp_dir = Path(settings.TFTP_ROOT)
    if not tftp_dir.exists():
        tftp_dir = Path("/var/lib/tftpboot")
        tftp_dir.mkdir(parents=True, exist_ok=True)
    return tftp_dir


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def detect_binary_type(filename: str) -> tuple[str, str, bool]:
    """
    Detect binary type, architecture, and SecureBoot support from filename
    
    Returns: (binary_type, architecture, secureboot)
    """
    filename_lower = filename.lower()
    
    # Detect SecureBoot
    secureboot = "snponly" in filename_lower or "secureboot" in filename_lower
    
    # Detect binary type
    if "snponly" in filename_lower:
        binary_type = "snponly"
    elif "undionly" in filename_lower:
        binary_type = "undionly"
    elif "ipxe32" in filename_lower or "i386" in filename_lower:
        binary_type = "ipxe32"
    elif "ipxe64" in filename_lower or "x64" in filename_lower or "amd64" in filename_lower:
        binary_type = "ipxe64"
    elif "ipxe" in filename_lower:
        binary_type = "ipxe"
    else:
        binary_type = "unknown"
    
    # Detect architecture
    if "x64" in filename_lower or "amd64" in filename_lower or "64" in filename_lower:
        architecture = "x64"
    elif "x86" in filename_lower or "i386" in filename_lower or "32" in filename_lower:
        architecture = "x86"
    elif "arm64" in filename_lower or "aarch64" in filename_lower:
        architecture = "arm64"
    else:
        architecture = "unknown"
    
    return binary_type, architecture, secureboot


@router.post("/upload", response_model=IPXEBinaryResponse, status_code=status.HTTP_201_CREATED)
async def upload_ipxe_binary(
    file: UploadFile = File(...),
    description: Optional[str] = None,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Upload an iPXE binary file"""
    tftp_dir = get_tftp_directory()
    
    # Validate file extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    allowed_extensions = [".efi", ".kpxe", ".pxe", ".com"]
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Detect binary properties
    binary_type, architecture, secureboot = detect_binary_type(file.filename)
    
    # Save file
    file_path = tftp_dir / file.filename
    
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        logger.error("Failed to save iPXE binary", error=str(e), filename=file.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Calculate file hash
    file_size = file_path.stat().st_size
    sha256_hash = calculate_sha256(file_path)
    
    logger.info(
        "iPXE binary uploaded",
        filename=file.filename,
        binary_type=binary_type,
        architecture=architecture,
        secureboot=secureboot,
        size_bytes=file_size
    )
    
    return IPXEBinaryResponse(
        filename=file.filename,
        binary_type=binary_type,
        architecture=architecture,
        secureboot=secureboot,
        version=None,  # Could be extracted from binary metadata
        size_bytes=file_size,
        sha256_hash=sha256_hash,
        download_url=f"/tftp/{file.filename}",
        uploaded_at=datetime.utcnow(),
        description=description
    )


@router.get("", response_model=List[IPXEBinaryResponse])
async def list_ipxe_binaries(
    binary_type: Optional[str] = None,
    architecture: Optional[str] = None,
    secureboot: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all available iPXE binaries"""
    tftp_dir = get_tftp_directory()
    
    if not tftp_dir.exists():
        return []
    
    binaries = []
    allowed_extensions = [".efi", ".kpxe", ".pxe", ".com"]
    
    for file_path in tftp_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in allowed_extensions:
            binary_type_detected, architecture_detected, secureboot_detected = detect_binary_type(file_path.name)
            
            # Apply filters
            if binary_type and binary_type_detected != binary_type:
                continue
            if architecture and architecture_detected != architecture:
                continue
            if secureboot is not None and secureboot_detected != secureboot:
                continue
            
            file_size = file_path.stat().st_size
            sha256_hash = calculate_sha256(file_path)
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            binaries.append(IPXEBinaryResponse(
                filename=file_path.name,
                binary_type=binary_type_detected,
                architecture=architecture_detected,
                secureboot=secureboot_detected,
                version=None,
                size_bytes=file_size,
                sha256_hash=sha256_hash,
                download_url=f"/tftp/{file_path.name}",
                uploaded_at=mtime,
                description=None
            ))
    
    return sorted(binaries, key=lambda b: b.uploaded_at, reverse=True)


@router.get("/{filename}", response_model=IPXEBinaryResponse)
async def get_ipxe_binary(
    filename: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get information about a specific iPXE binary"""
    tftp_dir = get_tftp_directory()
    file_path = tftp_dir / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"iPXE binary '{filename}' not found"
        )
    
    binary_type, architecture, secureboot = detect_binary_type(filename)
    file_size = file_path.stat().st_size
    sha256_hash = calculate_sha256(file_path)
    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    
    return IPXEBinaryResponse(
        filename=filename,
        binary_type=binary_type,
        architecture=architecture,
        secureboot=secureboot,
        version=None,
        size_bytes=file_size,
        sha256_hash=sha256_hash,
        download_url=f"/tftp/{filename}",
        uploaded_at=mtime,
        description=None
    )


@router.delete("/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ipxe_binary(
    filename: str,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Delete an iPXE binary"""
    tftp_dir = get_tftp_directory()
    file_path = tftp_dir / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"iPXE binary '{filename}' not found"
        )
    
    try:
        file_path.unlink()
        logger.info("iPXE binary deleted", filename=filename)
    except Exception as e:
        logger.error("Failed to delete iPXE binary", error=str(e), filename=filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.get("/recommended/{boot_mode}", response_model=IPXEBinaryResponse)
async def get_recommended_binary(
    boot_mode: str,  # "uefi", "uefi_secure", "legacy"
    architecture: str = "x64",  # "x86", "x64", "arm64"
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recommended iPXE binary for boot mode and architecture"""
    tftp_dir = get_tftp_directory()
    
    # Determine required binary type
    if boot_mode == "uefi_secure":
        required_type = "snponly"
        required_secureboot = True
    elif boot_mode == "uefi":
        required_type = "ipxe"
        required_secureboot = False
    else:  # legacy
        required_type = "undionly"
        required_secureboot = False
    
    # Find matching binary
    for file_path in tftp_dir.iterdir():
        if not file_path.is_file():
            continue
        
        binary_type, arch, secureboot = detect_binary_type(file_path.name)
        
        if (binary_type == required_type and 
            arch == architecture and 
            secureboot == required_secureboot):
            
            file_size = file_path.stat().st_size
            sha256_hash = calculate_sha256(file_path)
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            return IPXEBinaryResponse(
                filename=file_path.name,
                binary_type=binary_type,
                architecture=arch,
                secureboot=secureboot,
                version=None,
                size_bytes=file_size,
                sha256_hash=sha256_hash,
                download_url=f"/tftp/{file_path.name}",
                uploaded_at=mtime,
                description=None
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No suitable iPXE binary found for boot_mode={boot_mode}, architecture={architecture}"
    )

