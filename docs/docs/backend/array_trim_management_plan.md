# Array Operations - TRIM Management - Detaljni Plan Implementacije

**Prioritet:** 🔴 P0 - Kritično za MVP  
**Vreme:** 1 nedelja  
**Status:** 📋 Plan

---

## 📋 Pregled

Implementacija TRIM management sistema za ZFS array sa:
- TRIM resume/suspend/run/cancel operations
- TRIM progress tracking
- TRIM configuration
- TRIM status monitoring

---

## 🎯 Funkcionalni Zahtevi

### 1. TRIM Operations

**Zahtevi:**
- Resume TRIM operation
- Suspend TRIM operation
- Run TRIM operation
- Cancel TRIM operation
- Get TRIM status

**Endpoint-i:**
- `POST /api/array/trim/resume` - Resume TRIM
- `POST /api/array/trim/suspend` - Suspend TRIM
- `POST /api/array/trim/run` - Run TRIM
- `POST /api/array/trim/cancel` - Cancel TRIM
- `GET /api/array/trim/status` - Get TRIM status (opciono)

### 2. TRIM Configuration

**Zahtevi:**
- Get TRIM settings
- Update TRIM settings

**Endpoint-i:**
- `GET /api/settings/trim` - Get TRIM settings
- `PUT /api/settings/trim` - Update TRIM settings

---

## 🗄️ Database Schema

### TRIM Operations Table

```sql
CREATE TABLE trim_operations (
    id SERIAL PRIMARY KEY,
    pool_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'running', 'suspended', 'completed', 'cancelled', 'failed'
    progress_percent INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    suspended_at TIMESTAMP,
    resumed_at TIMESTAMP,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    error_message TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trim_operations_pool_name ON trim_operations(pool_name);
CREATE INDEX idx_trim_operations_status ON trim_operations(status);
```

---

## 📁 Struktura Fajlova

```
app/backend/
├── storage/
│   ├── trim_manager.py          # TRIM operations manager (novi)
│   └── zfs_utils.py             # Proširiti sa TRIM metodama
└── api/
    └── array.py                 # Proširiti sa TRIM endpoint-ima (ili storage.py)
```

---

## 🔧 Implementacija

### 1. TRIM Manager (`app/backend/storage/trim_manager.py`)

