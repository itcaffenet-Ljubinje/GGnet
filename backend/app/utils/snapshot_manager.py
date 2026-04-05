"""
Snapshot Manager - Async version
Manages image snapshots with retention policies and scheduling.
"""

import os
import subprocess
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sql_func
import structlog

from app.models.snapshot import Snapshot, RetentionPolicy
from app.models.image import Image
from app.models.machine import Machine

logger = structlog.get_logger()


class SnapshotManager:
    """Manages image snapshots"""
    
    def __init__(self, db: AsyncSession, snapshots_dir: Optional[str] = None):
        """
        Initialize Snapshot Manager
        
        Args:
            db: Async database session
            snapshots_dir: Base directory for snapshots (optional)
        """
        self.db = db
        self.snapshots_dir = snapshots_dir or "/var/lib/ggnet/snapshots"
        os.makedirs(self.snapshots_dir, exist_ok=True)
    
    async def create_snapshot(
        self, 
        image_id: int, 
        machine_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> Snapshot:
        """
        Create a snapshot of an image
        
        Args:
            image_id: Image ID
            machine_id: Optional machine ID
            description: Optional description
            
        Returns:
            Created Snapshot instance
        """
        # Get image
        stmt = select(Image).where(Image.id == image_id)
        result = await self.db.execute(stmt)
        image = result.scalar_one_or_none()
        
        if not image:
            raise ValueError(f"Image {image_id} not found")
        
        # Get machine if provided
        machine = None
        if machine_id:
            stmt = select(Machine).where(Machine.id == machine_id)
            result = await self.db.execute(stmt)
            machine = result.scalar_one_or_none()
            
            if not machine:
                raise ValueError(f"Machine {machine_id} not found")
        
        # Check if base image exists
        if not os.path.exists(image.file_path):
            raise FileNotFoundError(f"Image file not found: {image.file_path}")
        
        # Generate snapshot name
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        machine_name = machine.name if machine else "global"
        snapshot_name = f"{machine_name}_{image.name}_{timestamp}.qcow2"
        
        # Create snapshot directory structure
        image_type_dir = image.image_type.value if hasattr(image.image_type, 'value') else str(image.image_type)
        snapshots_dir = os.path.join(self.snapshots_dir, image_type_dir)
        os.makedirs(snapshots_dir, exist_ok=True)
        
        snapshot_path = os.path.join(snapshots_dir, snapshot_name)
        
        # Create snapshot using qemu-img
        try:
            result = subprocess.run(
                ['qemu-img', 'create', '-f', 'qcow2', '-b', image.file_path, 
                 '-F', image.format.value if hasattr(image.format, 'value') else str(image.format), 
                 snapshot_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                raise RuntimeError(f"Failed to create snapshot: {result.stderr}")
        except FileNotFoundError:
            logger.warning("qemu-img not found, creating placeholder snapshot file")
            # Fallback: create empty file if qemu-img not available
            Path(snapshot_path).touch()
        except Exception as e:
            logger.error("Failed to create snapshot file", error=str(e))
            raise
        
        # Create snapshot record
        snapshot = Snapshot(
            image_id=image_id,
            machine_id=machine_id,
            snapshot_path=snapshot_path,
            description=description or f"Snapshot of {image.name}" + (f" for {machine.name}" if machine else ""),
        )
        
        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)
        
        return snapshot
    
    async def delete_snapshot(self, snapshot_id: int) -> bool:
        """
        Delete a snapshot
        
        Args:
            snapshot_id: Snapshot ID
            
        Returns:
            True if deleted successfully
        """
        stmt = select(Snapshot).where(Snapshot.id == snapshot_id)
        result = await self.db.execute(stmt)
        snapshot = result.scalar_one_or_none()
        
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")
        
        # Delete snapshot file if it exists
        if os.path.exists(snapshot.snapshot_path):
            try:
                os.remove(snapshot.snapshot_path)
            except Exception as e:
                logger.warning("Failed to delete snapshot file", path=snapshot.snapshot_path, error=str(e))
        
        # Delete snapshot record
        await self.db.delete(snapshot)
        await self.db.commit()
        
        return True
    
    async def list_snapshots(
        self,
        image_id: Optional[int] = None,
        machine_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Snapshot]:
        """
        List snapshots with filters
        
        Args:
            image_id: Filter by image ID
            machine_id: Filter by machine ID
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of Snapshot instances
        """
        stmt = select(Snapshot)
        
        if image_id:
            stmt = stmt.where(Snapshot.image_id == image_id)
        
        if machine_id:
            stmt = stmt.where(Snapshot.machine_id == machine_id)
        
        if start_date:
            stmt = stmt.where(Snapshot.timestamp >= start_date)
        
        if end_date:
            stmt = stmt.where(Snapshot.timestamp <= end_date)
        
        stmt = stmt.order_by(Snapshot.timestamp.desc())
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_snapshot_stats(
        self,
        image_id: Optional[int] = None,
        machine_id: Optional[int] = None
    ) -> Dict:
        """
        Get snapshot statistics
        
        Args:
            image_id: Filter by image ID
            machine_id: Filter by machine ID
            
        Returns:
            Statistics dict
        """
        stmt = select(Snapshot)
        
        if image_id:
            stmt = stmt.where(Snapshot.image_id == image_id)
        
        if machine_id:
            stmt = stmt.where(Snapshot.machine_id == machine_id)
        
        # Get count
        count_stmt = select(sql_func.count()).select_from(stmt.subquery())
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0
        
        # Get oldest and newest snapshots
        oldest_stmt = stmt.order_by(Snapshot.timestamp.asc()).limit(1)
        newest_stmt = stmt.order_by(Snapshot.timestamp.desc()).limit(1)
        
        result = await self.db.execute(oldest_stmt)
        oldest = result.scalar_one_or_none()
        
        result = await self.db.execute(newest_stmt)
        newest = result.scalar_one_or_none()
        
        # Calculate total size
        all_snapshots = await self.list_snapshots(image_id=image_id, machine_id=machine_id, limit=10000)
        total_size = 0
        for snapshot in all_snapshots:
            if os.path.exists(snapshot.snapshot_path):
                try:
                    total_size += os.path.getsize(snapshot.snapshot_path)
                except Exception:
                    pass
        
        return {
            "total": total,
            "oldest_timestamp": oldest.timestamp.isoformat() if oldest else None,
            "newest_timestamp": newest.timestamp.isoformat() if newest else None,
            "total_size_bytes": total_size
        }
    
    async def apply_retention_policy(
        self,
        image_id: Optional[int] = None,
        machine_id: Optional[int] = None,
        policy: RetentionPolicy = RetentionPolicy.KEEP_LAST_N,
        policy_value: Optional[int] = None
    ) -> int:
        """
        Apply retention policy to snapshots
        
        Args:
            image_id: Filter by image ID
            machine_id: Filter by machine ID
            policy: Retention policy to apply
            policy_value: Policy value (e.g., N for KEEP_LAST_N, days for KEEP_DAYS)
            
        Returns:
            Number of snapshots deleted
        """
        snapshots = await self.list_snapshots(image_id=image_id, machine_id=machine_id, limit=10000)
        
        if not snapshots:
            return 0
        
        deleted_count = 0
        
        if policy == RetentionPolicy.KEEP_LAST_N:
            # Keep last N snapshots
            n = policy_value or 10
            if len(snapshots) > n:
                to_delete = snapshots[n:]
                for snapshot in to_delete:
                    try:
                        await self.delete_snapshot(snapshot.id)
                        deleted_count += 1
                    except Exception as e:
                        logger.warning("Failed to delete snapshot", snapshot_id=snapshot.id, error=str(e))
        
        elif policy == RetentionPolicy.KEEP_DAYS:
            # Keep snapshots for N days
            days = policy_value or 30
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            for snapshot in snapshots:
                if snapshot.timestamp < cutoff_date:
                    try:
                        await self.delete_snapshot(snapshot.id)
                        deleted_count += 1
                    except Exception as e:
                        logger.warning("Failed to delete snapshot", snapshot_id=snapshot.id, error=str(e))
        
        elif policy == RetentionPolicy.KEEP_DAILY:
            # Keep one snapshot per day
            snapshots_by_date: Dict = {}
            for snapshot in snapshots:
                date_key = snapshot.timestamp.date()
                if date_key not in snapshots_by_date:
                    snapshots_by_date[date_key] = []
                snapshots_by_date[date_key].append(snapshot)
            
            for date_key, date_snapshots in snapshots_by_date.items():
                # Keep the newest snapshot for each day
                date_snapshots.sort(key=lambda s: s.timestamp, reverse=True)
                to_delete = date_snapshots[1:]
                for snapshot in to_delete:
                    try:
                        await self.delete_snapshot(snapshot.id)
                        deleted_count += 1
                    except Exception as e:
                        logger.warning("Failed to delete snapshot", snapshot_id=snapshot.id, error=str(e))
        
        elif policy == RetentionPolicy.KEEP_WEEKLY:
            # Keep one snapshot per week
            snapshots_by_week: Dict = {}
            for snapshot in snapshots:
                week_key = snapshot.timestamp.isocalendar()[:2]  # (year, week)
                if week_key not in snapshots_by_week:
                    snapshots_by_week[week_key] = []
                snapshots_by_week[week_key].append(snapshot)
            
            for week_key, week_snapshots in snapshots_by_week.items():
                # Keep the newest snapshot for each week
                week_snapshots.sort(key=lambda s: s.timestamp, reverse=True)
                to_delete = week_snapshots[1:]
                for snapshot in to_delete:
                    try:
                        await self.delete_snapshot(snapshot.id)
                        deleted_count += 1
                    except Exception as e:
                        logger.warning("Failed to delete snapshot", snapshot_id=snapshot.id, error=str(e))
        
        elif policy == RetentionPolicy.KEEP_MONTHLY:
            # Keep one snapshot per month
            snapshots_by_month: Dict = {}
            for snapshot in snapshots:
                month_key = (snapshot.timestamp.year, snapshot.timestamp.month)
                if month_key not in snapshots_by_month:
                    snapshots_by_month[month_key] = []
                snapshots_by_month[month_key].append(snapshot)
            
            for month_key, month_snapshots in snapshots_by_month.items():
                # Keep the newest snapshot for each month
                month_snapshots.sort(key=lambda s: s.timestamp, reverse=True)
                to_delete = month_snapshots[1:]
                for snapshot in to_delete:
                    try:
                        await self.delete_snapshot(snapshot.id)
                        deleted_count += 1
                    except Exception as e:
                        logger.warning("Failed to delete snapshot", snapshot_id=snapshot.id, error=str(e))
        
        return deleted_count




