# Array Operations - Drive Management - Detaljni Plan Implementacije

**Prioritet:** 🔴 P0 - Kritično za MVP  
**Vreme:** 2 nedelje  
**Status:** 📋 Plan

---

## 📋 Pregled

Implementacija drive management sistema za ZFS array sa:
- Drive detection i listing
- Drive online/offline management
- Drive add/remove/replace operations
- Array extend operations
- Array export/delete operations
- SMART data monitoring

---

## 🎯 Funkcionalni Zahtevi

### 1. Drive Detection & Listing

**Zahtevi:**
- List all drives
- List free drives
- Get drive SMART data
- Get drive information

**Endpoint-i:**
- `GET /api/drives` - List all drives
- `GET /api/drives/free` - List free drives
- `GET /api/drives/{driveName}/smart` - Get SMART data

### 2. Array Drive Management

**Zahtevi:**
- Add drives to array
- Remove drives from array
- Replace drive
- Drive online/offline

**Endpoint-i:**
- `POST /api/array/drives` - Add drives
- `DELETE /api/array/drives/{driveUuid}` - Remove drive
- `POST /api/array/drives/{oldDriveUuid}/replace` - Replace drive
- `POST /api/array/drives/{driveUuid}/online` - Drive online
- `POST /api/array/drives/{driveUuid}/offline` - Drive offline

### 3. Array Operations

**Zahtevi:**
- Create array
- Extend array
- Export array
- Delete array
- Lookup stripes

**Endpoint-i:**
- `POST /api/array` - Create array
- `POST /api/array/extend` - Extend array
- `POST /api/array/export` - Export array
- `DELETE /api/array` - Delete array
- `GET /api/array/stripes/lookup` - Lookup stripes

---

## 🗄️ Database Schema

### Drives Table

```sql
CREATE TABLE drives (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(255) UNIQUE NOT NULL,  -- Drive UUID (from udev or ZFS)
    name VARCHAR(255) NOT NULL,  -- Drive name (e.g., "sda", "nvme0n1")
    path VARCHAR(255) NOT NULL,  -- Device path (e.g., "/dev/sda")
    model VARCHAR(255),  -- Drive model
    serial_number VARCHAR(255),  -- Serial number
    size_bytes BIGINT NOT NULL,  -- Drive size in bytes
    type VARCHAR(50),  -- 'hdd', 'ssd', 'nvme'
    status VARCHAR(50) DEFAULT 'free',  -- 'free', 'online', 'offline', 'failed', 'spare'
    pool_id INTEGER,  -- Associated pool (if in array)
    pool_name VARCHAR(255),  -- Pool name (if in array)
    slot_number INTEGER,  -- Physical slot number
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_drives_uuid ON drives(uuid);
CREATE INDEX idx_drives_name ON drives(name);
CREATE INDEX idx_drives_status ON drives(status);
CREATE INDEX idx_drives_pool_name ON drives(pool_name);
```

### Drive SMART Data Table (Opciono - za history)

```sql
CREATE TABLE drive_smart_data (
    id SERIAL PRIMARY KEY,
    drive_id INTEGER NOT NULL REFERENCES drives(id) ON DELETE CASCADE,
    smart_data JSON NOT NULL,  -- Full SMART data
    health_status VARCHAR(50),  -- 'passed', 'failed', 'warning'
    temperature INTEGER,  -- Temperature in Celsius
    power_on_hours INTEGER,
    read_errors INTEGER,
    write_errors INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_drive_smart_data_drive_id ON drive_smart_data(drive_id);
CREATE INDEX idx_drive_smart_data_created_at ON drive_smart_data(created_at);
```

---

## 📁 Struktura Fajlova

```
app/backend/
├── storage/
│   ├── drive_manager.py         # Drive detection i management (novi)
│   ├── array_manager.py         # Array operations (novi)
│   └── zfs_utils.py             # Već postoji - proširiti
└── api/
    ├── drives.py                # Drive API endpoints (novi)
    └── array.py                 # Array API endpoints (novi, ili proširiti storage.py)
```

---

## 🔧 Implementacija

### 1. Drive Manager (`app/backend/storage/drive_manager.py`)

