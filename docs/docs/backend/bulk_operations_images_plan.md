# Bulk Operations - Images - Detaljni Plan Implementacije

**Prioritet:** 🔴 P0 - Kritično za MVP  
**Vreme:** 2 nedelje  
**Status:** 📋 Plan

---

## 📋 Pregled

Implementacija bulk operacija za images sa:
- Batch backup operations (local i remote)
- Batch restore operations (local i remote)
- Batch test operations
- Progress tracking preko WebSocket-a
- Operation history tracking

---

## 🎯 Funkcionalni Zahtevi

### 1. Batch Image Operations

**Zahtevi:**
- Local backup images
- Remote backup images
- Local restore images
- Remote restore images
- Local test operations
- Remote test operations
- Operation history

**Endpoint-i:**
- `GET /api/batchImageOperations/history` - Operation history
- `POST /api/batchImageOperations/local/backup` - Local backup
- `POST /api/batchImageOperations/remote/backup` - Remote backup
- `POST /api/batchImageOperations/local/restore` - Local restore
- `POST /api/batchImageOperations/remote/restore` - Remote restore
- `POST /api/batchImageOperations/local/test` - Local test
- `POST /api/batchImageOperations/remote/test` - Remote test
- `GET /api/batchImageOperations/local/backup/images` - List images for backup
- `GET /api/batchImageOperations/remote/backup/images` - List images for backup
- `POST /api/batchImageOperations/local/restore/images` - List images for restore
- `POST /api/batchImageOperations/remote/restore/images` - List images for restore

---

## 🗄️ Database Schema

### Batch Image Operations Table

```sql
CREATE TABLE batch_image_operations (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL,  -- 'backup', 'restore', 'test'
    operation_mode VARCHAR(50) NOT NULL,  -- 'local', 'remote'
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    total_images INTEGER NOT NULL,
    completed_images INTEGER DEFAULT 0,
    failed_images INTEGER DEFAULT 0,
    source_path VARCHAR(500),  -- Source path for restore
    destination_path VARCHAR(500),  -- Destination path for backup
    remote_server VARCHAR(255),  -- Remote server for remote operations
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSON  -- Additional operation metadata
);

CREATE INDEX idx_batch_image_operations_status ON batch_image_operations(status);
CREATE INDEX idx_batch_image_operations_created_by ON batch_image_operations(created_by);
CREATE INDEX idx_batch_image_operations_type ON batch_image_operations(operation_type);
```

### Batch Image Operation Images Table

```sql
CREATE TABLE batch_image_operation_images (
    id SERIAL PRIMARY KEY,
    batch_operation_id INTEGER NOT NULL REFERENCES batch_image_operations(id) ON DELETE CASCADE,
    image_id INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    image_path VARCHAR(500) NOT NULL,  -- ZFS dataset path
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed'
    progress_percent INTEGER DEFAULT 0,
    bytes_transferred BIGINT DEFAULT 0,
    total_bytes BIGINT,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_batch_image_operation_images_batch_id ON batch_image_operation_images(batch_operation_id);
CREATE INDEX idx_batch_image_operation_images_image_id ON batch_image_operation_images(image_id);
CREATE INDEX idx_batch_image_operation_images_status ON batch_image_operation_images(status);
```

---

## 📁 Struktura Fajlova

```
app/backend/
├── images/
│   ├── batch_operations.py      # Batch operations manager (novi)
│   └── image_manager.py         # Proširiti sa backup/restore metodama
├── storage/
│   └── zfs_utils.py             # Već ima send/receive metode
└── api/
    └── batch_image_operations.py  # API endpoints (novi)
```

---

## 🔧 Implementacija

### 1. Batch Operations Manager (`app/backend/images/batch_operations.py`)

