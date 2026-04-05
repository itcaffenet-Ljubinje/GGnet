# Database models
# app/models/__init__.py

# Import glavnih modela
from .audit import AuditLog
from .user import User
from .image import Image
from .machine import Machine
from .session import Session
from .target import Target
from .writeback import Writeback
from .snapshot import Snapshot, RetentionPolicy
from .scheduled_job import ScheduledJob, JobExecution, JobType, JobStatus, ExecutionStatus
from .batch_operation import BatchOperation, BatchImageOperation, BatchMachineOperation, BatchOperationType, BatchOperationStatus
from .vm import VM, VMStatus
from .client import Client, ClientStatus
from .boot_event import BootEvent, BootEventType, BootEventStatus

# Napravi __all__ za lakši import
__all__ = [
    "AuditLog",
    "User",
    "Image",
    "Machine",
    "Session",
    "Target",
    "Writeback",
    "Snapshot",
    "RetentionPolicy",
    "ScheduledJob",
    "JobExecution",
    "JobType",
    "JobStatus",
    "ExecutionStatus",
    "BatchOperation",
    "BatchImageOperation",
    "BatchMachineOperation",
    "BatchOperationType",
    "BatchOperationStatus",
    "VM",
    "VMStatus",
    "Client",
    "ClientStatus",
    "BootEvent",
    "BootEventType",
    "BootEventStatus",
]

