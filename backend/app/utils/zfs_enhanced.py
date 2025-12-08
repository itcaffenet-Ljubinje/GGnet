"""
Enhanced ZFS utilities - Comprehensive ZFS operations
Based on ggNET2 implementation with improvements
"""

import subprocess
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import structlog

from app.core.exceptions import StorageError

logger = structlog.get_logger()


class ZFSError(StorageError):
    """ZFS-specific error"""
    pass


class ZFSUtils:
    """
    Enhanced ZFS utilities class for comprehensive ZFS operations
    """
    
    def __init__(self):
        """Initialize ZFS utilities"""
        self.zfs_cmd = "zfs"
        self.zpool_cmd = "zpool"
    
    def _run_command(
        self,
        command: List[str],
        check: bool = True,
        capture_output: bool = True,
        timeout: int = 300,
    ) -> subprocess.CompletedProcess:
        """
        Run ZFS/ZFS pool command
        
        Args:
            command: Command and arguments as list
            check: Raise exception on non-zero exit code
            capture_output: Capture stdout and stderr
            timeout: Command timeout in seconds
            
        Returns:
            CompletedProcess result
            
        Raises:
            ZFSError: If command fails
        """
        if not command or any(arg is None for arg in command):
            raise ZFSError(f"Invalid command: command list contains None values. Command: {command}")
        
        try:
            result = subprocess.run(
                command,
                check=check,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
            )
            return result
        except FileNotFoundError as e:
            logger.warning("ZFS command not found", command=command[0])
            raise ZFSError(
                f"ZFS not available: {command[0]} command not found. "
                "ZFS is only available on Linux systems with ZFS installed."
            ) from e
        except subprocess.TimeoutExpired as e:
            raise ZFSError(f"Command timeout: {' '.join(command)}") from e
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            raise ZFSError(f"ZFS command failed: {' '.join(command)} - {error_msg}") from e
        except Exception as e:
            raise ZFSError(f"Unexpected error running ZFS command: {e}") from e
    
    # Pool operations
    def pool_list(self) -> List[Dict[str, Any]]:
        """List all ZFS pools"""
        try:
            if not self.zpool_cmd:
                raise ZFSError("zpool command is not configured")
            
            result = self._run_command([self.zpool_cmd, "list", "-Hp", "-o", "name,size,allocated,free,health"])
            
            if not result.stdout or not result.stdout.strip():
                return []
            
            pools = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 5:
                    try:
                        pools.append({
                            "name": parts[0],
                            "size": int(parts[1]) if parts[1] else 0,
                            "allocated": int(parts[2]) if parts[2] else 0,
                            "free": int(parts[3]) if parts[3] else 0,
                            "health": parts[4] if parts[4] else "unknown",
                        })
                    except (ValueError, IndexError) as e:
                        logger.warning("Failed to parse pool line", line=line, error=str(e))
                        continue
            return pools
        except ZFSError:
            raise
        except Exception as e:
            raise ZFSError(f"Failed to list pools: {e}") from e
    
    def pool_status(self, pool_name: str) -> Dict[str, Any]:
        """Get pool status"""
        if not pool_name:
            raise ZFSError("Pool name is required and cannot be None")
        
        if not self.zpool_cmd:
            raise ZFSError("zpool command is not configured")
        
        try:
            result = self._run_command([self.zpool_cmd, "status", pool_name])
            
            status = {
                "name": pool_name,
                "status": "unknown",
                "state": "unknown",
                "output": result.stdout,
            }
            
            # Parse health state
            if "ONLINE" in result.stdout:
                status["state"] = "online"
            elif "DEGRADED" in result.stdout:
                status["state"] = "degraded"
            elif "FAULTED" in result.stdout:
                status["state"] = "faulted"
            elif "OFFLINE" in result.stdout:
                status["state"] = "offline"
            
            return status
        except ZFSError:
            raise
        except Exception as e:
            raise ZFSError(f"Failed to get pool status: {e}") from e
    
    def pool_create(
        self,
        pool_name: str,
        devices: List[str],
        topology: str = "stripe",
    ) -> None:
        """Create ZFS pool"""
        if not devices:
            raise ZFSError("No devices provided for pool creation")
        
        try:
            cmd = [self.zpool_cmd, "create", pool_name]
            
            # Add topology
            if topology == "mirror" and len(devices) >= 2:
                cmd.append("mirror")
                cmd.extend(devices)
            elif topology.startswith("raidz"):
                cmd.append(topology)
                cmd.extend(devices)
            else:  # stripe (default)
                cmd.extend(devices)
            
            self._run_command(cmd)
            logger.info("Created ZFS pool", pool_name=pool_name, topology=topology)
        except ZFSError:
            raise
        except Exception as e:
            raise ZFSError(f"Failed to create pool: {e}") from e
    
    def pool_destroy(self, pool_name: str, force: bool = False) -> None:
        """Destroy pool"""
        try:
            cmd = [self.zpool_cmd, "destroy"]
            if force:
                cmd.append("-f")
            cmd.append(pool_name)
            
            self._run_command(cmd)
            logger.info("Destroyed pool", pool_name=pool_name)
        except Exception as e:
            raise ZFSError(f"Failed to destroy pool: {e}")
    
    def pool_scrub(self, pool_name: str) -> None:
        """Start pool scrub"""
        try:
            self._run_command([self.zpool_cmd, "scrub", pool_name])
            logger.info("Started scrub", pool_name=pool_name)
        except Exception as e:
            raise ZFSError(f"Failed to start scrub: {e}")
    
    # Dataset operations
    def dataset_list(self, pool_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List ZFS datasets"""
        try:
            cmd = [self.zfs_cmd, "list", "-Hp", "-o", "name,type,used,available,referenced,mountpoint"]
            if pool_name:
                cmd.append(f"{pool_name}/*")
            
            result = self._run_command(cmd)
            datasets = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 6:
                    datasets.append({
                        "name": parts[0],
                        "type": parts[1],
                        "used": int(parts[2]),
                        "available": int(parts[3]),
                        "referenced": int(parts[4]),
                        "mountpoint": parts[5] if parts[5] != "-" else None,
                    })
            return datasets
        except Exception as e:
            raise ZFSError(f"Failed to list datasets: {e}") from e
    
    def dataset_create(
        self,
        dataset_name: str,
        dataset_type: str = "filesystem",
        properties: Optional[Dict[str, str]] = None,
    ) -> None:
        """Create ZFS dataset"""
        try:
            cmd = [self.zfs_cmd, "create"]
            
            if properties:
                for key, value in properties.items():
                    cmd.extend(["-o", f"{key}={value}"])
            
            if dataset_type == "volume":
                cmd.append("-V")
                if "volsize" not in (properties or {}):
                    raise ZFSError("Volume creation requires volsize property")
            
            cmd.append(dataset_name)
            
            self._run_command(cmd)
            logger.info("Created ZFS dataset", dataset_name=dataset_name, dataset_type=dataset_type)
        except Exception as e:
            raise ZFSError(f"Failed to create dataset: {e}") from e
    
    def dataset_destroy(self, dataset_name: str, recursive: bool = False, force: bool = False) -> None:
        """Destroy ZFS dataset"""
        try:
            cmd = [self.zfs_cmd, "destroy"]
            if recursive:
                cmd.append("-r")
            if force:
                cmd.append("-f")
            cmd.append(dataset_name)
            
            self._run_command(cmd)
            logger.info("Destroyed ZFS dataset", dataset_name=dataset_name)
        except Exception as e:
            raise ZFSError(f"Failed to destroy dataset: {e}") from e
    
    # Snapshot operations
    def snapshot_create(self, dataset_name: str, snapshot_name: str, recursive: bool = False) -> None:
        """Create ZFS snapshot"""
        try:
            full_snapshot_name = f"{dataset_name}@{snapshot_name}"
            cmd = [self.zfs_cmd, "snapshot"]
            if recursive:
                cmd.append("-r")
            cmd.append(full_snapshot_name)
            
            self._run_command(cmd)
            logger.info("Created snapshot", snapshot=full_snapshot_name)
        except Exception as e:
            raise ZFSError(f"Failed to create snapshot: {e}") from e
    
    def snapshot_list(self, dataset_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List ZFS snapshots"""
        try:
            cmd = [self.zfs_cmd, "list", "-Hp", "-t", "snapshot", "-o", "name,used,referenced,creation"]
            if dataset_name:
                cmd.append(f"{dataset_name}@*")
            
            result = self._run_command(cmd)
            snapshots = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 4:
                    full_name = parts[0]
                    if "@" in full_name:
                        dataset, snapshot = full_name.split("@", 1)
                    else:
                        dataset = full_name
                        snapshot = None
                    
                    snapshots.append({
                        "dataset": dataset,
                        "snapshot": snapshot,
                        "full_name": full_name,
                        "used": int(parts[1]),
                        "referenced": int(parts[2]),
                        "creation": parts[3],
                    })
            return snapshots
        except Exception as e:
            raise ZFSError(f"Failed to list snapshots: {e}") from e
    
    def snapshot_destroy(self, dataset_name: str, snapshot_name: str, recursive: bool = False) -> None:
        """Destroy ZFS snapshot"""
        try:
            full_snapshot_name = f"{dataset_name}@{snapshot_name}"
            cmd = [self.zfs_cmd, "destroy"]
            if recursive:
                cmd.append("-r")
            cmd.append(full_snapshot_name)
            
            self._run_command(cmd)
            logger.info("Destroyed snapshot", snapshot=full_snapshot_name)
        except Exception as e:
            raise ZFSError(f"Failed to destroy snapshot: {e}") from e
    
    def clone_create(
        self,
        snapshot_name: str,
        clone_name: str,
        properties: Optional[Dict[str, str]] = None,
    ) -> None:
        """Create ZFS clone from snapshot"""
        try:
            cmd = [self.zfs_cmd, "clone"]
            
            if properties:
                for key, value in properties.items():
                    cmd.extend(["-o", f"{key}={value}"])
            
            cmd.extend([snapshot_name, clone_name])
            
            self._run_command(cmd)
            logger.info("Created clone", clone_name=clone_name, snapshot=snapshot_name)
        except Exception as e:
            raise ZFSError(f"Failed to create clone: {e}") from e




