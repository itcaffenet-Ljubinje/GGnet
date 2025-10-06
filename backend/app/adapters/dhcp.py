"""
DHCP Configuration Adapter
Manages DHCP server configuration for diskless boot sessions
"""

import os
import tempfile
import subprocess
from pathlib import Path
from typing import List, Optional, Dict
import structlog

from app.models.machine import Machine
from app.core.config import get_settings
from app.core.exceptions import DHCPError

logger = structlog.get_logger(__name__)


class DHCPAdapter:
    """
    Manages DHCP server configuration for diskless boot
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.dhcp_config_path = Path("/etc/dhcp/dhcpd.conf")
        self.dhcp_config_backup_path = Path("/etc/dhcp/dhcpd.conf.backup")
        self.dhcp_service_name = "isc-dhcp-server"
    
    async def add_machine_to_dhcp(self, machine: Machine) -> bool:
        """
        Add machine configuration to DHCP server
        """
        logger.info(f"Adding machine {machine.id} to DHCP configuration")
        
        try:
            # Generate DHCP host entry
            host_entry = self._generate_host_entry(machine)
            
            # Add to DHCP configuration
            await self._add_host_entry_to_config(host_entry)
            
            # Reload DHCP server
            await self._reload_dhcp_server()
            
            logger.info(f"Successfully added machine {machine.id} to DHCP")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add machine {machine.id} to DHCP: {e}")
            raise DHCPError(f"Failed to add machine to DHCP: {e}")
    
    async def remove_machine_from_dhcp(self, machine: Machine) -> bool:
        """
        Remove machine configuration from DHCP server
        """
        logger.info(f"Removing machine {machine.id} from DHCP configuration")
        
        try:
            # Remove from DHCP configuration
            await self._remove_host_entry_from_config(machine)
            
            # Reload DHCP server
            await self._reload_dhcp_server()
            
            logger.info(f"Successfully removed machine {machine.id} from DHCP")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove machine {machine.id} from DHCP: {e}")
            raise DHCPError(f"Failed to remove machine from DHCP: {e}")
    
    async def update_machine_in_dhcp(self, machine: Machine) -> bool:
        """
        Update machine configuration in DHCP server
        """
        logger.info(f"Updating machine {machine.id} in DHCP configuration")
        
        try:
            # Remove old entry
            await self._remove_host_entry_from_config(machine)
            
            # Add new entry
            await self.add_machine_to_dhcp(machine)
            
            logger.info(f"Successfully updated machine {machine.id} in DHCP")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update machine {machine.id} in DHCP: {e}")
            raise DHCPError(f"Failed to update machine in DHCP: {e}")
    
    async def get_dhcp_status(self) -> Dict:
        """
        Get DHCP server status and configuration info
        """
        logger.info("Getting DHCP server status")
        
        try:
            status = {
                "service_running": False,
                "config_file_exists": False,
                "config_valid": False,
                "machines_configured": 0,
                "last_reload": None
            }
            
            # Check if service is running
            try:
                result = subprocess.run(
                    ["systemctl", "is-active", self.dhcp_service_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                status["service_running"] = result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                status["service_running"] = False
            
            # Check config file
            status["config_file_exists"] = self.dhcp_config_path.exists()
            
            # Validate config
            if status["config_file_exists"]:
                status["config_valid"] = await self._validate_dhcp_config()
                status["machines_configured"] = await self._count_configured_machines()
            
            logger.info("DHCP status retrieved", **status)
            return status
            
        except Exception as e:
            logger.error(f"Error getting DHCP status: {e}")
            return {"error": str(e)}
    
    def _generate_host_entry(self, machine: Machine) -> str:
        """
        Generate DHCP host entry for a machine
        """
        # Convert MAC address to DHCP format
        mac_dhcp = machine.mac_address
        
        # Generate host entry
        host_entry = f"""
