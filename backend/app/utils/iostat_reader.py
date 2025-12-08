"""
ZFS iostat reader module
"""

import subprocess
from typing import Dict, Any
import structlog

from app.core.exceptions import StorageError

logger = structlog.get_logger()


class IOStatReader:
    """
    IO statistics reader for ZFS pools
    """
    
    def __init__(self):
        """Initialize IO stat reader"""
        self.zpool_cmd = "zpool"
    
    def _run_command(
        self,
        command: list,
        check: bool = True,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run command"""
        try:
            result = subprocess.run(
                command,
                check=check,
                capture_output=capture_output,
                text=True,
                timeout=30,
            )
            return result
        except subprocess.TimeoutExpired as e:
            raise StorageError(f"Command timeout: {' '.join(command)}") from e
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            raise StorageError(f"Command failed: {' '.join(command)} - {error_msg}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error: {e}") from e
    
    def get_pool_iostat(self, pool_name: str) -> Dict[str, Any]:
        """
        Get pool IO statistics using zpool iostat
        
        Args:
            pool_name: Pool name
            
        Returns:
            IO statistics dictionary
        """
        try:
            result = self._run_command([
                self.zpool_cmd,
                "iostat",
                "-v",
                pool_name,
                "1",
                "1",
            ])
            
            lines = result.stdout.strip().split("\n")
            
            # Default values
            iostat = {
                "pool_name": pool_name,
                "capacity_alloc": 0,
                "capacity_free": 0,
                "capacity_percent": 0.0,
                "ops_read": 0,
                "ops_write": 0,
                "bandwidth_read": 0,
                "bandwidth_write": 0,
                "bandwidth_read_mb": 0.0,
                "bandwidth_write_mb": 0.0,
            }
            
            # Parse output (simplified parsing)
            # In production, would need more robust parsing
            for line in lines:
                if pool_name in line and "%" in line:
                    # Try to extract capacity percentage
                    try:
                        parts = line.split()
                        for part in parts:
                            if "%" in part:
                                iostat["capacity_percent"] = float(part.replace("%", ""))
                                break
                    except Exception:
                        pass
            
            return iostat
        except Exception as e:
            logger.warning("Failed to get pool iostat", pool=pool_name, error=str(e))
            return {
                "pool_name": pool_name,
                "error": str(e),
                "available": False,
            }




