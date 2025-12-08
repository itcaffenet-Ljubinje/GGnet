"""
ZFS (Z File System) management utilities
Provides functions to manage ZFS pools, datasets, and snapshots
"""

import subprocess
import json
import structlog
from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass

logger = structlog.get_logger()


@dataclass
class ZFSPool:
    """ZFS Pool information"""
    name: str
    size: int
    allocated: int
    free: int
    health: str
    mountpoint: Optional[str] = None
    features: List[str] = None


@dataclass
class ZFSDataset:
    """ZFS Dataset information"""
    name: str
    used: int
    available: int
    referenced: int
    mountpoint: Optional[str] = None
    type: str = "filesystem"  # filesystem, volume, snapshot
    compression: Optional[str] = None
    quota: Optional[int] = None
    reservation: Optional[int] = None


@dataclass
class ZFSSnapshot:
    """ZFS Snapshot information"""
    name: str
    used: int
    referenced: int
    created: str


class ZFSManager:
    """Manager for ZFS operations"""
    
    def __init__(self, zfs_path: str = "/usr/sbin/zfs", zpool_path: str = "/usr/sbin/zpool"):
        self.zfs_path = zfs_path
        self.zpool_path = zpool_path
        self._check_zfs_available()
    
    def _check_zfs_available(self) -> bool:
        """Check if ZFS utilities are available"""
        try:
            subprocess.run(
                [self.zfs_path, "--version"],
                capture_output=True,
                check=True,
                timeout=5
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("ZFS utilities not available")
            return False
    
    def _run_command(self, cmd: List[str], timeout: int = 30) -> Dict[str, Any]:
        """Run a ZFS/ZPool command and return JSON output"""
        try:
            result = subprocess.run(
                cmd + ["-H", "-p", "-o", "json"],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            if result.stdout:
                return json.loads(result.stdout)
            return {}
        except subprocess.CalledProcessError as e:
            logger.error(f"ZFS command failed: {e.stderr}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ZFS output: {e}")
            raise
        except subprocess.TimeoutExpired:
            logger.error("ZFS command timed out")
            raise
    
    def list_pools(self) -> List[ZFSPool]:
        """List all ZFS pools"""
        try:
            result = subprocess.run(
                [self.zpool_path, "list", "-H", "-o", "name,size,allocated,free,health"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            pools = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) >= 5:
                    pools.append(ZFSPool(
                        name=parts[0],
                        size=self._parse_size(parts[1]),
                        allocated=self._parse_size(parts[2]),
                        free=self._parse_size(parts[3]),
                        health=parts[4]
                    ))
            return pools
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"Failed to list ZFS pools: {e}")
            return []
    
    def get_pool_info(self, pool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a ZFS pool"""
        try:
            result = subprocess.run(
                [self.zpool_path, "get", "-H", "-o", "property,value", "all", pool_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            info = {}
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) >= 2:
                    info[parts[0]] = parts[1]
            return info
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"Failed to get pool info for {pool_name}: {e}")
            return None
    
    def list_datasets(self, pool_name: Optional[str] = None) -> List[ZFSDataset]:
        """List ZFS datasets (filesystems and volumes)"""
        try:
            cmd = [self.zfs_path, "list", "-H", "-o", "name,used,avail,refer,mountpoint,type,compression,quota,reservation"]
            if pool_name:
                cmd.append(pool_name)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            datasets = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) >= 6:
                    datasets.append(ZFSDataset(
                        name=parts[0],
                        used=self._parse_size(parts[1]) if parts[1] != '-' else 0,
                        available=self._parse_size(parts[2]) if parts[2] != '-' else 0,
                        referenced=self._parse_size(parts[3]) if parts[3] != '-' else 0,
                        mountpoint=parts[4] if parts[4] != '-' else None,
                        type=parts[5] if len(parts) > 5 else "filesystem",
                        compression=parts[6] if len(parts) > 6 and parts[6] != '-' else None,
                        quota=self._parse_size(parts[7]) if len(parts) > 7 and parts[7] != '-' else None,
                        reservation=self._parse_size(parts[8]) if len(parts) > 8 and parts[8] != '-' else None,
                    ))
            return datasets
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"Failed to list ZFS datasets: {e}")
            return []
    
    def create_pool(
        self,
        pool_name: str,
        vdevs: List[str],
        pool_type: str = "stripe",
        mountpoint: Optional[str] = None
    ) -> bool:
        """Create a new ZFS pool"""
        try:
            cmd = [self.zpool_path, "create"]
            
            if mountpoint:
                cmd.extend(["-m", mountpoint])
            
            cmd.append(pool_name)
            
            # Add VDEVs based on pool type
            if pool_type == "mirror" and len(vdevs) >= 2:
                cmd.append("mirror")
                cmd.extend(vdevs[:2])
            elif pool_type == "raidz" and len(vdevs) >= 3:
                cmd.append("raidz")
                cmd.extend(vdevs)
            elif pool_type == "raidz2" and len(vdevs) >= 4:
                cmd.append("raidz2")
                cmd.extend(vdevs)
            elif pool_type == "raidz3" and len(vdevs) >= 5:
                cmd.append("raidz3")
                cmd.extend(vdevs)
            else:
                # Stripe (RAID 0)
                cmd.extend(vdevs)
            
            subprocess.run(cmd, check=True, timeout=60, capture_output=True)
            logger.info(f"Created ZFS pool: {pool_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create ZFS pool {pool_name}: {e.stderr}")
            return False
    
    def destroy_pool(self, pool_name: str, force: bool = False) -> bool:
        """Destroy a ZFS pool"""
        try:
            cmd = [self.zpool_path, "destroy"]
            if force:
                cmd.append("-f")
            cmd.append(pool_name)
            
            subprocess.run(cmd, check=True, timeout=30, capture_output=True)
            logger.info(f"Destroyed ZFS pool: {pool_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to destroy ZFS pool {pool_name}: {e.stderr}")
            return False
    
    def create_dataset(
        self,
        dataset_name: str,
        pool_name: str,
        properties: Optional[Dict[str, str]] = None
    ) -> bool:
        """Create a ZFS dataset"""
        try:
            full_name = f"{pool_name}/{dataset_name}"
            cmd = [self.zfs_path, "create"]
            
            if properties:
                for key, value in properties.items():
                    cmd.extend(["-o", f"{key}={value}"])
            
            cmd.append(full_name)
            
            subprocess.run(cmd, check=True, timeout=30, capture_output=True)
            logger.info(f"Created ZFS dataset: {full_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create ZFS dataset {dataset_name}: {e.stderr}")
            return False
    
    def create_snapshot(self, dataset_name: str, snapshot_name: str) -> bool:
        """Create a ZFS snapshot"""
        try:
            snapshot_path = f"{dataset_name}@{snapshot_name}"
            subprocess.run(
                [self.zfs_path, "snapshot", snapshot_path],
                check=True,
                timeout=30,
                capture_output=True
            )
            logger.info(f"Created ZFS snapshot: {snapshot_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create snapshot {snapshot_name}: {e.stderr}")
            return False
    
    def list_snapshots(self, dataset_name: Optional[str] = None) -> List[ZFSSnapshot]:
        """List ZFS snapshots"""
        try:
            cmd = [self.zfs_path, "list", "-t", "snapshot", "-H", "-o", "name,used,refer,creation"]
            if dataset_name:
                cmd.append(dataset_name)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            snapshots = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) >= 4:
                    snapshots.append(ZFSSnapshot(
                        name=parts[0],
                        used=self._parse_size(parts[1]) if parts[1] != '-' else 0,
                        referenced=self._parse_size(parts[2]) if parts[2] != '-' else 0,
                        created=parts[3]
                    ))
            return snapshots
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"Failed to list ZFS snapshots: {e}")
            return []
    
    def _parse_size(self, size_str: str) -> int:
        """Parse ZFS size string (e.g., '100G', '1.5T') to bytes"""
        if not size_str or size_str == '-':
            return 0
        
        size_str = size_str.strip().upper()
        multipliers = {
            'K': 1024,
            'M': 1024 ** 2,
            'G': 1024 ** 3,
            'T': 1024 ** 4,
            'P': 1024 ** 5,
        }
        
        # Extract number and unit
        for unit, multiplier in multipliers.items():
            if size_str.endswith(unit):
                try:
                    number = float(size_str[:-1])
                    return int(number * multiplier)
                except ValueError:
                    return 0
        
        # Try to parse as plain number (bytes)
        try:
            return int(float(size_str))
        except ValueError:
            return 0