```python
"""
TRIM Manager for ZFS array TRIM operations
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.backend.config.models import TrimOperation
from app.backend.storage.zfs_utils import ZFSUtils
from app.backend.clients.websocket_hub import connection_manager
from app.backend.utils.exceptions import StorageError, NotFoundError

logger = logging.getLogger(__name__)


class TrimManager:
    """TRIM manager for ZFS pool operations"""
    
    def __init__(self):
        """Initialize TRIM manager"""
        self.zfs_utils = ZFSUtils()
        self.active_operations: Dict[str, asyncio.Task] = {}  # {pool_name: task}
    
    async def resume_trim(
        self,
        db: Session,
        pool_name: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Resume TRIM operation
        
        Args:
            db: Database session
            pool_name: Pool name
            user_id: User ID who initiated the operation
            
        Returns:
            TRIM operation result
        """
        # Check if pool exists
        if not self.zfs_utils.pool_exists(pool_name):
            raise NotFoundError(f"Pool {pool_name} not found")
        
        # Get or create TRIM operation
        trim_op = db.query(TrimOperation).filter(
            TrimOperation.pool_name == pool_name,
            TrimOperation.status.in_(['pending', 'suspended'])
        ).order_by(TrimOperation.created_at.desc()).first()
        
        if not trim_op:
            # Create new TRIM operation
            trim_op = TrimOperation(
                pool_name=pool_name,
                status='pending',
                created_by=user_id
            )
            db.add(trim_op)
            db.commit()
            db.refresh(trim_op)
        
        # Resume TRIM
        try:
            self.zfs_utils.trim_resume(pool_name)
            
            trim_op.status = 'running'
            trim_op.resumed_at = datetime.utcnow()
            if not trim_op.started_at:
                trim_op.started_at = datetime.utcnow()
            db.commit()
            
            # Start progress tracking task
            task = asyncio.create_task(self._track_trim_progress(db, trim_op.id, pool_name))
            self.active_operations[pool_name] = task
            
            # Send WebSocket notification
            await connection_manager.broadcast({
                "event": "trim_operation_resumed",
                "data": {
                    "operation_id": trim_op.id,
                    "pool_name": pool_name
                }
            })
            
            return {
                "operation_id": trim_op.id,
                "pool_name": pool_name,
                "status": "running"
            }
        
        except Exception as e:
            logger.error(f"Failed to resume TRIM for {pool_name}: {e}")
            trim_op.status = 'failed'
            trim_op.error_message = str(e)
            db.commit()
            raise StorageError(f"Failed to resume TRIM: {e}")
    
    async def suspend_trim(
        self,
        db: Session,
        pool_name: str
    ) -> Dict[str, Any]:
        """
        Suspend TRIM operation
        
        Args:
            db: Database session
            pool_name: Pool name
            
        Returns:
            TRIM operation result
        """
        trim_op = db.query(TrimOperation).filter(
            TrimOperation.pool_name == pool_name,
            TrimOperation.status == 'running'
        ).order_by(TrimOperation.created_at.desc()).first()
        
        if not trim_op:
            raise NotFoundError(f"No active TRIM operation for pool {pool_name}")
        
        try:
            self.zfs_utils.trim_suspend(pool_name)
            
            trim_op.status = 'suspended'
            trim_op.suspended_at = datetime.utcnow()
            db.commit()
            
            # Cancel progress tracking task
            if pool_name in self.active_operations:
                self.active_operations[pool_name].cancel()
                del self.active_operations[pool_name]
            
            # Send WebSocket notification
            await connection_manager.broadcast({
                "event": "trim_operation_suspended",
                "data": {
                    "operation_id": trim_op.id,
                    "pool_name": pool_name
                }
            })
            
            return {
                "operation_id": trim_op.id,
                "pool_name": pool_name,
                "status": "suspended"
            }
        
        except Exception as e:
            logger.error(f"Failed to suspend TRIM for {pool_name}: {e}")
            raise StorageError(f"Failed to suspend TRIM: {e}")
    
    async def run_trim(
        self,
        db: Session,
        pool_name: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run TRIM operation (start new or resume existing)
        
        Args:
            db: Database session
            pool_name: Pool name
            user_id: User ID who initiated the operation
            
        Returns:
            TRIM operation result
        """
        # Check if there's an active operation
        active_op = db.query(TrimOperation).filter(
            TrimOperation.pool_name == pool_name,
            TrimOperation.status == 'running'
        ).first()
        
        if active_op:
            raise StorageError(f"TRIM operation already running for pool {pool_name}")
        
        # Resume or start new
        return await self.resume_trim(db, pool_name, user_id)
    
    async def cancel_trim(
        self,
        db: Session,
        pool_name: str
    ) -> Dict[str, Any]:
        """
        Cancel TRIM operation
        
        Args:
            db: Database session
            pool_name: Pool name
            
        Returns:
            TRIM operation result
        """
        trim_op = db.query(TrimOperation).filter(
            TrimOperation.pool_name == pool_name,
            TrimOperation.status.in_(['pending', 'running', 'suspended'])
        ).order_by(TrimOperation.created_at.desc()).first()
        
        if not trim_op:
            raise NotFoundError(f"No active TRIM operation for pool {pool_name}")
        
        try:
            # Cancel TRIM (if running)
            if trim_op.status == 'running':
                self.zfs_utils.trim_cancel(pool_name)
            
            trim_op.status = 'cancelled'
            trim_op.cancelled_at = datetime.utcnow()
            db.commit()
            
            # Cancel progress tracking task
            if pool_name in self.active_operations:
                self.active_operations[pool_name].cancel()
                del self.active_operations[pool_name]
            
            # Send WebSocket notification
            await connection_manager.broadcast({
                "event": "trim_operation_cancelled",
                "data": {
                    "operation_id": trim_op.id,
                    "pool_name": pool_name
                }
            })
            
            return {
                "operation_id": trim_op.id,
                "pool_name": pool_name,
                "status": "cancelled"
            }
        
        except Exception as e:
            logger.error(f"Failed to cancel TRIM for {pool_name}: {e}")
            raise StorageError(f"Failed to cancel TRIM: {e}")
    
    async def _track_trim_progress(
        self,
        db: Session,
        operation_id: int,
        pool_name: str
    ):
        """
        Track TRIM operation progress (background task)
        
        Args:
            db: Database session
            operation_id: TRIM operation ID
            pool_name: Pool name
        """
        try:
            while True:
                # Get TRIM status from ZFS
                status = self.zfs_utils.trim_status(pool_name)
                
                # Update operation
                trim_op = db.query(TrimOperation).filter(TrimOperation.id == operation_id).first()
                if not trim_op:
                    break
                
                if status.get('status') == 'completed':
                    trim_op.status = 'completed'
                    trim_op.progress_percent = 100
                    trim_op.completed_at = datetime.utcnow()
                    db.commit()
                    
                    # Send completion notification
                    await connection_manager.broadcast({
                        "event": "trim_operation_completed",
                        "data": {
                            "operation_id": operation_id,
                            "pool_name": pool_name
                        }
                    })
                    break
                elif status.get('status') == 'failed':
                    trim_op.status = 'failed'
                    trim_op.error_message = status.get('error')
                    db.commit()
                    break
                else:
                    # Update progress
                    trim_op.progress_percent = status.get('progress', 0)
                    db.commit()
                    
                    # Send progress update
                    await connection_manager.broadcast({
                        "event": "trim_operation_progress",
                        "data": {
                            "operation_id": operation_id,
                            "pool_name": pool_name,
                            "progress": status.get('progress', 0)
                        }
                    })
                
                # Wait before next check
                await asyncio.sleep(5)  # Check every 5 seconds
        
        except asyncio.CancelledError:
            logger.info(f"TRIM progress tracking cancelled for {pool_name}")
        except Exception as e:
            logger.error(f"Error tracking TRIM progress for {pool_name}: {e}")
            # Mark operation as failed
            trim_op = db.query(TrimOperation).filter(TrimOperation.id == operation_id).first()
            if trim_op:
                trim_op.status = 'failed'
                trim_op.error_message = str(e)
                db.commit()
    
    def get_trim_status(
        self,
        db: Session,
        pool_name: str
    ) -> Dict[str, Any]:
        """
        Get TRIM status for pool
        
        Args:
            db: Database session
            pool_name: Pool name
            
        Returns:
            TRIM status
        """
        trim_op = db.query(TrimOperation).filter(
            TrimOperation.pool_name == pool_name
        ).order_by(TrimOperation.created_at.desc()).first()
        
        if not trim_op:
            return {
                "pool_name": pool_name,
                "status": "none",
                "has_active_operation": False
            }
        
        # Get current ZFS TRIM status
        zfs_status = self.zfs_utils.trim_status(pool_name)
        
        return {
            "operation_id": trim_op.id,
            "pool_name": pool_name,
            "status": trim_op.status,
            "progress_percent": trim_op.progress_percent,
            "started_at": trim_op.started_at.isoformat() if trim_op.started_at else None,
            "completed_at": trim_op.completed_at.isoformat() if trim_op.completed_at else None,
            "zfs_status": zfs_status,
            "has_active_operation": trim_op.status in ['pending', 'running', 'suspended']
        }
```

