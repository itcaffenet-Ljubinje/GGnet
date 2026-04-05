"""
Server commands API endpoints
Provides endpoints for executing and monitoring server commands
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import structlog
import subprocess
import uuid
from datetime import datetime
from enum import Enum

from app.core.dependencies import get_db, get_current_user, require_operator
from app.models.user import User

router = APIRouter(prefix="/server/commands", tags=["server-commands"])
logger = structlog.get_logger()

# In-memory command execution tracking (in production, use database)
_command_executions: Dict[str, Dict[str, Any]] = {}


class CommandStatus(str, Enum):
    """Command execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CommandRequest(BaseModel):
    """Command execution request"""
    command: str
    args: Optional[List[str]] = None
    timeout: Optional[int] = 30
    working_directory: Optional[str] = None


class CommandResponse(BaseModel):
    """Command execution response"""
    id: str
    command: str
    status: str
    return_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    duration_ms: Optional[float] = None


@router.get("", response_model=List[Dict[str, Any]])
async def list_commands(
    limit: int = 50,
    current_user: User = Depends(require_operator)
):
    """
    List available server commands and recent executions
    """
    try:
        # Return recent command executions
        recent_commands = list(_command_executions.values())[-limit:]
        return recent_commands
    except Exception as e:
        logger.error("Failed to list commands", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list commands: {str(e)}"
        )


@router.post("/run", response_model=CommandResponse)
async def run_command(
    request: CommandRequest,
    current_user: User = Depends(require_operator)
):
    """
    Execute a shell command
    """
    try:
        command_id = str(uuid.uuid4())
        started_at = datetime.now()
        
        # Build command
        cmd = [request.command]
        if request.args:
            cmd.extend(request.args)
        
        # Store command execution info
        execution_info = {
            "id": command_id,
            "command": " ".join(cmd),
            "status": CommandStatus.RUNNING.value,
            "started_at": started_at.isoformat(),
            "user_id": current_user.id,
            "username": current_user.username
        }
        _command_executions[command_id] = execution_info
        
        # Execute command
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=request.timeout or 30,
                cwd=request.working_directory,
                check=False
            )
            
            completed_at = datetime.now()
            duration_ms = (completed_at - started_at).total_seconds() * 1000
            
            execution_info.update({
                "status": CommandStatus.COMPLETED.value if result.returncode == 0 else CommandStatus.FAILED.value,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "completed_at": completed_at.isoformat(),
                "duration_ms": duration_ms
            })
            
            logger.info(
                "Command executed",
                command_id=command_id,
                command=execution_info["command"],
                return_code=result.returncode,
                duration_ms=duration_ms
            )
            
            return CommandResponse(**execution_info)
            
        except subprocess.TimeoutExpired:
            completed_at = datetime.now()
            execution_info.update({
                "status": CommandStatus.FAILED.value,
                "return_code": -1,
                "stderr": f"Command timed out after {request.timeout or 30} seconds",
                "completed_at": completed_at.isoformat()
            })
            return CommandResponse(**execution_info)
            
        except Exception as e:
            completed_at = datetime.now()
            execution_info.update({
                "status": CommandStatus.FAILED.value,
                "return_code": -1,
                "stderr": str(e),
                "completed_at": completed_at.isoformat()
            })
            return CommandResponse(**execution_info)
            
    except Exception as e:
        logger.error("Failed to run command", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run command: {str(e)}"
        )


@router.get("/{command_id}", response_model=CommandResponse)
async def get_command_status(
    command_id: str,
    current_user: User = Depends(require_operator)
):
    """
    Get status of a command execution
    """
    try:
        if command_id not in _command_executions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Command execution {command_id} not found"
            )
        
        return CommandResponse(**_command_executions[command_id])
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get command status", command_id=command_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get command status: {str(e)}"
        )


@router.post("/{command_id}/cancel", response_model=Dict[str, Any])
async def cancel_command(
    command_id: str,
    current_user: User = Depends(require_operator)
):
    """
    Cancel a running command (if possible)
    """
    try:
        if command_id not in _command_executions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Command execution {command_id} not found"
            )
        
        execution_info = _command_executions[command_id]
        
        if execution_info["status"] not in [CommandStatus.PENDING.value, CommandStatus.RUNNING.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Command is not in a cancellable state: {execution_info['status']}"
            )
        
        execution_info["status"] = CommandStatus.CANCELLED.value
        execution_info["completed_at"] = datetime.now().isoformat()
        
        logger.info("Command cancelled", command_id=command_id, user_id=current_user.id)
        
        return {
            "id": command_id,
            "status": "cancelled",
            "message": f"Command {command_id} cancelled"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel command", command_id=command_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel command: {str(e)}"
        )


@router.get("/lastExecution", response_model=Optional[CommandResponse])
async def get_last_execution(
    current_user: User = Depends(require_operator)
):
    """
    Get the last command execution
    """
    try:
        if not _command_executions:
            return None
        
        last_execution = max(_command_executions.values(), key=lambda x: x["started_at"])
        return CommandResponse(**last_execution)
    except Exception as e:
        logger.error("Failed to get last execution", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get last execution: {str(e)}"
        )