```python
"""
Drive Manager for physical drive detection and management
"""

import subprocess
import logging
import json
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.backend.config.models import Drive, DriveSMARTData
from app.backend.utils.exceptions import StorageError, NotFoundError

logger = logging.getLogger(__name__)


class DriveManager:
    """Drive manager for physical drive operations"""
    
    def __init__(self):
        """Initialize drive manager"""
        self.smartctl_cmd = "smartctl"
        self.lsblk_cmd = "lsblk"
        self.udev_cmd = "udevadm"
    
    def detect_drives(self) -> List[Dict[str, Any]]:
        """
        Detect all physical drives in the system
        
        Returns:
            List of drive dictionaries
        """
        drives = []
        
        try:
            # Use lsblk to list block devices
            result = subprocess.run(
                [self.lsblk_cmd, "-J", "-o", "NAME,SIZE,TYPE,MODEL,SERIAL"],
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            
            for device in data.get("blockdevices", []):
                # Only include disk devices (not partitions)
                if device.get("type") == "disk":
                    # Get device path
                    device_path = f"/dev/{device['name']}"
                    
                    # Get UUID from udev
                    uuid = self._get_device_uuid(device['name'])
                    
                    # Determine drive type
                    drive_type = self._determine_drive_type(device_path)
                    
                    drives.append({
                        "name": device['name'],
                        "path": device_path,
                        "uuid": uuid,
                        "size_bytes": self._parse_size(device.get('size', '0')),
                        "model": device.get('model', 'Unknown'),
                        "serial_number": device.get('serial', 'Unknown'),
                        "type": drive_type,
                        "status": "free"
                    })
            
            return drives
        
        except Exception as e:
            logger.error(f"Failed to detect drives: {e}")
            raise StorageError(f"Failed to detect drives: {e}")
    
    def _get_device_uuid(self, device_name: str) -> str:
        """
        Get device UUID from udev
        
        Args:
            device_name: Device name (e.g., "sda")
            
        Returns:
            Device UUID
        """
        try:
            result = subprocess.run(
                [self.udev_cmd, "info", "-q", "property", "-n", device_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse UUID from udev output
            for line in result.stdout.split('\n'):
                if line.startswith('ID_SERIAL_SHORT='):
                    return line.split('=', 1)[1]
                elif line.startswith('ID_WWN='):
                    return line.split('=', 1)[1]
            
            # Fallback to device name
            return device_name
        
        except Exception:
            return device_name
    
    def _determine_drive_type(self, device_path: str) -> str:
        """
        Determine drive type (hdd, ssd, nvme)
        
        Args:
            device_path: Device path
            
        Returns:
            Drive type
        """
        # Check if NVMe
        if '/nvme' in device_path:
            return 'nvme'
        
        # Check if SSD using /sys/block
        try:
            device_name = device_path.split('/')[-1]
            with open(f'/sys/block/{device_name}/queue/rotational', 'r') as f:
                rotational = f.read().strip()
                if rotational == '0':
                    return 'ssd'
                else:
                    return 'hdd'
        except Exception:
            return 'hdd'
    
    def _parse_size(self, size_str: str) -> int:
        """
        Parse size string to bytes
        
        Args:
            size_str: Size string (e.g., "500G", "1T")
            
        Returns:
            Size in bytes
        """
        if not size_str:
            return 0
        
        # Remove spaces and convert to uppercase
        size_str = size_str.strip().upper()
        
        # Extract number and unit
        match = re.match(r'^(\d+(?:\.\d+)?)([KMGT]?)$', size_str)
        if not match:
            return 0
        
        number = float(match.group(1))
        unit = match.group(2) or 'B'
        
        multipliers = {
            'B': 1,
            'K': 1024,
            'M': 1024**2,
            'G': 1024**3,
            'T': 1024**4
        }
        
        return int(number * multipliers.get(unit, 1))
    
    def get_smart_data(self, drive_name: str) -> Dict[str, Any]:
        """
        Get SMART data for drive
        
        Args:
            drive_name: Drive name (e.g., "sda")
            
        Returns:
            SMART data dictionary
        """
        device_path = f"/dev/{drive_name}"
        
        try:
            # Get SMART health status
            result = subprocess.run(
                [self.smartctl_cmd, "-H", device_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            health_status = "unknown"
            if "PASSED" in result.stdout:
                health_status = "passed"
            elif "FAILED" in result.stdout:
                health_status = "failed"
            elif "WARNING" in result.stdout:
                health_status = "warning"
            
            # Get detailed SMART data
            result = subprocess.run(
                [self.smartctl_cmd, "-A", "-j", device_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            smart_data = {}
            if result.returncode == 0:
                smart_data = json.loads(result.stdout)
            
            # Extract key metrics
            temperature = None
            power_on_hours = None
            
            if "temperature" in smart_data:
                temperature = smart_data["temperature"]["current"]
            elif "ata_smart_attributes" in smart_data:
                for attr in smart_data["ata_smart_attributes"]["table"]:
                    if attr["name"] == "Temperature_Celsius":
                        temperature = attr["value"]
                    elif attr["name"] == "Power_On_Hours":
                        power_on_hours = attr["raw"]["value"]
            
            return {
                "drive_name": drive_name,
                "device_path": device_path,
                "health_status": health_status,
                "temperature": temperature,
                "power_on_hours": power_on_hours,
                "smart_data": smart_data
            }
        
        except Exception as e:
            logger.error(f"Failed to get SMART data for {drive_name}: {e}")
            raise StorageError(f"Failed to get SMART data: {e}")
    
    def get_free_drives(self, db: Session) -> List[Dict[str, Any]]:
        """
        Get free drives (not in any pool)
        
        Args:
            db: Database session
            
        Returns:
            List of free drives
        """
        # Detect all drives
        all_drives = self.detect_drives()
        
        # Get drives in pools
        drives_in_pools = db.query(Drive).filter(Drive.pool_name.isnot(None)).all()
        pool_drive_paths = {d.path for d in drives_in_pools}
        
        # Filter free drives
        free_drives = [
            d for d in all_drives
            if d['path'] not in pool_drive_paths
        ]
        
        return free_drives
    
    def sync_drives_to_db(self, db: Session) -> int:
        """
        Sync detected drives to database
        
        Args:
            db: Database session
            
        Returns:
            Number of drives synced
        """
        detected_drives = self.detect_drives()
        synced = 0
        
        for drive_info in detected_drives:
            # Check if drive exists
            drive = db.query(Drive).filter(Drive.uuid == drive_info['uuid']).first()
            
            if not drive:
                # Create new drive
                drive = Drive(
                    uuid=drive_info['uuid'],
                    name=drive_info['name'],
                    path=drive_info['path'],
                    model=drive_info['model'],
                    serial_number=drive_info['serial_number'],
                    size_bytes=drive_info['size_bytes'],
                    type=drive_info['type'],
                    status='free'
                )
                db.add(drive)
                synced += 1
            else:
                # Update existing drive
                drive.name = drive_info['name']
                drive.path = drive_info['path']
                drive.model = drive_info['model']
                drive.serial_number = drive_info['serial_number']
                drive.size_bytes = drive_info['size_bytes']
                drive.type = drive_info['type']
        
        db.commit()
        return synced
```

