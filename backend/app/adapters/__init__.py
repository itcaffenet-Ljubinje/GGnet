"""
Adapters package for external system integrations
Handles targetcli, DHCP, TFTP, and other system tools
"""

from .targetcli import TargetCLIAdapter, TargetCLIError, create_target_for_machine, delete_target_for_machine

__all__ = [
    "TargetCLIAdapter",
    "TargetCLIError", 
    "create_target_for_machine",
    "delete_target_for_machine"
]