```python
"""
Batch Operations Manager for Images
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.backend.config.models import Image, BatchImageOperation, BatchImageOperationImage
from app.backend.images.image_manager import ImageManager
from app.backend.storage.zfs_utils import ZFSUtils
from app.backend.clients.websocket_hub import connection_manager
from app.backend.utils.exceptions import ImageError, NotFoundError, ZFSError

logger = logging.getLogger(__name__)


class BatchImageOperationsManager:
    """Batch operations manager for images"""
    
    def __init__(self):
        """Initialize batch operations manager"""
        self.image_manager = ImageManager()
        self.zfs_utils = ZFSUtils()
    
    async def execute_batch_backup(
        self,
        db: Session,
        image_ids: List[int],
        destination_path: str,
        operation_mode: str = "local",  # 'local' or 'remote'
        remote_server: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute batch backup operation
        
        Args:
            db: Database session
            image_ids: List of image IDs to backup
            destination_path: Destination path for backup
            operation_mode: 'local' or 'remote'
            remote_server: Remote server (for remote operations)
            user_id: User ID who initiated the operation
            
        Returns:
            Batch operation result
        """
        # Validate images exist
        images = db.query(Image).filter(Image.id.in_(image_ids)).all()
        if len(images) != len(image_ids):
            found_ids = {img.id for img in images}
            missing_ids = set(image_ids) - found_ids
            raise NotFoundError(f"Images not found: {missing_ids}")
        
        # Create batch operation record
        batch_op = BatchImageOperation(
            operation_type='backup',
            operation_mode=operation_mode,
            status='pending',
            total_images=len(image_ids),
            destination_path=destination_path,
            remote_server=remote_server,
            created_by=user_id
        )
        db.add(batch_op)
        db.commit()
        db.refresh(batch_op)
        
        # Create batch operation image records
        for image in images:
            batch_op_image = BatchImageOperationImage(
                batch_operation_id=batch_op.id,
                image_id=image.id,
                image_path=image.zfs_dataset,
                status='pending'
            )
            db.add(batch_op_image)
        db.commit()
        
        # Send WebSocket notification
        await connection_manager.broadcast({
            "event": "batch_image_operation_started",
            "data": {
                "operation_id": batch_op.id,
                "operation_type": "backup",
                "operation_mode": operation_mode,
                "total_images": len(image_ids)
            }
        })
        
        # Execute operation asynchronously
        asyncio.create_task(self._execute_backup(db, batch_op.id, images, destination_path, operation_mode, remote_server))
        
        return {
            "operation_id": batch_op.id,
            "operation_type": "backup",
            "operation_mode": operation_mode,
            "total_images": len(image_ids),
            "status": "running"
        }
    
    async def _execute_backup(
        self,
        db: Session,
        operation_id: int,
        images: List[Image],
        destination_path: str,
        operation_mode: str,
        remote_server: Optional[str]
    ):
        """
        Execute backup operation (background task)
        
        Args:
            db: Database session
            operation_id: Batch operation ID
            images: List of images
            destination_path: Destination path
            operation_mode: Operation mode
            remote_server: Remote server
        """
        # Update batch operation status
        batch_op = db.query(BatchImageOperation).filter(BatchImageOperation.id == operation_id).first()
        if not batch_op:
            return
        
        batch_op.status = 'running'
        batch_op.started_at = datetime.utcnow()
        db.commit()
        
        completed = 0
        failed = 0
        
        # Execute backup on each image
        for image in images:
            try:
                # Get batch operation image record
                batch_op_image = db.query(BatchImageOperationImage).filter(
                    BatchImageOperationImage.batch_operation_id == operation_id,
                    BatchImageOperationImage.image_id == image.id
                ).first()
                
                if not batch_op_image:
                    continue
                
                batch_op_image.status = 'running'
                batch_op_image.started_at = datetime.utcnow()
                db.commit()
                
                # Execute backup based on mode
                if operation_mode == 'local':
                    await self._backup_local(db, image, destination_path, batch_op_image)
                elif operation_mode == 'remote':
                    await self._backup_remote(db, image, destination_path, remote_server, batch_op_image)
                
                # Mark as completed
                batch_op_image.status = 'completed'
                batch_op_image.completed_at = datetime.utcnow()
                batch_op_image.progress_percent = 100
                completed += 1
                
            except Exception as e:
                logger.error(f"Error backing up image {image.id}: {e}")
                batch_op_image.status = 'failed'
                batch_op_image.error_message = str(e)
                batch_op_image.completed_at = datetime.utcnow()
                failed += 1
            
            db.commit()
            
            # Update batch operation progress
            batch_op.completed_images = completed
            batch_op.failed_images = failed
            db.commit()
            
            # Send progress update
            await connection_manager.broadcast({
                "event": "batch_image_operation_progress",
                "data": {
                    "operation_id": operation_id,
                    "completed": completed,
                    "failed": failed,
                    "total": len(images),
                    "progress": (completed + failed) / len(images) * 100
                }
            })
        
        # Mark batch operation as completed
        batch_op.status = 'completed' if failed == 0 else 'failed'
        batch_op.completed_at = datetime.utcnow()
        if failed > 0:
            batch_op.error_message = f"{failed} images failed"
        db.commit()
        
        # Send completion notification
        await connection_manager.broadcast({
            "event": "batch_image_operation_completed",
            "data": {
                "operation_id": operation_id,
                "status": batch_op.status,
                "completed": completed,
                "failed": failed,
                "total": len(images)
            }
        })
    
    async def _backup_local(
        self,
        db: Session,
        image: Image,
        destination_path: str,
        batch_op_image: BatchImageOperationImage
    ):
        """
        Backup image locally (ZFS send to file)
        
        Args:
            db: Database session
            image: Image to backup
            destination_path: Destination path
            batch_op_image: Batch operation image record
        """
        # Get snapshot path
        snapshot_path = f"{image.zfs_dataset}@{image.zfs_snapshot}"
        
        # Get send size
        send_size = self.zfs_utils.snapshot_get_send_size(snapshot_path)
        batch_op_image.total_bytes = send_size
        db.commit()
        
        # Create backup file path
        backup_file = f"{destination_path}/{image.name}.zfs"
        
        # Send snapshot to file
        # This would use zfs send | gzip > backup_file
        # For now, simplified version
        self.zfs_utils.snapshot_send(snapshot_path, backup_file)
        
        logger.info(f"Backed up image {image.name} to {backup_file}")
    
    async def _backup_remote(
        self,
        db: Session,
        image: Image,
        destination_path: str,
        remote_server: str,
        batch_op_image: BatchImageOperationImage
    ):
        """
        Backup image remotely (ZFS send over network)
        
        Args:
            db: Database session
            image: Image to backup
            destination_path: Destination path on remote server
            remote_server: Remote server address
            batch_op_image: Batch operation image record
        """
        # Get snapshot path
        snapshot_path = f"{image.zfs_dataset}@{image.zfs_snapshot}"
        
        # Get send size
        send_size = self.zfs_utils.snapshot_get_send_size(snapshot_path)
        batch_op_image.total_bytes = send_size
        db.commit()
        
        # Send snapshot to remote server
        # This would use zfs send | ssh remote_server "zfs receive ..."
        # For now, simplified version
        remote_path = f"{remote_server}:{destination_path}/{image.name}"
        self.zfs_utils.snapshot_send_remote(snapshot_path, remote_path)
        
        logger.info(f"Backed up image {image.name} to remote {remote_server}")
    
    async def execute_batch_restore(
        self,
        db: Session,
        image_paths: List[str],
        source_path: str,
        operation_mode: str = "local",
        remote_server: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute batch restore operation
        
        Similar to backup, but in reverse direction
        """
        # Implementation similar to backup
        pass
    
    async def execute_batch_test(
        self,
        db: Session,
        image_ids: List[int],
        operation_mode: str = "local",
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute batch test operation (verify backup/restore)
        
        Similar to backup, but only verifies without actual transfer
        """
        # Implementation for test operations
        pass
    
    def get_operation_history(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        operation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get batch operation history
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            operation_type: Optional filter by operation type
            
        Returns:
            List of batch operations
        """
        query = db.query(BatchImageOperation)
        
        if operation_type:
            query = query.filter(BatchImageOperation.operation_type == operation_type)
        
        operations = query.order_by(BatchImageOperation.created_at.desc()).offset(skip).limit(limit).all()
        
        result = []
        for op in operations:
            result.append({
                "id": op.id,
                "operation_type": op.operation_type,
                "operation_mode": op.operation_mode,
                "status": op.status,
                "total_images": op.total_images,
                "completed_images": op.completed_images,
                "failed_images": op.failed_images,
                "created_at": op.created_at.isoformat() if op.created_at else None,
                "completed_at": op.completed_at.isoformat() if op.completed_at else None
            })
        
        return result
```