### 2. Array Manager (`app/backend/storage/array_manager.py`)

```python
"""
Array Manager for ZFS pool/array operations
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.backend.storage.zfs_utils import ZFSUtils
from app.backend.storage.drive_manager import DriveManager
from app.backend.config.models import Drive
from app.backend.utils.exceptions import StorageError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class ArrayManager:
    """Array manager for ZFS pool operations"""
    
    def __init__(self):
        """Initialize array manager"""
        self.zfs_utils = ZFSUtils()
        self.drive_manager = DriveManager()
    
    def create_array(
        self,
        db: Session,
        pool_name: str,
        drive_uuids: List[str],
        topology: str = "stripe",  # 'stripe', 'mirror', 'raidz', 'raidz2', 'raidz3'
        properties: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create new ZFS array (pool)
        
        Args:
            db: Database session
            pool_name: Pool name
            drive_uuids: List of drive UUIDs to use
            topology: Array topology
            properties: Optional pool properties
            
        Returns:
            Pool creation result
        """
        # Get drives from database
        drives = db.query(Drive).filter(Drive.uuid.in_(drive_uuids)).all()
        if len(drives) != len(drive_uuids):
            found_uuids = {d.uuid for d in drives}
            missing_uuids = set(drive_uuids) - found_uuids
            raise NotFoundError(f"Drives not found: {missing_uuids}")
        
        # Verify drives are free
        for drive in drives:
            if drive.pool_name:
                raise ValidationError(f"Drive {drive.name} is already in pool {drive.pool_name}")
        
        # Get device paths
        device_paths = [drive.path for drive in drives]
        
        # Create pool
        try:
            self.zfs_utils.pool_create(pool_name, device_paths, topology, properties)
            
            # Update drives in database
            for drive in drives:
                drive.pool_name = pool_name
                drive.status = 'online'
                db.commit()
            
            return {
                "pool_name": pool_name,
                "topology": topology,
                "drives": len(drives),
                "status": "created"
            }
        
        except Exception as e:
            logger.error(f"Failed to create array {pool_name}: {e}")
            raise StorageError(f"Failed to create array: {e}")
    
    def extend_array(
        self,
        db: Session,
        pool_name: str,
        drive_uuids: List[str],
        topology: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extend array with new drives
        
        Args:
            db: Database session
            pool_name: Pool name
            drive_uuids: List of drive UUIDs to add
            topology: Optional topology for new vdev
            
        Returns:
            Extension result
        """
        # Get drives
        drives = db.query(Drive).filter(Drive.uuid.in_(drive_uuids)).all()
        if len(drives) != len(drive_uuids):
            raise NotFoundError("Some drives not found")
        
        # Verify drives are free
        for drive in drives:
            if drive.pool_name:
                raise ValidationError(f"Drive {drive.name} is already in pool")
        
        # Get device paths
        device_paths = [drive.path for drive in drives]
        
        # Extend pool
        try:
            self.zfs_utils.pool_add(pool_name, device_paths, topology)
            
            # Update drives
            for drive in drives:
                drive.pool_name = pool_name
                drive.status = 'online'
                db.commit()
            
            return {
                "pool_name": pool_name,
                "drives_added": len(drives),
                "status": "extended"
            }
        
        except Exception as e:
            logger.error(f"Failed to extend array {pool_name}: {e}")
            raise StorageError(f"Failed to extend array: {e}")
    
    def add_drives(
        self,
        db: Session,
        pool_name: str,
        drive_uuids: List[str],
        topology: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add drives to array (alias for extend_array)
        
        Args:
            db: Database session
            pool_name: Pool name
            drive_uuids: List of drive UUIDs
            topology: Optional topology
            
        Returns:
            Addition result
        """
        return self.extend_array(db, pool_name, drive_uuids, topology)
    
    def remove_drive(
        self,
        db: Session,
        drive_uuid: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Remove drive from array
        
        Args:
            db: Database session
            drive_uuid: Drive UUID
            force: Force removal
            
        Returns:
            Removal result
        """
        drive = db.query(Drive).filter(Drive.uuid == drive_uuid).first()
        if not drive:
            raise NotFoundError(f"Drive {drive_uuid} not found")
        
        if not drive.pool_name:
            raise ValidationError(f"Drive {drive.name} is not in any pool")
        
        pool_name = drive.pool_name
        
        # Remove drive from pool
        try:
            self.zfs_utils.pool_remove(pool_name, drive.path, force)
            
            # Update drive
            drive.pool_name = None
            drive.status = 'free'
            db.commit()
            
            return {
                "drive_uuid": drive_uuid,
                "pool_name": pool_name,
                "status": "removed"
            }
        
        except Exception as e:
            logger.error(f"Failed to remove drive {drive_uuid}: {e}")
            raise StorageError(f"Failed to remove drive: {e}")
    
    def replace_drive(
        self,
        db: Session,
        old_drive_uuid: str,
        new_drive_uuid: str
    ) -> Dict[str, Any]:
        """
        Replace drive in array
        
        Args:
            db: Database session
            old_drive_uuid: Old drive UUID
            new_drive_uuid: New drive UUID
            
        Returns:
            Replacement result
        """
        old_drive = db.query(Drive).filter(Drive.uuid == old_drive_uuid).first()
        new_drive = db.query(Drive).filter(Drive.uuid == new_drive_uuid).first()
        
        if not old_drive:
            raise NotFoundError(f"Old drive {old_drive_uuid} not found")
        if not new_drive:
            raise NotFoundError(f"New drive {new_drive_uuid} not found")
        
        if not old_drive.pool_name:
            raise ValidationError(f"Old drive {old_drive.name} is not in any pool")
        if new_drive.pool_name:
            raise ValidationError(f"New drive {new_drive.name} is already in pool {new_drive.pool_name}")
        
        pool_name = old_drive.pool_name
        
        # Replace drive
        try:
            self.zfs_utils.pool_replace(pool_name, old_drive.path, new_drive.path)
            
            # Update drives
            old_drive.pool_name = None
            old_drive.status = 'free'
            new_drive.pool_name = pool_name
            new_drive.status = 'online'
            db.commit()
            
            return {
                "pool_name": pool_name,
                "old_drive_uuid": old_drive_uuid,
                "new_drive_uuid": new_drive_uuid,
                "status": "replaced"
            }
        
        except Exception as e:
            logger.error(f"Failed to replace drive: {e}")
            raise StorageError(f"Failed to replace drive: {e}")
    
    def drive_online(
        self,
        db: Session,
        drive_uuid: str
    ) -> Dict[str, Any]:
        """
        Bring drive online
        
        Args:
            db: Database session
            drive_uuid: Drive UUID
            
        Returns:
            Online result
        """
        drive = db.query(Drive).filter(Drive.uuid == drive_uuid).first()
        if not drive:
            raise NotFoundError(f"Drive {drive_uuid} not found")
        
        if not drive.pool_name:
            raise ValidationError(f"Drive {drive.name} is not in any pool")
        
        try:
            self.zfs_utils.pool_online(drive.pool_name, drive.path)
            
            drive.status = 'online'
            db.commit()
            
            return {
                "drive_uuid": drive_uuid,
                "status": "online"
            }
        
        except Exception as e:
            logger.error(f"Failed to bring drive online: {e}")
            raise StorageError(f"Failed to bring drive online: {e}")
    
    def drive_offline(
        self,
        db: Session,
        drive_uuid: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Take drive offline
        
        Args:
            db: Database session
            drive_uuid: Drive UUID
            force: Force offline
            
        Returns:
            Offline result
        """
        drive = db.query(Drive).filter(Drive.uuid == drive_uuid).first()
        if not drive:
            raise NotFoundError(f"Drive {drive_uuid} not found")
        
        if not drive.pool_name:
            raise ValidationError(f"Drive {drive.name} is not in any pool")
        
        try:
            self.zfs_utils.pool_offline(drive.pool_name, drive.path, force)
            
            drive.status = 'offline'
            db.commit()
            
            return {
                "drive_uuid": drive_uuid,
                "status": "offline"
            }
        
        except Exception as e:
            logger.error(f"Failed to take drive offline: {e}")
            raise StorageError(f"Failed to take drive offline: {e}")
    
    def export_array(
        self,
        db: Session,
        pool_name: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Export array (unmount pool)
        
        Args:
            db: Database session
            pool_name: Pool name
            force: Force export
            
        Returns:
            Export result
        """
        try:
            self.zfs_utils.pool_export(pool_name, force)
            
            # Update drives
            drives = db.query(Drive).filter(Drive.pool_name == pool_name).all()
            for drive in drives:
                drive.pool_name = None
                drive.status = 'free'
            db.commit()
            
            return {
                "pool_name": pool_name,
                "status": "exported"
            }
        
        except Exception as e:
            logger.error(f"Failed to export array {pool_name}: {e}")
            raise StorageError(f"Failed to export array: {e}")
    
    def delete_array(
        self,
        db: Session,
        pool_name: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Delete array (destroy pool)
        
        Args:
            db: Database session
            pool_name: Pool name
            force: Force delete
            
        Returns:
            Delete result
        """
        try:
            # First export pool
            self.zfs_utils.pool_export(pool_name, force)
            
            # Destroy pool
            self.zfs_utils.pool_destroy(pool_name)
            
            # Update drives
            drives = db.query(Drive).filter(Drive.pool_name == pool_name).all()
            for drive in drives:
                drive.pool_name = None
                drive.status = 'free'
            db.commit()
            
            return {
                "pool_name": pool_name,
                "status": "deleted"
            }
        
        except Exception as e:
            logger.error(f"Failed to delete array {pool_name}: {e}")
            raise StorageError(f"Failed to delete array: {e}")
    
    def lookup_stripes(
        self,
        pool_name: str
    ) -> List[Dict[str, Any]]:
        """
        Lookup stripes (vdevs) in pool
        
        Args:
            pool_name: Pool name
            
        Returns:
            List of stripe/vdev information
        """
        try:
            # Get pool status
            status = self.zfs_utils.pool_status(pool_name)
            
            # Parse vdev information from status
            # This depends on zpool status output format
            vdevs = []
            
            # Implementation would parse zpool status output
            # For now, return basic structure
            return vdevs
        
        except Exception as e:
            logger.error(f"Failed to lookup stripes for {pool_name}: {e}")
            raise StorageError(f"Failed to lookup stripes: {e}")
```

