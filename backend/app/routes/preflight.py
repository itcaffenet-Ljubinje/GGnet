"""
Pre-flight checks API endpoints
Provides system validation before operations
"""

from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel, ConfigDict
import structlog
import shutil
import subprocess
import socket
from pathlib import Path

from app.core.dependencies import get_db, get_current_user, require_operator
from app.core.cache import cache_manager
from app.core.config import get_settings
from app.models.user import User

router = APIRouter(tags=["preflight"])
logger = structlog.get_logger()
settings = get_settings()


class PreflightCheckResult(BaseModel):
    name: str
    status: str  # "pass" or "fail"
    message: str
    details: Dict[str, Any] = {}


class PreflightResponse(BaseModel):
    summary: Dict[str, Any]
    checks: List[PreflightCheckResult]


async def check_database(db: AsyncSession) -> tuple[bool, str, Dict[str, Any]]:
    """Check PostgreSQL connectivity"""
    try:
        result = await db.execute(text("SELECT 1"))
        row = result.fetchone()
        if row and row[0] == 1:
            return True, "Database connection OK", {}
        return False, "Database query failed", {}
    except Exception as e:
        return False, f"Database error: {str(e)}", {"error": str(e)}


async def check_redis() -> tuple[bool, str, Dict[str, Any]]:
    """Check Redis connectivity"""
    try:
        await cache_manager.set("preflight_test", "ok", ttl=10)
        value = await cache_manager.get("preflight_test")
        
        if value == "ok":
            await cache_manager.delete("preflight_test")
            return True, "Redis connection OK", {}
        return False, "Redis test failed", {}
    except Exception as e:
        return False, f"Redis error: {str(e)}", {"error": str(e)}


def check_storage() -> tuple[bool, str, Dict[str, Any]]:
    """Check storage space"""
    try:
        images_dir = Path(settings.IMAGES_DIR)
        if not images_dir.exists():
            images_dir.mkdir(parents=True, exist_ok=True)
        
        stat = shutil.disk_usage(images_dir)
        free_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        used_percent = (stat.used / stat.total) * 100
        
        details = {
            "free_gb": round(free_gb, 2),
            "total_gb": round(total_gb, 2),
            "used_percent": round(used_percent, 2),
            "path": str(images_dir)
        }
        
        if free_gb < 10:
            return False, f"Low disk space: {free_gb:.1f}GB free (< 10GB)", details
        
        if used_percent > 95:
            return False, f"Disk usage too high: {used_percent:.1f}% (> 95%)", details
        
        return True, f"Storage OK: {free_gb:.1f}GB free / {total_gb:.1f}GB total", details
    except Exception as e:
        return False, f"Storage check error: {str(e)}", {"error": str(e)}


async def check_iscsi() -> tuple[bool, str, Dict[str, Any]]:
    """Check targetcli availability"""
    try:
        result = subprocess.run(
            ["which", "targetcli"],
            capture_output=True,
            timeout=5
        )
        
        details = {}
        if result.returncode == 0:
            path = result.stdout.decode().strip()
            details["path"] = path
            return True, f"targetcli available: {path}", details
        return False, "targetcli not found in PATH", details
    except FileNotFoundError:
        return False, "targetcli not installed", {}
    except Exception as e:
        return False, f"targetcli check error: {str(e)}", {"error": str(e)}


def check_network_interfaces() -> tuple[bool, str, Dict[str, Any]]:
    """Check network interfaces"""
    try:
        hostname = socket.gethostname()
        
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        
        details = {"hostname": hostname, "ip": ip}
        
        if ip == '127.0.0.1':
            return False, "No network interfaces found (only loopback)", details
        
        return True, f"Network OK: {hostname} ({ip})", details
    except Exception as e:
        return False, f"Network check error: {str(e)}", {"error": str(e)}


def check_dhcp_config() -> tuple[bool, str, Dict[str, Any]]:
    """Check dnsmasq configuration"""
    try:
        # Check for dnsmasq config
        dnsmasq_conf = Path("docker/dnsmasq/dnsmasq.conf")
        if not dnsmasq_conf.exists():
            dnsmasq_conf = Path("/etc/dnsmasq.conf")
        
        details = {"config_path": str(dnsmasq_conf)}
        
        if not dnsmasq_conf.exists():
            return False, "dnsmasq config file not found", details
        
        content = dnsmasq_conf.read_text()
        details["file_exists"] = True
        
        issues = []
        # Check for dnsmasq-specific configuration
        if "dhcp-range" not in content:
            issues.append("missing_dhcp_range")
        
        if "dhcp-match" not in content and "dhcp-boot" not in content:
            issues.append("missing_pxe_config")
        
        if "snponly.efi" not in content and "ipxe.efi" not in content and "undionly.kpxe" not in content:
            issues.append("missing_boot_files")
        
        if "enable-tftp" not in content:
            issues.append("tftp_not_enabled")
        
        if issues:
            return False, f"dnsmasq config issues: {', '.join(issues)}", {**details, "issues": issues}
        
        return True, "dnsmasq configuration OK", details
    except Exception as e:
        return False, f"dnsmasq config check error: {str(e)}", {"error": str(e)}


