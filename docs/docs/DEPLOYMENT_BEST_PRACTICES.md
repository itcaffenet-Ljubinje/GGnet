# Deployment Best Practices

Best practices for deploying ggNET2 in production.

## Pre-Deployment Checklist

### System Requirements

- [ ] Linux server (Ubuntu 20.04+ or Debian 11+)
- [ ] Minimum 16GB RAM (32GB+ recommended)
- [ ] Minimum 4 CPU cores (8+ recommended)
- [ ] SSD for ZFS cache and logs
- [ ] Network connectivity configured
- [ ] Firewall rules configured

### Software Dependencies

- [ ] Python 3.10+ installed
- [ ] PostgreSQL 14+ installed and configured
- [ ] ZFS installed and configured
- [ ] Node.js 18+ installed (for frontend)
- [ ] System utilities (smartmontools, util-linux, etc.)

### Security

- [ ] Change default admin password
- [ ] Configure firewall (UFW or iptables)
- [ ] Enable HTTPS/TLS
- [ ] Configure SSL certificates
- [ ] Set secure JWT secret key
- [ ] Disable debug mode
- [ ] Review file permissions

## Database Setup

### PostgreSQL Configuration

1. **Create Database:**
```bash
sudo -u postgres createdb ggnet2
sudo -u postgres createuser ggnet2
sudo -u postgres psql -c "ALTER USER ggnet2 WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ggnet2 TO ggnet2;"
```

2. **Configure PostgreSQL:**
Edit `/etc/postgresql/14/main/postgresql.conf`:
```ini
max_connections = 100
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 20MB
min_wal_size = 1GB
max_wal_size = 4GB
```

3. **Run Migrations:**
```bash
alembic upgrade head
```

4. **Initialize Default Data:**
```bash
python -m app.backend.auth.init_default_data
```

## ZFS Setup

### Pool Creation

1. **Create ZFS Pool:**
```bash
# For mirror (recommended for production)
zpool create -f pool0 mirror /dev/sda /dev/sdb

# For RAID-Z2 (4+ drives)
zpool create -f pool0 raidz2 /dev/sda /dev/sdb /dev/sdc /dev/sdd
```

2. **Configure Pool:**
```bash
# Set compression
zfs set compression=lz4 pool0

# Set ARC max (adjust based on RAM)
echo 8589934592 > /sys/module/zfs/parameters/zfs_arc_max

# Create datasets
zfs create pool0/ggnet2
zfs create pool0/ggnet2/images
zfs create pool0/ggnet2/clones
```

### Pool Monitoring

```bash
# Check pool status
zpool status pool0

# Monitor I/O
zpool iostat pool0 1

# Check ARC stats
arcstat 1
```

## Application Configuration

### Environment Variables

Create `.env` file:

```env
# Application
APP_NAME=ggnet2
DEBUG=False
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://ggnet2:secure_password@localhost:5432/ggnet2
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Security
SECRET_KEY=your-very-secure-secret-key-here-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ZFS
ZFS_POOL_NAME=pool0
ZFS_BASE_PATH=pool0/ggnet2
ZFS_IMAGES_PATH=pool0/ggnet2/images
ZFS_CLONES_PATH=pool0/ggnet2/clones

# Network
SERVER_IP=192.168.1.100
BRIDGE_NAME=vmbr0
DHCP_RANGE_START=192.168.1.100
DHCP_RANGE_END=192.168.1.200

# CORS
CORS_ORIGINS=https://yourdomain.com
CORS_ALLOW_CREDENTIALS=True
```

### File Permissions

```bash
# Set secure permissions
chmod 600 .env
chown ggnet2:ggnet2 .env

# Application files
chmod 755 app/
chown -R ggnet2:ggnet2 app/
```

## Service Configuration

### Systemd Service

Create `/etc/systemd/system/ggnet2.service`:

```ini
[Unit]
Description=ggNET2 Backend Service
After=network.target postgresql.service

[Service]
Type=simple
User=ggnet2
Group=ggnet2
WorkingDirectory=/opt/ggnet2
Environment="PATH=/opt/ggnet2/venv/bin"
ExecStart=/opt/ggnet2/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ggnet2
sudo systemctl start ggnet2
sudo systemctl status ggnet2
```

### Nginx Reverse Proxy

Create `/etc/nginx/sites-available/ggnet2`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend
    location / {
        root /opt/ggnet2/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/ggnet2 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL/TLS Configuration

### Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Firewall Configuration

### UFW

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

## Backup Strategy

### Database Backup

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR=/backup/ggnet2
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U ggnet2 ggnet2 | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
```

### ZFS Snapshots

```bash
# Create snapshot
zfs snapshot pool0/ggnet2@backup_$(date +%Y%m%d)

# List snapshots
zfs list -t snapshot pool0/ggnet2

# Send snapshot to backup location
zfs send pool0/ggnet2@backup_20250101 | \
  zfs receive backup-pool/ggnet2@backup_20250101
```

## Monitoring

### Log Rotation

Configure logrotate `/etc/logrotate.d/ggnet2`:

```
/opt/ggnet2/app/backend/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 ggnet2 ggnet2
}
```

### Health Checks

```bash
# API health check
curl -f http://localhost:8000/api/health || exit 1

# Database check
psql -U ggnet2 -d ggnet2 -c "SELECT 1;" || exit 1

# ZFS pool check
zpool status pool0 | grep -q "ONLINE" || exit 1
```

## Updates and Maintenance

### Application Updates

1. Backup database and ZFS snapshots
2. Pull latest code
3. Run migrations: `alembic upgrade head`
4. Restart service: `sudo systemctl restart ggnet2`
5. Verify functionality

### System Updates

```bash
# Update system packages
sudo apt update
sudo apt upgrade

# Reboot if kernel updated
sudo reboot
```

## Disaster Recovery

### Recovery Plan

1. **Database Recovery:**
   ```bash
   # Restore from backup
   gunzip < backup.sql.gz | psql -U ggnet2 ggnet2
   ```

2. **ZFS Recovery:**
   ```bash
   # Import pool
   zpool import pool0
   
   # Restore from snapshot
   zfs rollback pool0/ggnet2@backup_20250101
   ```

3. **Full System Recovery:**
   - Restore database
   - Restore ZFS snapshots
   - Restore configuration files
   - Verify services

## Security Hardening

1. **Disable Root Login:**
   ```bash
   sudo passwd -l root
   ```

2. **Fail2Ban:**
   ```bash
   sudo apt install fail2ban
   sudo systemctl enable fail2ban
   ```

3. **Regular Security Updates:**
   ```bash
   sudo apt install unattended-upgrades
   ```

4. **Audit Logging:**
   - Enable auditd
   - Monitor authentication attempts
   - Review logs regularly

## Performance Tuning

See [PERFORMANCE_TUNING.md](./PERFORMANCE_TUNING.md) for detailed optimization guide.

## Support

For issues or questions:
1. Check logs: `app/backend/logs/`
2. Review [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
3. Check GitHub issues
4. Contact support

