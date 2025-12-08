# Bulk Operations - Machines - Detaljni Plan Implementacije

**Prioritet:** 🔴 P0 - Kritično za MVP  
**Vreme:** 1 nedelja  
**Status:** 📋 Plan

---

## 📋 Pregled

Implementacija bulk operacija za machines sa:
- Batch operations (restart, shutdown, wake, turnOn)
- Progress tracking preko WebSocket-a
- Error handling i rollback
- Transaction management

---

## 🎯 Funkcionalni Zahtevi

### 1. Batch Operations

**Zahtevi:**
- Bulk restart machines
- Bulk shutdown machines
- Bulk wake machines
- Bulk turn on machines
- Generic batch operations sa custom actions

**Endpoint-i:**
- `POST /api/machines/batch` - Generic batch operations
- `POST /api/machines/restart` - Bulk restart
- `POST /api/machines/shutdown` - Bulk shutdown
- `POST /api/machines/wake` - Bulk wake
- `POST /api/machines/turnOn` - Bulk turn on

### 2. Progress Tracking

**Zahtevi:**
- Real-time progress updates preko WebSocket-a
- Operation status tracking
- Error reporting per machine
- Completion notifications

**WebSocket Events:**
- `batch_operation_started` - Operation started
- `batch_operation_progress` - Progress update
- `batch_operation_completed` - Operation completed
- `batch_operation_failed` - Operation failed

---

## 🗄️ Database Schema

### Batch Operations Table

```sql
CREATE TABLE batch_operations (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL,  -- 'restart', 'shutdown', 'wake', 'turnOn'
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed'
    total_machines INTEGER NOT NULL,
    completed_machines INTEGER DEFAULT 0,
    failed_machines INTEGER DEFAULT 0,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

CREATE INDEX idx_batch_operations_status ON batch_operations(status);
CREATE INDEX idx_batch_operations_created_by ON batch_operations(created_by);
```

### Batch Operation Machines Table

```sql
CREATE TABLE batch_operation_machines (
    id SERIAL PRIMARY KEY,
    batch_operation_id INTEGER NOT NULL REFERENCES batch_operations(id) ON DELETE CASCADE,
    machine_id INTEGER NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed'
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_batch_operation_machines_batch_id ON batch_operation_machines(batch_operation_id);
CREATE INDEX idx_batch_operation_machines_machine_id ON batch_operation_machines(machine_id);
CREATE INDEX idx_batch_operation_machines_status ON batch_operation_machines(status);
```

---

## 📁 Struktura Fajlova

```
app/backend/
├── machines/
│   ├── batch_operations.py      # Batch operations manager (novi)
│   └── machine_manager.py       # Proširiti sa bulk metodama
├── api/
│   └── machines.py              # Proširiti sa bulk endpoint-ima
└── websocket/
    └── hub.py                   # Proširiti sa batch operation eventima
```

---

## 🔧 Implementacija

### 1. Batch Operations Manager (`app/backend/machines/batch_operations.py`)