### 2. API Endpoints (`app/backend/api/batch_image_operations.py`)

```python
"""
Batch Image Operations API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.backend.config.database import get_db
from app.backend.images.batch_operations import BatchImageOperationsManager
from app.backend.auth.dependencies import get_current_user
from app.backend.config.models import User

router = APIRouter()
batch_ops_manager = BatchImageOperationsManager()


class BatchBackupRequest(BaseModel):
    """Batch backup request"""
    image_ids: List[int]
    destination_path: str
    operation_mode: str = "local"  # 'local' or 'remote'
    remote_server: Optional[str] = None


class BatchRestoreRequest(BaseModel):
    """Batch restore request"""
    image_paths: List[str]
    source_path: str
    operation_mode: str = "local"
    remote_server: Optional[str] = None


class BatchTestRequest(BaseModel):
    """Batch test request"""
    image_ids: List[int]
    operation_mode: str = "local"


@router.get("/history")
async def get_operation_history(
    skip: int = 0,
    limit: int = 100,
    operation_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get batch operation history
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        operation_type: Optional filter by operation type
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of batch operations
    """
    return batch_ops_manager.get_operation_history(db, skip, limit, operation_type)


@router.post("/local/backup")
async def local_backup(
    request: BatchBackupRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Execute local backup operation
    
    Args:
        request: Batch backup request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Batch operation result
    """
    try:
        return await batch_ops_manager.execute_batch_backup(
            db=db,
            image_ids=request.image_ids,
            destination_path=request.destination_path,
            operation_mode="local",
            user_id=current_user.id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remote/backup")
async def remote_backup(
    request: BatchBackupRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Execute remote backup operation
    
    Args:
        request: Batch backup request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Batch operation result
    """
    if not request.remote_server:
        raise HTTPException(status_code=400, detail="remote_server is required for remote operations")
    
    try:
        return await batch_ops_manager.execute_batch_backup(
            db=db,
            image_ids=request.image_ids,
            destination_path=request.destination_path,
            operation_mode="remote",
            remote_server=request.remote_server,
            user_id=current_user.id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/local/restore")
async def local_restore(
    request: BatchRestoreRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Execute local restore operation
    
    Args:
        request: Batch restore request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Batch operation result
    """
    try:
        return await batch_ops_manager.execute_batch_restore(
            db=db,
            image_paths=request.image_paths,
            source_path=request.source_path,
            operation_mode="local",
            user_id=current_user.id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remote/restore")
async def remote_restore(
    request: BatchRestoreRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Execute remote restore operation
    
    Args:
        request: Batch restore request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Batch operation result
    """
    if not request.remote_server:
        raise HTTPException(status_code=400, detail="remote_server is required for remote operations")
    
    try:
        return await batch_ops_manager.execute_batch_restore(
            db=db,
            image_paths=request.image_paths,
            source_path=request.source_path,
            operation_mode="remote",
            remote_server=request.remote_server,
            user_id=current_user.id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/local/test")
async def local_test(
    request: BatchTestRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Execute local test operation
    
    Args:
        request: Batch test request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Batch operation result
    """
    try:
        return await batch_ops_manager.execute_batch_test(
            db=db,
            image_ids=request.image_ids,
            operation_mode="local",
            user_id=current_user.id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remote/test")
async def remote_test(
    request: BatchTestRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Execute remote test operation
    
    Args:
        request: Batch test request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Batch operation result
    """
    try:
        return await batch_ops_manager.execute_batch_test(
            db=db,
            image_ids=request.image_ids,
            operation_mode="remote",
            user_id=current_user.id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/local/backup/images")
async def list_images_for_backup(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List images available for backup
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of images
    """
    images = db.query(Image).filter(Image.status == "active").all()
    return [
        {
            "id": img.id,
            "name": img.name,
            "zfs_dataset": img.zfs_dataset,
            "size_gb": img.size_gb
        }
        for img in images
    ]


@router.get("/remote/backup/images")
async def list_remote_images_for_backup(
    remote_server: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List images available for backup on remote server
    
    Args:
        remote_server: Remote server address
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of images
    """
    # Implementation would query remote server
    # For now, return empty list
    return []
```

