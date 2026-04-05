"""
Boot Event Logger
Utility for logging network boot events during the boot process
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.boot_event import BootEvent, BootEventType, BootEventStatus
from app.models.machine import Machine
from app.models.session import Session

logger = structlog.get_logger(__name__)


class BootEventLogger:
    """Utility class for logging boot events"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_event(
        self,
        event_type: BootEventType,
        status: BootEventStatus,
        message: str,
        machine_id: Optional[int] = None,
        session_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        client_ip: Optional[str] = None,
        server_ip: Optional[str] = None,
        mac_address: Optional[str] = None
    ) -> BootEvent:
        """
        Log a boot event
        
        Args:
            event_type: Type of boot event
            status: Status of the event
            message: Human-readable message
            machine_id: Optional machine ID
            session_id: Optional session ID
            details: Optional additional details (JSON)
            client_ip: Optional client IP address
            server_ip: Optional server IP address
            mac_address: Optional MAC address
            
        Returns:
            Created BootEvent instance
        """
        try:
            boot_event = BootEvent(
                machine_id=machine_id,
                session_id=session_id,
                event_type=event_type,
                status=status,
                message=message,
                details=details,
                client_ip=client_ip,
                server_ip=server_ip,
                mac_address=mac_address
            )
            
            self.db.add(boot_event)
            await self.db.commit()
            await self.db.refresh(boot_event)
            
            logger.info(
                "Boot event logged",
                event_id=boot_event.id,
                event_type=event_type.value,
                status=status.value,
                machine_id=machine_id,
                session_id=session_id
            )
            
            return boot_event
            
        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Failed to log boot event",
                error=str(e),
                event_type=event_type.value,
                machine_id=machine_id
            )
            # Don't raise - boot event logging should not break the boot process
            raise
    
    async def log_pxe_start(
        self,
        machine: Machine,
        session: Optional[Session] = None,
        client_ip: Optional[str] = None
    ) -> BootEvent:
        """Log PXE boot start"""
        return await self.log_event(
            event_type=BootEventType.PXE_START,
            status=BootEventStatus.IN_PROGRESS,
            message=f"PXE boot started for machine {machine.name}",
            machine_id=machine.id,
            session_id=session.id if session else None,
            client_ip=client_ip,
            mac_address=machine.mac_address,
            details={"machine_name": machine.name}
        )
    
    async def log_dhcp_request(
        self,
        machine: Machine,
        session: Optional[Session] = None,
        client_ip: Optional[str] = None
    ) -> BootEvent:
        """Log DHCP request"""
        return await self.log_event(
            event_type=BootEventType.DHCP_REQUEST,
            status=BootEventStatus.IN_PROGRESS,
            message=f"DHCP request received from {machine.name}",
            machine_id=machine.id,
            session_id=session.id if session else None,
            client_ip=client_ip,
            mac_address=machine.mac_address,
            details={"machine_name": machine.name}
        )
    
    async def log_tftp_request(
        self,
        machine: Machine,
        session: Optional[Session] = None,
        filename: Optional[str] = None,
        client_ip: Optional[str] = None
    ) -> BootEvent:
        """Log TFTP request"""
        return await self.log_event(
            event_type=BootEventType.TFTP_REQUEST,
            status=BootEventStatus.IN_PROGRESS,
            message=f"TFTP request for boot file from {machine.name}",
            machine_id=machine.id,
            session_id=session.id if session else None,
            client_ip=client_ip,
            mac_address=machine.mac_address,
            details={
                "machine_name": machine.name,
                "filename": filename
            }
        )
    
    async def log_ipxe_load(
        self,
        machine: Machine,
        session: Optional[Session] = None,
        script_url: Optional[str] = None,
        client_ip: Optional[str] = None
    ) -> BootEvent:
        """Log iPXE script load"""
        return await self.log_event(
            event_type=BootEventType.IPXE_LOAD,
            status=BootEventStatus.IN_PROGRESS,
            message=f"iPXE script loaded for {machine.name}",
            machine_id=machine.id,
            session_id=session.id if session else None,
            client_ip=client_ip,
            mac_address=machine.mac_address,
            details={
                "machine_name": machine.name,
                "script_url": script_url
            }
        )
    
    async def log_iscsi_connect(
        self,
        machine: Machine,
        session: Optional[Session] = None,
        target_iqn: Optional[str] = None,
        client_ip: Optional[str] = None
    ) -> BootEvent:
        """Log iSCSI connection"""
        return await self.log_event(
            event_type=BootEventType.ISCSI_CONNECT,
            status=BootEventStatus.IN_PROGRESS,
            message=f"iSCSI connection initiated for {machine.name}",
            machine_id=machine.id,
            session_id=session.id if session else None,
            client_ip=client_ip,
            mac_address=machine.mac_address,
            details={
                "machine_name": machine.name,
                "target_iqn": target_iqn
            }
        )
    
    async def log_iscsi_connected(
        self,
        machine: Machine,
        session: Optional[Session] = None,
        target_iqn: Optional[str] = None,
        client_ip: Optional[str] = None
    ) -> BootEvent:
        """Log successful iSCSI connection"""
        return await self.log_event(
            event_type=BootEventType.ISCSI_CONNECT,
            status=BootEventStatus.SUCCESS,
            message=f"iSCSI connection established for {machine.name}",
            machine_id=machine.id,
            session_id=session.id if session else None,
            client_ip=client_ip,
            mac_address=machine.mac_address,
            details={
                "machine_name": machine.name,
                "target_iqn": target_iqn
            }
        )
    
    async def log_boot_success(
        self,
        machine: Machine,
        session: Optional[Session] = None,
        boot_time_seconds: Optional[float] = None,
        client_ip: Optional[str] = None
    ) -> BootEvent:
        """Log successful boot"""
        details = {"machine_name": machine.name}
        if boot_time_seconds:
            details["boot_time_seconds"] = boot_time_seconds
        
        return await self.log_event(
            event_type=BootEventType.BOOT_SUCCESS,
            status=BootEventStatus.SUCCESS,
            message=f"Boot completed successfully for {machine.name}",
            machine_id=machine.id,
            session_id=session.id if session else None,
            client_ip=client_ip,
            mac_address=machine.mac_address,
            details=details
        )
    
    async def log_boot_failed(
        self,
        machine: Machine,
        session: Optional[Session] = None,
        error_message: Optional[str] = None,
        client_ip: Optional[str] = None
    ) -> BootEvent:
        """Log failed boot"""
        details = {"machine_name": machine.name}
        if error_message:
            details["error"] = error_message
        
        return await self.log_event(
            event_type=BootEventType.BOOT_FAILED,
            status=BootEventStatus.FAILED,
            message=f"Boot failed for {machine.name}: {error_message or 'Unknown error'}",
            machine_id=machine.id,
            session_id=session.id if session else None,
            client_ip=client_ip,
            mac_address=machine.mac_address,
            details=details
        )
    
    async def log_boot_timeout(
        self,
        machine: Machine,
        session: Optional[Session] = None,
        timeout_seconds: Optional[int] = None,
        client_ip: Optional[str] = None
    ) -> BootEvent:
        """Log boot timeout"""
        details = {"machine_name": machine.name}
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        
        return await self.log_event(
            event_type=BootEventType.BOOT_TIMEOUT,
            status=BootEventStatus.TIMEOUT,
            message=f"Boot timeout for {machine.name}",
            machine_id=machine.id,
            session_id=session.id if session else None,
            client_ip=client_ip,
            mac_address=machine.mac_address,
            details=details
        )
    
    async def log_pxe_end(
        self,
        machine: Machine,
        session: Optional[Session] = None,
        client_ip: Optional[str] = None
    ) -> BootEvent:
        """Log PXE boot end"""
        return await self.log_event(
            event_type=BootEventType.PXE_END,
            status=BootEventStatus.SUCCESS,
            message=f"PXE boot completed for {machine.name}",
            machine_id=machine.id,
            session_id=session.id if session else None,
            client_ip=client_ip,
            mac_address=machine.mac_address,
            details={"machine_name": machine.name}
        )

