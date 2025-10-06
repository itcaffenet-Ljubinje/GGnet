# GGnet Operations Runbook

This runbook provides step-by-step instructions for common operational tasks in GGnet.

## 📋 Table of Contents

- [System Administration](#system-administration)
- [User Management](#user-management)
- [Machine Management](#machine-management)
- [Image Management](#image-management)
- [Session Management](#session-management)
- [Target Management](#target-management)
- [Network Configuration](#network-configuration)
- [Backup and Recovery](#backup-and-recovery)
- [Monitoring and Alerting](#monitoring-and-alerting)
- [Troubleshooting](#troubleshooting)
- [Emergency Procedures](#emergency-procedures)

## 🔧 System Administration

### Starting/Stopping Services

#### Start All Services
```bash
# Start core services
sudo systemctl start ggnet-backend
sudo systemctl start ggnet-worker
sudo systemctl start redis-server
sudo systemctl start postgresql

# Check status
sudo systemctl status ggnet-backend ggnet-worker redis-server postgresql
```

#### Stop All Services
```bash
# Stop services gracefully
sudo systemctl stop ggnet-worker
sudo systemctl stop ggnet-backend
sudo systemctl stop redis-server
sudo systemctl stop postgresql
```

#### Restart Services
```bash
# Restart backend services
sudo systemctl restart ggnet-backend ggnet-worker

# Restart infrastructure services
sudo systemctl restart redis-server postgresql nginx
```

### Service Configuration

#### Update Configuration
```bash
# Edit configuration
sudo nano /opt/ggnet/backend/.env

# Reload configuration
sudo systemctl reload ggnet-backend
```

#### Enable/Disable Services
```bash
# Enable services to start on boot
sudo systemctl enable ggnet-backend ggnet-worker

# Disable services
sudo systemctl disable ggnet-backend ggnet-worker
```

### System Maintenance

#### Update Application
```bash
# Stop services
sudo systemctl stop ggnet-backend ggnet-worker

# Backup current installation
sudo cp -r /opt/ggnet /opt/ggnet.backup.$(date +%Y%m%d)

# Update application files
sudo cp -r backend/* /opt/ggnet/backend/
sudo chown -R ggnet:ggnet /opt/ggnet

# Update dependencies
sudo -u ggnet /opt/ggnet/venv/bin/pip install -r /opt/ggnet/backend/requirements.txt

# Run database migrations
sudo -u ggnet /opt/ggnet/venv/bin/alembic upgrade head

# Start services
sudo systemctl start ggnet-backend ggnet-worker
```

#### Clean Up Logs
```bash
# Rotate logs
sudo logrotate -f /etc/logrotate.d/ggnet

# Clean old logs
sudo find /opt/ggnet/logs -name "*.log.*" -mtime +30 -delete
```

## 👥 User Management

### Creating Users

#### Create Admin User
```bash
# Using the web interface
# 1. Login as admin
# 2. Go to Settings → Users
# 3. Click "Add User"
# 4. Fill in details and select "Admin" role

# Using command line
sudo -u ggnet /opt/ggnet/venv/bin/python /opt/ggnet/backend/create_admin.py
```

#### Create Operator User
```bash
# Using API
curl -X POST http://localhost:8000/users \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "operator1",
    "email": "operator1@example.com",
    "full_name": "Operator One",
    "role": "operator",
    "password": "secure_password"
  }'
```

### Managing User Permissions

#### View User Roles
```bash
# List all users
curl -H "Authorization: Bearer <admin_token>" \
  http://localhost:8000/users
```

#### Update User Role
```bash
# Change user role
curl -X PUT http://localhost:8000/users/2 \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"role": "admin"}'
```

#### Reset User Password
```bash
# Reset password via API
curl -X PUT http://localhost:8000/users/2 \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"password": "new_password"}'
```

### User Session Management

#### View Active Sessions
```bash
# Check active user sessions
curl -H "Authorization: Bearer <admin_token>" \
  http://localhost:8000/auth/sessions
```

#### Revoke User Sessions
```bash
# Revoke all sessions for a user
curl -X DELETE http://localhost:8000/auth/sessions/user/2 \
  -H "Authorization: Bearer <admin_token>"
```

## 🖥️ Machine Management

### Adding Machines

#### Add Single Machine
```bash
# Using web interface
# 1. Go to Machines → Add Machine
# 2. Enter MAC address: 00:11:22:33:44:55
# 3. Enter IP address: 192.168.1.100
# 4. Select boot mode: UEFI
# 5. Add description: "Workstation 1"
# 6. Click "Create Machine"

# Using API
curl -X POST http://localhost:8000/machines \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Workstation 1",
    "mac_address": "00:11:22:33:44:55",
    "ip_address": "192.168.1.100",
    "boot_mode": "UEFI",
    "description": "Main workstation"
  }'
```

#### Bulk Import Machines
```bash
# Create CSV file
cat > machines.csv << EOF
name,mac_address,ip_address,boot_mode,description
Workstation 1,00:11:22:33:44:55,192.168.1.100,UEFI,Main workstation
Workstation 2,00:11:22:33:44:56,192.168.1.101,UEFI,Secondary workstation
Workstation 3,00:11:22:33:44:57,192.168.1.102,BIOS,Legacy workstation
EOF

# Import via API (if bulk import endpoint exists)
curl -X POST http://localhost:8000/machines/bulk \
  -H "Authorization: Bearer <token>" \
  -F "file=@machines.csv"
```

### Managing Machine Status

#### Update Machine Status
```bash
# Mark machine as active
curl -X PUT http://localhost:8000/machines/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'

# Mark machine as maintenance
curl -X PUT http://localhost:8000/machines/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "maintenance"}'
```

#### Delete Machine
```bash
# Delete machine
curl -X DELETE http://localhost:8000/machines/1 \
  -H "Authorization: Bearer <token>"
```

## 🖼️ Image Management

### Uploading Images

#### Upload via Web Interface
```bash
# 1. Go to Images → Upload Image
# 2. Select file (VHDX, RAW, QCOW2)
# 3. Enter name and description
# 4. Select image type (System, Application, Data)
# 5. Click "Upload"
```

#### Upload via API
```bash
# Upload image file
curl -X POST http://localhost:8000/images/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/image.vhdx" \
  -F "name=Windows 10 Pro" \
  -F "description=Windows 10 Professional" \
  -F "image_type=SYSTEM"
```

### Image Conversion

#### Monitor Conversion Progress
```bash
# Check conversion status
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/images/1/conversion-status
```

#### Trigger Manual Conversion
```bash
# Trigger conversion
curl -X POST http://localhost:8000/images/1/convert \
  -H "Authorization: Bearer <token>"
```

### Image Management

#### List All Images
```bash
# Get all images
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/images
```

#### Delete Image
```bash
# Delete image
curl -X DELETE http://localhost:8000/images/1 \
  -H "Authorization: Bearer <token>"
```

## 🎯 Session Management

### Starting Sessions

#### Start Diskless Boot Session
```bash
# Using web interface
# 1. Go to Sessions → Start Session
# 2. Select machine
# 3. Select target
# 4. Choose session type: "Diskless Boot"
# 5. Click "Start Session"

# Using API
curl -X POST http://localhost:8000/sessions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "machine_id": 1,
    "target_id": 1,
    "session_type": "DISKLESS_BOOT"
  }'
```

#### Start Maintenance Session
```bash
# Start maintenance session
curl -X POST http://localhost:8000/sessions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "machine_id": 1,
    "target_id": 1,
    "session_type": "MAINTENANCE"
  }'
```

### Monitoring Sessions

#### View Active Sessions
```bash
# List active sessions
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/sessions?status=active
```

#### Get Session Details
```bash
# Get session details
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/sessions/1
```

#### Stop Session
```bash
# Stop session
curl -X POST http://localhost:8000/sessions/1/stop \
  -H "Authorization: Bearer <token>"
```

### Session Statistics

#### Get Session Stats
```bash
# Get session statistics
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/sessions/stats
```

## 🎯 Target Management

### Creating iSCSI Targets

#### Create Target via Web Interface
```bash
# 1. Go to Targets → Create Target
# 2. Select machine
# 3. Select image
# 4. Configure target settings
# 5. Click "Create Target"
```

#### Create Target via API
```bash
# Create iSCSI target
curl -X POST http://localhost:8000/api/v1/targets \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "machine_id": 1,
    "image_id": 1,
    "description": "Windows 10 target"
  }'
```

### Managing Targets

#### List All Targets
```bash
# Get all targets
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/targets
```

#### Update Target
```bash
# Update target description
curl -X PUT http://localhost:8000/api/v1/targets/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"description": "Updated description"}'
```

#### Delete Target
```bash
# Delete target
curl -X DELETE http://localhost:8000/api/v1/targets/1 \
  -H "Authorization: Bearer <token>"
```

## 🌐 Network Configuration

### DHCP Configuration

#### Configure DHCP Server
```bash
# Edit DHCP configuration
sudo nano /etc/dhcp/dhcpd.conf

# Add subnet configuration
subnet 192.168.1.0 netmask 255.255.255.0 {
    range 192.168.1.100 192.168.1.200;
    option routers 192.168.1.1;
    option domain-name-servers 192.168.1.1;
    
    # PXE boot configuration
    next-server 192.168.1.10;
    filename "bootx64.efi";
}

# Restart DHCP server
sudo systemctl restart isc-dhcp-server
```

#### Add DHCP Reservations
```bash
# Add static reservation
host workstation1 {
    hardware ethernet 00:11:22:33:44:55;
    fixed-address 192.168.1.100;
    option host-name "workstation1";
}
```

### TFTP Configuration

#### Configure TFTP Server
```bash
# Edit TFTP configuration
sudo nano /etc/default/tftpd-hpa

# Set TFTP directory
TFTP_DIRECTORY="/var/lib/tftpboot"
TFTP_ADDRESS="0.0.0.0:69"
TFTP_OPTIONS="--secure"

# Restart TFTP server
sudo systemctl restart tftpd-hpa
```

#### Deploy Boot Files
```bash
# Copy boot files
sudo cp /usr/lib/ipxe/ipxe.efi /var/lib/tftpboot/bootx64.efi
sudo cp /usr/lib/ipxe/undionly.kpxe /var/lib/tftpboot/

# Set permissions
sudo chown -R tftp:tftp /var/lib/tftpboot
sudo chmod -R 755 /var/lib/tftpboot
```

### iSCSI Configuration

#### Configure iSCSI Target
```bash
# Start target service
sudo systemctl start target

# Configure targetcli
sudo targetcli
targetcli> /backstores/fileio create disk1 /var/lib/ggnet/images/image1.raw 10G
targetcli> /iscsi create iqn.2025.ggnet:target1
targetcli> /iscsi/iqn.2025.ggnet:target1/tpg1/luns create /backstores/fileio/disk1
targetcli> /iscsi/iqn.2025.ggnet:target1/tpg1/acls create iqn.2025.ggnet:initiator1
targetcli> saveconfig
targetcli> exit
```

## 💾 Backup and Recovery

### Database Backup

#### Create Database Backup
```bash
# Create backup
sudo -u postgres pg_dump ggnet > /opt/ggnet/backups/ggnet_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip /opt/ggnet/backups/ggnet_$(date +%Y%m%d_%H%M%S).sql
```

#### Automated Backup Script
```bash
# Create backup script
sudo nano /opt/ggnet/scripts/backup.sh

#!/bin/bash
BACKUP_DIR="/opt/ggnet/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
sudo -u postgres pg_dump ggnet | gzip > $BACKUP_DIR/ggnet_db_$DATE.sql.gz

# Configuration backup
tar -czf $BACKUP_DIR/ggnet_config_$DATE.tar.gz /opt/ggnet/backend/.env /etc/nginx/sites-available/ggnet.conf

# Images backup (if needed)
# tar -czf $BACKUP_DIR/ggnet_images_$DATE.tar.gz /var/lib/ggnet/images/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

# Make executable
sudo chmod +x /opt/ggnet/scripts/backup.sh

# Add to crontab
echo "0 2 * * * /opt/ggnet/scripts/backup.sh" | sudo crontab -
```

### Database Recovery

#### Restore from Backup
```bash
# Stop services
sudo systemctl stop ggnet-backend ggnet-worker

# Restore database
sudo -u postgres psql ggnet < /opt/ggnet/backups/ggnet_20240101_120000.sql

# Start services
sudo systemctl start ggnet-backend ggnet-worker
```

### Configuration Recovery

#### Restore Configuration
```bash
# Extract configuration backup
tar -xzf /opt/ggnet/backups/ggnet_config_20240101_120000.tar.gz -C /

# Restart services
sudo systemctl restart ggnet-backend nginx
```

## 📊 Monitoring and Alerting

### Health Monitoring

#### Check System Health
```bash
# Basic health check
curl http://localhost:8000/health/

# Detailed health check
curl http://localhost:8000/health/detailed
```

#### Monitor System Resources
```bash
# Check CPU usage
curl http://localhost:8000/metrics/ | grep cpu

# Check memory usage
curl http://localhost:8000/metrics/ | grep memory

# Check disk usage
df -h
```

### Log Monitoring

#### View Application Logs
```bash
# View recent logs
sudo journalctl -u ggnet-backend -f

# View error logs
sudo journalctl -u ggnet-backend --priority=err

# View logs from specific time
sudo journalctl -u ggnet-backend --since "2024-01-01 10:00:00"
```

#### Monitor Log Files
```bash
# Monitor application log
tail -f /opt/ggnet/logs/app.log

# Monitor error log
tail -f /opt/ggnet/logs/error.log

# Monitor audit log
tail -f /opt/ggnet/logs/audit.log
```

### Alerting Setup

#### Configure Prometheus Alerts
```bash
# Edit alert rules
sudo nano /etc/prometheus/alert_rules.yml

groups:
- name: ggnet
  rules:
  - alert: GGnetServiceDown
    expr: up{job="ggnet"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "GGnet service is down"
      
  - alert: HighCPUUsage
    expr: ggnet_system_cpu_percent > 90
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage detected"
```

## 🔧 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
sudo systemctl status ggnet-backend

# Check logs
sudo journalctl -u ggnet-backend -n 50

# Check configuration
sudo -u ggnet /opt/ggnet/venv/bin/python -c "
from app.core.config import get_settings
print(get_settings())
"
```

#### Database Connection Issues
```bash
# Test database connection
sudo -u postgres psql -c "SELECT 1;"

# Check database status
sudo systemctl status postgresql

# Test application database connection
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

#### Redis Connection Issues
```bash
# Test Redis connection
redis-cli ping

# Check Redis status
sudo systemctl status redis-server

# Check Redis logs
sudo journalctl -u redis-server -f
```

#### Image Upload Issues
```bash
# Check disk space
df -h

# Check file permissions
ls -la /var/lib/ggnet/images/

# Check upload directory
ls -la /opt/ggnet/uploads/

# Check nginx configuration
sudo nginx -t
```

#### iSCSI Target Issues
```bash
# Check targetcli
sudo targetcli ls

# Check iSCSI service
sudo systemctl status target

# Check network connectivity
telnet <server_ip> 3260

# Check firewall
sudo ufw status
```

### Performance Issues

#### High CPU Usage
```bash
# Check running processes
htop

# Check system load
uptime

# Check specific process
ps aux | grep ggnet

# Profile application
sudo -u ggnet /opt/ggnet/venv/bin/python -m cProfile /opt/ggnet/backend/app/main.py
```

#### High Memory Usage
```bash
# Check memory usage
free -h

# Check memory by process
ps aux --sort=-%mem | head

# Check Redis memory
redis-cli info memory
```

#### Slow Database Queries
```bash
# Check slow queries
sudo -u postgres psql ggnet -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"

# Check database size
sudo -u postgres psql ggnet -c "
SELECT pg_size_pretty(pg_database_size('ggnet'));
"
```

## 🚨 Emergency Procedures

### Service Recovery

#### Complete Service Restart
```bash
# Stop all services
sudo systemctl stop ggnet-worker
sudo systemctl stop ggnet-backend
sudo systemctl stop redis-server
sudo systemctl stop postgresql

# Wait 10 seconds
sleep 10

# Start services in order
sudo systemctl start postgresql
sleep 5
sudo systemctl start redis-server
sleep 5
sudo systemctl start ggnet-backend
sleep 5
sudo systemctl start ggnet-worker

# Check status
sudo systemctl status ggnet-backend ggnet-worker
```

#### Emergency Database Recovery
```bash
# Stop services
sudo systemctl stop ggnet-backend ggnet-worker

# Restore from latest backup
LATEST_BACKUP=$(ls -t /opt/ggnet/backups/ggnet_db_*.sql.gz | head -1)
sudo -u postgres psql ggnet < $LATEST_BACKUP

# Start services
sudo systemctl start ggnet-backend ggnet-worker
```

### Data Recovery

#### Recover Deleted Images
```bash
# Check if files exist in trash
ls -la /var/lib/ggnet/images/.trash/

# Restore from backup
tar -xzf /opt/ggnet/backups/ggnet_images_20240101_120000.tar.gz -C /
```

#### Recover Configuration
```bash
# Restore from backup
tar -xzf /opt/ggnet/backups/ggnet_config_20240101_120000.tar.gz -C /

# Restart services
sudo systemctl restart ggnet-backend nginx
```

### Security Incidents

#### Suspend User Access
```bash
# Disable user account
curl -X PUT http://localhost:8000/users/2 \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'

# Revoke all sessions
curl -X DELETE http://localhost:8000/auth/sessions/user/2 \
  -H "Authorization: Bearer <admin_token>"
```

#### Emergency Shutdown
```bash
# Stop all services immediately
sudo systemctl stop ggnet-worker
sudo systemctl stop ggnet-backend

# Block network access
sudo ufw deny 8000
sudo ufw deny 3260

# Notify administrators
echo "Emergency shutdown initiated" | mail -s "GGnet Emergency" admin@example.com
```

---

This runbook provides comprehensive operational procedures for GGnet. Keep it updated as the system evolves and new procedures are developed.
