#!/usr/bin/env python3
"""
iSCSI Target Management Script for GGnet Diskless Server

This script provides functions to create, manage, and delete iSCSI targets
using targetcli (LIO - Linux-IO Target).
"""

import subprocess
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import shlex

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class iSCSIError(Exception):
    """Custom exception for iSCSI operations"""
    pass


class iSCSIManager:
    """Manager class for iSCSI target operations"""
    
    def __init__(self, targetcli_path: str = "/usr/bin/targetcli", mock_mode: bool = False):
        self.targetcli_path = targetcli_path
        self.mock_mode = mock_mode
        
        if not mock_mode and not Path(targetcli_path).exists():
            raise iSCSIError(f"targetcli not found at {targetcli_path}")
        
        # Check if we have root privileges (required for targetcli)
        if not mock_mode and os.geteuid() != 0:
            logger.warning("Running without root privileges - some operations may fail")
    
    def _run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run a shell command and return (returncode, stdout, stderr)"""
        if self.mock_mode:
            logger.info(f"MOCK: Would run command: {' '.join(cmd)}")
            return 0, "Mock command executed successfully", ""
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            raise iSCSIError(f"Command timed out: {' '.join(cmd)}")
        except Exception as e:
            raise iSCSIError(f"Failed to execute command: {e}")
    
    def _targetcli(self, command: str) -> Tuple[int, str, str]:
        """Execute targetcli command"""
        cmd = [self.targetcli_path] + shlex.split(command)
        return self._run_command(cmd)
    
    def create_fileio_backstore(self, name: str, file_path: str, size: Optional[int] = None) -> bool:
        """Create a fileio backstore"""
        try:
            # Check if file exists
            if not Path(file_path).exists():
                raise iSCSIError(f"Image file not found: {file_path}")
            
            # Create backstore command
            if size:
                cmd = f"/backstores/fileio create name={name} file_or_dev={file_path} size={size}"
            else:
                cmd = f"/backstores/fileio create name={name} file_or_dev={file_path}"
            
            returncode, stdout, stderr = self._targetcli(cmd)
            
            if returncode != 0:
                raise iSCSIError(f"Failed to create backstore: {stderr}")
            
            logger.info(f"Created fileio backstore: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create fileio backstore {name}: {e}")
            raise iSCSIError(f"Failed to create backstore: {e}")
    
    def create_iscsi_target(self, iqn: str) -> bool:
        """Create iSCSI target"""
        try:
            cmd = f"/iscsi create {iqn}"
            returncode, stdout, stderr = self._targetcli(cmd)
            
            if returncode != 0:
                # Check if target already exists
                if "already exists" in stderr.lower():
                    logger.warning(f"iSCSI target {iqn} already exists")
                    return True
                raise iSCSIError(f"Failed to create iSCSI target: {stderr}")
            
            logger.info(f"Created iSCSI target: {iqn}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create iSCSI target {iqn}: {e}")
            raise iSCSIError(f"Failed to create target: {e}")
    
    def create_lun(self, iqn: str, lun_id: int, backstore_name: str) -> bool:
        """Create LUN mapping"""
        try:
            cmd = f"/iscsi/{iqn}/tpg1/luns create /backstores/fileio/{backstore_name} lun={lun_id}"
            returncode, stdout, stderr = self._targetcli(cmd)
            
            if returncode != 0:
                raise iSCSIError(f"Failed to create LUN: {stderr}")
            
            logger.info(f"Created LUN {lun_id} for target {iqn}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create LUN {lun_id} for {iqn}: {e}")
            raise iSCSIError(f"Failed to create LUN: {e}")
    
    def create_acl(self, iqn: str, initiator_iqn: str) -> bool:
        """Create ACL for initiator"""
        try:
            cmd = f"/iscsi/{iqn}/tpg1/acls create {initiator_iqn}"
            returncode, stdout, stderr = self._targetcli(cmd)
            
            if returncode != 0:
                # Check if ACL already exists
                if "already exists" in stderr.lower():
                    logger.warning(f"ACL for {initiator_iqn} already exists")
                    return True
                raise iSCSIError(f"Failed to create ACL: {stderr}")
            
            logger.info(f"Created ACL for initiator {initiator_iqn}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create ACL for {initiator_iqn}: {e}")
            raise iSCSIError(f"Failed to create ACL: {e}")
    
    def set_portal(self, iqn: str, ip: str = "0.0.0.0", port: int = 3260) -> bool:
        """Set portal IP and port"""
        try:
            # Delete default portal first
            cmd = f"/iscsi/{iqn}/tpg1/portals delete 0.0.0.0 3260"
            self._targetcli(cmd)  # Ignore errors for this
            
            # Create new portal
            cmd = f"/iscsi/{iqn}/tpg1/portals create {ip} {port}"
            returncode, stdout, stderr = self._targetcli(cmd)
            
            if returncode != 0:
                raise iSCSIError(f"Failed to set portal: {stderr}")
            
            logger.info(f"Set portal for {iqn}: {ip}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set portal for {iqn}: {e}")
            raise iSCSIError(f"Failed to set portal: {e}")
    
    def enable_target(self, iqn: str) -> bool:
        """Enable iSCSI target"""
        try:
            cmd = f"/iscsi/{iqn}/tpg1 set attribute authentication=0"
            self._targetcli(cmd)
            
            cmd = f"/iscsi/{iqn}/tpg1 set attribute generate_node_acls=1"
            self._targetcli(cmd)
            
            cmd = f"/iscsi/{iqn}/tpg1 set attribute demo_mode_write_protect=0"
            self._targetcli(cmd)
            
            logger.info(f"Enabled iSCSI target: {iqn}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable target {iqn}: {e}")
            raise iSCSIError(f"Failed to enable target: {e}")
    
    def delete_target(self, iqn: str) -> bool:
        """Delete iSCSI target and associated backstores"""
        try:
            # Get target info first to find associated backstores
            backstores = self.get_target_backstores(iqn)
            
            # Delete iSCSI target
            cmd = f"/iscsi delete {iqn}"
            returncode, stdout, stderr = self._targetcli(cmd)
            
            if returncode != 0 and "does not exist" not in stderr.lower():
                raise iSCSIError(f"Failed to delete iSCSI target: {stderr}")
            
            # Delete associated backstores
            for backstore in backstores:
                cmd = f"/backstores/fileio delete {backstore}"
                returncode, stdout, stderr = self._targetcli(cmd)
                if returncode != 0 and "does not exist" not in stderr.lower():
                    logger.warning(f"Failed to delete backstore {backstore}: {stderr}")
            
            logger.info(f"Deleted iSCSI target: {iqn}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete target {iqn}: {e}")
            raise iSCSIError(f"Failed to delete target: {e}")
    
    def get_target_backstores(self, iqn: str) -> List[str]:
        """Get list of backstores associated with target"""
        try:
            cmd = f"ls /iscsi/{iqn}/tpg1/luns"
            returncode, stdout, stderr = self._targetcli(cmd)
            
            if returncode != 0:
                return []
            
            # Parse output to extract backstore names
            backstores = []
            for line in stdout.split('\n'):
                if 'fileio' in line and '->' in line:
                    # Extract backstore name from line like "lun0 -> /backstores/fileio/backstore_name"
                    parts = line.split('->')
                    if len(parts) > 1:
                        backstore_path = parts[1].strip()
                        backstore_name = backstore_path.split('/')[-1]
                        backstores.append(backstore_name)
            
            return backstores
            
        except Exception as e:
            logger.error(f"Failed to get backstores for {iqn}: {e}")
            return []
    
    def save_config(self) -> bool:
        """Save targetcli configuration"""
        try:
            cmd = "saveconfig"
            returncode, stdout, stderr = self._targetcli(cmd)
            
            if returncode != 0:
                raise iSCSIError(f"Failed to save config: {stderr}")
            
            logger.info("Saved targetcli configuration")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise iSCSIError(f"Failed to save config: {e}")
    
    def create_complete_target(
        self, 
        iqn: str, 
        system_image_path: str, 
        extra_image_path: Optional[str] = None,
        portal_ip: str = "0.0.0.0",
        portal_port: int = 3260
    ) -> Dict[str, any]:
        """Create complete iSCSI target with system and optional extra disk"""
        try:
            target_info = {
                "iqn": iqn,
                "portal": f"{portal_ip}:{portal_port}",
                "luns": {},
                "backstores": []
            }
            
            # Generate unique backstore names
            base_name = iqn.split(':')[-1].replace('.', '_')
            system_backstore = f"{base_name}_system"
            
            # Create system disk backstore (LUN 0)
            self.create_fileio_backstore(system_backstore, system_image_path)
            target_info["backstores"].append(system_backstore)
            
            # Create iSCSI target
            self.create_iscsi_target(iqn)
            
            # Create system LUN
            self.create_lun(iqn, 0, system_backstore)
            target_info["luns"][0] = {
                "backstore": system_backstore,
                "image_path": system_image_path,
                "type": "system"
            }
            
            # Create extra disk if provided (LUN 1)
            if extra_image_path:
                extra_backstore = f"{base_name}_extra"
                self.create_fileio_backstore(extra_backstore, extra_image_path)
                self.create_lun(iqn, 1, extra_backstore)
                target_info["backstores"].append(extra_backstore)
                target_info["luns"][1] = {
                    "backstore": extra_backstore,
                    "image_path": extra_image_path,
                    "type": "extra"
                }
            
            # Set portal
            self.set_portal(iqn, portal_ip, portal_port)
            
            # Enable target
            self.enable_target(iqn)
            
            # Save configuration
            self.save_config()
            
            logger.info(f"Successfully created complete iSCSI target: {iqn}")
            return target_info
            
        except Exception as e:
            logger.error(f"Failed to create complete target {iqn}: {e}")
            # Cleanup on failure
            try:
                self.delete_target(iqn)
            except:
                pass
            raise iSCSIError(f"Failed to create complete target: {e}")


def main():
    """Command line interface for iSCSI manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GGnet iSCSI Target Manager")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode (no actual commands)")
    parser.add_argument("--targetcli", default="/usr/bin/targetcli", help="Path to targetcli binary")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create target command
    create_parser = subparsers.add_parser("create", help="Create iSCSI target")
    create_parser.add_argument("iqn", help="iSCSI Qualified Name")
    create_parser.add_argument("system_image", help="Path to system image file")
    create_parser.add_argument("--extra-image", help="Path to extra disk image file")
    create_parser.add_argument("--portal-ip", default="0.0.0.0", help="Portal IP address")
    create_parser.add_argument("--portal-port", type=int, default=3260, help="Portal port")
    
    # Delete target command
    delete_parser = subparsers.add_parser("delete", help="Delete iSCSI target")
    delete_parser.add_argument("iqn", help="iSCSI Qualified Name")
    
    # List targets command
    list_parser = subparsers.add_parser("list", help="List iSCSI targets")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        manager = iSCSIManager(targetcli_path=args.targetcli, mock_mode=args.mock)
        
        if args.command == "create":
            result = manager.create_complete_target(
                iqn=args.iqn,
                system_image_path=args.system_image,
                extra_image_path=args.extra_image,
                portal_ip=args.portal_ip,
                portal_port=args.portal_port
            )
            print(json.dumps(result, indent=2))
            
        elif args.command == "delete":
            manager.delete_target(args.iqn)
            print(f"Deleted target: {args.iqn}")
            
        elif args.command == "list":
            # TODO: Implement list functionality
            print("List functionality not yet implemented")
            
        return 0
        
    except iSCSIError as e:
        logger.error(f"iSCSI operation failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