### 2. ZFSUtils Extensions (`app/backend/storage/zfs_utils.py`)

```python
# Dodati metode u postojeći ZFSUtils

def trim_resume(self, pool_name: str) -> None:
    """
    Resume TRIM operation on pool
    
    Args:
        pool_name: Pool name
        
    Raises:
        ZFSError: If resume fails
    """
    try:
        # ZFS TRIM is automatic, but we can trigger it
        # For manual TRIM, we use zpool trim
        self._run_command([self.zpool_cmd, "trim", pool_name])
        logger.info(f"Resumed TRIM for pool {pool_name}")
    except Exception as e:
        raise ZFSError(f"Failed to resume TRIM: {e}")

def trim_suspend(self, pool_name: str) -> None:
    """
    Suspend TRIM operation on pool
    
    Args:
        pool_name: Pool name
        
    Raises:
        ZFSError: If suspend fails
    """
    try:
        # ZFS doesn't have direct suspend, but we can cancel and track
        # For now, we'll track the operation state
        # Actual suspend would require process management
        logger.info(f"Suspended TRIM for pool {pool_name} (tracked)")
    except Exception as e:
        raise ZFSError(f"Failed to suspend TRIM: {e}")

def trim_run(self, pool_name: str) -> None:
    """
    Run TRIM operation on pool
    
    Args:
        pool_name: Pool name
        
    Raises:
        ZFSError: If run fails
    """
    try:
        self._run_command([self.zpool_cmd, "trim", pool_name])
        logger.info(f"Started TRIM for pool {pool_name}")
    except Exception as e:
        raise ZFSError(f"Failed to run TRIM: {e}")

def trim_cancel(self, pool_name: str) -> None:
    """
    Cancel TRIM operation on pool
    
    Args:
        pool_name: Pool name
        
    Raises:
        ZFSError: If cancel fails
    """
    try:
        # ZFS doesn't have direct cancel, but we can track cancellation
        # Actual cancellation would require process management
        logger.info(f"Cancelled TRIM for pool {pool_name} (tracked)")
    except Exception as e:
        raise ZFSError(f"Failed to cancel TRIM: {e}")

def trim_status(self, pool_name: str) -> Dict[str, Any]:
    """
    Get TRIM status for pool
    
    Args:
        pool_name: Pool name
        
    Returns:
        TRIM status dictionary
    """
    try:
        # Get pool status
        status = self.pool_status(pool_name)
        
        # Check for TRIM in progress
        # This depends on zpool status output format
        # For now, return basic structure
        return {
            "status": "unknown",  # 'running', 'completed', 'none'
            "progress": 0,
            "error": None
        }
    except Exception as e:
        raise ZFSError(f"Failed to get TRIM status: {e}")
```

