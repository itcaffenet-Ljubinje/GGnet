"""
iPXE Script Generator
Generates iPXE boot scripts for diskless boot sessions
"""

from typing import Dict, List, Optional
import structlog

from app.models.machine import Machine
from app.models.target import Target
from app.models.image import Image
from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class iPXEScriptGenerator:
    """
    Generates iPXE boot scripts for diskless boot sessions
    """
    
    def __init__(self):
        self.settings = get_settings()
    
    def generate_machine_boot_script(
        self, 
        machine: Machine, 
        target: Target, 
        image: Image
    ) -> str:
        """
        Generate iPXE boot script for a specific machine
        """
        logger.info(f"Generating iPXE boot script for machine {machine.id}")
        
        # Get machine-specific configuration
        machine_config = self._get_machine_config(machine)
        
        # Generate the boot script
        script_lines = [
            "#!ipxe",
            f"# Boot script for machine: {machine.name}",
            f"# Machine ID: {machine.id}",
            f"# Target IQN: {target.iqn}",
            "",
            "# Set console output",
            "console --x 1024 --y 768",
            "",
            "# Set timeout",
            "set timeout 10000",
            "",
            "# Display boot message",
            f"echo Booting {machine.name} from GGnet diskless system...",
            "echo",
            "",
            "# Configure network (if needed)",
            "dhcp",
            "",
            "# Set iSCSI parameters",
            f"set initiator-iqn {target.initiator_iqn}",
            f"set target-iqn {target.iqn}",
            f"set portal-ip {self.settings.ISCSI_PORTAL_IP}",
            f"set portal-port {self.settings.ISCSI_PORTAL_PORT}",
            f"set lun-id {target.lun_id}",
            "",
            "# Sanity check",
            "echo Initiator IQN: ${initiator-iqn}",
            "echo Target IQN: ${target-iqn}",
            "echo Portal: ${portal-ip}:${portal-port}",
            "echo LUN ID: ${lun-id}",
            "echo",
            "",
            "# Connect to iSCSI target",
            "echo Connecting to iSCSI target...",
            f"sanboot iscsi:{self.settings.ISCSI_PORTAL_IP}::{target.lun_id}:{target.iqn}",
            "",
            "# Fallback boot options",
            "echo iSCSI boot failed, trying PXE boot...",
            "sleep 3",
            "chain tftp://${next-server}/pxelinux.0",
            "",
            "# Final fallback",
            "echo All boot methods failed",
            "sleep 10",
            "reboot"
        ]
        
        # Add machine-specific customizations
        if machine_config.get("custom_boot_params"):
            script_lines.extend([
                "",
                "# Machine-specific boot parameters",
                *machine_config["custom_boot_params"]
            ])
        
        script_content = "\n".join(script_lines)
        
        logger.info(f"Generated iPXE script for machine {machine.id}", 
                   script_length=len(script_content))
        
        return script_content
    
    def generate_generic_boot_script(self) -> str:
        """
        Generate a generic iPXE boot script for unknown machines
        """
        logger.info("Generating generic iPXE boot script")
        
        script_lines = [
            "#!ipxe",
            "# Generic GGnet diskless boot script",
            "",
            "# Set console output",
            "console --x 1024 --y 768",
            "",
            "# Set timeout",
            "set timeout 10000",
            "",
            "# Display boot message",
            "echo Welcome to GGnet Diskless System",
            "echo",
            "",
            "# Configure network",
            "dhcp",
            "",
            "# Get machine information",
            "echo Machine MAC: ${net0/mac}",
            "echo Machine IP: ${net0/ip}",
            "echo",
            "",
            "# Try to get machine-specific boot script",
            "echo Attempting to load machine-specific boot script...",
            f"chain tftp://{self.settings.ISCSI_PORTAL_IP}/machines/${{net0/mac:hexhyp}}.ipxe ||",
            f"chain tftp://{self.settings.ISCSI_PORTAL_IP}/machines/${{net0/mac}}.ipxe ||",
            "",
            "# Fallback to PXE boot",
            "echo Machine-specific script not found, falling back to PXE...",
            "sleep 3",
            "chain tftp://${next-server}/pxelinux.0",
            "",
            "# Final fallback",
            "echo All boot methods failed",
            "sleep 10",
            "reboot"
        ]
        
        script_content = "\n".join(script_lines)
        
        logger.info("Generated generic iPXE script", 
                   script_length=len(script_content))
        
        return script_content
    
    def get_machine_script_filename(self, machine: Machine) -> str:
        """
        Get the filename for a machine's boot script
        """
        # Use MAC address as filename (with hyphens)
        mac_filename = machine.mac_address.replace(":", "-").lower()
        return f"machines/{mac_filename}.ipxe"
    
    def get_machine_script_path(self, machine: Machine) -> str:
        """
        Get the full path for a machine's boot script
        """
        filename = self.get_machine_script_filename(machine)
        return f"{self.settings.TFTP_ROOT}/{filename}"
    
    def _get_machine_config(self, machine: Machine) -> Dict:
        """
        Get machine-specific configuration for boot script generation
        """
        config = {
            "custom_boot_params": [],
            "boot_timeout": 10000,
            "console_settings": "--x 1024 --y 768"
        }
        
        # Add machine-specific customizations based on machine properties
        if machine.boot_mode == "uefi":
            config["custom_boot_params"].extend([
                "# UEFI-specific settings",
                "set uefi-boot true"
            ])
        
        if machine.description and "custom" in machine.description.lower():
            config["custom_boot_params"].extend([
                "# Custom machine configuration",
                "echo Custom machine detected"
            ])
        
        return config
    
    def validate_script_syntax(self, script_content: str) -> bool:
        """
        Basic validation of iPXE script syntax
        """
        try:
            lines = script_content.split("\n")
            
            # Check for required elements
            has_shebang = any(line.strip().startswith("#!ipxe") for line in lines)
            has_sanboot = any("sanboot" in line.lower() for line in lines)
            has_echo = any("echo" in line.lower() for line in lines)
            
            if not has_shebang:
                logger.warning("iPXE script missing shebang (#!ipxe)")
                return False
            
            if not has_sanboot:
                logger.warning("iPXE script missing sanboot command")
                return False
            
            logger.info("iPXE script syntax validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating iPXE script syntax: {e}")
            return False
    
    def get_script_info(self, script_content: str) -> Dict:
        """
        Extract information from an iPXE script
        """
        info = {
            "lines": 0,
            "has_sanboot": False,
            "has_chain": False,
            "target_iqn": None,
            "portal_ip": None,
            "lun_id": None
        }
        
        try:
            lines = script_content.split("\n")
            info["lines"] = len(lines)
            
            for line in lines:
                line_lower = line.lower().strip()
                
                if "sanboot" in line_lower:
                    info["has_sanboot"] = True
                    
                    # Extract iSCSI details
                    if "iscsi:" in line_lower:
                        parts = line.split(":")
                        if len(parts) >= 4:
                            info["portal_ip"] = parts[1]
                            info["lun_id"] = parts[2]
                            info["target_iqn"] = parts[3]
                
                if "chain" in line_lower:
                    info["has_chain"] = True
            
            logger.info("Extracted script information", **info)
            return info
            
        except Exception as e:
            logger.error(f"Error extracting script information: {e}")
            return info