host {machine.name.lower().replace(' ', '-')} {{
    hardware ethernet {mac_dhcp};
    fixed-address {machine.ip_address};
    option host-name "{machine.name}";
    next-server {self.settings.ISCSI_PORTAL_IP};
    filename "machines/{machine.mac_address.replace(':', '-').lower()}.ipxe";
}}"""
        
        return host_entry.strip()
    
    async def _add_host_entry_to_config(self, host_entry: str) -> None:
        """
        Add host entry to DHCP configuration file
        """
        logger.info("Adding host entry to DHCP configuration")
        
        try:
            # Read current config
            if self.dhcp_config_path.exists():
                with open(self.dhcp_config_path, 'r') as f:
                    config_content = f.read()
            else:
                config_content = self._get_default_dhcp_config()
            
            # Add host entry
            if "# GGnet machines" not in config_content:
                config_content += "\n\n# GGnet machines\n"
            
            config_content += f"\n{host_entry}\n"
            
            # Write updated config
            with open(self.dhcp_config_path, 'w') as f:
                f.write(config_content)
            
            logger.info("Host entry added to DHCP configuration")
            
        except Exception as e:
            logger.error(f"Failed to add host entry to DHCP config: {e}")
            raise
    
    async def _remove_host_entry_from_config(self, machine: Machine) -> None:
        """
        Remove host entry from DHCP configuration file
        """
        logger.info(f"Removing host entry for machine {machine.id} from DHCP configuration")
        
        try:
            if not self.dhcp_config_path.exists():
                logger.warning("DHCP config file does not exist")
                return
            
            # Read current config
            with open(self.dhcp_config_path, 'r') as f:
                config_content = f.read()
            
            # Find and remove host entry
            lines = config_content.split('\n')
            new_lines = []
            in_host_block = False
            host_name = machine.name.lower().replace(' ', '-')
            
            for line in lines:
                if f"host {host_name}" in line:
                    in_host_block = True
                    continue
                elif in_host_block and line.strip() == "}":
                    in_host_block = False
                    continue
                elif not in_host_block:
                    new_lines.append(line)
            
            # Write updated config
            with open(self.dhcp_config_path, 'w') as f:
                f.write('\n'.join(new_lines))
            
            logger.info(f"Host entry removed for machine {machine.id}")
            
        except Exception as e:
            logger.error(f"Failed to remove host entry from DHCP config: {e}")
            raise
    
    async def _reload_dhcp_server(self) -> None:
        """
        Reload DHCP server configuration
        """
        logger.info("Reloading DHCP server")
        
        try:
            # Test configuration first
            result = subprocess.run(
                ["dhcpd", "-t", "-cf", str(self.dhcp_config_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"DHCP config test failed: {result.stderr}")
                raise DHCPError(f"DHCP configuration test failed: {result.stderr}")
            
            # Reload service
            result = subprocess.run(
                ["systemctl", "reload", self.dhcp_service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"DHCP reload failed: {result.stderr}")
                raise DHCPError(f"Failed to reload DHCP server: {result.stderr}")
            
            logger.info("DHCP server reloaded successfully")
            
        except subprocess.TimeoutExpired:
            logger.error("DHCP reload timed out")
            raise DHCPError("DHCP reload operation timed out")
        except FileNotFoundError:
            logger.error("DHCP server not found")
            raise DHCPError("DHCP server not installed or not in PATH")
        except Exception as e:
            logger.error(f"Unexpected error during DHCP reload: {e}")
            raise DHCPError(f"Unexpected error during DHCP reload: {e}")
    
    async def _validate_dhcp_config(self) -> bool:
        """
        Validate DHCP configuration file
        """
        try:
            result = subprocess.run(
                ["dhcpd", "-t", "-cf", str(self.dhcp_config_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    async def _count_configured_machines(self) -> int:
        """
        Count number of machines configured in DHCP
        """
        try:
            if not self.dhcp_config_path.exists():
                return 0
            
            with open(self.dhcp_config_path, 'r') as f:
                content = f.read()
            
            # Count host entries
            count = content.count("host ")
            return count
        except Exception:
            return 0
    
    def _get_default_dhcp_config(self) -> str:
        """
        Get default DHCP configuration template
        """
        return f"""# GGnet DHCP Configuration
# Generated automatically by GGnet system

# Global options
option domain-name "ggnet.local";
option domain-name-servers {self.settings.ISCSI_PORTAL_IP};

# Default lease time
default-lease-time 600;
max-lease-time 7200;

# Authoritative
authoritative;

# Subnet configuration
subnet {self.settings.ISCSI_PORTAL_IP.split('.')[0]}.{self.settings.ISCSI_PORTAL_IP.split('.')[1]}.{self.settings.ISCSI_PORTAL_IP.split('.')[2]}.0 netmask 255.255.255.0 {{
    range {self.settings.ISCSI_PORTAL_IP.split('.')[0]}.{self.settings.ISCSI_PORTAL_IP.split('.')[1]}.{self.settings.ISCSI_PORTAL_IP.split('.')[2]}.100 {self.settings.ISCSI_PORTAL_IP.split('.')[0]}.{self.settings.ISCSI_PORTAL_IP.split('.')[1]}.{self.settings.ISCSI_PORTAL_IP.split('.')[2]}.200;
    option routers {self.settings.ISCSI_PORTAL_IP};
    option broadcast-address {self.settings.ISCSI_PORTAL_IP.split('.')[0]}.{self.settings.ISCSI_PORTAL_IP.split('.')[1]}.{self.settings.ISCSI_PORTAL_IP.split('.')[2]}.255;
    next-server {self.settings.ISCSI_PORTAL_IP};
    filename "boot.ipxe";
}}

# GGnet machines
"""


# Convenience functions for use in other modules
async def add_machine_to_dhcp(machine: Machine) -> bool:
    """
    Add machine to DHCP configuration
    """
    adapter = DHCPAdapter()
    return await adapter.add_machine_to_dhcp(machine)


async def remove_machine_from_dhcp(machine: Machine) -> bool:
    """
    Remove machine from DHCP configuration
    """
    adapter = DHCPAdapter()
    return await adapter.remove_machine_from_dhcp(machine)


async def update_machine_in_dhcp(machine: Machine) -> bool:
    """
    Update machine in DHCP configuration
    """
    adapter = DHCPAdapter()
    return await adapter.update_machine_in_dhcp(machine)