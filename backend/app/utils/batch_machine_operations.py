"""
Batch Machine Operations Manager - Async version
Handles bulk operations on machines (restart, shutdown, wake, turn-on)
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.models.batch_operation import (
    BatchOperation, BatchMachineOperation, BatchOperationType, BatchOperationStatus
)
from app.models.machine import Machine

logger = structlog.get_logger()


class BatchMachineOperationsManager:
    """Manages batch operations on machines"""
    
    def __init__(self, db: AsyncSession, websocket_manager=None):
        """
        Initialize batch operations manager
        
        Args:
            db: Async database session
            websocket_manager: Optional WebSocket event manager
        """
        self.db = db
        self.websocket_manager = websocket_manager
        self.active_operations: Dict[int, asyncio.Task] = {}
    
    async def execute_batch_operation(
        self,
        operation_type: BatchOperationType,
        machine_ids: List[int],
        created_by: int = 1
    ) -> BatchOperation:
        """
        Execute batch operation on multiple machines
        
        Args:
            operation_type: Type of operation to perform
            machine_ids: List of machine IDs
            created_by: User ID who created the operation
            
        Returns:
            BatchOperation instance
        """
        # Create batch operation record
        batch_op = BatchOperation(
            operation_type=operation_type,
            status=BatchOperationStatus.PENDING,
            total_items=len(machine_ids),
            completed_items=0,
            failed_items=0,
            created_by=created_by
        )
        
        self.db.add(batch_op)
        await self.db.flush()
        
        # Create batch operation machine records
        for machine_id in machine_ids:
            batch_op_machine = BatchMachineOperation(
                batch_operation_id=batch_op.id,
                machine_id=machine_id,
                status=BatchOperationStatus.PENDING,
            )
            self.db.add(batch_op_machine)
        
        await self.db.commit()
        await self.db.refresh(batch_op)
        
        # Start operation in background task
        task = asyncio.create_task(
            self._execute_operation_task(batch_op.id, operation_type, machine_ids)
        )
        self.active_operations[batch_op.id] = task
        
        return batch_op
    
    async def _execute_operation_task(
        self,
        batch_op_id: int,
        operation_type: BatchOperationType,
        machine_ids: List[int]
    ):
        """Execute operation in background task"""
        try:
            # Update status to running
            stmt = select(BatchOperation).where(BatchOperation.id == batch_op_id)
            result = await self.db.execute(stmt)
            batch_op = result.scalar_one_or_none()
            
            if not batch_op:
                return
            
            batch_op.status = BatchOperationStatus.RUNNING
            batch_op.started_at = datetime.utcnow()
            await self.db.commit()
            
            # Emit WebSocket event for operation start
            if self.websocket_manager:
                try:
                    await self.websocket_manager.broadcast({
                        'type': 'batch_operation_start',
                        'operation_id': batch_op_id,
                        'operation_type': operation_type.value,
                        'total_items': batch_op.total_items
                    })
                except Exception as e:
                    logger.warning("Failed to emit WebSocket event", error=str(e))
            
            # Execute operation on each machine
            for machine_id in machine_ids:
                # Get machine
                stmt = select(Machine).where(Machine.id == machine_id)
                result = await self.db.execute(stmt)
                machine = result.scalar_one_or_none()
                
                if not machine:
                    continue
                
                # Get batch operation machine record
                stmt = select(BatchMachineOperation).where(
                    BatchMachineOperation.batch_operation_id == batch_op_id,
                    BatchMachineOperation.machine_id == machine_id
                )
                result = await self.db.execute(stmt)
                batch_op_machine = result.scalar_one_or_none()
                
                if not batch_op_machine:
                    continue
                
                # Execute operation
                success, error = await self._execute_single_operation(operation_type, machine)
                
                # Update batch operation machine status
                if success:
                    batch_op_machine.status = BatchOperationStatus.COMPLETED
                    batch_op_machine.completed_at = datetime.utcnow()
                    batch_op.completed_items += 1
                else:
                    batch_op_machine.status = BatchOperationStatus.FAILED
                    batch_op_machine.error_message = error
                    batch_op.failed_items += 1
                    batch_op.completed_items += 1
                
                await self.db.commit()
                
                # Emit WebSocket event for progress update
                if self.websocket_manager:
                    try:
                        await self.websocket_manager.broadcast({
                            'type': 'batch_operation_progress',
                            'operation_id': batch_op_id,
                            'completed_items': batch_op.completed_items,
                            'failed_items': batch_op.failed_items,
                            'total_items': batch_op.total_items
                        })
                    except Exception as e:
                        logger.warning("Failed to emit WebSocket event", error=str(e))
                
                # Small delay between operations
                await asyncio.sleep(0.5)
            
            # Update batch operation status
            batch_op.status = BatchOperationStatus.COMPLETED
            batch_op.completed_at = datetime.utcnow()
            await self.db.commit()
            
            # Emit WebSocket event for operation complete
            if self.websocket_manager:
                try:
                    await self.websocket_manager.broadcast({
                        'type': 'batch_operation_complete',
                        'operation_id': batch_op_id,
                        'completed_items': batch_op.completed_items,
                        'failed_items': batch_op.failed_items,
                        'total_items': batch_op.total_items
                    })
                except Exception as e:
                    logger.warning("Failed to emit WebSocket event", error=str(e))
            
            logger.info("Batch machine operation completed", batch_op_id=batch_op_id)
            
        except Exception as e:
            logger.error("Batch machine operation failed", batch_op_id=batch_op_id, error=str(e))
            # Mark operation as failed
            stmt = select(BatchOperation).where(BatchOperation.id == batch_op_id)
            result = await self.db.execute(stmt)
            batch_op = result.scalar_one_or_none()
            if batch_op:
                batch_op.status = BatchOperationStatus.FAILED
                batch_op.error_message = str(e)
                await self.db.commit()
        finally:
            # Remove from active operations
            if batch_op_id in self.active_operations:
                del self.active_operations[batch_op_id]
    
    async def _execute_single_operation(
        self,
        operation_type: BatchOperationType,
        machine: Machine
    ) -> Tuple[bool, Optional[str]]:
        """Execute single operation on a machine"""
        try:
            if operation_type == BatchOperationType.MACHINE_RESTART:
                return await self._restart_machine(machine)
            elif operation_type == BatchOperationType.MACHINE_SHUTDOWN:
                return await self._shutdown_machine(machine)
            elif operation_type == BatchOperationType.MACHINE_WAKE:
                return await self._wake_machine(machine)
            elif operation_type == BatchOperationType.MACHINE_TURN_ON:
                return await self._turn_on_machine(machine)
            else:
                return False, f"Unknown operation type: {operation_type}"
        except Exception as e:
            return False, str(e)
    
    async def _restart_machine(self, machine: Machine) -> Tuple[bool, Optional[str]]:
        """Restart a machine"""
        if not machine.ip_address:
            return False, "Machine IP address not set"
        
        try:
            # TODO: Implement actual restart logic
            # For now, simulate operation
            await asyncio.sleep(1)
            return True, None
        except Exception as e:
            return False, f"Failed to restart machine: {str(e)}"
    
    async def _shutdown_machine(self, machine: Machine) -> Tuple[bool, Optional[str]]:
        """Shutdown a machine"""
        if not machine.ip_address:
            return False, "Machine IP address not set"
        
        try:
            # TODO: Implement actual shutdown logic
            await asyncio.sleep(1)
            return True, None
        except Exception as e:
            return False, f"Failed to shutdown machine: {str(e)}"
    
    async def _wake_machine(self, machine: Machine) -> Tuple[bool, Optional[str]]:
        """Wake a machine using Wake-on-LAN"""
        if not machine.mac_address:
            return False, "Machine MAC address not set"
        
        try:
            # TODO: Implement Wake-on-LAN
            await asyncio.sleep(1)
            return True, None
        except Exception as e:
            return False, f"Failed to wake machine: {str(e)}"
    
    async def _turn_on_machine(self, machine: Machine) -> Tuple[bool, Optional[str]]:
        """Turn on a machine"""
        # Similar to wake, but may use IPMI or other power management
        return await self._wake_machine(machine)
    
    async def get_operation_status(self, operation_id: int) -> Optional[Dict]:
        """Get status of a batch operation"""
        stmt = select(BatchOperation).where(BatchOperation.id == operation_id)
        result = await self.db.execute(stmt)
        batch_op = result.scalar_one_or_none()
        
        if not batch_op:
            return None
        
        # Get machine details
        stmt = select(BatchMachineOperation).where(
            BatchMachineOperation.batch_operation_id == operation_id
        )
        result = await self.db.execute(stmt)
        machines = result.scalars().all()
        
        return {
            'id': batch_op.id,
            'operation_type': batch_op.operation_type.value,
            'status': batch_op.status.value,
            'total_items': batch_op.total_items,
            'completed_items': batch_op.completed_items,
            'failed_items': batch_op.failed_items,
            'created_at': batch_op.created_at.isoformat() if batch_op.created_at else None,
            'started_at': batch_op.started_at.isoformat() if batch_op.started_at else None,
            'completed_at': batch_op.completed_at.isoformat() if batch_op.completed_at else None,
            'error_message': batch_op.error_message,
            'machines': [{
                'machine_id': m.machine_id,
                'status': m.status.value,
                'error_message': m.error_message,
                'completed_at': m.completed_at.isoformat() if m.completed_at else None
            } for m in machines]
        }
    
    async def cancel_operation(self, operation_id: int) -> bool:
        """Cancel a running operation"""
        stmt = select(BatchOperation).where(BatchOperation.id == operation_id)
        result = await self.db.execute(stmt)
        batch_op = result.scalar_one_or_none()
        
        if not batch_op:
            return False
        
        if batch_op.status not in [BatchOperationStatus.PENDING, BatchOperationStatus.RUNNING]:
            return False
        
        batch_op.status = BatchOperationStatus.CANCELLED
        await self.db.commit()
        
        # Cancel background task if running
        if operation_id in self.active_operations:
            task = self.active_operations[operation_id]
            task.cancel()
            del self.active_operations[operation_id]
        
        return True




