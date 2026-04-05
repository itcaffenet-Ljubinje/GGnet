"""
Memory monitoring utilities using free -b command
Provides memory information matching ggRock implementation
"""

import subprocess
import structlog
from typing import Dict, Any, Optional, List

logger = structlog.get_logger()


class MemoryMonitorError(Exception):
    """Memory monitoring error"""
    pass


class MemoryMonitor:
    """
    Memory monitor using free -b command (matching ggRock implementation)
    """
    
    def __init__(self):
        """Initialize memory monitor"""
        self.free_cmd = "free"
    
    def _run_command(
        self,
        command: List[str],
        timeout: int = 5,
        check: bool = False
    ) -> subprocess.CompletedProcess:
        """
        Run free command
        
        Args:
            command: Command and arguments as list
            timeout: Command timeout in seconds
            check: Raise exception on non-zero exit code
            
        Returns:
            CompletedProcess result
            
        Raises:
            MemoryMonitorError: If command fails
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=check
            )
            return result
        except subprocess.TimeoutExpired as e:
            raise MemoryMonitorError(f"Command timeout: {' '.join(command)}") from e
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            raise MemoryMonitorError(f"Command failed: {' '.join(command)} - {error_msg}") from e
        except Exception as e:
            raise MemoryMonitorError(f"Unexpected error running command: {e}") from e
    
    def get_memory_info(self) -> Dict[str, Any]:
        """
        Get memory information using free -b command
        
        Returns:
            Dictionary with memory information in bytes
        """
        try:
            cmd = [self.free_cmd, "-b"]
            result = self._run_command(cmd, timeout=5, check=True)
            
            # Parse free -b output
            # Example output:
            #               total        used        free      shared  buff/cache   available
            # Mem:    8589934592  2147483648  4294967296   268435456  2147483648  5368709120
            # Swap:   2147483648   536870912  1610612736           0           0
            
            lines = result.stdout.strip().split('\n')
            memory_info = {
                "total_bytes": 0,
                "used_bytes": 0,
                "free_bytes": 0,
                "shared_bytes": 0,
                "buff_cache_bytes": 0,
                "available_bytes": 0,
                "swap_total_bytes": 0,
                "swap_used_bytes": 0,
                "swap_free_bytes": 0,
                "available": True
            }
            
            for line in lines:
                parts = line.split()
                if len(parts) < 2:
                    continue
                
                if parts[0] == "Mem:":
                    if len(parts) >= 7:
                        memory_info["total_bytes"] = int(parts[1])
                        memory_info["used_bytes"] = int(parts[2])
                        memory_info["free_bytes"] = int(parts[3])
                        memory_info["shared_bytes"] = int(parts[4])
                        memory_info["buff_cache_bytes"] = int(parts[5])
                        memory_info["available_bytes"] = int(parts[6])
                
                elif parts[0] == "Swap:":
                    if len(parts) >= 4:
                        memory_info["swap_total_bytes"] = int(parts[1])
                        memory_info["swap_used_bytes"] = int(parts[2])
                        memory_info["swap_free_bytes"] = int(parts[3])
            
            # Calculate percentages
            if memory_info["total_bytes"] > 0:
                memory_info["used_percent"] = round(
                    (memory_info["used_bytes"] / memory_info["total_bytes"]) * 100, 2
                )
                memory_info["free_percent"] = round(
                    (memory_info["free_bytes"] / memory_info["total_bytes"]) * 100, 2
                )
                memory_info["available_percent"] = round(
                    (memory_info["available_bytes"] / memory_info["total_bytes"]) * 100, 2
                )
            else:
                memory_info["used_percent"] = 0.0
                memory_info["free_percent"] = 0.0
                memory_info["available_percent"] = 0.0
            
            if memory_info["swap_total_bytes"] > 0:
                memory_info["swap_used_percent"] = round(
                    (memory_info["swap_used_bytes"] / memory_info["swap_total_bytes"]) * 100, 2
                )
            else:
                memory_info["swap_used_percent"] = 0.0
            
            # Add human-readable sizes
            memory_info["total_gb"] = round(memory_info["total_bytes"] / (1024**3), 2)
            memory_info["used_gb"] = round(memory_info["used_bytes"] / (1024**3), 2)
            memory_info["free_gb"] = round(memory_info["free_bytes"] / (1024**3), 2)
            memory_info["available_gb"] = round(memory_info["available_bytes"] / (1024**3), 2)
            memory_info["swap_total_gb"] = round(memory_info["swap_total_bytes"] / (1024**3), 2)
            memory_info["swap_used_gb"] = round(memory_info["swap_used_bytes"] / (1024**3), 2)
            memory_info["swap_free_gb"] = round(memory_info["swap_free_bytes"] / (1024**3), 2)
            
            return memory_info
            
        except MemoryMonitorError:
            raise
        except Exception as e:
            logger.warning("Failed to get memory info", error=str(e))
            return {
                "total_bytes": 0,
                "used_bytes": 0,
                "free_bytes": 0,
                "shared_bytes": 0,
                "buff_cache_bytes": 0,
                "available_bytes": 0,
                "swap_total_bytes": 0,
                "swap_used_bytes": 0,
                "swap_free_bytes": 0,
                "used_percent": 0.0,
                "free_percent": 0.0,
                "available_percent": 0.0,
                "swap_used_percent": 0.0,
                "total_gb": 0.0,
                "used_gb": 0.0,
                "free_gb": 0.0,
                "available_gb": 0.0,
                "swap_total_gb": 0.0,
                "swap_used_gb": 0.0,
                "swap_free_gb": 0.0,
                "available": False,
                "error": str(e)
            }

