# GGnet Backup and Restore Guide

This guide provides comprehensive procedures for backing up and restoring GGnet data and configuration.

## 📋 Table of Contents

- [Backup Strategy](#backup-strategy)
- [Backup Procedures](#backup-procedures)
- [Restore Procedures](#restore-procedures)
- [Automated Backup Scripts](#automated-backup-scripts)
- [Disaster Recovery](#disaster-recovery)
- [Backup Verification](#backup-verification)
- [Best Practices](#best-practices)

## 🎯 Backup Strategy

### Backup Types

#### 1. Full System Backup
- Complete application installation
- Database with all data
- Configuration files
- User data and images
- Log files
- System configuration

#### 2. Incremental Backup
- Changes since last backup
- Database transaction logs
- New or modified files
- Configuration changes

#### 3. Differential Backup
- Changes since last full backup
- Database deltas
- File system changes

### Backup Frequency

#### Production Environment
- **Full Backup**: Daily at 2:00 AM
- **Incremental Backup**: Every 4 hours
- **Configuration Backup**: Before any changes
- **Database Backup**: Every 6 hours

#### Development Environment
- **Full Backup**: Weekly
- **Incremental Backup**: Daily
- **Configuration Backup**: Before deployments

### Retention Policy

#### Backup Retention
- **Daily Backups**: 30 days
- **Weekly Backups**: 12 weeks
- **Monthly Backups**: 12 months
- **Yearly Backups**: 7 years

#### Storage Locations
- **Primary**: Local storage (`/opt/ggnet/backups/`)
- **Secondary**: Network storage (NFS/SMB)
- **Offsite**: Cloud storage (AWS S3, Google Cloud)

## 💾 Backup Procedures

### Complete System Backup

#### Manual Full Backup
```bash
#!/bin/bash
# Complete system backup script

BACKUP_DIR="/opt/ggnet/backups/full_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "Starting complete system backup to $BACKUP_DIR..."

# 1. Database backup
echo "Backing up database..."
sudo -u postgres pg_dump ggnet | gzip > $BACKUP_DIR/database.sql.gz

# 2. Application files backup
echo "Backing up application files..."
tar -czf $BACKUP_DIR/application.tar.gz \
    /opt/ggnet/backend \
    --exclude=/opt/ggnet/backend/venv \
    --exclude=/opt/ggnet/backend/__pycache__ \
    --exclude=/opt/ggnet/backend/.git

# 3. Configuration backup
echo "Backing up configuration..."
tar -czf $BACKUP_DIR/config.tar.gz \
    /opt/ggnet/backend/.env \
    /etc/nginx/sites-available/ggnet.conf \
    /etc/systemd/system/ggnet-*.service \
    /etc/dhcp/dhcpd.conf \
    /etc/default/tftpd-hpa

# 4. Data backup
echo "Backing up data..."
tar -czf $BACKUP_DIR/data.tar.gz \
    /var/lib/ggnet/images/ \
    /var/lib/ggnet/uploads/ \
    /var/lib/tftpboot/

# 5. Logs backup
echo "Backing up logs..."
tar -czf $BACKUP_DIR/logs.tar.gz \
    /opt/ggnet/logs/ \
    /var/log/nginx/ \
    /var/log/postgresql/

# 6. System information
echo "Backing up system information..."
{
    echo "=== System Information ==="
    uname -a
    echo
    echo "=== Installed Packages ==="
    dpkg -l | grep -E "(ggnet|postgresql|redis|nginx)"
    echo
    echo "=== Service Status ==="
    systemctl status ggnet-backend ggnet-worker postgresql redis-server nginx
    echo
    echo "=== Disk Usage ==="
    df -h
    echo
    echo "=== Memory Usage ==="
    free -h
} > $BACKUP_DIR/system_info.txt

# 7. Create backup manifest
echo "Creating backup manifest..."
{
    echo "Backup Date: $(date)"
    echo "Backup Type: Full System Backup"
    echo "Backup Location: $BACKUP_DIR"
    echo
    echo "Files:"
    ls -la $BACKUP_DIR/
    echo
    echo "Sizes:"
    du -sh $BACKUP_DIR/*
} > $BACKUP_DIR/manifest.txt

echo "Complete system backup finished: $BACKUP_DIR"
```

#### Database-Only Backup
```bash
#!/bin/bash
# Database backup script

BACKUP_DIR="/opt/ggnet/backups/db_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "Starting database backup..."

# Full database backup
sudo -u postgres pg_dump ggnet | gzip > $BACKUP_DIR/database.sql.gz

# Schema-only backup
sudo -u postgres pg_dump -s ggnet > $BACKUP_DIR/schema.sql

# Data-only backup
sudo -u postgres pg_dump -a ggnet | gzip > $BACKUP_DIR/data.sql.gz

# Individual table backups
sudo -u postgres pg_dump -t users ggnet > $BACKUP_DIR/users.sql
sudo -u postgres pg_dump -t machines ggnet > $BACKUP_DIR/machines.sql
sudo -u postgres pg_dump -t images ggnet > $BACKUP_DIR/images.sql
sudo -u postgres pg_dump -t targets ggnet > $BACKUP_DIR/targets.sql
sudo -u postgres pg_dump -t sessions ggnet > $BACKUP_DIR/sessions.sql

echo "Database backup completed: $BACKUP_DIR"
```

#### Configuration Backup
```bash
#!/bin/bash
# Configuration backup script

BACKUP_DIR="/opt/ggnet/backups/config_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "Starting configuration backup..."

# Application configuration
cp /opt/ggnet/backend/.env $BACKUP_DIR/

# Web server configuration
cp /etc/nginx/sites-available/ggnet.conf $BACKUP_DIR/

# Systemd services
cp /etc/systemd/system/ggnet-*.service $BACKUP_DIR/

# Database configuration
cp /etc/postgresql/*/main/postgresql.conf $BACKUP_DIR/
cp /etc/postgresql/*/main/pg_hba.conf $BACKUP_DIR/

# Redis configuration
cp /etc/redis/redis.conf $BACKUP_DIR/

# DHCP configuration
cp /etc/dhcp/dhcpd.conf $BACKUP_DIR/

# TFTP configuration
cp /etc/default/tftpd-hpa $BACKUP_DIR/

# iSCSI configuration
sudo targetcli saveconfig $BACKUP_DIR/targetcli_config.json

echo "Configuration backup completed: $BACKUP_DIR"
```

### Incremental Backup

#### File System Incremental Backup
```bash
#!/bin/bash
# Incremental backup script

LAST_BACKUP="/opt/ggnet/backups/last_full_backup"
BACKUP_DIR="/opt/ggnet/backups/incremental_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "Starting incremental backup..."

# Find files modified since last backup
if [ -f "$LAST_BACKUP" ]; then
    LAST_DATE=$(cat $LAST_BACKUP)
    find /opt/ggnet/backend -newer $LAST_DATE -type f > $BACKUP_DIR/changed_files.txt
    find /var/lib/ggnet -newer $LAST_DATE -type f >> $BACKUP_DIR/changed_files.txt
else
    echo "No previous backup found, creating full backup"
    find /opt/ggnet/backend -type f > $BACKUP_DIR/changed_files.txt
    find /var/lib/ggnet -type f >> $BACKUP_DIR/changed_files.txt
fi

# Create incremental archive
tar -czf $BACKUP_DIR/incremental.tar.gz -T $BACKUP_DIR/changed_files.txt

# Update last backup timestamp
date > $LAST_BACKUP

echo "Incremental backup completed: $BACKUP_DIR"
```

#### Database Incremental Backup
```bash
#!/bin/bash
# Database incremental backup script

BACKUP_DIR="/opt/ggnet/backups/db_incremental_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "Starting database incremental backup..."

# Get last backup timestamp
LAST_BACKUP="/opt/ggnet/backups/last_db_backup"
if [ -f "$LAST_BACKUP" ]; then
    LAST_DATE=$(cat $LAST_BACKUP)
    
    # Backup only changed data
    sudo -u postgres psql ggnet -c "
    COPY (
        SELECT * FROM sessions 
        WHERE updated_at > '$LAST_DATE'
    ) TO STDOUT WITH CSV HEADER;
    " > $BACKUP_DIR/sessions_incremental.csv
    
    sudo -u postgres psql ggnet -c "
    COPY (
        SELECT * FROM audit_logs 
        WHERE created_at > '$LAST_DATE'
    ) TO STDOUT WITH CSV HEADER;
    " > $BACKUP_DIR/audit_logs_incremental.csv
else
    echo "No previous database backup found"
fi

# Update last backup timestamp
date > $LAST_BACKUP

echo "Database incremental backup completed: $BACKUP_DIR"
```

## 🔄 Restore Procedures

### Complete System Restore

#### From Full Backup
```bash
#!/bin/bash
# Complete system restore script

BACKUP_DIR="$1"
if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "Starting complete system restore from $BACKUP_DIR..."

# 1. Stop all services
echo "Stopping services..."
sudo systemctl stop ggnet-backend ggnet-worker nginx

# 2. Restore database
echo "Restoring database..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS ggnet;"
sudo -u postgres psql -c "CREATE DATABASE ggnet;"
sudo -u postgres psql ggnet < $BACKUP_DIR/database.sql.gz

# 3. Restore application files
echo "Restoring application files..."
sudo rm -rf /opt/ggnet/backend
tar -xzf $BACKUP_DIR/application.tar.gz -C /
sudo chown -R ggnet:ggnet /opt/ggnet

# 4. Restore configuration
echo "Restoring configuration..."
tar -xzf $BACKUP_DIR/config.tar.gz -C /

# 5. Restore data
echo "Restoring data..."
tar -xzf $BACKUP_DIR/data.tar.gz -C /

# 6. Restore logs
echo "Restoring logs..."
tar -xzf $BACKUP_DIR/logs.tar.gz -C /

# 7. Restart services
echo "Restarting services..."
sudo systemctl start postgresql redis-server nginx
sudo systemctl start ggnet-backend ggnet-worker

# 8. Verify restoration
echo "Verifying restoration..."
sleep 10
curl -f http://localhost:8000/health/ || echo "Health check failed"

echo "Complete system restore finished"
```

#### Database-Only Restore
```bash
#!/bin/bash
# Database restore script

BACKUP_DIR="$1"
if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

echo "Starting database restore from $BACKUP_DIR..."

# Stop services
sudo systemctl stop ggnet-backend ggnet-worker

# Restore database
if [ -f "$BACKUP_DIR/database.sql.gz" ]; then
    echo "Restoring full database..."
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS ggnet;"
    sudo -u postgres psql -c "CREATE DATABASE ggnet;"
    sudo -u postgres psql ggnet < $BACKUP_DIR/database.sql.gz
elif [ -f "$BACKUP_DIR/schema.sql" ] && [ -f "$BACKUP_DIR/data.sql.gz" ]; then
    echo "Restoring schema and data separately..."
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS ggnet;"
    sudo -u postgres psql -c "CREATE DATABASE ggnet;"
    sudo -u postgres psql ggnet < $BACKUP_DIR/schema.sql
    sudo -u postgres psql ggnet < $BACKUP_DIR/data.sql.gz
else
    echo "No valid database backup found"
    exit 1
fi

# Start services
sudo systemctl start ggnet-backend ggnet-worker

# Verify restoration
sleep 5
curl -f http://localhost:8000/health/ || echo "Health check failed"

echo "Database restore completed"
```

#### Configuration Restore
```bash
#!/bin/bash
# Configuration restore script

BACKUP_DIR="$1"
if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

echo "Starting configuration restore from $BACKUP_DIR..."

# Stop services
sudo systemctl stop ggnet-backend ggnet-worker nginx

# Restore configuration files
if [ -f "$BACKUP_DIR/.env" ]; then
    cp $BACKUP_DIR/.env /opt/ggnet/backend/
fi

if [ -f "$BACKUP_DIR/ggnet.conf" ]; then
    cp $BACKUP_DIR/ggnet.conf /etc/nginx/sites-available/
fi

if [ -f "$BACKUP_DIR/ggnet-backend.service" ]; then
    cp $BACKUP_DIR/ggnet-*.service /etc/systemd/system/
    sudo systemctl daemon-reload
fi

if [ -f "$BACKUP_DIR/postgresql.conf" ]; then
    cp $BACKUP_DIR/postgresql.conf /etc/postgresql/*/main/
fi

if [ -f "$BACKUP_DIR/redis.conf" ]; then
    cp $BACKUP_DIR/redis.conf /etc/redis/
fi

if [ -f "$BACKUP_DIR/dhcpd.conf" ]; then
    cp $BACKUP_DIR/dhcpd.conf /etc/dhcp/
fi

if [ -f "$BACKUP_DIR/tftpd-hpa" ]; then
    cp $BACKUP_DIR/tftpd-hpa /etc/default/
fi

if [ -f "$BACKUP_DIR/targetcli_config.json" ]; then
    sudo targetcli restoreconfig $BACKUP_DIR/targetcli_config.json
fi

# Start services
sudo systemctl start postgresql redis-server nginx
sudo systemctl start ggnet-backend ggnet-worker

echo "Configuration restore completed"
```

### Selective Restore

#### Restore Specific Tables
```bash
#!/bin/bash
# Restore specific database tables

BACKUP_DIR="$1"
TABLE_NAME="$2"

if [ -z "$BACKUP_DIR" ] || [ -z "$TABLE_NAME" ]; then
    echo "Usage: $0 <backup_directory> <table_name>"
    exit 1
fi

echo "Restoring table $TABLE_NAME from $BACKUP_DIR..."

# Stop services
sudo systemctl stop ggnet-backend

# Restore specific table
if [ -f "$BACKUP_DIR/${TABLE_NAME}.sql" ]; then
    sudo -u postgres psql ggnet < $BACKUP_DIR/${TABLE_NAME}.sql
    echo "Table $TABLE_NAME restored successfully"
else
    echo "Table backup not found: $BACKUP_DIR/${TABLE_NAME}.sql"
    exit 1
fi

# Start services
sudo systemctl start ggnet-backend

echo "Table restore completed"
```

#### Restore Specific Files
```bash
#!/bin/bash
# Restore specific files

BACKUP_DIR="$1"
FILE_PATTERN="$2"

if [ -z "$BACKUP_DIR" ] || [ -z "$FILE_PATTERN" ]; then
    echo "Usage: $0 <backup_directory> <file_pattern>"
    exit 1
fi

echo "Restoring files matching $FILE_PATTERN from $BACKUP_DIR..."

# Extract specific files
tar -tzf $BACKUP_DIR/application.tar.gz | grep "$FILE_PATTERN" | \
    tar -xzf $BACKUP_DIR/application.tar.gz -C /

echo "File restore completed"
```

## 🤖 Automated Backup Scripts

### Cron-Based Backup

#### Daily Full Backup
```bash
# Add to crontab
# 0 2 * * * /opt/ggnet/scripts/daily_backup.sh

#!/bin/bash
# Daily backup script

BACKUP_DIR="/opt/ggnet/backups/daily_$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Database backup
sudo -u postgres pg_dump ggnet | gzip > $BACKUP_DIR/database.sql.gz

# Application backup
tar -czf $BACKUP_DIR/application.tar.gz \
    /opt/ggnet/backend \
    --exclude=/opt/ggnet/backend/venv \
    --exclude=/opt/ggnet/backend/__pycache__

# Configuration backup
tar -czf $BACKUP_DIR/config.tar.gz \
    /opt/ggnet/backend/.env \
    /etc/nginx/sites-available/ggnet.conf \
    /etc/systemd/system/ggnet-*.service

# Data backup
tar -czf $BACKUP_DIR/data.tar.gz /var/lib/ggnet/images/

# Clean old backups (keep 30 days)
find /opt/ggnet/backups -name "daily_*" -mtime +30 -exec rm -rf {} \;

# Log backup completion
echo "$(date): Daily backup completed to $BACKUP_DIR" >> /opt/ggnet/logs/backup.log
```

#### Hourly Incremental Backup
```bash
# Add to crontab
# 0 * * * * /opt/ggnet/scripts/hourly_backup.sh

#!/bin/bash
# Hourly incremental backup script

BACKUP_DIR="/opt/ggnet/backups/hourly_$(date +%Y%m%d_%H)"
mkdir -p $BACKUP_DIR

# Database incremental backup
sudo -u postgres psql ggnet -c "
COPY (
    SELECT * FROM sessions 
    WHERE updated_at > NOW() - INTERVAL '1 hour'
) TO STDOUT WITH CSV HEADER;
" > $BACKUP_DIR/sessions_hourly.csv

# File incremental backup
find /opt/ggnet/backend -newer /opt/ggnet/backups/last_hourly_backup -type f | \
    tar -czf $BACKUP_DIR/files_hourly.tar.gz -T -

# Update timestamp
date > /opt/ggnet/backups/last_hourly_backup

# Clean old hourly backups (keep 7 days)
find /opt/ggnet/backups -name "hourly_*" -mtime +7 -exec rm -rf {} \;

echo "$(date): Hourly backup completed to $BACKUP_DIR" >> /opt/ggnet/logs/backup.log
```

### Systemd Timer-Based Backup

#### Create Backup Service
```bash
# Create service file
sudo nano /etc/systemd/system/ggnet-backup.service

[Unit]
Description=GGnet Backup Service
After=ggnet-backend.service

[Service]
Type=oneshot
User=ggnet
ExecStart=/opt/ggnet/scripts/backup.sh
StandardOutput=journal
StandardError=journal

# Create timer file
sudo nano /etc/systemd/system/ggnet-backup.timer

[Unit]
Description=GGnet Backup Timer
Requires=ggnet-backup.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target

# Enable and start timer
sudo systemctl enable ggnet-backup.timer
sudo systemctl start ggnet-backup.timer
```

## 🚨 Disaster Recovery

### Complete System Recovery

#### Bare Metal Recovery
```bash
#!/bin/bash
# Bare metal recovery script

BACKUP_DIR="$1"
if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

echo "Starting bare metal recovery from $BACKUP_DIR..."

# 1. Install base system packages
sudo apt update
sudo apt install -y python3 python3-venv python3-pip \
    postgresql postgresql-contrib redis-server \
    nginx qemu-utils targetcli-fb tftpd-hpa isc-dhcp-server

# 2. Create system user
sudo useradd -r -m -d /opt/ggnet -s /usr/sbin/nologin ggnet

# 3. Create directories
sudo mkdir -p /opt/ggnet/{backend,logs,backups}
sudo mkdir -p /var/lib/ggnet/{images,uploads}
sudo mkdir -p /var/lib/tftpboot

# 4. Restore from backup
tar -xzf $BACKUP_DIR/application.tar.gz -C /
tar -xzf $BACKUP_DIR/config.tar.gz -C /
tar -xzf $BACKUP_DIR/data.tar.gz -C /

# 5. Set permissions
sudo chown -R ggnet:ggnet /opt/ggnet
sudo chown -R ggnet:ggnet /var/lib/ggnet
sudo chown -R tftp:tftp /var/lib/tftpboot

# 6. Install Python dependencies
sudo -u ggnet python3 -m venv /opt/ggnet/venv
sudo -u ggnet /opt/ggnet/venv/bin/pip install -r /opt/ggnet/backend/requirements.txt

# 7. Restore database
sudo -u postgres psql -c "CREATE DATABASE ggnet;"
sudo -u postgres psql ggnet < $BACKUP_DIR/database.sql.gz

# 8. Start services
sudo systemctl start postgresql redis-server nginx
sudo systemctl start ggnet-backend ggnet-worker
sudo systemctl enable ggnet-backend ggnet-worker

echo "Bare metal recovery completed"
```

#### Cloud Recovery
```bash
#!/bin/bash
# Cloud recovery script

BACKUP_URL="$1"
if [ -z "$BACKUP_URL" ]; then
    echo "Usage: $0 <backup_url>"
    exit 1
fi

echo "Starting cloud recovery from $BACKUP_URL..."

# Download backup
wget -O /tmp/ggnet_backup.tar.gz "$BACKUP_URL"

# Extract backup
tar -xzf /tmp/ggnet_backup.tar.gz -C /tmp/

# Run bare metal recovery
/tmp/ggnet_backup/scripts/bare_metal_recovery.sh /tmp/ggnet_backup

echo "Cloud recovery completed"
```

### Data Recovery

#### Recover Deleted Data
```bash
#!/bin/bash
# Data recovery script

BACKUP_DIR="$1"
TABLE_NAME="$2"
RECOVERY_DATE="$3"

if [ -z "$BACKUP_DIR" ] || [ -z "$TABLE_NAME" ] || [ -z "$RECOVERY_DATE" ]; then
    echo "Usage: $0 <backup_directory> <table_name> <recovery_date>"
    exit 1
fi

echo "Recovering $TABLE_NAME data from $RECOVERY_DATE..."

# Stop services
sudo systemctl stop ggnet-backend

# Create recovery table
sudo -u postgres psql ggnet -c "
CREATE TABLE ${TABLE_NAME}_recovery AS 
SELECT * FROM $TABLE_NAME WHERE 1=0;
"

# Restore data from backup
sudo -u postgres psql ggnet -c "
INSERT INTO ${TABLE_NAME}_recovery 
SELECT * FROM $TABLE_NAME 
WHERE updated_at <= '$RECOVERY_DATE';
"

# Verify recovery
sudo -u postgres psql ggnet -c "
SELECT COUNT(*) FROM ${TABLE_NAME}_recovery;
"

echo "Data recovery completed. Review ${TABLE_NAME}_recovery table."
```

## ✅ Backup Verification

### Backup Integrity Check
```bash
#!/bin/bash
# Backup verification script

BACKUP_DIR="$1"
if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

echo "Verifying backup integrity for $BACKUP_DIR..."

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "ERROR: Backup directory not found"
    exit 1
fi

# Check database backup
if [ -f "$BACKUP_DIR/database.sql.gz" ]; then
    echo "Verifying database backup..."
    if gzip -t "$BACKUP_DIR/database.sql.gz"; then
        echo "✓ Database backup is valid"
    else
        echo "✗ Database backup is corrupted"
        exit 1
    fi
fi

# Check application backup
if [ -f "$BACKUP_DIR/application.tar.gz" ]; then
    echo "Verifying application backup..."
    if tar -tzf "$BACKUP_DIR/application.tar.gz" > /dev/null; then
        echo "✓ Application backup is valid"
    else
        echo "✗ Application backup is corrupted"
        exit 1
    fi
fi

# Check configuration backup
if [ -f "$BACKUP_DIR/config.tar.gz" ]; then
    echo "Verifying configuration backup..."
    if tar -tzf "$BACKUP_DIR/config.tar.gz" > /dev/null; then
        echo "✓ Configuration backup is valid"
    else
        echo "✗ Configuration backup is corrupted"
        exit 1
    fi
fi

# Check data backup
if [ -f "$BACKUP_DIR/data.tar.gz" ]; then
    echo "Verifying data backup..."
    if tar -tzf "$BACKUP_DIR/data.tar.gz" > /dev/null; then
        echo "✓ Data backup is valid"
    else
        echo "✗ Data backup is corrupted"
        exit 1
    fi
fi

echo "All backup files are valid"
```

### Test Restore
```bash
#!/bin/bash
# Test restore script

BACKUP_DIR="$1"
TEST_DIR="/tmp/ggnet_test_restore"

if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

echo "Testing restore from $BACKUP_DIR..."

# Create test directory
mkdir -p $TEST_DIR

# Test database restore
if [ -f "$BACKUP_DIR/database.sql.gz" ]; then
    echo "Testing database restore..."
    sudo -u postgres psql -c "CREATE DATABASE ggnet_test;"
    sudo -u postgres psql ggnet_test < $BACKUP_DIR/database.sql.gz
    
    # Verify database
    TABLE_COUNT=$(sudo -u postgres psql ggnet_test -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    echo "✓ Database restore successful. Tables: $TABLE_COUNT"
    
    # Cleanup test database
    sudo -u postgres psql -c "DROP DATABASE ggnet_test;"
fi

# Test file restore
if [ -f "$BACKUP_DIR/application.tar.gz" ]; then
    echo "Testing file restore..."
    tar -xzf $BACKUP_DIR/application.tar.gz -C $TEST_DIR
    
    # Verify files
    if [ -f "$TEST_DIR/opt/ggnet/backend/app/main.py" ]; then
        echo "✓ File restore successful"
    else
        echo "✗ File restore failed"
        exit 1
    fi
    
    # Cleanup test files
    rm -rf $TEST_DIR
fi

echo "Test restore completed successfully"
```

## 📋 Best Practices

### Backup Best Practices

#### 1. Regular Testing
- Test backups monthly
- Verify restore procedures
- Document recovery times
- Practice disaster recovery

#### 2. Multiple Locations
- Local storage for quick access
- Network storage for redundancy
- Offsite storage for disaster recovery
- Cloud storage for long-term retention

#### 3. Encryption
- Encrypt sensitive backups
- Use strong encryption keys
- Secure key management
- Regular key rotation

#### 4. Monitoring
- Monitor backup success/failure
- Alert on backup issues
- Track backup sizes
- Monitor storage usage

### Restore Best Practices

#### 1. Documentation
- Document restore procedures
- Keep procedures updated
- Test procedures regularly
- Train staff on procedures

#### 2. Testing
- Test restore procedures
- Verify data integrity
- Check application functionality
- Validate configuration

#### 3. Communication
- Notify stakeholders of restore
- Document restore activities
- Report restore results
- Update procedures as needed

---

This backup and restore guide ensures reliable data protection and recovery for GGnet. Regular testing and updates are essential for maintaining effective backup procedures.