async def save_boot_script_for_machine(
    machine: Machine, 
    script_content: str
) -> str:
    """
    Save boot script for a machine to TFTP directory
    """
    from app.adapters.tftp import TFTPAdapter
    
    logger.info(f"Saving boot script for machine {machine.id}")
    
    try:
        tftp_adapter = TFTPAdapter()
        script_path = await tftp_adapter.save_boot_script(script_content, machine)
        
        logger.info(f"Boot script saved for machine {machine.id}", 
                   script_path=script_path)
        
        return script_path
        
    except Exception as e:
        logger.error(f"Failed to save boot script for machine {machine.id}: {e}")
        raise


def generate_dhcp_config_entry(machine: Machine) -> str:
    """
    Generate DHCP configuration entry for a machine
    """
    logger.info(f"Generating DHCP config entry for machine {machine.id}")
    
    # Convert MAC address to DHCP format (with colons)
    mac_dhcp = machine.mac_address
    
    # Generate host entry
    host_entry = f"""
host {machine.name.lower().replace(' ', '-')} {{
    hardware ethernet {mac_dhcp};
    fixed-address {machine.ip_address};
    option host-name "{machine.name}";
    next-server {get_settings().ISCSI_PORTAL_IP};
    filename "machines/{machine.mac_address.replace(':', '-').lower()}.ipxe";
}}"""
    
    logger.info(f"Generated DHCP config entry for machine {machine.id}")
    return host_entry.strip()


def generate_pxe_config_entry(machine: Machine) -> str:
    """
    Generate PXE configuration entry for a machine
    """
    logger.info(f"Generating PXE config entry for machine {machine.id}")
    
    # Generate PXE config content
    pxe_config = f"""DEFAULT linux
LABEL linux
    KERNEL vmlinuz
    APPEND initrd=initrd.img root=/dev/ram0 rw quiet
    IPAPPEND 2
    PROMPT 0
    TIMEOUT 50"""
    
    logger.info(f"Generated PXE config entry for machine {machine.id}")
    return pxe_config