### 3. Router Integration (`app/backend/api/router.py`)

```python
# Dodati u router.py

from app.backend.api import batch_image_operations

api_router.include_router(
    batch_image_operations.router,
    prefix="/batchImageOperations",
    tags=["batch-image-operations"]
)
```

---

## 🧪 Test Plan

### Unit Tests

1. **Batch Operations Manager Tests**
   - Test batch backup creation
   - Test batch restore creation
   - Test batch test creation
   - Test operation execution
   - Test progress tracking
   - Test error handling

2. **ZFS Operations Tests**
   - Test snapshot send
   - Test snapshot receive
   - Test send size calculation
   - Test remote operations

### Integration Tests

1. **Batch Operations Flow**
   - Test local backup
   - Test remote backup
   - Test local restore
   - Test remote restore
   - Test error scenarios
   - Test cancellation

2. **WebSocket Integration**
   - Test progress updates
   - Test completion notifications
   - Test error notifications

### Performance Tests

1. **Large Batch Operations**
   - Test with 50+ images
   - Test concurrent operations
   - Test timeout handling
   - Test resource usage

---

## 📦 Dependencies

### Python Packages

```txt
# No additional packages needed - uses existing ZFS utilities
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add batch image operations tables"

# Apply migration
alembic upgrade head
```

