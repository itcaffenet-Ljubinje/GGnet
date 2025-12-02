# GGnet Upgrade Guide

This guide provides step-by-step instructions for upgrading GGnet to newer versions.

## 📋 Table of Contents

- [Pre-Upgrade Checklist](#pre-upgrade-checklist)
- [Backup Procedures](#backup-procedures)
- [Upgrade Methods](#upgrade-methods)
- [Version-Specific Upgrades](#version-specific-upgrades)
- [Post-Upgrade Verification](#post-upgrade-verification)
- [Rollback Procedures](#rollback-procedures)
- [Troubleshooting Upgrades](#troubleshooting-upgrades)

## ✅ Pre-Upgrade Checklist

### System Requirements Check
```bash
# Check current version
curl -H "Authorization: Bearer <token>" http://localhost:8000/health/ | jq '.version'

# Check system resources
df -h
free -h
uname -a

# Check Python version
python3 --version

# Check Node.js version (if frontend is deployed)
node --version
```

### Dependencies Check
```bash
# Check database version
sudo -u postgres psql -c "SELECT version();"

# Check Redis version
redis-cli --version

# Check installed packages
pip list | grep -E "(fastapi|sqlalchemy|redis)"
```

### Service Status Check
```bash
# Check all services are running
sudo systemctl status ggnet-backend ggnet-worker redis-server postgresql

# Check for any errors in logs
sudo journalctl -u ggnet-backend --since "1 hour ago" | grep -i error
```

## 💾 Backup Procedures

### Complete System Backup
```bash
#!/bin/bash
# Complete backup script

BACKUP_DIR="/opt/ggnet/backups/upgrade_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "Starting complete system backup..."

# 1. Database backup
echo "Backing up database..."
sudo -u postgres pg_dump ggnet | gzip > $BACKUP_DIR/database.sql.gz

# 2. Configuration backup
echo "Backing up configuration..."
tar -czf $BACKUP_DIR/config.tar.gz \
    /opt/ggnet/backend/.env \
    /etc/nginx/sites-available/ggnet.conf \
    /etc/systemd/system/ggnet-*.service

# 3. Application files backup
echo "Backing up application files..."
tar -czf $BACKUP_DIR/application.tar.gz \
    /opt/ggnet/backend \
    --exclude=/opt/ggnet/backend/venv \
    --exclude=/opt/ggnet/backend/__pycache__

# 4. Images backup (optional)
echo "Backing up images..."
tar -czf $BACKUP_DIR/images.tar.gz /var/lib/ggnet/images/

# 5. Logs backup
echo "Backing up logs..."
tar -czf $BACKUP_DIR/logs.tar.gz /opt/ggnet/logs/

echo "Backup completed: $BACKUP_DIR"
```

### Quick Backup (Minimal)
```bash
# Quick backup for minor upgrades
BACKUP_DIR="/opt/ggnet/backups/quick_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Database only
sudo -u postgres pg_dump ggnet > $BACKUP_DIR/database.sql

# Configuration only
cp /opt/ggnet/backend/.env $BACKUP_DIR/
cp /etc/nginx/sites-available/ggnet.conf $BACKUP_DIR/

echo "Quick backup completed: $BACKUP_DIR"
```

## 🚀 Upgrade Methods

### Method 1: Automated Upgrade (Recommended)

#### Using Git (Development/Staging)
```bash
# Stop services
sudo systemctl stop ggnet-backend ggnet-worker

# Create backup
sudo /opt/ggnet/scripts/backup.sh

# Pull latest changes
cd /opt/ggnet
sudo -u ggnet git fetch origin
sudo -u ggnet git checkout main
sudo -u ggnet git pull origin main

# Update dependencies
sudo -u ggnet /opt/ggnet/venv/bin/pip install -r backend/requirements.txt

# Run database migrations
sudo -u ggnet /opt/ggnet/venv/bin/alembic upgrade head

# Start services
sudo systemctl start ggnet-backend ggnet-worker

# Verify upgrade
curl http://localhost:8000/health/
```

#### Using Package Manager (Production)
```bash
# Update package repository
sudo apt update

# Upgrade GGnet package
sudo apt upgrade ggnet

# Restart services
sudo systemctl restart ggnet-backend ggnet-worker
```

### Method 2: Manual Upgrade

#### Download and Install
```bash
# Download latest release
cd /tmp
wget https://github.com/your-org/ggnet/releases/latest/download/ggnet-latest.tar.gz

# Extract
tar -xzf ggnet-latest.tar.gz
cd ggnet-*

# Stop services
sudo systemctl stop ggnet-backend ggnet-worker

# Backup current installation
sudo cp -r /opt/ggnet /opt/ggnet.backup.$(date +%Y%m%d)

# Install new version
sudo cp -r backend/* /opt/ggnet/backend/
sudo chown -R ggnet:ggnet /opt/ggnet

# Update dependencies
sudo -u ggnet /opt/ggnet/venv/bin/pip install -r /opt/ggnet/backend/requirements.txt

# Run migrations
sudo -u ggnet /opt/ggnet/venv/bin/alembic upgrade head

# Start services
sudo systemctl start ggnet-backend ggnet-worker
```

### Method 3: Docker Upgrade

#### Using Docker Compose
```bash
# Navigate to infra directory
cd /opt/ggnet/infra

# Pull latest images
docker compose pull

# Stop services
docker compose down

# Start with new images
docker compose up -d --build

# Verify upgrade
docker compose ps
```

## 🔄 Version-Specific Upgrades

### Upgrade from v1.0.x to v1.1.x

#### Breaking Changes
- New database schema for enhanced session tracking
- Updated API endpoints for target management
- New configuration options for image processing

#### Upgrade Steps
```bash
# 1. Backup current installation
sudo /opt/ggnet/scripts/backup.sh

# 2. Stop services
sudo systemctl stop ggnet-backend ggnet-worker

# 3. Update application
sudo -u ggnet git pull origin main

# 4. Update dependencies
sudo -u ggnet /opt/ggnet/venv/bin/pip install -r backend/requirements.txt

# 5. Run database migrations
sudo -u ggnet /opt/ggnet/venv/bin/alembic upgrade head

# 6. Update configuration
sudo nano /opt/ggnet/backend/.env
# Add new configuration options:
# IMAGE_PROCESSING_WORKERS=2
# SESSION_TIMEOUT_MINUTES=30

# 7. Start services
sudo systemctl start ggnet-backend ggnet-worker

# 8. Verify upgrade
curl http://localhost:8000/health/ | jq '.version'
```

### Upgrade from v1.1.x to v1.2.x

#### Breaking Changes
- New Redis configuration for session management
- Updated WebSocket API for real-time updates
- New monitoring endpoints

#### Upgrade Steps
```bash
# 1. Backup
sudo /opt/ggnet/scripts/backup.sh

# 2. Stop services
sudo systemctl stop ggnet-backend ggnet-worker

# 3. Update Redis configuration
sudo nano /etc/redis/redis.conf
# Add: maxmemory-policy allkeys-lru

# 4. Update application
sudo -u ggnet git pull origin main

# 5. Update dependencies
sudo -u ggnet /opt/ggnet/venv/bin/pip install -r backend/requirements.txt

# 6. Run migrations
sudo -u ggnet /opt/ggnet/venv/bin/alembic upgrade head

# 7. Update systemd services
sudo cp infra/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# 8. Start services
sudo systemctl start ggnet-backend ggnet-worker

# 9. Verify
curl http://localhost:8000/health/detailed
```

### Upgrade from v1.2.x to v2.0.x

#### Major Breaking Changes
- Complete API redesign
- New authentication system
- Updated database schema
- New frontend architecture

#### Pre-Upgrade Preparation
```bash
# 1. Export current data
sudo -u ggnet /opt/ggnet/venv/bin/python /opt/ggnet/backend/scripts/export_data.py

# 2. Document current configuration
sudo cp /opt/ggnet/backend/.env /opt/ggnet/backend/.env.v1.2

# 3. List all current users
curl -H "Authorization: Bearer <token>" http://localhost:8000/users > users_backup.json
```

#### Upgrade Steps
```bash
# 1. Complete backup
sudo /opt/ggnet/scripts/backup.sh

# 2. Stop all services
sudo systemctl stop ggnet-backend ggnet-worker

# 3. Create migration workspace
sudo mkdir -p /opt/ggnet/migration
cd /opt/ggnet/migration

# 4. Download v2.0
wget https://github.com/your-org/ggnet/releases/download/v2.0.0/ggnet-v2.0.0.tar.gz
tar -xzf ggnet-v2.0.0.tar.gz

# 5. Run migration script
sudo -u ggnet python migrate_v1_to_v2.py

# 6. Install v2.0
sudo cp -r ggnet-v2.0.0/backend/* /opt/ggnet/backend/
sudo chown -R ggnet:ggnet /opt/ggnet

# 7. Update dependencies
sudo -u ggnet /opt/ggnet/venv/bin/pip install -r /opt/ggnet/backend/requirements.txt

# 8. Run new migrations
sudo -u ggnet /opt/ggnet/venv/bin/alembic upgrade head

# 9. Update configuration
sudo nano /opt/ggnet/backend/.env
# Update configuration for v2.0

# 10. Start services
sudo systemctl start ggnet-backend ggnet-worker

# 11. Verify upgrade
curl http://localhost:8000/health/ | jq '.version'
```

## ✅ Post-Upgrade Verification

### Basic Health Checks
```bash
# 1. Check service status
sudo systemctl status ggnet-backend ggnet-worker

# 2. Check health endpoint
curl http://localhost:8000/health/

# 3. Check version
curl http://localhost:8000/health/ | jq '.version'

# 4. Check database connectivity
sudo -u ggnet /opt/ggnet/venv/bin/python -c "
import asyncio
from app.core.database import get_db
async def test():
    async with get_db() as db:
        result = await db.execute('SELECT 1')
        print('Database OK:', result.scalar())
asyncio.run(test())
"
```

### Functional Testing
```bash
# 1. Test authentication
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 2. Test API endpoints
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | jq -r '.access_token')

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/machines

# 3. Test WebSocket connection
# Use browser developer tools to test WebSocket connection

# 4. Test image upload
curl -X POST http://localhost:8000/images/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test_image.vhdx" \
  -F "name=Test Image" \
  -F "image_type=SYSTEM"
```

### Performance Verification
```bash
# 1. Check system resources
htop
free -h
df -h

# 2. Check response times
time curl http://localhost:8000/health/

# 3. Check database performance
sudo -u postgres psql ggnet -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 5;
"

# 4. Check Redis performance
redis-cli info stats
```

## 🔄 Rollback Procedures

### Quick Rollback (Recent Backup)
```bash
# 1. Stop services
sudo systemctl stop ggnet-backend ggnet-worker

# 2. Restore from backup
BACKUP_DIR="/opt/ggnet/backups/upgrade_20240101_120000"
sudo cp -r $BACKUP_DIR/application.tar.gz /tmp/
cd /tmp
tar -xzf application.tar.gz

# 3. Restore application files
sudo cp -r backend/* /opt/ggnet/backend/
sudo chown -R ggnet:ggnet /opt/ggnet

# 4. Restore database
sudo -u postgres psql ggnet < $BACKUP_DIR/database.sql.gz

# 5. Restore configuration
tar -xzf $BACKUP_DIR/config.tar.gz -C /

# 6. Start services
sudo systemctl start ggnet-backend ggnet-worker

# 7. Verify rollback
curl http://localhost:8000/health/
```

### Database-Only Rollback
```bash
# 1. Stop services
sudo systemctl stop ggnet-backend ggnet-worker

# 2. Restore database only
sudo -u postgres psql ggnet < /opt/ggnet/backups/database.sql

# 3. Start services
sudo systemctl start ggnet-backend ggnet-worker
```

### Configuration Rollback
```bash
# 1. Restore configuration
sudo cp /opt/ggnet/backend/.env.backup /opt/ggnet/backend/.env

# 2. Restart services
sudo systemctl restart ggnet-backend ggnet-worker
```

## 🔧 Troubleshooting Upgrades

### Common Upgrade Issues

#### Database Migration Failures
```bash
# Check migration status
sudo -u ggnet /opt/ggnet/venv/bin/alembic current

# Check migration history
sudo -u ggnet /opt/ggnet/venv/bin/alembic history

# Manual migration
sudo -u ggnet /opt/ggnet/venv/bin/alembic upgrade +1

# Rollback migration
sudo -u ggnet /opt/ggnet/venv/bin/alembic downgrade -1
```

#### Dependency Conflicts
```bash
# Check for conflicts
sudo -u ggnet /opt/ggnet/venv/bin/pip check

# Reinstall dependencies
sudo -u ggnet /opt/ggnet/venv/bin/pip install --force-reinstall -r backend/requirements.txt

# Clean and reinstall
sudo -u ggnet /opt/ggnet/venv/bin/pip uninstall -r backend/requirements.txt -y
sudo -u ggnet /opt/ggnet/venv/bin/pip install -r backend/requirements.txt
```

#### Service Startup Failures
```bash
# Check service logs
sudo journalctl -u ggnet-backend -f

# Check configuration
sudo -u ggnet /opt/ggnet/venv/bin/python -c "
from app.core.config import get_settings
print(get_settings())
"

# Test configuration
sudo -u ggnet /opt/ggnet/venv/bin/python -m app.main
```

#### API Compatibility Issues
```bash
# Check API version
curl http://localhost:8000/health/ | jq '.api_version'

# Test API endpoints
curl http://localhost:8000/docs

# Check for deprecated endpoints
grep -r "deprecated" /opt/ggnet/backend/app/routes/
```

### Recovery Procedures

#### Complete System Recovery
```bash
# 1. Stop all services
sudo systemctl stop ggnet-backend ggnet-worker redis-server postgresql

# 2. Restore from complete backup
BACKUP_DIR="/opt/ggnet/backups/complete_20240101_120000"
cd $BACKUP_DIR

# 3. Restore database
sudo -u postgres psql < database.sql.gz

# 4. Restore application
tar -xzf application.tar.gz -C /

# 5. Restore configuration
tar -xzf config.tar.gz -C /

# 6. Restore images
tar -xzf images.tar.gz -C /

# 7. Start services
sudo systemctl start postgresql redis-server ggnet-backend ggnet-worker

# 8. Verify recovery
curl http://localhost:8000/health/
```

#### Partial Recovery
```bash
# Recover specific components
# Database only
sudo -u postgres psql ggnet < /opt/ggnet/backups/database.sql

# Configuration only
sudo cp /opt/ggnet/backups/.env /opt/ggnet/backend/

# Images only
tar -xzf /opt/ggnet/backups/images.tar.gz -C /
```

### Emergency Procedures

#### Emergency Rollback
```bash
# Immediate rollback to last known good state
sudo systemctl stop ggnet-backend ggnet-worker

# Restore from last backup
LATEST_BACKUP=$(ls -t /opt/ggnet/backups/complete_*.tar.gz | head -1)
tar -xzf $LATEST_BACKUP -C /

# Start services
sudo systemctl start ggnet-backend ggnet-worker

# Notify administrators
echo "Emergency rollback completed" | mail -s "GGnet Emergency Rollback" admin@example.com
```

#### Data Recovery
```bash
# Recover lost data
# Check backup integrity
tar -tzf /opt/ggnet/backups/database.sql.gz > /dev/null

# Restore specific tables
sudo -u postgres psql ggnet -c "
DROP TABLE IF EXISTS sessions CASCADE;
"
sudo -u postgres psql ggnet < /opt/ggnet/backups/sessions_backup.sql
```

---

## 📝 Upgrade Checklist

### Pre-Upgrade
- [ ] Review release notes
- [ ] Check system requirements
- [ ] Create complete backup
- [ ] Test backup restoration
- [ ] Notify users of maintenance window
- [ ] Prepare rollback plan

### During Upgrade
- [ ] Stop services gracefully
- [ ] Run backup procedures
- [ ] Update application files
- [ ] Update dependencies
- [ ] Run database migrations
- [ ] Update configuration
- [ ] Start services
- [ ] Verify basic functionality

### Post-Upgrade
- [ ] Run health checks
- [ ] Test critical functionality
- [ ] Monitor system performance
- [ ] Check logs for errors
- [ ] Verify user access
- [ ] Update documentation
- [ ] Notify users of completion

### Rollback (if needed)
- [ ] Stop services
- [ ] Restore from backup
- [ ] Verify restoration
- [ ] Start services
- [ ] Test functionality
- [ ] Document issues
- [ ] Plan next upgrade attempt

---

This upgrade guide ensures safe and reliable upgrades of GGnet. Always test upgrades in a staging environment before applying to production.
