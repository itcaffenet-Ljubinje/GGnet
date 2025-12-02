"""
TFTP Adapter
Manages TFTP server for iPXE boot scripts and network boot files
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Dict, List
import structlog

from app.models.machine import Machine
from app.core.config import get_settings
from app.core.exceptions import TFTPError

logger = structlog.get_logger(__name__)


class TFTPAdapter:
    """
    Manages TFTP server for network boot files
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.tftp_root = self.settings.TFTP_ROOT
        self.machines_dir = self.tftp_root / "machines"
        self.boot_dir = self.tftp_root / "boot"
        self.tftp_service_name = "tftpd-hpa"
    
    async def save_boot_script(self, script_content: str, machine: Machine) -> str:
        """
        Save iPXE boot script for a machine
        """
        logger.info(f"Saving boot script for machine {machine.id}")
        
        try:
            # Ensure directories exist
            self.machines_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = self._get_machine_script_filename(machine)
            script_path = self.machines_dir / filename
            
            # Write script content
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Set appropriate permissions
            os.chmod(script_path, 0o644)
            
            logger.info(f"Boot script saved for machine {machine.id}", 
                       script_path=str(script_path))
            
            return str(script_path)
            
        except Exception as e:
            logger.error(f"Failed to save boot script for machine {machine.id}: {e}")
            raise TFTPError(f"Failed to save boot script: {e}")
    
    async def remove_boot_script(self, filename: str) -> bool:
        """
        Remove boot script file
        """
        logger.info(f"Removing boot script: {filename}")
        
        try:
            script_path = self.tftp_root / filename
            
            if script_path.exists():
                script_path.unlink()
                logger.info(f"Boot script removed: {filename}")
                return True
            else:
                logger.warning(f"Boot script not found: {filename}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove boot script {filename}: {e}")
            raise TFTPError(f"Failed to remove boot script: {e}")
    
    async def save_generic_boot_script(self, script_content: str) -> str:
        """
        Save generic boot script
        """
        logger.info("Saving generic boot script")
        
        try:
            # Ensure directories exist
            self.boot_dir.mkdir(parents=True, exist_ok=True)
            
            # Save generic script
            script_path = self.boot_dir / "boot.ipxe"
            
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Set appropriate permissions
            os.chmod(script_path, 0o644)
            
            logger.info("Generic boot script saved", script_path=str(script_path))
            
            return str(script_path)
            
        except Exception as e:
            logger.error(f"Failed to save generic boot script: {e}")
            raise TFTPError(f"Failed to save generic boot script: {e}")
    
    async def copy_boot_files(self, source_dir: Path) -> bool:
        """
        Copy boot files from source directory to TFTP root
        """
        logger.info(f"Copying boot files from {source_dir}")
        
        try:
            if not source_dir.exists():
                logger.error(f"Source directory does not exist: {source_dir}")
                return False
            
            # Copy files to boot directory
            self.boot_dir.mkdir(parents=True, exist_ok=True)
            
            for file_path in source_dir.iterdir():
                if file_path.is_file():
                    dest_path = self.boot_dir / file_path.name
                    shutil.copy2(file_path, dest_path)
                    os.chmod(dest_path, 0o644)
                    logger.info(f"Copied boot file: {file_path.name}")
            
            logger.info("Boot files copied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy boot files: {e}")
            raise TFTPError(f"Failed to copy boot files: {e}")
    
    async def get_tftp_status(self) -> Dict:
        """
        Get TFTP server status and configuration info
        """
        logger.info("Getting TFTP server status")
        
        try:
            status = {
                "service_running": False,
                "tftp_root_exists": False,
                "machines_dir_exists": False,
                "boot_dir_exists": False,
                "machine_scripts_count": 0,
                "boot_files_count": 0
            }
            
            # Check if service is running
            try:
                import subprocess
                result = subprocess.run(
                    ["systemctl", "is-active", self.tftp_service_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                status["service_running"] = result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                status["service_running"] = False
            
            # Check directories
            status["tftp_root_exists"] = self.tftp_root.exists()
            status["machines_dir_exists"] = self.machines_dir.exists()
            status["boot_dir_exists"] = self.boot_dir.exists()
            
            # Count files
            if self.machines_dir.exists():
                status["machine_scripts_count"] = len(list(self.machines_dir.glob("*.ipxe")))
            
            if self.boot_dir.exists():
                status["boot_files_count"] = len(list(self.boot_dir.iterdir()))
            
            logger.info("TFTP status retrieved", **status)
            return status
            
        except Exception as e:
            logger.error(f"Error getting TFTP status: {e}")
            return {"error": str(e)}
    
    async def list_machine_scripts(self) -> List[Dict]:
        """
        List all machine boot scripts
        """
        logger.info("Listing machine boot scripts")
        
        try:
            scripts = []
            
            if not self.machines_dir.exists():
                return scripts
            
            for script_file in self.machines_dir.glob("*.ipxe"):
                try:
                    stat = script_file.stat()
                    scripts.append({
                        "filename": script_file.name,
                        "path": str(script_file),
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "machine_mac": self._extract_mac_from_filename(script_file.name)
                    })
                except Exception as e:
                    logger.warning(f"Error reading script file {script_file.name}: {e}")
            
            logger.info(f"Found {len(scripts)} machine scripts")
            return scripts
            
        except Exception as e:
            logger.error(f"Error listing machine scripts: {e}")
            return []
    
    async def get_script_content(self, filename: str) -> Optional[str]:
        """
        Get content of a boot script
        """
        logger.info(f"Getting script content: {filename}")
        
        try:
            script_path = self.tftp_root / filename
            
            if not script_path.exists():
                logger.warning(f"Script file not found: {filename}")
                return None
            
            with open(script_path, 'r') as f:
                content = f.read()
            
            logger.info(f"Retrieved script content: {filename}")
            return content
            
        except Exception as e:
            logger.error(f"Error getting script content {filename}: {e}")
            return None
    
    def _get_machine_script_filename(self, machine: Machine) -> str:
        """
        Get filename for machine boot script
        """
        # Use MAC address as filename (with hyphens)
        mac_filename = machine.mac_address.replace(":", "-").lower()
        return f"{mac_filename}.ipxe"
    
    def _extract_mac_from_filename(self, filename: str) -> Optional[str]:
        """
        Extract MAC address from script filename
        """
        try:
            # Remove .ipxe extension
            name = filename.replace(".ipxe", "")
            # Convert hyphens back to colons
            mac = name.replace("-", ":")
            # Validate MAC format
            if len(mac) == 17 and mac.count(":") == 5:
                return mac
            return None
        except Exception:
            return None
    
    async def cleanup_old_scripts(self, max_age_days: int = 7) -> int:
        """
        Clean up old boot scripts
        """
        logger.info(f"Cleaning up scripts older than {max_age_days} days")
        
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            cleaned_count = 0
            
            if not self.machines_dir.exists():
                return 0
            
            for script_file in self.machines_dir.glob("*.ipxe"):
                try:
                    file_age = current_time - script_file.stat().st_mtime
                    if file_age > max_age_seconds:
                        script_file.unlink()
                        cleaned_count += 1
                        logger.info(f"Cleaned up old script: {script_file.name}")
                except Exception as e:
                    logger.warning(f"Error cleaning up script {script_file.name}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} old scripts")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during script cleanup: {e}")
            return 0


# Convenience functions for use in other modules
async def save_boot_script_to_tftp(script_content: str, filename: str) -> str:
    """
    Save boot script to TFTP directory
    """
    adapter = TFTPAdapter()
    
    try:
        # Ensure directories exist
        adapter.machines_dir.mkdir(parents=True, exist_ok=True)
        
        # Save script
        script_path = adapter.tftp_root / filename
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Set permissions
        os.chmod(script_path, 0o644)
        
        logger.info(f"Boot script saved to TFTP: {filename}")
        return str(script_path)
        
    except Exception as e:
        logger.error(f"Failed to save boot script to TFTP: {e}")
        raise TFTPError(f"Failed to save boot script to TFTP: {e}")


async def remove_boot_script_from_tftp(filename: str) -> bool:
    """
    Remove boot script from TFTP directory
    """
    adapter = TFTPAdapter()
    return await adapter.remove_boot_script(filename)


# Convenience functions for external imports
async def get_tftp_status() -> Dict:
    """
    Get TFTP server status and configuration info
    """
    adapter = TFTPAdapter()
    return await adapter.get_tftp_status()


async def initialize_tftp_server() -> bool:
    """
    Initialize TFTP server directories and configuration
    """
    logger.info("Initializing TFTP server")
    
    try:
        adapter = TFTPAdapter()
        
        # Create directories
        adapter.tftp_root.mkdir(parents=True, exist_ok=True)
        adapter.machines_dir.mkdir(parents=True, exist_ok=True)
        adapter.boot_dir.mkdir(parents=True, exist_ok=True)
        
        # Set permissions
        os.chmod(adapter.tftp_root, 0o755)
        os.chmod(adapter.machines_dir, 0o755)
        os.chmod(adapter.boot_dir, 0o755)
        
        logger.info("TFTP server initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize TFTP server: {e}")
        return False