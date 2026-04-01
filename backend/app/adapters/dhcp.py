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
        # dnsmasq configuration paths
        self.dhcp_config_path = Path("/etc/dnsmasq.conf")
        self.dhcp_config_backup_path = Path("/etc/dnsmasq.conf.backup")
        self.dhcp_service_name = "dnsmasq"
    
    async def add_machine_to_dhcp(self, machine: Machine) -> bool:
        """
        Add machine configuration to dnsmasq DHCP server
        """
        logger.info(f"Adding machine {machine.id} to dnsmasq configuration")
        
        try:
            # Generate dnsmasq host entry
            host_entry = self._generate_host_entry(machine)
            
            # Generate boot file entry
            boot_entry = self._generate_dhcp_boot_entry(machine)
            
            # Add to dnsmasq configuration
            await self._add_host_entry_to_config(host_entry)
            await self._add_boot_entry_to_config(boot_entry)
            
            # Reload dnsmasq server
            await self._reload_dhcp_server()
            
            logger.info(f"Successfully added machine {machine.id} to dnsmasq")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add machine {machine.id} to dnsmasq: {e}")
            raise DHCPError(f"Failed to add machine to dnsmasq: {e}")
    
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
    
    async def reload_dhcp_server(self) -> bool:
        """
        Public method to reload dnsmasq server configuration
        """
        try:
            await self._reload_dhcp_server()
            return True
        except Exception as e:
            logger.error(f"Failed to reload dnsmasq server: {e}")
            return False
    
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
        Generate dnsmasq host entry for a machine
        Format: dhcp-host=<mac>,<ip>,<hostname>,<lease-time>,<tag>
        """
        # Convert MAC address format
        mac_dhcp = machine.mac_address
        hostname = machine.name.lower().replace(' ', '-')
        tag = f"ggnet-{machine.id}"
        lease_time = "12h"
        
        # Generate dnsmasq host entry
        host_entry = f"dhcp-host={mac_dhcp},{machine.ip_address},{hostname},{lease_time},set:{tag}"
        
        return host_entry
    
    def _generate_dhcp_boot_entry(self, machine: Machine) -> str:
        """
        Generate dnsmasq boot file entry for a machine
        Format: dhcp-boot=tag:<tag>,<filename>,<server>
        """
        tag = f"ggnet-{machine.id}"
        boot_filename = f"machines/{machine.mac_address.replace(':', '-').lower()}.ipxe"
        server_ip = self.settings.ISCSI_PORTAL_IP
        
        boot_entry = f"dhcp-boot=tag:{tag},{boot_filename},{server_ip}"
        return boot_entry
    
    async def _add_host_entry_to_config(self, host_entry: str) -> None:
        """
        Add host entry to dnsmasq configuration file
        Also adds corresponding boot file entry
        """
        logger.info("Adding host entry to dnsmasq configuration")
        
        try:
            # Read current config
            if self.dhcp_config_path.exists():
                with open(self.dhcp_config_path, 'r') as f:
                    config_content = f.read()
            else:
                config_content = self._get_default_dhcp_config()
            
            # Extract machine tag from host entry to generate boot entry
            # host_entry format: dhcp-host=mac,ip,name,lease,set:tag
            if "set:" in host_entry:
                tag = host_entry.split("set:")[1].strip()
                # Get machine from tag (tag format: ggnet-{machine_id})
                # We need machine object to generate boot entry, so we'll add it separately
                # For now, just add the host entry
            
            # Add host entry section if it doesn't exist
            if "# GGnet machines" not in config_content:
                config_content += "\n\n# GGnet machines\n"
            
            config_content += f"{host_entry}\n"
            
            # Write updated config
            with open(self.dhcp_config_path, 'w') as f:
                f.write(config_content)
            
            logger.info("Host entry added to dnsmasq configuration")
            
        except Exception as e:
            logger.error(f"Failed to add host entry to dnsmasq config: {e}")
            raise
    
    async def _remove_host_entry_from_config(self, machine: Machine) -> None:
        """
        Remove host entry and boot entry from dnsmasq configuration file
        """
        logger.info(f"Removing host entry for machine {machine.id} from dnsmasq configuration")
        
        try:
            if not self.dhcp_config_path.exists():
                logger.warning("dnsmasq config file does not exist")
                return
            
            # Read current config
            with open(self.dhcp_config_path, 'r') as f:
                config_content = f.read()
            
            # Find and remove host entry and boot entry
            lines = config_content.split('\n')
            new_lines = []
            tag = f"ggnet-{machine.id}"
            mac_address = machine.mac_address
            
            for line in lines:
                # Skip host entry for this machine
                if line.strip().startswith("dhcp-host=") and mac_address in line:
                    continue
                # Skip boot entry for this machine
                elif line.strip().startswith("dhcp-boot=") and f"tag:{tag}" in line:
                    continue
                else:
                    new_lines.append(line)
            
            # Write updated config
            with open(self.dhcp_config_path, 'w') as f:
                f.write('\n'.join(new_lines))
            
            logger.info(f"Host entry removed for machine {machine.id}")
            
        except Exception as e:
            logger.error(f"Failed to remove host entry from dnsmasq config: {e}")
            raise
    
    async def _add_boot_entry_to_config(self, boot_entry: str) -> None:
        """
        Add boot file entry to dnsmasq configuration
        """
        logger.info("Adding boot entry to dnsmasq configuration")
        
        try:
            # Read current config
            if self.dhcp_config_path.exists():
                with open(self.dhcp_config_path, 'r') as f:
                    config_content = f.read()
            else:
                config_content = self._get_default_dhcp_config()
            
            # Add boot entry section if it doesn't exist
            if "# GGnet machine boot files" not in config_content:
                config_content += "\n# GGnet machine boot files\n"
            
            config_content += f"{boot_entry}\n"
            
            # Write updated config
            with open(self.dhcp_config_path, 'w') as f:
                f.write(config_content)
            
            logger.info("Boot entry added to dnsmasq configuration")
            
        except Exception as e:
            logger.error(f"Failed to add boot entry to dnsmasq config: {e}")
            raise
    
    async def _reload_dhcp_server(self) -> None:
        """
        Reload dnsmasq server configuration
        """
        logger.info("Reloading dnsmasq server")
        
        try:
            # Test configuration first
            result = subprocess.run(
                ["dnsmasq", "--test"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"dnsmasq config test failed: {result.stderr}")
                raise DHCPError(f"dnsmasq configuration test failed: {result.stderr}")
            
            # Reload service
            result = subprocess.run(
                ["systemctl", "reload", self.dhcp_service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"dnsmasq reload failed: {result.stderr}")
                raise DHCPError(f"Failed to reload dnsmasq server: {result.stderr}")
            
            logger.info("dnsmasq server reloaded successfully")
            
        except subprocess.TimeoutExpired:
            logger.error("dnsmasq reload timed out")
            raise DHCPError("dnsmasq reload operation timed out")
        except FileNotFoundError:
            logger.error("dnsmasq not found")
            raise DHCPError("dnsmasq not installed or not in PATH")
        except Exception as e:
            logger.error(f"Unexpected error during dnsmasq reload: {e}")
            raise DHCPError(f"Unexpected error during dnsmasq reload: {e}")
    
    async def _validate_dhcp_config(self) -> bool:
        """
        Validate dnsmasq configuration file
        """
        try:
            result = subprocess.run(
                ["dnsmasq", "--test"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    async def _count_configured_machines(self) -> int:
        """
        Count number of machines configured in dnsmasq
        """
        try:
            if not self.dhcp_config_path.exists():
                return 0
            
            with open(self.dhcp_config_path, 'r') as f:
                content = f.read()
            
            # Count dnsmasq host entries (dhcp-host= lines in GGnet machines section)
            lines = content.split('\n')
            count = 0
            in_ggnet_section = False
            
            for line in lines:
                if "# GGnet machines" in line:
                    in_ggnet_section = True
                elif line.strip().startswith("#") and in_ggnet_section and "GGnet" not in line:
                    # End of GGnet section
                    break
                elif in_ggnet_section and line.strip().startswith("dhcp-host="):
                    count += 1
            
            return count
        except Exception:
            return 0
    
    def _get_default_dhcp_config(self) -> str:
        """
        Get default dnsmasq configuration template
        """
        ip_parts = self.settings.ISCSI_PORTAL_IP.split('.')
        subnet_base = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
        gateway = f"{subnet_base}.1"
        range_start = f"{subnet_base}.100"
        range_end = f"{subnet_base}.200"
        
        return f"""# ============================================================================