```python
"""
Batch Operations Manager for Machines
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.backend.config.models import Machine, BatchOperation, BatchOperationMachine
from app.backend.machines.machine_manager import MachineManager
from app.backend.clients.websocket_hub import WebSocketHub
from app.backend.utils.exceptions import MachineError, NotFoundError

logger = logging.getLogger(__name__)


class BatchOperationsManager:
    """Batch operations manager for machines"""
    
    def __init__(self):
        """Initialize batch operations manager"""
        self.machine_manager = MachineManager()
        self.websocket_hub = WebSocketHub()
    
    async def execute_batch_operation(
        self,
        db: Session,
        machine_ids: List[int],
        operation_type: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute batch operation on multiple machines
        
        Args:
            db: Database session
            machine_ids: List of machine IDs
            operation_type: Operation type ('restart', 'shutdown', 'wake', 'turnOn')
            user_id: User ID who initiated the operation
            
        Returns:
            Batch operation result
        """
        # Validate operation type
        valid_operations = ['restart', 'shutdown', 'wake', 'turnOn']
        if operation_type not in valid_operations:
            raise ValueError(f"Invalid operation type: {operation_type}")
        
        # Validate machines exist
        machines = db.query(Machine).filter(Machine.id.in_(machine_ids)).all()
        if len(machines) != len(machine_ids):
            found_ids = {m.id for m in machines}
            missing_ids = set(machine_ids) - found_ids
            raise NotFoundError(f"Machines not found: {missing_ids}")
        
        # Create batch operation record
        batch_op = BatchOperation(
            operation_type=operation_type,
            status='pending',
            total_machines=len(machine_ids),
            created_by=user_id
        )
        db.add(batch_op)
        db.commit()
        db.refresh(batch_op)
        
        # Create batch operation machine records
        for machine_id in machine_ids:
            batch_op_machine = BatchOperationMachine(
                batch_operation_id=batch_op.id,
                machine_id=machine_id,
                status='pending'
            )
            db.add(batch_op_machine)
        db.commit()
        
        # Send WebSocket notification
        await self.websocket_hub.broadcast({
            "event": "batch_operation_started",
            "data": {
                "operation_id": batch_op.id,
                "operation_type": operation_type,
                "total_machines": len(machine_ids)
            }
        })
        
        # Execute operation asynchronously
        asyncio.create_task(self._execute_operation(db, batch_op.id, machines, operation_type))
        
        return {
            "operation_id": batch_op.id,
            "operation_type": operation_type,
            "total_machines": len(machine_ids),
            "status": "running"
        }
    
    async def _execute_operation(
        self,
        db: Session,
        operation_id: int,
        machines: List[Machine],
        operation_type: str
    ):
        """
        Execute operation on machines (background task)
        
        Args:
            db: Database session
            operation_id: Batch operation ID
            machines: List of machines
            operation_type: Operation type
        """
        # Update batch operation status
        batch_op = db.query(BatchOperation).filter(BatchOperation.id == operation_id).first()
        if not batch_op:
            return
        
        batch_op.status = 'running'
        batch_op.started_at = datetime.utcnow()
        db.commit()
        
        completed = 0
        failed = 0
        
        # Execute operation on each machine
        for machine in machines:
            try:
                # Get batch operation machine record
                batch_op_machine = db.query(BatchOperationMachine).filter(
                    BatchOperationMachine.batch_operation_id == operation_id,
                    BatchOperationMachine.machine_id == machine.id
                ).first()
                
                if not batch_op_machine:
                    continue
                
                batch_op_machine.status = 'running'
                batch_op_machine.started_at = datetime.utcnow()
                db.commit()
                
                # Execute operation based on type
                if operation_type == 'restart':
                    await self._restart_machine(db, machine)
                elif operation_type == 'shutdown':
                    await self._shutdown_machine(db, machine)
                elif operation_type == 'wake':
                    await self._wake_machine(db, machine)
                elif operation_type == 'turnOn':
                    await self._turn_on_machine(db, machine)
                
                # Mark as completed
                batch_op_machine.status = 'completed'
                batch_op_machine.completed_at = datetime.utcnow()
                completed += 1
                
            except Exception as e:
                logger.error(f"Error executing {operation_type} on machine {machine.id}: {e}")
                batch_op_machine.status = 'failed'
                batch_op_machine.error_message = str(e)
                batch_op_machine.completed_at = datetime.utcnow()
                failed += 1
            
            db.commit()
            
            # Update batch operation progress
            batch_op.completed_machines = completed
            batch_op.failed_machines = failed
            db.commit()
            
            # Send progress update
            await self.websocket_hub.broadcast({
                "event": "batch_operation_progress",
                "data": {
                    "operation_id": operation_id,
                    "completed": completed,
                    "failed": failed,
                    "total": len(machines),
                    "progress": (completed + failed) / len(machines) * 100
                }
            })
        
        # Mark batch operation as completed
        batch_op.status = 'completed' if failed == 0 else 'failed'
        batch_op.completed_at = datetime.utcnow()
        if failed > 0:
            batch_op.error_message = f"{failed} machines failed"
        db.commit()
        
        # Send completion notification
        await self.websocket_hub.broadcast({
            "event": "batch_operation_completed",
            "data": {
                "operation_id": operation_id,
                "status": batch_op.status,
                "completed": completed,
                "failed": failed,
                "total": len(machines)
            }
        })
    
    async def _restart_machine(self, db: Session, machine: Machine):
        """Restart machine"""
        # Implementation depends on how machines are restarted
        # This could be via Wake-on-LAN, iSCSI, or other methods
        self.machine_manager.restart_machine(db, machine.id)
    
    async def _shutdown_machine(self, db: Session, machine: Machine):
        """Shutdown machine"""
        # Implementation depends on how machines are shut down
        self.machine_manager.shutdown_machine(db, machine.id)
    
    async def _wake_machine(self, db: Session, machine: Machine):
        """Wake machine using Wake-on-LAN"""
        # Implementation for Wake-on-LAN
        self.machine_manager.wake_machine(db, machine.id)
    
    async def _turn_on_machine(self, db: Session, machine: Machine):
        """Turn on machine"""
        # Implementation for turning on machine
        self.machine_manager.turn_on_machine(db, machine.id)
    
    def get_batch_operation_status(
        self,
        db: Session,
        operation_id: int
    ) -> Dict[str, Any]:
        """
        Get batch operation status
        
        Args:
            db: Database session
            operation_id: Batch operation ID
            
        Returns:
            Batch operation status
        """
        batch_op = db.query(BatchOperation).filter(BatchOperation.id == operation_id).first()
        if not batch_op:
            raise NotFoundError(f"Batch operation {operation_id} not found")
        
        # Get machine details
        machines = db.query(BatchOperationMachine).filter(
            BatchOperationMachine.batch_operation_id == operation_id
        ).all()
        
        return {
            "operation_id": batch_op.id,
            "operation_type": batch_op.operation_type,
            "status": batch_op.status,
            "total_machines": batch_op.total_machines,
            "completed_machines": batch_op.completed_machines,
            "failed_machines": batch_op.failed_machines,
            "progress": (batch_op.completed_machines + batch_op.failed_machines) / batch_op.total_machines * 100 if batch_op.total_machines > 0 else 0,
            "created_at": batch_op.created_at.isoformat() if batch_op.created_at else None,
            "started_at": batch_op.started_at.isoformat() if batch_op.started_at else None,
            "completed_at": batch_op.completed_at.isoformat() if batch_op.completed_at else None,
            "machines": [
                {
                    "machine_id": m.machine_id,
                    "status": m.status,
                    "error_message": m.error_message
                }
                for m in machines
            ]
        }
```

