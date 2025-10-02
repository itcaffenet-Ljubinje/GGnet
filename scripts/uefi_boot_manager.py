#!/usr/bin/env python3
"""
UEFI Boot Manager for GGnet Diskless Server

This script manages UEFI boot configuration, iPXE scripts, and boot files
for diskless Windows 11 clients with SecureBoot support.
"""

import os
import sys
import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from string import Template
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UEFIBootError(Exception):
    """Custom exception for UEFI boot operations"""
    pass


class UEFIBootManager:
    """Manager class for UEFI boot operations"""
    
    def __init__(self, tftp_root: str = "/var/lib/tftpboot", mock_mode: bool = False):
        self.tftp_root = Path(tftp_root)
        self.mock_mode = mock_mode
        
        # Boot file paths
        self.ipxe_script_path = self.tftp_root / "boot.ipxe"
        self.uefi_boot_path = self.tftp_root / "bootx64.efi"
        self.grub_cfg_path = self.tftp_root / "grub.cfg"
        
        # Create TFTP root if it doesn't exist
        if not mock_mode:
            self.tftp_root.mkdir(parents=True, exist_ok=True)
    
    def generate_ipxe_script(
        self,
        machine_mac: str,
        server_ip: str,
        iscsi_target: str,
        iscsi_port: int = 3260,
        boot_params: Optional[Dict] = None
    ) -> str:
        """Generate iPXE boot script for a specific machine"""
        
        boot_params = boot_params or {}
        
        # iPXE script template
        ipxe_template = Template("""#!ipxe
# GGnet Diskless Boot Script
# Generated for MAC: ${mac_address}

echo Starting GGnet Diskless Boot...
echo MAC Address: ${mac_address}
echo Server: ${server_ip}
echo Target: ${iscsi_target}

# Configure network
dhcp

# Set iSCSI parameters
set initiator-iqn iqn.2025.ggnet.client:${mac_clean}
set target-ip ${server_ip}
set target-port ${iscsi_port}
set target-iqn ${iscsi_target}

# Connect to iSCSI target
echo Connecting to iSCSI target...
sanboot iscsi:$${target-ip}:$${target-port}:$${target-iqn}

# If sanboot fails, try alternative boot methods
echo iSCSI boot failed, trying alternative methods...

# HTTP boot fallback (if available)
chain http://${server_ip}/boot/wimboot

# If all else fails, show error
echo Boot failed - please contact administrator
shell
""")
        
        # Clean MAC address for use in IQN
        mac_clean = machine_mac.replace(":", "").replace("-", "").lower()
        
        script_content = ipxe_template.substitute(
            mac_address=machine_mac,
            mac_clean=mac_clean,
            server_ip=server_ip,
            iscsi_target=iscsi_target,
            iscsi_port=iscsi_port,
            **boot_params
        )
        
        return script_content
    
    def create_machine_ipxe_script(
        self,
        machine_mac: str,
        server_ip: str,
        iscsi_target: str,
        iscsi_port: int = 3260
    ) -> Path:
        """Create machine-specific iPXE script"""
        try:
            # Generate script content
            script_content = self.generate_ipxe_script(
                machine_mac, server_ip, iscsi_target, iscsi_port
            )
            
            # Create machine-specific script file
            mac_clean = machine_mac.replace(":", "").replace("-", "").lower()
            script_file = self.tftp_root / f"boot-{mac_clean}.ipxe"
            
            if not self.mock_mode:
                with open(script_file, 'w') as f:
                    f.write(script_content)
                
                # Make executable
                script_file.chmod(0o644)
            
            logger.info(f"Created iPXE script for {machine_mac}: {script_file}")
            return script_file
            
        except Exception as e:
            logger.error(f"Failed to create iPXE script for {machine_mac}: {e}")
            raise UEFIBootError(f"Failed to create iPXE script: {e}")
    
    def generate_grub_config(
        self,
        machines: List[Dict],
        server_ip: str,
        default_timeout: int = 10
    ) -> str:
        """Generate GRUB configuration for UEFI boot"""
        
        grub_template = Template("""# GGnet Diskless Server GRUB Configuration
# Auto-generated - do not edit manually

set timeout=${timeout}
set default=0

# Load modules
insmod part_gpt
insmod part_msdos
insmod fat
insmod ntfs
insmod chain
insmod normal
insmod configfile

# Set graphics mode
if loadfont /EFI/BOOT/unicode.pf2 ; then
    set gfxmode=auto
    insmod efi_gop
    insmod efi_uga
    insmod gfxterm
    terminal_output gfxterm
fi

# Main menu
menuentry "GGnet Diskless Boot" {
    echo "Starting GGnet Diskless Boot..."
    echo "Detecting network configuration..."
    
    # Load network modules
    insmod efinet
    insmod net
    insmod tftp
    insmod http
    
    # Configure network
    net_bootp
    
    # Chain to iPXE
    chainloader /bootx64.efi
}

menuentry "Network Boot (iPXE)" {
    echo "Loading iPXE..."
    chainloader /ipxe.efi
}

menuentry "Local Boot" {
    echo "Attempting local boot..."
    # Try to boot from local disk
    search --set=root --file /EFI/Microsoft/Boot/bootmgfw.efi
    chainloader /EFI/Microsoft/Boot/bootmgfw.efi
}

menuentry "UEFI Firmware Settings" {
    echo "Entering UEFI firmware settings..."
    fwsetup
}

menuentry "Reboot" {
    echo "Rebooting..."
    reboot
}

menuentry "Shutdown" {
    echo "Shutting down..."
    halt
}
""")
        
        config_content = grub_template.substitute(
            timeout=default_timeout,
            server_ip=server_ip
        )
        
        return config_content
    
    def create_grub_config(
        self,
        machines: List[Dict],
        server_ip: str,
        timeout: int = 10
    ) -> Path:
        """Create GRUB configuration file"""
        try:
            config_content = self.generate_grub_config(machines, server_ip, timeout)
            
            if not self.mock_mode:
                with open(self.grub_cfg_path, 'w') as f:
                    f.write(config_content)
                
                self.grub_cfg_path.chmod(0o644)
            
            logger.info(f"Created GRUB config: {self.grub_cfg_path}")
            return self.grub_cfg_path
            
        except Exception as e:
            logger.error(f"Failed to create GRUB config: {e}")
            raise UEFIBootError(f"Failed to create GRUB config: {e}")
    
    def install_uefi_boot_files(self, source_dir: Optional[str] = None) -> bool:
        """Install UEFI boot files (bootx64.efi, etc.)"""
        try:
            if self.mock_mode:
                logger.info("MOCK: Would install UEFI boot files")
                return True
            
            # Create EFI directory structure
            efi_boot_dir = self.tftp_root / "EFI" / "BOOT"
            efi_boot_dir.mkdir(parents=True, exist_ok=True)
            
            # If source directory provided, copy files from there
            if source_dir and Path(source_dir).exists():
                source_path = Path(source_dir)
                
                # Copy UEFI boot files
                boot_files = [
                    "bootx64.efi",
                    "grubx64.efi", 
                    "ipxe.efi",
                    "unicode.pf2"
                ]
                
                for boot_file in boot_files:
                    src_file = source_path / boot_file
                    if src_file.exists():
                        dst_file = efi_boot_dir / boot_file
                        shutil.copy2(src_file, dst_file)
                        logger.info(f"Copied {boot_file} to {dst_file}")
            
            else:
                # Create placeholder files or download from distribution
                logger.warning("No source directory provided for UEFI boot files")
                logger.info("You need to manually copy the following files to {efi_boot_dir}:")
                logger.info("- bootx64.efi (UEFI boot loader)")
                logger.info("- grubx64.efi (GRUB EFI binary)")
                logger.info("- ipxe.efi (iPXE EFI binary)")
                logger.info("- unicode.pf2 (GRUB font file)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to install UEFI boot files: {e}")
            raise UEFIBootError(f"Failed to install boot files: {e}")
    
    def create_secure_boot_config(self, cert_path: Optional[str] = None) -> Dict:
        """Create Secure Boot configuration"""
        try:
            config = {
                "secure_boot_enabled": False,
                "certificate_path": cert_path,
                "signed_bootloader": None,
                "instructions": []
            }
            
            if cert_path and Path(cert_path).exists():
                config["secure_boot_enabled"] = True
                config["signed_bootloader"] = str(self.tftp_root / "EFI" / "BOOT" / "bootx64.efi")
                config["instructions"].append("Secure Boot certificate found")
            else:
                config["instructions"] = [
                    "To enable Secure Boot support:",
                    "1. Obtain a code signing certificate",
                    "2. Sign the UEFI bootloader with sbsign",
                    "3. Install the certificate in client firmware",
                    "4. Update this configuration with certificate path"
                ]
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to create Secure Boot config: {e}")
            raise UEFIBootError(f"Failed to create Secure Boot config: {e}")
    
    def generate_pxe_config(self, machine_mac: str, server_ip: str) -> str:
        """Generate PXE configuration for legacy BIOS boot"""
        
        pxe_template = Template("""# GGnet PXE Configuration for ${mac_address}
DEFAULT ggnet_boot
TIMEOUT 100
PROMPT 0

LABEL ggnet_boot
    MENU LABEL GGnet Diskless Boot
    KERNEL pxelinux.0
    APPEND initrd=initrd.img boot=live fetch=http://${server_ip}/boot/filesystem.squashfs

LABEL local_boot
    MENU LABEL Boot from Local Disk
    LOCALBOOT 0x80
""")
        
        return pxe_template.substitute(
            mac_address=machine_mac,
            server_ip=server_ip
        )
    
    def setup_dhcp_config(
        self,
        machines: List[Dict],
        server_ip: str,
        dhcp_config_path: str = "/etc/dhcp/dhcpd.conf"
    ) -> str:
        """Generate DHCP configuration for network boot"""
        
        dhcp_template = Template("""# GGnet DHCP Configuration
# Auto-generated - review before applying

# Global settings
default-lease-time 600;
max-lease-time 7200;
authoritative;

# Network boot settings
option space PXE;
option PXE.mtftp-ip code 1 = ip-address;
option PXE.mtftp-cport code 2 = unsigned integer 16;
option PXE.mtftp-sport code 3 = unsigned integer 16;
option PXE.mtftp-tmout code 4 = unsigned integer 8;
option PXE.mtftp-delay code 5 = unsigned integer 8;
option arch code 93 = unsigned integer 16;

# Subnet configuration (adjust as needed)
subnet 192.168.1.0 netmask 255.255.255.0 {
    range 192.168.1.100 192.168.1.200;
    option routers 192.168.1.1;
    option domain-name-servers 8.8.8.8, 8.8.4.4;
    option broadcast-address 192.168.1.255;
    
    # Boot server
    next-server ${server_ip};
    
    # Boot file selection based on client architecture
    if option arch = 00:07 {
        filename "EFI/BOOT/bootx64.efi";  # UEFI x64
    } elsif option arch = 00:09 {
        filename "EFI/BOOT/bootx64.efi";  # UEFI x64 alternative
    } elsif option arch = 00:0b {
        filename "EFI/BOOT/bootaa64.efi"; # UEFI ARM64
    } else {
        filename "pxelinux.0";            # Legacy BIOS
    }
}

# Machine-specific configurations
${machine_configs}
""")
        
        # Generate machine-specific configs
        machine_configs = []
        for machine in machines:
            mac = machine.get('mac_address', '').replace(':', ':')
            name = machine.get('name', 'unknown')
            ip = machine.get('ip_address')
            
            if mac:
                config = f"""
# {name}
host {name.lower().replace(' ', '-')} {{
    hardware ethernet {mac};"""
                
                if ip:
                    config += f"\n    fixed-address {ip};"
                
                config += f"""
    option host-name "{name}";
}}"""
                machine_configs.append(config)
        
        dhcp_content = dhcp_template.substitute(
            server_ip=server_ip,
            machine_configs='\n'.join(machine_configs)
        )
        
        return dhcp_content
    
    def validate_boot_environment(self) -> Dict:
        """Validate the boot environment setup"""
        validation = {
            "status": "ok",
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        try:
            # Check TFTP root
            if not self.tftp_root.exists():
                validation["errors"].append(f"TFTP root directory not found: {self.tftp_root}")
            elif not os.access(self.tftp_root, os.R_OK):
                validation["errors"].append(f"TFTP root not readable: {self.tftp_root}")
            
            # Check UEFI boot files
            efi_boot_dir = self.tftp_root / "EFI" / "BOOT"
            required_files = ["bootx64.efi"]
            
            for file_name in required_files:
                file_path = efi_boot_dir / file_name
                if not file_path.exists():
                    validation["warnings"].append(f"UEFI boot file missing: {file_path}")
            
            # Check iPXE scripts
            if not self.ipxe_script_path.exists():
                validation["warnings"].append(f"iPXE script not found: {self.ipxe_script_path}")
            
            # Check GRUB config
            if not self.grub_cfg_path.exists():
                validation["warnings"].append(f"GRUB config not found: {self.grub_cfg_path}")
            
            # Recommendations
            validation["recommendations"] = [
                "Ensure TFTP server is running and configured",
                "Verify DHCP server is configured for network boot",
                "Test boot process with a client machine",
                "Consider implementing Secure Boot for production use"
            ]
            
            # Set overall status
            if validation["errors"]:
                validation["status"] = "error"
            elif validation["warnings"]:
                validation["status"] = "warning"
            
            return validation
            
        except Exception as e:
            validation["status"] = "error"
            validation["errors"].append(f"Validation failed: {e}")
            return validation


def main():
    """Command line interface for UEFI boot manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GGnet UEFI Boot Manager")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode")
    parser.add_argument("--tftp-root", default="/var/lib/tftpboot", help="TFTP root directory")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create iPXE script
    ipxe_parser = subparsers.add_parser("create-ipxe", help="Create iPXE script")
    ipxe_parser.add_argument("mac", help="Machine MAC address")
    ipxe_parser.add_argument("server_ip", help="Server IP address")
    ipxe_parser.add_argument("iscsi_target", help="iSCSI target IQN")
    ipxe_parser.add_argument("--port", type=int, default=3260, help="iSCSI port")
    
    # Create GRUB config
    grub_parser = subparsers.add_parser("create-grub", help="Create GRUB config")
    grub_parser.add_argument("server_ip", help="Server IP address")
    grub_parser.add_argument("--timeout", type=int, default=10, help="Boot timeout")
    
    # Install boot files
    install_parser = subparsers.add_parser("install-boot-files", help="Install UEFI boot files")
    install_parser.add_argument("--source", help="Source directory for boot files")
    
    # Validate environment
    validate_parser = subparsers.add_parser("validate", help="Validate boot environment")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        manager = UEFIBootManager(tftp_root=args.tftp_root, mock_mode=args.mock)
        
        if args.command == "create-ipxe":
            script_file = manager.create_machine_ipxe_script(
                machine_mac=args.mac,
                server_ip=args.server_ip,
                iscsi_target=args.iscsi_target,
                iscsi_port=args.port
            )
            print(f"Created iPXE script: {script_file}")
            
        elif args.command == "create-grub":
            config_file = manager.create_grub_config(
                machines=[],  # Empty for now
                server_ip=args.server_ip,
                timeout=args.timeout
            )
            print(f"Created GRUB config: {config_file}")
            
        elif args.command == "install-boot-files":
            manager.install_uefi_boot_files(source_dir=args.source)
            print("UEFI boot files installation completed")
            
        elif args.command == "validate":
            result = manager.validate_boot_environment()
            print(json.dumps(result, indent=2))
            
        return 0
        
    except UEFIBootError as e:
        logger.error(f"UEFI boot operation failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

