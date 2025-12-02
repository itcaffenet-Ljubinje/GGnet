#!/usr/bin/env python3
"""
GGnet Pre-flight System Checks

Validates system configuration before accepting client connections.

Usage:
    python3 preflight.py [--json]
"""
import sys
import asyncio
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from sqlalchemy import text


async def check_database() -> Tuple[bool, str]:
    """Check PostgreSQL connectivity"""
    try:
        from app.core.database import get_async_engine
        
        async_engine = get_async_engine()
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                return True, "Database connection OK"
        return False, "Database query failed"
    except ImportError:
        return False, "Cannot import database module"
    except Exception as e:
        return False, f"Database error: {str(e)}"


async def check_redis() -> Tuple[bool, str]:
    """Check Redis connectivity"""
    try:
        from app.core.cache import cache_manager
        
        # Test Redis connection
        await cache_manager.set("preflight_test", "ok", ttl=10)
        value = await cache_manager.get("preflight_test")
        
        if value == "ok":
            await cache_manager.delete("preflight_test")
            return True, "Redis connection OK"
        return False, "Redis test failed"
    except ImportError:
        return False, "Cannot import cache module"
    except Exception as e:
        return False, f"Redis error: {str(e)}"


def check_storage() -> Tuple[bool, str]:
    """Check storage space"""
    try:
        # Check images directory
        images_dir = Path("/opt/ggnet/images")
        if not images_dir.exists():
            return False, f"Images directory does not exist: {images_dir}"
        
        stat = shutil.disk_usage(images_dir)
        free_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        used_percent = (stat.used / stat.total) * 100
        
        if free_gb < 10:
            return False, f"Low disk space: {free_gb:.1f}GB free (< 10GB)"
        
        if used_percent > 95:
            return False, f"Disk usage too high: {used_percent:.1f}% (> 95%)"
        
        return True, f"Storage OK: {free_gb:.1f}GB free / {total_gb:.1f}GB total ({100-used_percent:.1f}% available)"
    except Exception as e:
        return False, f"Storage check error: {str(e)}"


async def check_iscsi() -> Tuple[bool, str]:
    """Check targetcli availability"""
    try:
        import subprocess
        
        result = subprocess.run(
            ["which", "targetcli"],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return True, f"targetcli available: {result.stdout.decode().strip()}"
        return False, "targetcli not found in PATH"
    except FileNotFoundError:
        return False, "targetcli not installed"
    except Exception as e:
        return False, f"targetcli check error: {str(e)}"


def check_network_interfaces() -> Tuple[bool, str]:
    """Check network interfaces"""
    try:
        import socket
        
        # Get hostname
        hostname = socket.gethostname()
        
        # Get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't have to be reachable
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        
        if ip == '127.0.0.1':
            return False, "No network interfaces found (only loopback)"
        
        return True, f"Network OK: {hostname} ({ip})"
    except Exception as e:
        return False, f"Network check error: {str(e)}"


def check_dhcp_config() -> Tuple[bool, str]:
    """Check DHCP configuration"""
    try:
        dhcp_conf = Path("docker/dhcp/dhcpd.conf")
        if not dhcp_conf.exists():
            dhcp_conf = Path("/etc/dhcp/dhcpd.conf")
        
        if not dhcp_conf.exists():
            return False, "DHCP config file not found"
        
        content = dhcp_conf.read_text()
        
        # Check for critical settings
        if "option arch" not in content:
            return False, "DHCP config missing architecture detection (option arch)"
        
        if "snponly.efi" not in content and "ipxe.efi" not in content:
            return False, "DHCP config missing iPXE boot files"
        
        return True, "DHCP configuration OK"
    except Exception as e:
        return False, f"DHCP config check error: {str(e)}"


def check_tftp_files() -> Tuple[bool, str]:
    """Check TFTP boot files"""
    try:
        tftp_dir = Path("/var/lib/tftp")
        if not tftp_dir.exists():
            tftp_dir = Path("infra/tftp")
        
        if not tftp_dir.exists():
            return False, "TFTP directory not found"
        
        required_files = ["snponly.efi", "ipxe.efi", "undionly.kpxe"]
        missing = []
        
        for file in required_files:
            if not (tftp_dir / file).exists():
                missing.append(file)
        
        if missing:
            return False, f"Missing TFTP files: {', '.join(missing)}"
        
        return True, f"TFTP files OK ({len(required_files)} files present)"
    except Exception as e:
        return False, f"TFTP check error: {str(e)}"


async def run_all_checks() -> Dict[str, any]:
    """Run all pre-flight checks"""
    checks = []
    
    # Database
    ok, msg = await check_database()
    checks.append({"name": "database", "status": "pass" if ok else "fail", "message": msg})
    
    # Redis
    ok, msg = await check_redis()
    checks.append({"name": "redis", "status": "pass" if ok else "fail", "message": msg})
    
    # Storage
    ok, msg = check_storage()
    checks.append({"name": "storage", "status": "pass" if ok else "fail", "message": msg})
    
    # iSCSI
    ok, msg = await check_iscsi()
    checks.append({"name": "iscsi", "status": "pass" if ok else "fail", "message": msg})
    
    # Network
    ok, msg = check_network_interfaces()
    checks.append({"name": "network", "status": "pass" if ok else "fail", "message": msg})
    
    # DHCP
    ok, msg = check_dhcp_config()
    checks.append({"name": "dhcp", "status": "pass" if ok else "fail", "message": msg})
    
    # TFTP
    ok, msg = check_tftp_files()
    checks.append({"name": "tftp", "status": "pass" if ok else "fail", "message": msg})
    
    # Summary
    total = len(checks)
    passed = sum(1 for c in checks if c["status"] == "pass")
    failed = total - passed
    all_passed = failed == 0
    
    return {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "status": "ready" if all_passed else "not_ready"
        },
        "checks": checks
    }


def print_results(results: Dict):
    """Print check results in human-readable format"""
    print()
    print("=" * 60)
    print(" GGnet Pre-flight System Checks")
    print("=" * 60)
    print()
    
    for check in results["checks"]:
        status_icon = "✓" if check["status"] == "pass" else "✗"
        status_color = "\033[92m" if check["status"] == "pass" else "\033[91m"
        reset_color = "\033[0m"
        
        print(f"{status_color}{status_icon}{reset_color} {check['name']:15s} {check['message']}")
    
    print()
    print("=" * 60)
    
    summary = results["summary"]
    if summary["status"] == "ready":
        print(f"\033[92m✅ All checks passed! System is ready.\033[0m")
        print(f"   {summary['passed']}/{summary['total']} checks successful")
    else:
        print(f"\033[91m❌ Some checks failed! System is not ready.\033[0m")
        print(f"   {summary['passed']}/{summary['total']} checks successful")
        print(f"   {summary['failed']}/{summary['total']} checks failed")
    
    print("=" * 60)
    print()


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="GGnet Pre-flight System Checks"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    args = parser.parse_args()
    
    # Add backend to Python path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Run checks
    results = await run_all_checks()
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_results(results)
    
    # Exit code: 0 if all passed, 1 if any failed
    return 0 if results["summary"]["status"] == "ready" else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