### 2. Machine Manager Extensions (`app/backend/machines/machine_manager.py`)

```python
# Dodati metode u MachineManager klasu

def restart_machine(self, db: Session, machine_id: int) -> Machine:
    """
    Restart machine
    
    Args:
        db: Database session
        machine_id: Machine ID
        
    Returns:
        Updated machine
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise NotFoundError(f"Machine {machine_id} not found")
    
    # Implementation for restart
    # This could use Wake-on-LAN, iSCSI commands, or other methods
    # For now, just update status
    machine.status = 'booting'
    db.commit()
    
    return machine

def shutdown_machine(self, db: Session, machine_id: int) -> Machine:
    """
    Shutdown machine
    
    Args:
        db: Database session
        machine_id: Machine ID
        
    Returns:
        Updated machine
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise NotFoundError(f"Machine {machine_id} not found")
    
    # Implementation for shutdown
    # This could use iSCSI commands or other methods
    machine.status = 'offline'
    db.commit()
    
    return machine

def wake_machine(self, db: Session, machine_id: int) -> Machine:
    """
    Wake machine using Wake-on-LAN
    
    Args:
        db: Database session
        machine_id: Machine ID
        
    Returns:
        Updated machine
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise NotFoundError(f"Machine {machine_id} not found")
    
    # Implementation for Wake-on-LAN
    # Use wakeonlan library or subprocess
    import subprocess
    subprocess.run(['wakeonlan', machine.mac_address])
    
    machine.status = 'booting'
    db.commit()
    
    return machine

def turn_on_machine(self, db: Session, machine_id: int) -> Machine:
    """
    Turn on machine
    
    Args:
        db: Database session
        machine_id: Machine ID
        
    Returns:
        Updated machine
    """
    # Similar to wake_machine, but might use different method
    return self.wake_machine(db, machine_id)
```

