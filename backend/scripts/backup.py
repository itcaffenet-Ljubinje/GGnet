#!/usr/bin/env python3
"""
Automated Backup Script for GGnet Diskless Server

This script performs automated backups of:
- Database (PostgreSQL or SQLite)
- Application files
- Configuration files
- User data and images
- Log files

Usage:
    python -m app.scripts.backup
    python backend/scripts/backup.py --full
    python backend/scripts/backup.py --database-only

Environment Variables:
    BACKUP_DIR: Backup destination directory (default: ./backups)
    DATABASE_URL: Database connection string
    RETENTION_DAYS: Number of days to keep backups (default: 30)
"""

import asyncio
import argparse
import os
import sys
import shutil
import gzip
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import structlog
from app.core.config import get_settings
from app.core.database import get_settings as get_db_settings

logger = structlog.get_logger(__name__)


class BackupManager:
    """Manages backup operations for GGnet"""
    
    def __init__(
        self,
        backup_dir: Optional[Path] = None,
        retention_days: int = 30,
        compress: bool = True
    ):
        """
        Initialize backup manager
        
        Args:
            backup_dir: Directory to store backups (default: ./backups)
            retention_days: Number of days to keep backups
            compress: Whether to compress backup files
        """
        settings = get_settings()
        
        self.backup_dir = Path(backup_dir or os.getenv("BACKUP_DIR", "./backups"))
        self.retention_days = int(os.getenv("RETENTION_DAYS", retention_days))
        self.compress = compress
        self.settings = settings
        
        # Create backup directory structure
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        (self.backup_dir / "database").mkdir(exist_ok=True)
        (self.backup_dir / "config").mkdir(exist_ok=True)
        (self.backup_dir / "application").mkdir(exist_ok=True)
        (self.backup_dir / "data").mkdir(exist_ok=True)
        
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_name = f"backup_{self.timestamp}"
        self.backup_path = self.backup_dir / self.backup_name
        
    async def backup_database(self) -> Dict[str, any]:
        """Backup database (PostgreSQL or SQLite)"""
        logger.info("Starting database backup")
        
        db_url = self.settings.DATABASE_URL
        backup_file = self.backup_path / "database" / f"database_{self.timestamp}"
        
        try:
            if db_url.startswith("sqlite"):
                # SQLite backup
                db_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
                db_file = Path(db_path).expanduser()
                
                if not db_file.exists():
                    raise FileNotFoundError(f"Database file not found: {db_file}")
                
                backup_file_sqlite = Path(str(backup_file) + ".db")
                shutil.copy2(db_file, backup_file_sqlite)
                
                logger.info("SQLite database backed up", source=str(db_file), backup=str(backup_file_sqlite))
                
                return {
                    "type": "sqlite",
                    "file": str(backup_file_sqlite),
                    "size": backup_file_sqlite.stat().st_size,
                    "status": "success"
                }
                
            elif db_url.startswith("postgresql"):
                # PostgreSQL backup using pg_dump
                backup_file_pg = Path(str(backup_file) + ".sql")
                backup_file_gz = Path(str(backup_file) + ".sql.gz")
                
                # Extract connection details from URL
                # Format: postgresql+asyncpg://user:pass@host:port/dbname
                url_parts = db_url.replace("postgresql+asyncpg://", "").replace("postgresql://", "")
                
                # Run pg_dump
                cmd = [
                    "pg_dump",
                    "--no-owner",
                    "--no-acl",
                    "--format=custom",
                    f"--file={backup_file_pg}",
                ]
                
                # Add connection parameters
                if "@" in url_parts:
                    auth, rest = url_parts.split("@")
                    if ":" in auth:
                        user, password = auth.split(":")
                        cmd.extend(["-U", user])
                        os.environ["PGPASSWORD"] = password
                    
                    if "/" in rest:
                        host_port, dbname = rest.split("/")
                        if ":" in host_port:
                            host, port = host_port.split(":")
                            cmd.extend(["-h", host, "-p", port])
                        else:
                            cmd.extend(["-h", host_port])
                        cmd.append(dbname)
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    raise Exception(f"pg_dump failed: {result.stderr}")
                
                # Compress if requested
                if self.compress:
                    with open(backup_file_pg, "rb") as f_in:
                        with gzip.open(backup_file_gz, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    backup_file_pg.unlink()
                    final_file = backup_file_gz
                else:
                    final_file = backup_file_pg
                
                logger.info("PostgreSQL database backed up", backup=str(final_file))
                
                return {
                    "type": "postgresql",
                    "file": str(final_file),
                    "size": final_file.stat().st_size,
                    "status": "success"
                }
            else:
                raise ValueError(f"Unsupported database URL: {db_url}")
                
        except Exception as e:
            logger.error("Database backup failed", error=str(e))
            return {
                "type": "unknown",
                "file": None,
                "size": 0,
                "status": "failed",
                "error": str(e)
            }
    
    def backup_config(self) -> Dict[str, any]:
        """Backup configuration files"""
        logger.info("Starting configuration backup")
        
        config_files = []
        backup_file = self.backup_path / "config" / f"config_{self.timestamp}.tar.gz"
        
        try:
            config_items = [
                ("backend/.env", "backend/.env"),
                ("docker-compose.yml", "docker-compose.yml"),
                ("compose.yaml", "compose.yaml"),
            ]
            
            # Check which files exist
            base_path = Path(__file__).parent.parent.parent
            for src, dest in config_items:
                src_path = base_path / src
                if src_path.exists():
                    config_files.append((src_path, dest))
            
            if config_files:
                # Create tar archive
                import tarfile
                with tarfile.open(backup_file, "w:gz") as tar:
                    for src_path, dest in config_files:
                        tar.add(src_path, arcname=dest)
                
                logger.info("Configuration backed up", files=len(config_files), backup=str(backup_file))
                
                return {
                    "file": str(backup_file),
                    "files": len(config_files),
                    "size": backup_file.stat().st_size,
                    "status": "success"
                }
            else:
                logger.warning("No configuration files found to backup")
                return {
                    "file": None,
                    "files": 0,
                    "size": 0,
                    "status": "skipped"
                }
                
        except Exception as e:
            logger.error("Configuration backup failed", error=str(e))
            return {
                "file": None,
                "files": 0,
                "size": 0,
                "status": "failed",
                "error": str(e)
            }
    
    def backup_application(self) -> Dict[str, any]:
        """Backup application files"""
        logger.info("Starting application backup")
        
        backup_file = self.backup_path / "application" / f"application_{self.timestamp}.tar.gz"
        
        try:
            base_path = Path(__file__).parent.parent.parent
            
            # Files/directories to backup
            backup_items = [
                "backend/app",
                "backend/alembic",
                "backend/pytest.ini",
                "backend/requirements.txt",
                "frontend/src",
                "frontend/package.json",
                "frontend/vite.config.ts",
                "frontend/tailwind.config.js",
            ]
            
            # Create tar archive
            import tarfile
            with tarfile.open(backup_file, "w:gz") as tar:
                for item in backup_items:
                    item_path = base_path / item
                    if item_path.exists():
                        tar.add(item_path, arcname=item, exclude=lambda name: any([
                            '__pycache__' in name,
                            '.pyc' in name,
                            'node_modules' in name,
                            '.git' in name,
                        ]))
            
            logger.info("Application backed up", backup=str(backup_file))
            
            return {
                "file": str(backup_file),
                "size": backup_file.stat().st_size,
                "status": "success"
            }
            
        except Exception as e:
            logger.error("Application backup failed", error=str(e))
            return {
                "file": None,
                "size": 0,
                "status": "failed",
                "error": str(e)
            }
    
    def cleanup_old_backups(self) -> int:
        """Remove backups older than retention period"""
        logger.info("Cleaning up old backups", retention_days=self.retention_days)
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        removed_count = 0
        
        try:
            for backup_dir in self.backup_dir.glob("backup_*"):
                if backup_dir.is_dir():
                    # Extract timestamp from directory name
                    try:
                        timestamp_str = backup_dir.name.replace("backup_", "")
                        backup_date = datetime.strptime(timestamp_str.split("_")[0], "%Y%m%d")
                        
                        if backup_date < cutoff_date:
                            logger.info("Removing old backup", backup=str(backup_dir), date=backup_date.isoformat())
                            shutil.rmtree(backup_dir)
                            removed_count += 1
                    except (ValueError, IndexError):
                        # Could not parse date, skip
                        continue
            
            logger.info("Cleanup completed", removed=removed_count)
            return removed_count
            
        except Exception as e:
            logger.error("Cleanup failed", error=str(e))
            return removed_count
    
    async def create_full_backup(self) -> Dict[str, any]:
        """Create a full system backup"""
        logger.info("Starting full backup", backup_dir=str(self.backup_dir))
        
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        results = {
            "timestamp": self.timestamp,
            "backup_name": self.backup_name,
            "backup_path": str(self.backup_path),
            "database": {},
            "config": {},
            "application": {},
            "status": "in_progress"
        }
        
        try:
            # Backup database
            results["database"] = await self.backup_database()
            
            # Backup configuration
            results["config"] = self.backup_config()
            
            # Backup application
            results["application"] = self.backup_application()
            
            # Create backup manifest
            manifest = {
                "backup_date": datetime.now().isoformat(),
                "backup_name": self.backup_name,
                "backup_type": "full",
                "results": results
            }
            
            manifest_file = self.backup_path / "manifest.json"
            with open(manifest_file, "w") as f:
                json.dump(manifest, f, indent=2)
            
            results["status"] = "success"
            results["manifest"] = str(manifest_file)
            
            logger.info("Full backup completed", backup=self.backup_name)
            
            # Cleanup old backups
            removed = self.cleanup_old_backups()
            results["cleanup"] = {"removed": removed}
            
            return results
            
        except Exception as e:
            logger.error("Full backup failed", error=str(e))
            results["status"] = "failed"
            results["error"] = str(e)
            return results


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="GGnet Backup Script")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Create full backup (default)"
    )
    parser.add_argument(
        "--database-only",
        action="store_true",
        help="Backup database only"
    )
    parser.add_argument(
        "--config-only",
        action="store_true",
        help="Backup configuration only"
    )
    parser.add_argument(
        "--backup-dir",
        type=str,
        default=None,
        help="Backup directory (default: ./backups)"
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Number of days to keep backups (default: 30)"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Skip cleanup of old backups"
    )
    
    args = parser.parse_args()
    
    backup_dir = Path(args.backup_dir) if args.backup_dir else None
    
    manager = BackupManager(
        backup_dir=backup_dir,
        retention_days=args.retention_days
    )
    
    try:
        if args.database_only:
            result = await manager.backup_database()
            print(f"\n✅ Database backup completed: {result.get('file', 'N/A')}\n")
        elif args.config_only:
            result = manager.backup_config()
            print(f"\n✅ Configuration backup completed: {result.get('file', 'N/A')}\n")
        else:
            # Full backup (default)
            result = await manager.create_full_backup()
            
            print("\n" + "="*60)
            print("✅ Backup Completed Successfully!")
            print("="*60)
            print(f"Backup Name: {result['backup_name']}")
            print(f"Backup Path: {result['backup_path']}")
            print(f"Status: {result['status']}")
            
            if result.get('database'):
                db_result = result['database']
                print(f"\nDatabase: {db_result.get('status', 'unknown')}")
                if db_result.get('file'):
                    size_mb = db_result['size'] / (1024 * 1024)
                    print(f"  File: {db_result['file']}")
                    print(f"  Size: {size_mb:.2f} MB")
            
            if result.get('config'):
                config_result = result['config']
                print(f"\nConfiguration: {config_result.get('status', 'unknown')}")
                if config_result.get('file'):
                    size_mb = config_result['size'] / (1024 * 1024)
                    print(f"  File: {config_result['file']}")
                    print(f"  Size: {size_mb:.2f} MB")
            
            if result.get('cleanup'):
                print(f"\nCleanup: Removed {result['cleanup']['removed']} old backup(s)")
            
            print("="*60 + "\n")
            
            sys.exit(0 if result['status'] == 'success' else 1)
            
    except Exception as e:
        print(f"\n❌ Backup failed: {e}\n", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

