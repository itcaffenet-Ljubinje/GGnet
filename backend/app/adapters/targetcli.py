"""
targetcli adapter for iSCSI target management
Provides automated iSCSI target creation, configuration, and management
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import structlog
from app.core.config import get_settings

# Configure structured logging
logger = structlog.get_logger(__name__)


class TargetCLIError(Exception):
    """Custom exception for targetcli operations"""
    pass


class TargetCLIAdapter:
    """Adapter for targetcli command-line interface"""
    
    def __init__(self, targetcli_path: str = None):
        self.settings = get_settings()
        self.targetcli_path = targetcli_path or self.settings.TARGETCLI_PATH
        self._check_targetcli()
        
        # iSCSI configuration
        self.iscsi_prefix = self.settings.ISCSI_TARGET_PREFIX
        self.portal_ip = self.settings.ISCSI_PORTAL_IP
        self.portal_port = self.settings.ISCSI_PORTAL_PORT
        
        logger.info("TargetCLI adapter initialized", 
                   targetcli_path=self.targetcli_path,
                   iscsi_prefix=self.iscsi_prefix)
    
    def _check_targetcli(self) -> bool:
        """Check if targetcli is available"""
        try:
            result = subprocess.run(
                [self.targetcli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"targetcli found: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"targetcli check failed: {result.stderr}")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"targetcli not found: {e}")
            return False
    
    async def _run_targetcli_command(
        self, 
        commands: List[str], 
        timeout: int = 30
    ) -> Tuple[str, str, int]:
        """
        Run targetcli commands and return output
        
        Args:
            commands: List of targetcli commands to execute
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (stdout, stderr, returncode)
        """
        try:
            # Create temporary script file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as script_file:
                script_content = "#!/usr/bin/env python3\n"
                script_content += "import targetcli\n"
                script_content += "import json\n\n"
                
                for command in commands:
                    script_content += f"targetcli.execute_command('{command}')\n"
                
                script_file.write(script_content)
                script_file.flush()
                
                # Execute the script
                result = await asyncio.create_subprocess_exec(
                    self.targetcli_path,
                    script_file.name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(
                    result.communicate(), 
                    timeout=timeout
                )
                
                # Clean up script file
                os.unlink(script_file.name)
                
                return stdout.decode(), stderr.decode(), result.returncode
                
        except TimeoutError:
            logger.error(f"targetcli command timed out after {timeout} seconds")
            raise TargetCLIError(f"Command timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"targetcli command failed: {e}")
            raise TargetCLIError(f"Command execution failed: {e}")
    
    async def create_fileio_backstore(
        self, 
        name: str, 
        file_path: str, 
        size: int = None
    ) -> Dict:
        """
        Create a fileio backstore
        
        Args:
            name: Backstore name
            file_path: Path to the file
            size: File size in bytes (optional, for sparse files)
            
        Returns:
            Dict with backstore information
        """
        logger.info(f"Creating fileio backstore: {name} -> {file_path}")
        
        # Ensure file exists and has correct size
        if not os.path.exists(file_path):
            if size:
                # Create sparse file
                with open(file_path, 'wb') as f:
                    f.truncate(size)
                logger.info(f"Created sparse file: {file_path} ({size} bytes)")
            else:
                raise TargetCLIError(f"File does not exist: {file_path}")
        
        # Create fileio backstore
        command = f"/backstores/fileio create name={name} file_or_device={file_path}"
        
        stdout, stderr, returncode = await self._run_targetcli_command([command])
        
        if returncode == 0:
            logger.info(f"Fileio backstore created: {name}")
            return {
                "name": name,
                "type": "fileio",
                "file_path": file_path,
                "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
            }
        else:
            error_msg = stderr.strip() or stdout.strip()
            logger.error(f"Failed to create fileio backstore: {error_msg}")
            raise TargetCLIError(f"Failed to create fileio backstore: {error_msg}")
    
    async def create_iscsi_target(
        self, 
        target_id: str, 
        description: str = None
    ) -> Dict:
        """
        Create an iSCSI target
        
        Args:
            target_id: Unique target identifier
            description: Target description
            
        Returns:
            Dict with target information
        """
        logger.info(f"Creating iSCSI target: {target_id}")
        
        # Generate IQN
        iqn = f"{self.iscsi_prefix}:target-{target_id}"
        
        # Create iSCSI target
        command = f"/iscsi create {iqn}"
        if description:
            command += f" description={description}"
        
        stdout, stderr, returncode = await self._run_targetcli_command([command])
        
        if returncode == 0:
            logger.info(f"iSCSI target created: {iqn}")
            return {
                "iqn": iqn,
                "target_id": target_id,
                "description": description,
                "portal_ip": self.portal_ip,
                "portal_port": self.portal_port
            }
        else:
            error_msg = stderr.strip() or stdout.strip()
            logger.error(f"Failed to create iSCSI target: {error_msg}")
            raise TargetCLIError(f"Failed to create iSCSI target: {error_msg}")
    
    async def create_lun(
        self, 
        iqn: str, 
        backstore_path: str, 
        lun_id: int = 0
    ) -> Dict:
        """
        Create a LUN and map it to a backstore
        
        Args:
            iqn: Target IQN
            backstore_path: Path to the backstore
            lun_id: LUN ID (default: 0)
            
        Returns:
            Dict with LUN information
        """
        logger.info(f"Creating LUN {lun_id} for target {iqn}")
        
        # Create LUN
        command = f"/iscsi/{iqn}/tpg1/luns create {backstore_path}"
        
        stdout, stderr, returncode = await self._run_targetcli_command([command])
        
        if returncode == 0:
            logger.info(f"LUN {lun_id} created for target {iqn}")
            return {
                "lun_id": lun_id,
                "iqn": iqn,
                "backstore_path": backstore_path
            }
        else:
            error_msg = stderr.strip() or stdout.strip()
            logger.error(f"Failed to create LUN: {error_msg}")
            raise TargetCLIError(f"Failed to create LUN: {error_msg}")
    
    async def create_acl(
        self, 
        iqn: str, 
        initiator_iqn: str
    ) -> Dict:
        """
        Create ACL for an initiator
        
        Args:
            iqn: Target IQN
            initiator_iqn: Initiator IQN
            
        Returns:
            Dict with ACL information
        """
        logger.info(f"Creating ACL for initiator {initiator_iqn} on target {iqn}")
        
        # Create ACL
        command = f"/iscsi/{iqn}/tpg1/acls create {initiator_iqn}"
        
        stdout, stderr, returncode = await self._run_targetcli_command([command])
        
        if returncode == 0:
            logger.info(f"ACL created for initiator {initiator_iqn}")
            return {
                "iqn": iqn,
                "initiator_iqn": initiator_iqn
            }
        else:
            error_msg = stderr.strip() or stdout.strip()
            logger.error(f"Failed to create ACL: {error_msg}")
            raise TargetCLIError(f"Failed to create ACL: {error_msg}")
    
    async def enable_target_portal(
        self, 
        iqn: str, 
        ip: str = None, 
        port: int = None
    ) -> Dict:
        """
        Enable target portal
        
        Args:
            iqn: Target IQN
            ip: Portal IP (default: configured IP)
            port: Portal port (default: configured port)
            
        Returns:
            Dict with portal information
        """
        logger.info(f"Enabling portal for target {iqn}")
        
        portal_ip = ip or self.portal_ip
        portal_port = port or self.portal_port
        
        # Enable portal
        command = f"/iscsi/{iqn}/tpg1/portals create {portal_ip}:{portal_port}"
        
        stdout, stderr, returncode = await self._run_targetcli_command([command])
        
        if returncode == 0:
            logger.info(f"Portal enabled: {portal_ip}:{portal_port}")
            return {
                "iqn": iqn,
                "ip": portal_ip,
                "port": portal_port
            }
        else:
            error_msg = stderr.strip() or stdout.strip()
            logger.error(f"Failed to enable portal: {error_msg}")
            raise TargetCLIError(f"Failed to enable portal: {error_msg}")
    
    async def create_complete_target(
        self,
        target_id: str,
        image_path: str,
        initiator_iqn: str,
        description: str = None,
        lun_id: int = 0
    ) -> Dict:
        """
        Create a complete iSCSI target with backstore, LUN, and ACL
        
        Args:
            target_id: Unique target identifier
            image_path: Path to the disk image
            initiator_iqn: Initiator IQN for ACL
            description: Target description
            lun_id: LUN ID
            
        Returns:
            Dict with complete target information
        """
        logger.info(f"Creating complete iSCSI target: {target_id}")
        
        try:
            # 1. Create fileio backstore
            backstore_name = f"img_{target_id}"
            backstore_info = await self.create_fileio_backstore(
                backstore_name, 
                image_path
            )
            
            # 2. Create iSCSI target
            target_info = await self.create_iscsi_target(target_id, description)
            iqn = target_info["iqn"]
            
            # 3. Create LUN
            backstore_path = f"/backstores/fileio/{backstore_name}"
            lun_info = await self.create_lun(iqn, backstore_path, lun_id)
            
            # 4. Create ACL
            acl_info = await self.create_acl(iqn, initiator_iqn)
            
            # 5. Enable portal
            portal_info = await self.enable_target_portal(iqn)
            
            # 6. Save configuration
            await self.save_config()
            
            result = {
                "target_id": target_id,
                "iqn": iqn,
                "backstore": backstore_info,
                "lun": lun_info,
                "acl": acl_info,
                "portal": portal_info,
                "image_path": image_path,
                "initiator_iqn": initiator_iqn,
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Complete iSCSI target created successfully: {target_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create complete target {target_id}: {e}")
            # Attempt cleanup
            try:
                await self.delete_target(target_id)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup target {target_id}: {cleanup_error}")
            raise
    
    async def delete_target(self, target_id: str) -> bool:
        """
        Delete an iSCSI target and its associated resources
        
        Args:
            target_id: Target identifier
            
        Returns:
            True if successful
        """
        logger.info(f"Deleting iSCSI target: {target_id}")
        
        try:
            iqn = f"{self.iscsi_prefix}:target-{target_id}"
            backstore_name = f"img_{target_id}"
            
            # Delete commands in reverse order
            commands = [
                f"/iscsi/{iqn}/tpg1/acls delete {iqn}",
                f"/iscsi/{iqn}/tpg1/luns delete 0",
                f"/iscsi delete {iqn}",
                f"/backstores/fileio delete {backstore_name}"
            ]
            
            for command in commands:
                try:
                    stdout, stderr, returncode = await self._run_targetcli_command([command])
                    if returncode != 0:
                        logger.warning(f"Command failed (may be expected): {command}")
                except Exception as e:
                    logger.warning(f"Command failed (may be expected): {command} - {e}")
            
            # Save configuration
            await self.save_config()
            
            logger.info(f"iSCSI target deleted: {target_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete target {target_id}: {e}")
            return False
    
    async def list_targets(self) -> List[Dict]:
        """
        List all iSCSI targets
        
        Returns:
            List of target information dictionaries
        """
        logger.info("Listing iSCSI targets")
        
        try:
            # Get targetcli configuration
            command = "ls"
            stdout, stderr, returncode = await self._run_targetcli_command([command])
            
            if returncode == 0:
                # Parse output to extract target information
                targets = self._parse_targetcli_output(stdout)
                logger.info(f"Found {len(targets)} iSCSI targets")
                return targets
            else:
                error_msg = stderr.strip() or stdout.strip()
                logger.error(f"Failed to list targets: {error_msg}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to list targets: {e}")
            return []
    
    def _parse_targetcli_output(self, output: str) -> List[Dict]:
        """
        Parse targetcli output to extract target information
        
        Args:
            output: Raw targetcli output
            
        Returns:
            List of parsed target information
        """
        targets = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if 'iqn.' in line and 'tpg1' in line:
                # Extract IQN from line like "iqn.2025.ggnet:target-123 [tpg1]"
                match = re.search(r'(iqn\.[^\s]+)', line)
                if match:
                    iqn = match.group(1)
                    target_id = iqn.split(':')[-1].replace('target-', '')
                    targets.append({
                        "iqn": iqn,
                        "target_id": target_id,
                        "status": "active"
                    })
        
        return targets
    
    async def save_config(self) -> bool:
        """
        Save targetcli configuration
        
        Returns:
            True if successful
        """
        try:
            command = "saveconfig"
            stdout, stderr, returncode = await self._run_targetcli_command([command])
            
            if returncode == 0:
                logger.info("targetcli configuration saved")
                return True
            else:
                error_msg = stderr.strip() or stdout.strip()
                logger.error(f"Failed to save configuration: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    async def get_target_status(self, target_id: str) -> Dict:
        """
        Get status of a specific target
        
        Args:
            target_id: Target identifier
            
        Returns:
            Dict with target status information
        """
        logger.info(f"Getting status for target: {target_id}")
        
        try:
            iqn = f"{self.iscsi_prefix}:target-{target_id}"
            command = f"ls /iscsi/{iqn}"
            
            stdout, stderr, returncode = await self._run_targetcli_command([command])
            
            if returncode == 0:
                # Parse status information
                status = self._parse_target_status(stdout)
                status["target_id"] = target_id
                status["iqn"] = iqn
                return status
            else:
                return {
                    "target_id": target_id,
                    "iqn": iqn,
                    "status": "not_found",
                    "error": stderr.strip() or stdout.strip()
                }
                
        except Exception as e:
            logger.error(f"Failed to get target status: {e}")
            return {
                "target_id": target_id,
                "status": "error",
                "error": str(e)
            }
    
    def _parse_target_status(self, output: str) -> Dict:
        """
        Parse target status from targetcli output
        
        Args:
            output: Raw targetcli output
            
        Returns:
            Dict with parsed status information
        """
        status = {
            "status": "unknown",
            "luns": [],
            "acls": [],
            "portals": []
        }
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            if 'lun' in line.lower():
                status["luns"].append(line)
            elif 'acl' in line.lower():
                status["acls"].append(line)
            elif 'portal' in line.lower():
                status["portals"].append(line)
            elif 'tpg1' in line:
                status["status"] = "active"
        
        return status


# Convenience functions for common operations
async def create_target_for_machine(
    machine_id: int,
    machine_mac: str,
    image_path: str,
    description: str = None
) -> Dict:
    """
    Create an iSCSI target for a specific machine
    
    Args:
        machine_id: Machine ID
        machine_mac: Machine MAC address
        image_path: Path to the disk image
        description: Target description
        
    Returns:
        Dict with target information
    """
    adapter = TargetCLIAdapter()
    
    # Generate target ID from machine ID
    target_id = f"machine_{machine_id}"
    
    # Generate initiator IQN from MAC address
    # Format: iqn.2025.ggnet:initiator-<mac_without_colons>
    mac_clean = machine_mac.replace(':', '').replace('-', '')
    initiator_iqn = f"iqn.2025.ggnet:initiator-{mac_clean}"
    
    return await adapter.create_complete_target(
        target_id=target_id,
        image_path=image_path,
        initiator_iqn=initiator_iqn,
        description=description or f"Target for machine {machine_id}"
    )


async def delete_target_for_machine(machine_id: int) -> bool:
    """
    Delete iSCSI target for a specific machine
    
    Args:
        machine_id: Machine ID
        
    Returns:
        True if successful
    """
    adapter = TargetCLIAdapter()
    target_id = f"machine_{machine_id}"
    return await adapter.delete_target(target_id)
