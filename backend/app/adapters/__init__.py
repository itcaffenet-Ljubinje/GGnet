"""
Adapters package for external system integrations
Handles targetcli, DHCP, TFTP, iPXE, and other system tools
"""

from .targetcli import TargetCLIAdapter, TargetCLIError, create_target_for_machine, delete_target_for_machine
from .ipxe import iPXEScriptGenerator, generate_boot_script_for_session, save_boot_script_for_machine
from .dhcp import (
    DHCPAdapter,
    DHCPError,
    update_machine_in_dhcp as update_dhcp_for_machines,
    add_machine_to_dhcp,
    remove_machine_from_dhcp,
)
from .tftp import TFTPAdapter, TFTPError, initialize_tftp_server, save_boot_script_to_tftp, get_tftp_status

__all__ = [
    # TargetCLI
    "TargetCLIAdapter",
    "TargetCLIError", 
    "create_target_for_machine",
    "delete_target_for_machine",
    
    # iPXE
    "iPXEScriptGenerator",
    "generate_boot_script_for_session",
    "save_boot_script_for_machine",
    
    # DHCP
    "DHCPAdapter",
    "DHCPError",
    "update_dhcp_for_machines",
    "add_machine_to_dhcp",
    "remove_machine_from_dhcp",
    
    # TFTP
    "TFTPAdapter",
    "TFTPError",
    "initialize_tftp_server",
    "save_boot_script_to_tftp",
    "get_tftp_status"
]