### 3. API Endpoints (`app/backend/api/array.py`)

```python
# Dodati u postojeći array.py

from app.backend.storage.trim_manager import TrimManager

trim_manager = TrimManager()


@router.post("/trim/resume")
async def resume_trim(
    pool_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Resume TRIM operation
    
    Args:
        pool_name: Pool name
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        TRIM operation result
    """
    try:
        return await trim_manager.resume_trim(db, pool_name, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trim/suspend")
async def suspend_trim(
    pool_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Suspend TRIM operation
    
    Args:
        pool_name: Pool name
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        TRIM operation result
    """
    try:
        return await trim_manager.suspend_trim(db, pool_name)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trim/run")
async def run_trim(
    pool_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Run TRIM operation
    
    Args:
        pool_name: Pool name
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        TRIM operation result
    """
    try:
        return await trim_manager.run_trim(db, pool_name, current_user.id)
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trim/cancel")
async def cancel_trim(
    pool_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Cancel TRIM operation
    
    Args:
        pool_name: Pool name
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        TRIM operation result
    """
    try:
        return await trim_manager.cancel_trim(db, pool_name)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trim/status")
async def get_trim_status(
    pool_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get TRIM status
    
    Args:
        pool_name: Pool name
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        TRIM status
    """
    try:
        return trim_manager.get_trim_status(db, pool_name)
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 4. Settings API Extensions (`app/backend/api/settings.py`)

```python
# Dodati u postojeći settings.py