def check_tftp_files() -> tuple[bool, str, Dict[str, Any]]:
    """Check TFTP boot files"""
    try:
        tftp_dir = Path(settings.TFTP_ROOT)
        if not tftp_dir.exists():
            tftp_dir = Path("/var/lib/tftpboot")
        
        details = {"tftp_dir": str(tftp_dir)}
        
        if not tftp_dir.exists():
            return False, "TFTP directory not found", details
        
        required_files = ["snponly.efi", "ipxe.efi", "undionly.kpxe"]
        missing = []
        present = []
        
        for file in required_files:
            file_path = tftp_dir / file
            if file_path.exists():
                present.append(file)
            else:
                missing.append(file)
        
        details["required_files"] = required_files
        details["present"] = present
        details["missing"] = missing
        
        if missing:
            return False, f"Missing TFTP files: {', '.join(missing)}", details
        
        return True, f"TFTP files OK ({len(required_files)} files present)", details
    except Exception as e:
        return False, f"TFTP check error: {str(e)}", {"error": str(e)}


@router.get("", response_model=PreflightResponse)
async def run_preflight_checks(
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Run all pre-flight system checks"""
    checks = []
    
    # Database
    ok, msg, details = await check_database(db)
    checks.append(PreflightCheckResult(
        name="database",
        status="pass" if ok else "fail",
        message=msg,
        details=details
    ))
    
    # Redis
    ok, msg, details = await check_redis()
    checks.append(PreflightCheckResult(
        name="redis",
        status="pass" if ok else "fail",
        message=msg,
        details=details
    ))
    
    # Storage
    ok, msg, details = check_storage()
    checks.append(PreflightCheckResult(
        name="storage",
        status="pass" if ok else "fail",
        message=msg,
        details=details
    ))
    
    # iSCSI
    ok, msg, details = await check_iscsi()
    checks.append(PreflightCheckResult(
        name="iscsi",
        status="pass" if ok else "fail",
        message=msg,
        details=details
    ))
    
    # Network
    ok, msg, details = check_network_interfaces()
    checks.append(PreflightCheckResult(
        name="network",
        status="pass" if ok else "fail",
        message=msg,
        details=details
    ))
    
    # DHCP
    ok, msg, details = check_dhcp_config()
    checks.append(PreflightCheckResult(
        name="dhcp",
        status="pass" if ok else "fail",
        message=msg,
        details=details
    ))
    
    # TFTP
    ok, msg, details = check_tftp_files()
    checks.append(PreflightCheckResult(
        name="tftp",
        status="pass" if ok else "fail",
        message=msg,
        details=details
    ))
    
    # Summary
    total = len(checks)
    passed = sum(1 for c in checks if c.status == "pass")
    failed = total - passed
    all_passed = failed == 0
    
    return PreflightResponse(
        summary={
            "total": total,
            "passed": passed,
            "failed": failed,
            "status": "ready" if all_passed else "not_ready"
        },
        checks=checks
    )


@router.get("/{check_name}", response_model=PreflightCheckResult)
async def run_single_check(
    check_name: str,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Run a single pre-flight check"""
    check_functions = {
        "database": lambda: check_database(db),
        "redis": check_redis,
        "storage": check_storage,
        "iscsi": check_iscsi,
        "network": check_network_interfaces,
        "dhcp": check_dhcp_config,
        "tftp": check_tftp_files
    }
    
    if check_name not in check_functions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown check: {check_name}. Available checks: {', '.join(check_functions.keys())}"
        )
    
    check_func = check_functions[check_name]
    
    if check_name == "database":
        ok, msg, details = await check_database(db)
    elif check_name in ["redis", "iscsi"]:
        ok, msg, details = await check_func()
    else:
        ok, msg, details = check_func()
    
    return PreflightCheckResult(
        name=check_name,
        status="pass" if ok else "fail",
        message=msg,
        details=details
    )