### 3. API Endpoints (`app/backend/api/machines.py`)

```python
# Dodati u postojeći machines.py

from app.backend.machines.batch_operations import BatchOperationsManager
from app.backend.auth.dependencies import get_current_user

batch_ops_manager = BatchOperationsManager()


class BatchOperationRequest(BaseModel):
    """Batch operation request"""
    machine_ids: List[int]
    operation_type: str  # 'restart', 'shutdown', 'wake', 'turnOn'


class BulkActionRequest(BaseModel):
    """Bulk action request"""
    machine_ids: List[int]


@router.post("/batch")
async def batch_operations(
    request: BatchOperationRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Execute batch operation on multiple machines
    
    Args:
        request: Batch operation request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Batch operation result
    """
    try:
        result = await batch_ops_manager.execute_batch_operation(
            db=db,
            machine_ids=request.machine_ids,
            operation_type=request.operation_type,
            user_id=current_user.id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/restart")
async def bulk_restart(
    request: BulkActionRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Bulk restart machines
    
    Args:
        request: Bulk action request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Batch operation result
    """
    return await batch_operations(
        request=BatchOperationRequest(
            machine_ids=request.machine_ids,
            operation_type='restart'
        ),
        current_user=current_user,
        db=db
    )


@router.post("/shutdown")
async def bulk_shutdown(
    request: BulkActionRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Bulk shutdown machines
    
    Args:
        request: Bulk action request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Batch operation result
    """
    return await batch_operations(
        request=BatchOperationRequest(
            machine_ids=request.machine_ids,
            operation_type='shutdown'
        ),
        current_user=current_user,
        db=db
    )


@router.post("/wake")
async def bulk_wake(
    request: BulkActionRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Bulk wake machines
    
    Args:
        request: Bulk action request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Batch operation result
    """
    return await batch_operations(
        request=BatchOperationRequest(
            machine_ids=request.machine_ids,
            operation_type='wake'
        ),
        current_user=current_user,
        db=db
    )


@router.post("/turnOn")
async def bulk_turn_on(
    request: BulkActionRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Bulk turn on machines
    
    Args:
        request: Bulk action request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Batch operation result
    """
    return await batch_operations(
        request=BatchOperationRequest(
            machine_ids=request.machine_ids,
            operation_type='turnOn'
        ),
        current_user=current_user,
        db=db
    )


@router.get("/batch/{operation_id}")
async def get_batch_operation_status(
    operation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get batch operation status
    
    Args:
        operation_id: Batch operation ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Batch operation status
    """
    try:
        return batch_ops_manager.get_batch_operation_status(db, operation_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

---

## 🧪 Test Plan

### Unit Tests

1. **Batch Operations Manager Tests**
   - Test batch operation creation
   - Test operation execution
   - Test error handling
   - Test progress tracking

2. **Machine Manager Tests**
   - Test restart_machine
   - Test shutdown_machine
   - Test wake_machine
   - Test turn_on_machine

### Integration Tests

1. **Batch Operations Flow**
   - Test bulk restart
   - Test bulk shutdown
   - Test bulk wake
   - Test bulk turn on
   - Test error scenarios

2. **WebSocket Integration**
   - Test progress updates
   - Test completion notifications
   - Test error notifications

### Performance Tests

1. **Large Batch Operations**
   - Test with 100+ machines
   - Test concurrent operations
   - Test timeout handling

---

## 📦 Dependencies

### Python Packages

```txt
wakeonlan>=2.1.0  # Wake-on-LAN support (opciono)
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add batch operations tables"

# Apply migration
alembic upgrade head
```

---

## ✅ Checklist

### Setup
- [ ] Install dependencies
- [ ] Create database migrations
- [ ] Setup WebSocket hub

### Implementation
- [ ] Batch Operations Manager
- [ ] Machine Manager extensions
- [ ] API Endpoints
- [ ] WebSocket events

### Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] Performance tests

### Documentation
- [ ] API documentation
- [ ] WebSocket events documentation

---

*Plan kreiran za Bulk Operations - Machines implementaciju.*