class TrimSettingsRequest(BaseModel):
    """TRIM settings request"""
    enabled: bool = True
    interval_days: int = 7  # TRIM interval in days
    auto_trim: bool = False  # Auto-trim on schedule


@router.get("/trim")
async def get_trim_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get TRIM settings
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        TRIM settings
    """
    # Get settings from database
    settings = settings_manager.get_settings(db, ["trim_enabled", "trim_interval_days", "trim_auto"])
    
    return {
        "enabled": settings.get("trim_enabled", "true") == "true",
        "interval_days": int(settings.get("trim_interval_days", "7")),
        "auto_trim": settings.get("trim_auto", "false") == "true"
    }


@router.put("/trim")
async def update_trim_settings(
    request: TrimSettingsRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update TRIM settings
    
    Args:
        request: TRIM settings request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated settings
    """
    # Update settings in database
    settings_manager.update_setting(db, "trim_enabled", str(request.enabled).lower())
    settings_manager.update_setting(db, "trim_interval_days", str(request.interval_days))
    settings_manager.update_setting(db, "trim_auto", str(request.auto_trim).lower())
    
    return {
        "enabled": request.enabled,
        "interval_days": request.interval_days,
        "auto_trim": request.auto_trim
    }
```

---

## 🧪 Test Plan

### Unit Tests

1. **TrimManager Tests**
   - Test resume_trim
   - Test suspend_trim
   - Test run_trim
   - Test cancel_trim
   - Test progress tracking
   - Test error handling

2. **ZFSUtils Tests**
   - Test trim_resume
   - Test trim_suspend
   - Test trim_run
   - Test trim_cancel
   - Test trim_status

### Integration Tests

1. **TRIM Operations Flow**
   - Test resume/suspend cycle
   - Test run/cancel cycle
   - Test progress tracking
   - Test error scenarios

2. **WebSocket Integration**
   - Test progress updates
   - Test completion notifications
   - Test cancellation notifications

---

## 📦 Dependencies

### Python Packages

```txt
# No additional packages needed - uses existing ZFS utilities
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add TRIM operations table"

# Apply migration
alembic upgrade head
```

### Existing Code

- ✅ `ZFSUtils` - već postoji
- ✅ `SettingsManager` - već postoji
- ✅ `connection_manager` - već postoji

### New Code

- ⚠️ `TrimManager` - treba kreirati
- ⚠️ `TrimOperation` model - treba dodati
- ⚠️ ZFS TRIM metode - treba dodati u ZFSUtils

---

## ⚠️ Napomene

### ZFS TRIM Behavior

**Problem:** ZFS TRIM je automatski, ali možemo ga trigger-ovati i pratiti

**Rešenje:**
- Koristiti `zpool trim` za manual TRIM
- Pratiti TRIM status kroz pool status
- Implementirati progress tracking

### TRIM Progress Tracking

**Problem:** ZFS ne daje direktan progress output za TRIM

**Rešenje:**
1. **Pool status monitoring:** Pratiti pool status promene
2. **Time-based estimation:** Koristiti vreme za progress estimation
3. **ZFS events:** Koristiti ZFS events ako su dostupni

---

## ✅ Checklist

### Setup
- [ ] Create database migrations
- [ ] Proveriti ZFS TRIM support

### Implementation
- [ ] TrimManager
- [ ] ZFSUtils TRIM metode
- [ ] API Endpoints
- [ ] Settings API extensions
- [ ] Progress tracking

### Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] Progress tracking tests

### Documentation
- [ ] API documentation
- [ ] TRIM operations guide

---

*Plan kreiran za Array Operations - TRIM Management implementaciju.*