### Existing Code

- ✅ `ImageManager` - već postoji
- ✅ `ZFSUtils` - već ima `snapshot_send`, `snapshot_receive`, `snapshot_get_send_size`
- ✅ `Image` model - već postoji
- ✅ `connection_manager` - već postoji u `websocket_hub.py`

### New Code

- ⚠️ `BatchImageOperationsManager` - treba kreirati
- ⚠️ `BatchImageOperation` model - treba dodati
- ⚠️ `BatchImageOperationImage` model - treba dodati
- ⚠️ `snapshot_send_remote()` - treba dodati u ZFSUtils (opciono)

---

## ⚠️ Napomene

### Remote Operations

**Problem:** Remote operations zahtevaju SSH ili drugi network protokol

**Rešenje:**
1. **SSH-based:** Koristiti `zfs send | ssh remote "zfs receive"`
2. **ZFS over network:** Koristiti ZFS network protocol (ako je podržan)
3. **API-based:** Koristiti REST API na remote serveru

**Preporuka:** Početi sa SSH-based pristupom, kasnije dodati API-based

### Progress Tracking

**Problem:** ZFS send/receive ne daje direktan progress output

**Rešenje:**
1. **pv (pipe viewer):** Koristiti `pv` za progress tracking
2. **File size monitoring:** Pratiti veličinu output fajla
3. **Network monitoring:** Pratiti network transfer za remote operacije

---

## ✅ Checklist

### Setup
- [ ] Install dependencies (pv za progress tracking)
- [ ] Create database migrations
- [ ] Setup remote server access (SSH keys)

### Implementation
- [ ] Batch Operations Manager
- [ ] Database models
- [ ] API Endpoints
- [ ] ZFS remote operations
- [ ] Progress tracking

### Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] Performance tests
- [ ] Remote operations tests

### Documentation
- [ ] API documentation
- [ ] Remote server setup guide
- [ ] Progress tracking documentation

---

*Plan kreiran za Bulk Operations - Images implementaciju.*

