"""
ARC (Adaptive Replacement Cache) monitoring module
"""

from typing import Dict, Any
from pathlib import Path
import structlog

from app.core.exceptions import StorageError

logger = structlog.get_logger()


class ARCMonitor:
    """
    ARC monitor for reading ZFS ARC statistics
    """
    
    def __init__(self):
        """Initialize ARC monitor"""
        self.arcstats_path = Path("/proc/spl/kstat/zfs/arcstats")
    
    def get_arc_stats(self) -> Dict[str, Any]:
        """
        Get ARC statistics from /proc/spl/kstat/zfs/arcstats
        
        Returns:
            ARC statistics dictionary
            
        Raises:
            StorageError: If ARC stats cannot be read
        """
        try:
            if not self.arcstats_path.exists():
                # Fallback if ARC stats file doesn't exist
                logger.warning("ARC stats file not found, returning default values")
                return {
                    "size": 0,
                    "used": 0,
                    "free": 0,
                    "hit_rate": 0.0,
                    "miss_rate": 0.0,
                    "hits": 0,
                    "misses": 0,
                    "available": False,
                }
            
            stats = {}
            
            # Read ARC stats file
            with open(self.arcstats_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    # Parse line: name type value
                    parts = line.split()
                    if len(parts) >= 3:
                        name = parts[0]
                        try:
                            value = int(parts[2])
                            stats[name] = value
                        except ValueError:
                            continue
            
            # Calculate derived metrics
            size = stats.get("size", 0)
            c = stats.get("c", 0)  # Target ARC size
            c_min = stats.get("c_min", 0)  # Minimum ARC size
            c_max = stats.get("c_max", 0)  # Maximum ARC size
            
            hits = stats.get("hits", 0)
            misses = stats.get("misses", 0)
            total = hits + misses
            
            hit_rate = (hits / total * 100) if total > 0 else 0.0
            miss_rate = (misses / total * 100) if total > 0 else 0.0
            
            return {
                "size": size,
                "used": c,
                "free": c_max - c if c_max > c else 0,
                "target": c,
                "min": c_min,
                "max": c_max,
                "hit_rate": round(hit_rate, 2),
                "miss_rate": round(miss_rate, 2),
                "hits": hits,
                "misses": misses,
                "total": total,
                "available": True,
                "raw_stats": stats,  # Include raw stats for advanced use
            }
        except PermissionError:
            raise StorageError("Permission denied: ARC stats requires root privileges")
        except Exception as e:
            logger.warning("Failed to read ARC stats", error=str(e))
            return {
                "size": 0,
                "used": 0,
                "free": 0,
                "hit_rate": 0.0,
                "miss_rate": 0.0,
                "hits": 0,
                "misses": 0,
                "available": False,
                "error": str(e),
            }