# GGnet - dnsmasq Configuration
# Generated automatically by GGnet system
# ============================================================================
# dnsmasq provides integrated DHCP + TFTP + DNS (ggRock-style)
# ============================================================================

# Interface configuration
interface=eth0
bind-interfaces

# DHCP configuration
dhcp-range={range_start},{range_end},255.255.255.0,12h
dhcp-option=option:router,{gateway}
dhcp-option=option:dns-server,8.8.8.8,8.8.4.4
dhcp-option=option:domain-name,ggnet.local

# PXE Boot configuration - Architecture detection
# UEFI SecureBoot support
dhcp-match=set:efi-x86_64,option:client-arch,7
dhcp-match=set:efi-x86_64,option:client-arch,9
dhcp-match=set:efi-x86,option:client-arch,6
dhcp-match=set:bios,option:client-arch,0
dhcp-match=set:ipxe,175

# Boot files per architecture (default)
dhcp-boot=tag:efi-x86_64,tag:!ipxe,snponly.efi,{self.settings.ISCSI_PORTAL_IP}
dhcp-boot=tag:efi-x86,tag:!ipxe,ipxe32.efi,{self.settings.ISCSI_PORTAL_IP}
dhcp-boot=tag:bios,tag:!ipxe,undionly.kpxe,{self.settings.ISCSI_PORTAL_IP}
dhcp-boot=tag:ipxe,http://{self.settings.ISCSI_PORTAL_IP}:8000/boot/script.ipxe

# TFTP configuration
enable-tftp
tftp-root={self.settings.TFTP_ROOT}
tftp-secure
tftp-no-blocksize

# DNS configuration
domain=ggnet.local
expand-hosts

# Logging
log-dhcp
log-queries
log-facility=/var/log/dnsmasq.log

# Performance
cache-size=1000
dns-forward-max=150

# Security
bogus-priv
domain-needed
no-resolv
server=8.8.8.8
server=8.8.4.4

# GGnet machines
# Static DHCP leases will be added here automatically
# Format: dhcp-host=<mac>,<ip>,<hostname>,<lease-time>,set:<tag>

# GGnet machine boot files
# Machine-specific boot files will be added here automatically
# Format: dhcp-boot=tag:<tag>,<filename>,<server>
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


def generate_dhcp_config_entry(machine: Machine) -> str:
    """
    Generate DHCP host entry text for a machine (convenience export for tests).
    """
    adapter = DHCPAdapter()
    return adapter._generate_host_entry(machine)  # type: ignore[attr-defined]