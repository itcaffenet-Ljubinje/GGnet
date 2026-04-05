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
from app.core.config import get_settings

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
        self.settings = get_settings()
        # ZFS configuration from settings
        self.pool_name = self.settings.ZFS_POOL_NAME
        self.dataset_prefix = self.settings.ZFS_DATASET_PREFIX
        self.clients_dataset = self.settings.ZFS_CLIENTS_DATASET
        self.images_bin_dataset = self.settings.ZFS_IMAGES_BIN_DATASET
        self.lsblk_script = self.settings.ZFS_LSBLK_SCRIPT
    
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
    
    # GGnet-specific ZFS operations (matching ggRock functionality)
    def list_images_bin_volumes(self, pool_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List image bin volumes: zfs list -Hp -t volume -r {pool}/{prefix}/images_bin
        
        Args:
            pool_name: ZFS pool name (default: from settings)
            
        Returns:
            List of volume dictionaries
        """
        try:
            if pool_name is None:
                pool_name = self.pool_name
            dataset_path = f"{pool_name}/{self.dataset_prefix}/{self.images_bin_dataset}"
            cmd = [
                self.zfs_cmd, "list", "-Hp", "-t", "volume", "-r",
                "-o", "name,creation,volsize,used,compressratio,receive_resume_token",
                dataset_path
            ]
            
            result = self._run_command(cmd, check=False)
            
            if result.returncode != 0:
                # Dataset might not exist, return empty list
                logger.debug("Images bin dataset not found or empty", dataset=dataset_path)
                return []
            
            volumes = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 5:
                    volumes.append({
                        "name": parts[0],
                        "creation": parts[1] if len(parts) > 1 else None,
                        "volsize": int(parts[2]) if len(parts) > 2 and parts[2] != "-" else 0,
                        "used": int(parts[3]) if len(parts) > 3 and parts[3] != "-" else 0,
                        "compressratio": parts[4] if len(parts) > 4 and parts[4] != "-" else None,
                        "receive_resume_token": parts[5] if len(parts) > 5 and parts[5] != "-" else None,
                    })
            return volumes
        except Exception as e:
            logger.warning("Failed to list images bin volumes", error=str(e))
            return []
    
    def list_client_volumes(self, pool_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List client volumes: zfs list -Hp -r {pool}/{prefix}/clients
        
        Args:
            pool_name: ZFS pool name (default: from settings)
            
        Returns:
            List of client volume dictionaries
        """
        try:
            if pool_name is None:
                pool_name = self.pool_name
            dataset_path = f"{pool_name}/{self.dataset_prefix}/{self.clients_dataset}"
            cmd = [
                self.zfs_cmd, "list", "-Hp", "-r",
                "-o", "name,creation,volsize,used,compressratio,origin",
                dataset_path
            ]
            
            result = self._run_command(cmd, check=False)
            
            if result.returncode != 0:
                # Dataset might not exist, return empty list
                logger.debug("Clients dataset not found or empty", dataset=dataset_path)
                return []
            
            volumes = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 5:
                    volumes.append({
                        "name": parts[0],
                        "creation": parts[1] if len(parts) > 1 else None,
                        "volsize": int(parts[2]) if len(parts) > 2 and parts[2] != "-" else 0,
                        "used": int(parts[3]) if len(parts) > 3 and parts[3] != "-" else 0,
                        "compressratio": parts[4] if len(parts) > 4 and parts[4] != "-" else None,
                        "origin": parts[5] if len(parts) > 5 and parts[5] != "-" else None,
                    })
            return volumes
        except Exception as e:
            logger.warning("Failed to list client volumes", error=str(e))
            return []
    
    def get_pool_status_with_lsblk(self, pool_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get pool status with custom lsblk script: zpool status -t -c upath,{lsblk_script}
        
        Args:
            pool_name: ZFS pool name (default: from settings)
            
        Returns:
            Pool status dictionary
        """
        try:
            if pool_name is None:
                pool_name = self.pool_name
            cmd = [
                "bash", "-c",
                f"ZPOOL_SCRIPTS_AS_ROOT=1 {self.zpool_cmd} status -t -c upath,{self.lsblk_script} {pool_name}"
            ]
            
            result = self._run_command(cmd, timeout=30, check=False)
            
            if result.returncode != 0:
                return {
                    "pool_name": pool_name,
                    "available": False,
                    "error": result.stderr.strip() if result.stderr else "Pool not found or unavailable"
                }
            
            # Parse zpool status output
            status = {
                "pool_name": pool_name,
                "available": True,
                "status_output": result.stdout,
                "health": "unknown",
                "state": "unknown"
            }
            
            # Basic parsing of status output
            lines = result.stdout.split("\n")
            for line in lines:
                line = line.strip()
                if "state:" in line.lower():
                    status["state"] = line.split(":", 1)[1].strip() if ":" in line else "unknown"
                elif "status:" in line.lower():
                    status["health"] = line.split(":", 1)[1].strip() if ":" in line else "unknown"
            
            return status
        except Exception as e:
            logger.warning("Failed to get pool status with lsblk", pool=pool_name, error=str(e))
            return {
                "pool_name": pool_name,
                "available": False,
                "error": str(e)
            }
    
    def get_pool_list_detailed(self, pool_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed pool list: zpool list -vHp -g {pool}
        
        Args:
            pool_name: ZFS pool name (default: from settings)
            
        Returns:
            Detailed pool information dictionary
        """
        try:
            if pool_name is None:
                pool_name = self.pool_name
            cmd = [self.zpool_cmd, "list", "-vHp", "-g", pool_name]
            
            result = self._run_command(cmd, timeout=30, check=False)
            
            if result.returncode != 0:
                return {
                    "pool_name": pool_name,
                    "available": False,
                    "error": result.stderr.strip() if result.stderr else "Pool not found"
                }
            
            # Parse detailed pool list output
            pool_info = {
                "pool_name": pool_name,
                "available": True,
                "output": result.stdout,
                "vdevs": []
            }
            
            # Parse output lines
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    pool_info["vdevs"].append({
                        "name": parts[0],
                        "size": parts[1] if len(parts) > 1 else None,
                        "allocated": parts[2] if len(parts) > 2 else None,
                        "free": parts[3] if len(parts) > 3 else None,
                        "expandsz": parts[4] if len(parts) > 4 else None,
                        "frag": parts[5] if len(parts) > 5 else None,
                        "cap": parts[6] if len(parts) > 6 else None,
                        "dedup": parts[7] if len(parts) > 7 else None,
                        "health": parts[8] if len(parts) > 8 else None,
                        "altroot": parts[9] if len(parts) > 9 else None,
                    })
            
            return pool_info
        except Exception as e:
            logger.warning("Failed to get detailed pool list", pool=pool_name, error=str(e))
            return {
                "pool_name": pool_name,
                "available": False,
                "error": str(e)
            }
    
    def ensure_dataset_exists(self, dataset_path: str, dataset_type: str = "filesystem") -> bool:
        """
        Ensure a ZFS dataset exists, create it if it doesn't
        
        Args:
            dataset_path: Full path to dataset (e.g., pool0/ggnet/clients)
            dataset_type: Type of dataset ("filesystem" or "volume")
            
        Returns:
            True if dataset exists or was created, False otherwise
        """
        try:
            # Check if dataset exists
            cmd = [self.zfs_cmd, "list", "-H", "-o", "name", dataset_path]
            result = self._run_command(cmd, check=False)
            
            if result.returncode == 0:
                # Dataset exists
                logger.debug("Dataset already exists", dataset=dataset_path)
                return True
            
            # Dataset doesn't exist, create it
            logger.info("Creating ZFS dataset", dataset=dataset_path, type=dataset_type)
            self.dataset_create(dataset_path, dataset_type=dataset_type)
            return True
            
        except Exception as e:
            logger.warning("Failed to ensure dataset exists", dataset=dataset_path, error=str(e))
            return False
    
    def ensure_zfs_datasets(self, pool_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Ensure required ZFS datasets exist, create them if they don't
        
        Args:
            pool_name: ZFS pool name (default: from settings)
            
        Returns:
            Dictionary with status of each dataset
        """
        if pool_name is None:
            pool_name = self.pool_name
        
        result = {
            "pool_name": pool_name,
            "datasets": {},
            "all_created": True,
            "errors": []
        }
        
        try:
            # Check if pool exists first
            pools = self.pool_list()
            pool_exists = any(p["name"] == pool_name for p in pools)
            
            if not pool_exists:
                error_msg = f"ZFS pool '{pool_name}' does not exist"
                logger.warning(error_msg)
                result["errors"].append(error_msg)
                result["all_created"] = False
                return result
            
            # Ensure clients dataset exists
            clients_path = f"{pool_name}/{self.dataset_prefix}/{self.clients_dataset}"
            try:
                clients_created = self.ensure_dataset_exists(clients_path, dataset_type="filesystem")
                result["datasets"]["clients"] = {
                    "path": clients_path,
                    "exists": clients_created,
                    "error": None
                }
                if not clients_created:
                    result["all_created"] = False
            except Exception as e:
                error_msg = f"Failed to ensure clients dataset: {str(e)}"
                logger.warning(error_msg, dataset=clients_path, error=str(e))
                result["datasets"]["clients"] = {
                    "path": clients_path,
                    "exists": False,
                    "error": str(e)
                }
                result["errors"].append(error_msg)
                result["all_created"] = False
            
            # Ensure images_bin dataset exists
            images_bin_path = f"{pool_name}/{self.dataset_prefix}/{self.images_bin_dataset}"
            try:
                images_bin_created = self.ensure_dataset_exists(images_bin_path, dataset_type="filesystem")
                result["datasets"]["images_bin"] = {
                    "path": images_bin_path,
                    "exists": images_bin_created,
                    "error": None
                }
                if not images_bin_created:
                    result["all_created"] = False
            except Exception as e:
                error_msg = f"Failed to ensure images_bin dataset: {str(e)}"
                logger.warning(error_msg, dataset=images_bin_path, error=str(e))
                result["datasets"]["images_bin"] = {
                    "path": images_bin_path,
                    "exists": False,
                    "error": str(e)
                }
                result["errors"].append(error_msg)
                result["all_created"] = False
            
            logger.info("ZFS datasets check completed", pool=pool_name, all_created=result["all_created"])
            return result
            
        except Exception as e:
            error_msg = f"Failed to ensure ZFS datasets: {str(e)}"
            logger.error(error_msg, pool=pool_name, error=str(e))
            result["errors"].append(error_msg)
            result["all_created"] = False
            return result