### 3. ZFSUtils Extensions (`app/backend/storage/zfs_utils.py`)

```python
# Dodati metode u postojeći ZFSUtils

def pool_add(
    self,
    pool_name: str,
    devices: List[str],
    topology: Optional[str] = None
) -> None:
    """
    Add devices to pool
    
    Args:
        pool_name: Pool name
        devices: List of device paths
        topology: Optional topology (mirror, raidz, etc.)
        
    Raises:
        ZFSError: If add fails
    """
    try:
        cmd = [self.zpool_cmd, "add", pool_name]
        
        if topology:
            if topology == "mirror":
                cmd.append("mirror")
            elif topology.startswith("raidz"):
                cmd.append(topology)
        
        cmd.extend(devices)
        
        self._run_command(cmd)
        logger.info(f"Added devices to pool {pool_name}")
    except Exception as e:
        raise ZFSError(f"Failed to add devices to pool: {e}")

def pool_remove(
    self,
    pool_name: str,
    device: str,
    force: bool = False
) -> None:
    """
    Remove device from pool
    
    Args:
        pool_name: Pool name
        device: Device path
        force: Force removal
        
    Raises:
        ZFSError: If removal fails
    """
    try:
        cmd = [self.zpool_cmd, "remove"]
        if force:
            cmd.append("-f")
        cmd.extend([pool_name, device])
        
        self._run_command(cmd)
        logger.info(f"Removed device {device} from pool {pool_name}")
    except Exception as e:
        raise ZFSError(f"Failed to remove device: {e}")

def pool_replace(
    self,
    pool_name: str,
    old_device: str,
    new_device: str
) -> None:
    """
    Replace device in pool
    
    Args:
        pool_name: Pool name
        old_device: Old device path
        new_device: New device path
        
    Raises:
        ZFSError: If replacement fails
    """
    try:
        self._run_command([
            self.zpool_cmd, "replace", pool_name, old_device, new_device
        ])
        logger.info(f"Replaced device {old_device} with {new_device} in pool {pool_name}")
    except Exception as e:
        raise ZFSError(f"Failed to replace device: {e}")

def pool_online(
    self,
    pool_name: str,
    device: str
) -> None:
    """
    Bring device online in pool
    
    Args:
        pool_name: Pool name
        device: Device path
        
    Raises:
        ZFSError: If online fails
    """
    try:
        self._run_command([self.zpool_cmd, "online", pool_name, device])
        logger.info(f"Brought device {device} online in pool {pool_name}")
    except Exception as e:
        raise ZFSError(f"Failed to bring device online: {e}")

def pool_offline(
    self,
    pool_name: str,
    device: str,
    force: bool = False
) -> None:
    """
    Take device offline in pool
    
    Args:
        pool_name: Pool name
        device: Device path
        force: Force offline
        
    Raises:
        ZFSError: If offline fails
    """
    try:
        cmd = [self.zpool_cmd, "offline"]
        if force:
            cmd.append("-f")
        cmd.extend([pool_name, device])
        
        self._run_command(cmd)
        logger.info(f"Took device {device} offline in pool {pool_name}")
    except Exception as e:
        raise ZFSError(f"Failed to take device offline: {e}")

def pool_destroy(
    self,
    pool_name: str,
    force: bool = False
) -> None:
    """
    Destroy pool
    
    Args:
        pool_name: Pool name
        force: Force destroy
        
    Raises:
        ZFSError: If destroy fails
    """
    try:
        cmd = [self.zpool_cmd, "destroy"]
        if force:
            cmd.append("-f")
        cmd.append(pool_name)
        
        self._run_command(cmd)
        logger.info(f"Destroyed pool {pool_name}")
    except Exception as e:
        raise ZFSError(f"Failed to destroy pool: {e}")
```

