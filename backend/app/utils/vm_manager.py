"""
VM management module - QEMU/KVM virtual machine management via libvirt
Async version adapted for current project
"""

import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

try:
    import libvirt
    LIBVIRT_AVAILABLE = True
except ImportError:
    LIBVIRT_AVAILABLE = False
    libvirt = None

from app.models.vm import VM, VMStatus
from app.models.image import Image
from app.utils.zfs_enhanced import ZFSUtils
from app.core.config import get_settings

logger = structlog.get_logger()


class VMError(Exception):
    """VM management error"""
    pass


class VMManager:
    """
    VM manager for QEMU/KVM virtual machine management
    Async version
    """
    
    def __init__(self):
        """Initialize VM manager"""
        if not LIBVIRT_AVAILABLE:
            logger.warning("libvirt is not available. VM management will be limited.")
            self.conn = None
        else:
            try:
                self.conn = libvirt.open('qemu:///system')
                if self.conn is None:
                    logger.warning("Failed to connect to libvirt daemon")
                    self.conn = None
            except Exception as e:
                logger.warning(f"Failed to connect to libvirt: {e}")
                self.conn = None
        
        self.settings = get_settings()
        self.zfs_utils = ZFSUtils()
        self.bridge_name = getattr(self.settings, 'BRIDGE_NAME', 'virbr0')
        self.vnc_proxy_port = getattr(self.settings, 'VNC_PROXY_PORT', 6080)
        self.vnc_token_dir = Path(getattr(self.settings, 'VNC_TOKEN_DIR', '/var/lib/ggnet/vnc_tokens'))
        self.vnc_token_dir.mkdir(parents=True, exist_ok=True)
    
    def _is_libvirt_available(self) -> bool:
        """Check if libvirt is available"""
        return LIBVIRT_AVAILABLE and self.conn is not None
    
    def _generate_domain_xml(
        self,
        name: str,
        vm_uuid: str,
        vcpus: int,
        ram_mb: int,
        disk_path: Optional[str] = None,
        drives_connection: str = "local",
        iscsi_target: Optional[str] = None,
        vnc_port: Optional[int] = None,
    ) -> str:
        """
        Generate libvirt domain XML
        
        Args:
            name: VM name
            vm_uuid: VM UUID
            vcpus: Number of vCPUs
            ram_mb: RAM in MB
            disk_path: Disk image path (ZFS volume) - for local drives
            drives_connection: "local" or "network"
            iscsi_target: iSCSI target IQN - for network drives
            vnc_port: Optional VNC port
            
        Returns:
            Domain XML string
        """
        # Create root element
        domain = ET.Element("domain", type="kvm")
        
        # Name and UUID
        ET.SubElement(domain, "name").text = name
        ET.SubElement(domain, "uuid").text = vm_uuid
        
        # Memory and CPU
        ET.SubElement(domain, "memory", unit="MiB").text = str(ram_mb)
        ET.SubElement(domain, "currentMemory", unit="MiB").text = str(ram_mb)
        ET.SubElement(domain, "vcpu").text = str(vcpus)
        
        # OS configuration
        os_elem = ET.SubElement(domain, "os")
        ET.SubElement(os_elem, "type", arch="x86_64", machine="pc-q35-7.2").text = "hvm"
        # Boot device depends on drives_connection
        if drives_connection == "network":
            ET.SubElement(os_elem, "boot", dev="network")
            ET.SubElement(os_elem, "boot", dev="hd")
        else:
            ET.SubElement(os_elem, "boot", dev="hd")
        
        # Features
        features = ET.SubElement(domain, "features")
        ET.SubElement(features, "acpi")
        ET.SubElement(features, "apic")
        
        # CPU configuration
        cpu = ET.SubElement(domain, "cpu", mode="host-passthrough", check="none")
        
        # Clock
        clock = ET.SubElement(domain, "clock", offset="utc")
        ET.SubElement(clock, "timer", name="rtc", tickpolicy="catchup")
        ET.SubElement(clock, "timer", name="pit", tickpolicy="delay")
        ET.SubElement(clock, "timer", name="hpet", present="no")
        
        # Devices
        devices = ET.SubElement(domain, "devices")
        
        # Disk - Local or Network
        if drives_connection == "network" and iscsi_target:
            # Network boot disk (iSCSI)
            # TODO: Get server IP for iSCSI connection
            server_ip = "127.0.0.1"  # Placeholder
            
            disk = ET.SubElement(devices, "disk", type="network", device="disk")
            ET.SubElement(disk, "driver", name="qemu", type="raw", cache="none", io="native")
            source = ET.SubElement(disk, "source", protocol="iscsi")
            ET.SubElement(source, "host", name=server_ip, port="3260")
            ET.SubElement(source, "target", iqn=iscsi_target)
            ET.SubElement(disk, "target", dev="vda", bus="virtio")
            ET.SubElement(disk, "boot", order="1")
        else:
            # Local disk (ZFS volume or file)
            if not disk_path:
                raise VMError("Local disk path is required for local drives connection")
            disk = ET.SubElement(devices, "disk", type="block", device="disk")
            ET.SubElement(disk, "driver", name="qemu", type="raw", cache="none", io="native")
            ET.SubElement(disk, "source", dev=disk_path)
            ET.SubElement(disk, "target", dev="vda", bus="virtio")
        
        # Network interface (bridge)
        interface = ET.SubElement(devices, "interface", type="bridge")
        ET.SubElement(interface, "source", bridge=self.bridge_name)
        ET.SubElement(interface, "model", type="virtio")
        
        # Graphics (VNC)
        graphics = ET.SubElement(devices, "graphics", type="vnc", port=str(vnc_port) if vnc_port else "-1", listen="127.0.0.1", autoport="yes")
        
        # Video
        video = ET.SubElement(devices, "video")
        ET.SubElement(video, "model", type="qxl", ram="65536", vram="65536", heads="1", primary="yes")
        
        # Input devices
        ET.SubElement(devices, "input", type="tablet", bus="usb")
        ET.SubElement(devices, "input", type="keyboard", bus="usb")
        
        # Serial console
        ET.SubElement(devices, "serial", type="pty")
        ET.SubElement(devices, "console", type="pty")
        
        # Convert to string
        return ET.tostring(domain, encoding="unicode")
    
    async def create_vm(
        self,
        db: AsyncSession,
        name: str,
        image_id: int,
        vcpus: int = 2,
        ram_mb: int = 4096,
        drives_connection: str = "local",
        mac_address: Optional[str] = None,
        boot_mode: str = "uefi",
        created_by: int = 1,
    ) -> VM:
        """
        Create new virtual machine
        
        Args:
            db: Async database session
            name: VM name
            image_id: Image ID to use
            vcpus: Number of vCPUs
            ram_mb: RAM in MB
            drives_connection: "local" or "network"
            mac_address: MAC address (required for network boot)
            boot_mode: Boot mode ("uefi" or "legacy")
            created_by: User ID who created the VM
            
        Returns:
            Created VM model
            
        Raises:
            VMError: If VM creation fails
        """
        # Get image
        stmt = select(Image).where(Image.id == image_id)
        result = await db.execute(stmt)
        image = result.scalar_one_or_none()
        
        if not image:
            raise VMError(f"Image with ID {image_id} not found")
        
        # Check if VM already exists
        stmt = select(VM).where(VM.name == name)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise VMError(f"VM with name '{name}' already exists")
        
        try:
            # Generate VM UUID
            vm_uuid = str(uuid.uuid4())
            
            # For now, use image file path directly (simplified)
            # In production, you'd clone the image using ZFS
            disk_path = image.file_path
            
            # Handle network boot if requested
            iscsi_target = None
            if drives_connection == "network":
                if not mac_address:
                    raise VMError("MAC address is required for network boot")
                # TODO: Create iSCSI target
                # For now, just set a placeholder
                mac_clean = mac_address.replace(":", "-")
                iscsi_target = f"iqn.ggnet.vm.{mac_clean}"
            
            # Generate domain XML
            domain_xml = self._generate_domain_xml(
                name=name,
                vm_uuid=vm_uuid,
                vcpus=vcpus,
                ram_mb=ram_mb,
                disk_path=disk_path,
                drives_connection=drives_connection,
                iscsi_target=iscsi_target,
            )
            
            # Create domain in libvirt if available
            if self._is_libvirt_available():
                try:
                    domain = self.conn.defineXML(domain_xml)
                    if domain is None:
                        raise VMError("Failed to define VM domain in libvirt")
                except Exception as e:
                    logger.warning(f"Failed to create libvirt domain: {e}")
                    # Continue without libvirt if it fails
            
            # Create VM record
            vm = VM(
                name=name,
                vm_id=vm_uuid,
                image_id=image_id,
                vcpus=vcpus,
                ram_mb=ram_mb,
                disk_path=disk_path,
                drives_connection=drives_connection,
                iscsi_target=iscsi_target,
                mac_address=mac_address,
                boot_mode=boot_mode,
                status=VMStatus.STOPPED,
                created_by=created_by,
            )
            
            db.add(vm)
            await db.commit()
            await db.refresh(vm)
            
            logger.info("Created VM", vm_id=vm.id, name=name, vm_uuid=vm_uuid)
            return vm
            
        except Exception as e:
            await db.rollback()
            raise VMError(f"Failed to create VM: {e}") from e
    
    async def start_vm(self, db: AsyncSession, vm_id: int) -> VM:
        """Start virtual machine"""
        stmt = select(VM).where(VM.id == vm_id)
        result = await db.execute(stmt)
        vm = result.scalar_one_or_none()
        
        if not vm:
            raise VMError(f"VM with ID {vm_id} not found")
        
        if not self._is_libvirt_available():
            # Update status only
            vm.status = VMStatus.RUNNING
            await db.commit()
            await db.refresh(vm)
            return vm
        
        try:
            domain = self.conn.lookupByUUIDString(vm.vm_id)
            if domain.create() < 0:
                raise VMError(f"Failed to start VM {vm.name}")
            
            # Setup VNC token
            await self._setup_vnc_token(db, vm, domain)
            
            vm.status = VMStatus.RUNNING
            await db.commit()
            await db.refresh(vm)
            
            logger.info("Started VM", vm_id=vm.id, name=vm.name)
            return vm
        except libvirt.libvirtError as e:
            raise VMError(f"Failed to start VM: {e}") from e
        except Exception as e:
            await db.rollback()
            raise VMError(f"Failed to start VM: {e}") from e
    
    async def stop_vm(self, db: AsyncSession, vm_id: int, force: bool = False) -> VM:
        """Stop virtual machine"""
        stmt = select(VM).where(VM.id == vm_id)
        result = await db.execute(stmt)
        vm = result.scalar_one_or_none()
        
        if not vm:
            raise VMError(f"VM with ID {vm_id} not found")
        
        if not self._is_libvirt_available():
            vm.status = VMStatus.STOPPED
            await db.commit()
            await db.refresh(vm)
            return vm
        
        try:
            domain = self.conn.lookupByUUIDString(vm.vm_id)
            if force:
                if domain.destroy() < 0:
                    raise VMError(f"Failed to force stop VM {vm.name}")
            else:
                if domain.shutdown() < 0:
                    raise VMError(f"Failed to stop VM {vm.name}")
            
            await self._cleanup_vnc_token(vm)
            
            vm.status = VMStatus.STOPPED
            await db.commit()
            await db.refresh(vm)
            
            logger.info("Stopped VM", vm_id=vm.id, name=vm.name)
            return vm
        except libvirt.libvirtError as e:
            raise VMError(f"Failed to stop VM: {e}") from e
        except Exception as e:
            await db.rollback()
            raise VMError(f"Failed to stop VM: {e}") from e
    
    async def delete_vm(self, db: AsyncSession, vm_id: int, force: bool = False) -> None:
        """Delete virtual machine"""
        stmt = select(VM).where(VM.id == vm_id)
        result = await db.execute(stmt)
        vm = result.scalar_one_or_none()
        
        if not vm:
            raise VMError(f"VM with ID {vm_id} not found")
        
        if not force and vm.status == VMStatus.RUNNING:
            raise VMError(f"VM {vm.name} is running. Use force=True to delete anyway.")
        
        try:
            # Undefine domain in libvirt if available
            if self._is_libvirt_available():
                try:
                    domain = self.conn.lookupByUUIDString(vm.vm_id)
                    if domain.undefine() < 0:
                        raise VMError(f"Failed to undefine VM {vm.name}")
                except libvirt.libvirtError:
                    logger.warning(f"VM domain {vm.vm_id} not found in libvirt, continuing")
            
            # Cleanup VNC token
            await self._cleanup_vnc_token(vm)
            
            # Delete VM record
            await db.delete(vm)
            await db.commit()
            
            logger.info("Deleted VM", vm_id=vm_id, name=vm.name)
        except Exception as e:
            await db.rollback()
            raise VMError(f"Failed to delete VM: {e}") from e
    
    async def get_vm_info(self, db: AsyncSession, vm_id: int) -> Dict[str, Any]:
        """Get VM information including libvirt stats"""
        stmt = select(VM).where(VM.id == vm_id)
        result = await db.execute(stmt)
        vm = result.scalar_one_or_none()
        
        if not vm:
            raise VMError(f"VM with ID {vm_id} not found")
        
        info = {
            "id": vm.id,
            "name": vm.name,
            "vm_id": vm.vm_id,
            "vcpus": vm.vcpus,
            "ram_mb": vm.ram_mb,
            "status": vm.status.value,
            "disk_path": vm.disk_path,
            "zfs_clone": vm.zfs_clone,
            "vnc_port": vm.vnc_port,
            "vnc_token": vm.vnc_token,
            "created_at": vm.created_at.isoformat() if vm.created_at else None,
            "updated_at": vm.updated_at.isoformat() if vm.updated_at else None,
        }
        
        # Add image info
        if vm.image_id:
            stmt = select(Image).where(Image.id == vm.image_id)
            result = await db.execute(stmt)
            image = result.scalar_one_or_none()
            if image:
                info["image"] = {
                    "id": image.id,
                    "name": image.name,
                    "image_type": image.image_type.value,
                }
        
        # Get libvirt domain info if running and available
        if vm.status == VMStatus.RUNNING and self._is_libvirt_available():
            try:
                domain = self.conn.lookupByUUIDString(vm.vm_id)
                if domain:
                    domain_info = domain.info()
                    info["libvirt_info"] = {
                        "state": domain_info[0],
                        "max_memory": domain_info[1],
                        "memory": domain_info[2],
                        "vcpus": domain_info[3],
                        "cpu_time": domain_info[4],
                    }
            except Exception as e:
                logger.warning(f"Failed to get libvirt info: {e}")
        
        return info
    
    async def _setup_vnc_token(self, db: AsyncSession, vm: VM, domain) -> None:
        """Setup VNC token for VM"""
        # Generate token
        import secrets
        token = secrets.token_urlsafe(32)
        
        # Get VNC port from domain
        try:
            vnc_port = domain.vncDisplay()
            if vnc_port:
                vm.vnc_port = int(vnc_port)
        except Exception:
            pass
        
        vm.vnc_token = token
        await db.commit()
        
        # Save token to file
        token_file = self.vnc_token_dir / f"{vm.vm_id}.token"
        token_file.write_text(token)
    
    async def _cleanup_vnc_token(self, vm: VM) -> None:
        """Cleanup VNC token"""
        if vm.vnc_token:
            token_file = self.vnc_token_dir / f"{vm.vm_id}.token"
            if token_file.exists():
                token_file.unlink()
        
        vm.vnc_port = None
        vm.vnc_token = None




