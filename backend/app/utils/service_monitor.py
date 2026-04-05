"""
Service monitoring utilities using systemctl
Provides detailed service status information
"""

import subprocess
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = structlog.get_logger()


class ServiceMonitorError(Exception):
    """Service monitoring error"""
    pass


class ServiceMonitor:
    """
    Service monitor for checking systemd service status using systemctl
    """
    
    def __init__(self):
        """Initialize service monitor"""
        self.systemctl_cmd = "systemctl"
    
    def _run_command(
        self,
        command: List[str],
        timeout: int = 10,
        check: bool = False
    ) -> subprocess.CompletedProcess:
        """
        Run systemctl command
        
        Args:
            command: Command and arguments as list
            timeout: Command timeout in seconds
            check: Raise exception on non-zero exit code
            
        Returns:
            CompletedProcess result
            
        Raises:
            ServiceMonitorError: If command fails
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=check
            )
            return result
        except subprocess.TimeoutExpired as e:
            raise ServiceMonitorError(f"Command timeout: {' '.join(command)}") from e
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            raise ServiceMonitorError(f"Command failed: {' '.join(command)} - {error_msg}") from e
        except Exception as e:
            raise ServiceMonitorError(f"Unexpected error running command: {e}") from e
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        Get detailed service status using systemctl show
        
        Args:
            service_name: Name of the systemd service
            
        Returns:
            Dictionary with service status information
        """
        try:
            # Run systemctl show with specific properties
            cmd = [
                self.systemctl_cmd,
                "--no-pager",
                "show",
                "-p", "ActiveState",
                "-p", "SubState",
                "-p", "ActiveEnterTimestamp",
                "-p", "InactiveExitTimestamp",
                "-p", "ActiveExitTimestamp",
                "-p", "InactiveEnterTimestamp",
                service_name
            ]
            
            result = self._run_command(cmd, timeout=10, check=False)
            
            if result.returncode != 0:
                return {
                    "name": service_name,
                    "active_state": "unknown",
                    "sub_state": "unknown",
                    "available": False,
                    "error": result.stderr.strip() if result.stderr else "Service not found"
                }
            
            # Parse output
            status = {
                "name": service_name,
                "available": True,
                "active_state": "unknown",
                "sub_state": "unknown",
                "active_enter_timestamp": None,
                "inactive_exit_timestamp": None,
                "active_exit_timestamp": None,
                "inactive_enter_timestamp": None
            }
            
            for line in result.stdout.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == "ActiveState":
                        status["active_state"] = value
                    elif key == "SubState":
                        status["sub_state"] = value
                    elif key == "ActiveEnterTimestamp":
                        status["active_enter_timestamp"] = value if value else None
                    elif key == "InactiveExitTimestamp":
                        status["inactive_exit_timestamp"] = value if value else None
                    elif key == "ActiveExitTimestamp":
                        status["active_exit_timestamp"] = value if value else None
                    elif key == "InactiveEnterTimestamp":
                        status["inactive_enter_timestamp"] = value if value else None
            
            return status
            
        except ServiceMonitorError:
            raise
        except Exception as e:
            logger.warning("Failed to get service status", service=service_name, error=str(e))
            return {
                "name": service_name,
                "active_state": "unknown",
                "sub_state": "unknown",
                "available": False,
                "error": str(e)
            }
    
    def is_service_active(self, service_name: str) -> bool:
        """
        Check if service is active
        
        Args:
            service_name: Name of the systemd service
            
        Returns:
            True if service is active, False otherwise
        """
        try:
            cmd = [self.systemctl_cmd, "is-active", service_name]
            result = self._run_command(cmd, timeout=5, check=False)
            return result.returncode == 0 and result.stdout.strip() == "active"
        except Exception as e:
            logger.warning("Failed to check service active status", service=service_name, error=str(e))
            return False
    
    def list_services(self, service_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get status for multiple services
        
        Args:
            service_names: List of service names to check. If None, checks common GGnet services
            
        Returns:
            List of service status dictionaries
        """
        if service_names is None:
            # Default services to monitor
            service_names = [
                "nginx",
                "networking",
                "ggnet-backend",
                "ggnet-worker",
                "ggnet-preflight",
                "zfs.target",
                "dnsmasq",
                "cockpit.socket",
                "postgresql",
                "redis-server",
                "tftpd-hpa"
            ]
        
        services = []
        for service_name in service_names:
            try:
                status = self.get_service_status(service_name)
                services.append(status)
            except Exception as e:
                logger.warning("Failed to get service status", service=service_name, error=str(e))
                services.append({
                    "name": service_name,
                    "active_state": "unknown",
                    "sub_state": "unknown",
                    "available": False,
                    "error": str(e)
                })
        
        return services
    
    def restart_service(self, service_name: str) -> bool:
        """
        Restart a systemd service
        
        Args:
            service_name: Name of the systemd service
            
        Returns:
            True if restart was successful, False otherwise
        """
        try:
            cmd = [self.systemctl_cmd, "restart", service_name]
            result = self._run_command(cmd, timeout=30, check=True)
            logger.info("Service restarted", service=service_name)
            return True
        except ServiceMonitorError as e:
            logger.error("Failed to restart service", service=service_name, error=str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error restarting service", service=service_name, error=str(e))
            return False