### 4. API Endpoints (`app/backend/api/drives.py`)

```python
"""
Drives API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.backend.config.database import get_db
from app.backend.storage.drive_manager import DriveManager
from app.backend.auth.dependencies import get_current_user
from app.backend.config.models import User

router = APIRouter()
drive_manager = DriveManager()


@router.get("/")
async def list_drives(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List all drives
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of drives
    """
    # Sync drives to database
    drive_manager.sync_drives_to_db(db)
    
    # Get drives from database
    drives = db.query(Drive).all()
    
    return [
        {
            "uuid": d.uuid,
            "name": d.name,
            "path": d.path,
            "model": d.model,
            "serial_number": d.serial_number,
            "size_bytes": d.size_bytes,
            "type": d.type,
            "status": d.status,
            "pool_name": d.pool_name
        }
        for d in drives
    ]


@router.get("/free")
async def list_free_drives(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List free drives (not in any pool)
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of free drives
    """
    return drive_manager.get_free_drives(db)


@router.get("/{drive_name}/smart")
async def get_smart_data(
    drive_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get SMART data for drive
    
    Args:
        drive_name: Drive name (e.g., "sda")
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        SMART data
    """
    try:
        return drive_manager.get_smart_data(drive_name)
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 5. API Endpoints (`app/backend/api/array.py`)

```python
"""
Array API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.backend.config.database import get_db
from app.backend.storage.array_manager import ArrayManager
from app.backend.auth.dependencies import get_current_user
from app.backend.config.models import User

router = APIRouter()
array_manager = ArrayManager()


class ArrayCreateRequest(BaseModel):
    """Array creation request"""
    pool_name: str
    drive_uuids: List[str]
    topology: str = "stripe"  # 'stripe', 'mirror', 'raidz', 'raidz2', 'raidz3'
    properties: Optional[Dict[str, str]] = None


class ArrayExtendRequest(BaseModel):
    """Array extend request"""
    pool_name: str
    drive_uuids: List[str]
    topology: Optional[str] = None


class ArrayAddDrivesRequest(BaseModel):
    """Array add drives request"""
    pool_name: str
    drive_uuids: List[str]
    topology: Optional[str] = None


class DriveReplaceRequest(BaseModel):
    """Drive replace request"""
    old_drive_uuid: str
    new_drive_uuid: str


@router.post("/")
async def create_array(
    request: ArrayCreateRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create new array (pool)
    
    Args:
        request: Array creation request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Array creation result
    """
    try:
        return array_manager.create_array(
            db=db,
            pool_name=request.pool_name,
            drive_uuids=request.drive_uuids,
            topology=request.topology,
            properties=request.properties
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extend")
async def extend_array(
    request: ArrayExtendRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Extend array with new drives
    
    Args:
        request: Array extend request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Extension result
    """
    try:
        return array_manager.extend_array(
            db=db,
            pool_name=request.pool_name,
            drive_uuids=request.drive_uuids,
            topology=request.topology
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drives")
async def add_drives(
    request: ArrayAddDrivesRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Add drives to array
    
    Args:
        request: Add drives request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Addition result
    """
    try:
        return array_manager.add_drives(
            db=db,
            pool_name=request.pool_name,
            drive_uuids=request.drive_uuids,
            topology=request.topology
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drives/{drive_uuid}/online")
async def drive_online(
    drive_uuid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Bring drive online
    
    Args:
        drive_uuid: Drive UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Online result
    """
    try:
        return array_manager.drive_online(db, drive_uuid)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drives/{drive_uuid}/offline")
async def drive_offline(
    drive_uuid: str,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Take drive offline
    
    Args:
        drive_uuid: Drive UUID
        force: Force offline
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Offline result
    """
    try:
        return array_manager.drive_offline(db, drive_uuid, force)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drives/{old_drive_uuid}/replace")
async def replace_drive(
    old_drive_uuid: str,
    request: DriveReplaceRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Replace drive in array
    
    Args:
        old_drive_uuid: Old drive UUID
        request: Drive replace request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Replacement result
    """
    try:
        return array_manager.replace_drive(
            db=db,
            old_drive_uuid=old_drive_uuid,
            new_drive_uuid=request.new_drive_uuid
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/drives/{drive_uuid}")
async def remove_drive(
    drive_uuid: str,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Remove drive from array
    
    Args:
        drive_uuid: Drive UUID
        force: Force removal
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Removal result
    """
    try:
        return array_manager.remove_drive(db, drive_uuid, force)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_array(
    pool_name: str,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Export array
    
    Args:
        pool_name: Pool name
        force: Force export
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Export result
    """
    try:
        return array_manager.export_array(db, pool_name, force)
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/")
async def delete_array(
    pool_name: str,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete array
    
    Args:
        pool_name: Pool name
        force: Force delete
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Delete result
    """
    try:
        return array_manager.delete_array(db, pool_name, force)
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stripes/lookup")
async def lookup_stripes(
    pool_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Lookup stripes (vdevs) in pool
    
    Args:
        pool_name: Pool name
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of stripe/vdev information
    """
    try:
        return array_manager.lookup_stripes(pool_name)
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🧪 Test Plan

### Unit Tests

1. **DriveManager Tests**
   - Test drive detection
   - Test SMART data retrieval
   - Test free drives listing
   - Test drive sync to database

2. **ArrayManager Tests**
   - Test array creation
   - Test array extension
   - Test drive add/remove/replace
   - Test drive online/offline
   - Test array export/delete

3. **ZFSUtils Tests**
   - Test pool_add
   - Test pool_remove
   - Test pool_replace
   - Test pool_online/offline
   - Test pool_destroy

### Integration Tests

1. **Drive Operations Flow**
   - Test drive detection and sync
   - Test array creation with drives
   - Test drive replacement
   - Test error scenarios

2. **Array Operations Flow**
   - Test array creation
   - Test array extension
   - Test array export
   - Test array deletion

### Security Tests

1. **Drive Validation**
   - Test drive ownership validation
   - Test pool membership validation
   - Test unauthorized operations

---

## 📦 Dependencies

### Python Packages

```txt
smartmontools  # System package (smartctl command)
util-linux     # System package (lsblk command)
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add drives and array management tables"

# Apply migration
alembic upgrade head
```

### Existing Code

- ✅ `ZFSUtils` - već postoji sa osnovnim pool operacijama
- ⚠️ Treba dodati: `pool_add`, `pool_remove`, `pool_replace`, `pool_online`, `pool_offline`, `pool_destroy`

---

## ⚠️ Napomene

### Drive Detection

**Problem:** Drive detection zavisi od system utilities (lsblk, udevadm)

**Rešenje:**
- Koristiti `lsblk` za listing
- Koristiti `udevadm` za UUID
- Fallback na device name ako UUID nije dostupan

### SMART Data

**Problem:** SMART data zahteva `smartctl` (smartmontools)

**Rešenje:**
- Proveriti da li je `smartctl` instaliran
- Handle gracefully ako nije dostupan
- Opciono: cache SMART data u bazi

### Array Operations Safety

**Problem:** Array operacije su destruktivne

**Rešenje:**
- Implementirati validation checks
- Zahtevati confirmation za destruktivne operacije
- Implementirati dry-run mode

---

## ✅ Checklist

### Setup
- [ ] Install smartmontools
- [ ] Install util-linux
- [ ] Create database migrations
- [ ] Setup drive detection

### Implementation
- [ ] DriveManager
- [ ] ArrayManager
- [ ] ZFSUtils extensions
- [ ] API Endpoints

### Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] Security tests
- [ ] Safety tests

### Documentation
- [ ] API documentation
- [ ] Drive detection guide
- [ ] Array operations safety guide

---

*Plan kreiran za Array Operations - Drive Management implementaciju.*

