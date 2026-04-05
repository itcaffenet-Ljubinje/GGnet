# Production Readiness Guide za ggNET2

**Datum kreiranja:** 2025-01-26  
**Status:** 📋 Kompletan Production Readiness Guide

---

## 📊 Pregled

Ovaj dokument sadrži kompletan vodič za production readiness ggNET2 sistema. Pokriva sve aspekte potrebne za siguran i stabilan production deployment.

---

## 🔒 Security Hardening

### 1. Authentication & Authorization

#### 1.1 Change Default Passwords
```bash
# Change admin password via API or UI
curl -X PUT http://localhost:8000/api/v1/users/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password": "new_secure_password"}'

# Or via UI: Settings → Users → Change Password
```

**Checklist:**
- [ ] Admin password changed from default
- [ ] All default user passwords changed
- [ ] Strong password policy enforced
- [ ] Password expiration policy configured (optional)

#### 1.2 JWT Secret Key
```bash
# Generate secure JWT secret key
openssl rand -hex 32

# Update .env file
JWT_SECRET_KEY=your_generated_secret_key_here
```

**Checklist:**
- [ ] JWT secret key changed from default
- [ ] Secret key is at least 32 characters
- [ ] Secret key stored securely (not in git)
- [ ] Secret key rotated periodically

#### 1.3 Review RBAC Permissions
```bash
# List all roles and permissions
curl http://localhost:8000/api/v1/users/roles \
  -H "Authorization: Bearer $TOKEN"
```

**Checklist:**
- [ ] All roles reviewed
- [ ] Permissions follow least privilege principle
- [ ] Test permission enforcement
- [ ] Document role hierarchy
- [ ] Regular permission audits scheduled

### 2. Network Security

#### 2.1 Firewall Configuration
```bash
# Review firewall rules
sudo ufw status verbose

# Ensure only necessary ports are open
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw deny 8000/tcp    # Backend (only accessible via Nginx)
```

**Checklist:**
- [ ] Firewall enabled and configured
- [ ] Only necessary ports open
- [ ] Backend API not directly accessible
- [ ] SSH access restricted (key-based only)
- [ ] Rate limiting configured

#### 2.2 SSL/TLS Configuration
```bash
# Verify SSL certificate
sudo certbot certificates

# Test SSL configuration
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Check SSL rating
# Visit: https://www.ssllabs.com/ssltest/
```

**Checklist:**
- [ ] SSL/TLS certificates installed
- [ ] Auto-renewal configured
- [ ] Strong cipher suites enabled
- [ ] HSTS enabled (optional)
- [ ] Certificate expiration monitored

#### 2.3 CORS Configuration
```python
# Review CORS settings in app/main.py
CORS_ORIGINS = [
    "https://your-domain.com",
    "https://www.your-domain.com",
]
```

**Checklist:**
- [ ] CORS origins restricted to known domains
- [ ] No wildcard origins in production
- [ ] Credentials handling configured correctly
- [ ] CORS headers reviewed

### 3. Input Validation & Sanitization

#### 3.1 API Input Validation
```python
# All API endpoints should use Pydantic models for validation
# Example:
class MachineCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    mac_address: str = Field(..., regex=r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
```

**Checklist:**
- [ ] All API endpoints validate input
- [ ] Pydantic models used for validation
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified
- [ ] File upload validation (if applicable)
- [ ] Path traversal prevention

#### 3.2 Frontend Input Validation
```javascript
// All forms should validate input client-side
// Example:
const validateMachineName = (name) => {
  if (!name || name.length < 1 || name.length > 255) {
    return 'Machine name must be between 1 and 255 characters';
  }
  return null;
};
```

**Checklist:**
- [ ] All forms validate input
- [ ] Client-side validation implemented
- [ ] Server-side validation enforced
- [ ] Error messages don't leak sensitive info
- [ ] Input sanitization applied

### 4. Rate Limiting

#### 4.1 API Rate Limiting
```python
# Rate limiting is configured in app/main.py
# Review and adjust limits as needed
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"]
)
```

**Checklist:**
- [ ] Rate limiting enabled
- [ ] Limits appropriate for production
- [ ] Different limits for different endpoints
- [ ] Rate limit headers returned
- [ ] Rate limit errors handled gracefully

### 5. Security Headers

#### 5.1 Nginx Security Headers
```nginx
# Add to Nginx configuration
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

**Checklist:**
- [ ] Security headers configured
- [ ] CSP policy reviewed
- [ ] Headers tested
- [ ] Security headers monitoring

---

## 📊 Monitoring & Logging

### 1. Logging Configuration

#### 1.1 Application Logging
```python
# Configure logging in app/main.py
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            '/opt/ggnet2/logs/app.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)
```

**Checklist:**
- [ ] Logging configured
- [ ] Log rotation configured
- [ ] Log levels appropriate (INFO in production)
- [ ] Sensitive data not logged
- [ ] Log files secured (permissions)
- [ ] Log retention policy defined

#### 1.2 Access Logging
```nginx
# Nginx access logs
access_log /var/log/nginx/ggnet2_access.log;
error_log /var/log/nginx/ggnet2_error.log;
```

**Checklist:**
- [ ] Access logs configured
- [ ] Error logs configured
- [ ] Log rotation configured
- [ ] Log analysis tools setup (optional)

### 2. Monitoring Setup

#### 2.1 System Monitoring
```bash
# Install monitoring tools (optional)
sudo apt install -y htop iotop nethogs

# Setup system monitoring
# Consider: Prometheus, Grafana, or cloud monitoring
```

**Checklist:**
- [ ] System metrics monitored (CPU, RAM, disk)
- [ ] Network metrics monitored
- [ ] Disk I/O monitored
- [ ] Alerts configured
- [ ] Dashboard created

#### 2.2 Application Monitoring
```python
# Add application metrics
from prometheus_client import Counter, Histogram, Gauge

api_requests = Counter('api_requests_total', 'Total API requests')
api_latency = Histogram('api_latency_seconds', 'API latency')
active_users = Gauge('active_users', 'Active users')
```

**Checklist:**
- [ ] Application metrics collected
- [ ] API response times monitored
- [ ] Error rates monitored
- [ ] User activity monitored
- [ ] Custom metrics defined

#### 2.3 Database Monitoring
```bash
# PostgreSQL monitoring
# Enable pg_stat_statements extension
sudo -u postgres psql -d ggnet2 -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"
```

**Checklist:**
- [ ] Database performance monitored
- [ ] Slow queries identified
- [ ] Connection pool monitored
- [ ] Database size monitored
- [ ] Backup status monitored

### 3. Alerting

#### 3.1 Alert Configuration
```bash
# Setup alerting (example with Prometheus Alertmanager)
# Or use cloud monitoring (AWS CloudWatch, Datadog, etc.)
```

**Alert Conditions:**
- [ ] High CPU usage (>80%)
- [ ] High memory usage (>90%)
- [ ] Disk space low (<20% free)
- [ ] API error rate high (>5%)
- [ ] Database connection pool exhausted
- [ ] Service down
- [ ] SSL certificate expiring soon

**Checklist:**
- [ ] Alerts configured
- [ ] Alert channels setup (email, Slack, PagerDuty)
- [ ] Alert thresholds appropriate
- [ ] Alert testing performed
- [ ] On-call rotation defined

---

## 💾 Backup Strategy

### 1. Database Backup

#### 1.1 Automated Database Backup
```bash
# Create backup script
sudo vim /opt/ggnet2/scripts/backup_db.sh
```

**Backup Script:**
```bash
#!/bin/bash
BACKUP_DIR="/opt/ggnet2/backups/db"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U ggnet2 -d ggnet2 -F c -f $BACKUP_DIR/db_$DATE.dump

# Compress
gzip $BACKUP_DIR/db_$DATE.dump

# Remove old backups
find $BACKUP_DIR -name "db_*.dump.gz" -mtime +$RETENTION_DAYS -delete

# Verify backup
if [ -f $BACKUP_DIR/db_$DATE.dump.gz ]; then
    echo "Backup successful: db_$DATE.dump.gz"
else
    echo "Backup failed!" | mail -s "ggNET2 Backup Failed" admin@example.com
    exit 1
fi
```

```bash
# Make executable
chmod +x /opt/ggnet2/scripts/backup_db.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /opt/ggnet2/scripts/backup_db.sh
```

**Checklist:**
- [ ] Automated backup script created
- [ ] Backup scheduled (daily recommended)
- [ ] Backup retention policy defined
- [ ] Backup verification implemented
- [ ] Backup restoration tested
- [ ] Off-site backup configured (optional)

#### 1.2 Backup Restoration
```bash
# Test restoration procedure
# Stop application
sudo systemctl stop ggnet2-backend

# Restore database
gunzip < /opt/ggnet2/backups/db/db_20250126_020000.dump.gz | \
  pg_restore -U ggnet2 -d ggnet2 -c

# Start application
sudo systemctl start ggnet2-backend
```

**Checklist:**
- [ ] Restoration procedure documented
- [ ] Restoration tested
- [ ] Restoration time estimated
- [ ] Rollback plan defined

### 2. Configuration Backup

#### 2.1 Configuration Files Backup
```bash
# Backup configuration files
sudo vim /opt/ggnet2/scripts/backup_config.sh
```

**Backup Script:**
```bash
#!/bin/bash
BACKUP_DIR="/opt/ggnet2/backups/config"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup configuration files
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
  /opt/ggnet2/.env \
  /etc/nginx/sites-available/ggnet2 \
  /etc/systemd/system/ggnet2-*.service \
  /opt/ggnet2/alembic.ini

echo "Configuration backup created: config_$DATE.tar.gz"
```

**Checklist:**
- [ ] Configuration backup script created
- [ ] Configuration backup scheduled
- [ ] Configuration version controlled (git)
- [ ] Configuration restoration tested

### 3. ZFS Snapshot Strategy

#### 3.1 Automated ZFS Snapshots
```bash
# Create snapshot script
sudo vim /opt/ggnet2/scripts/zfs_snapshot.sh
```

**Snapshot Script:**
```bash
#!/bin/bash
POOL_NAME="pool0"
RETENTION_DAYS=7

# Create snapshot
sudo zfs snapshot ${POOL_NAME}@backup_$(date +%Y%m%d_%H%M%S)

# Remove old snapshots
sudo zfs list -t snapshot -o name | grep "@backup_" | \
  while read snap; do
    snap_date=$(echo $snap | grep -oP '@backup_\K[0-9]{8}')
    if [ ! -z "$snap_date" ]; then
      days_old=$(( ($(date +%s) - $(date -d "$snap_date" +%s)) / 86400 ))
      if [ $days_old -gt $RETENTION_DAYS ]; then
        sudo zfs destroy $snap
      fi
    fi
  done
```

**Checklist:**
- [ ] ZFS snapshot script created
- [ ] Snapshots scheduled
- [ ] Snapshot retention policy defined
- [ ] Snapshot restoration tested
- [ ] Snapshot space monitored

### 4. Disaster Recovery Plan

#### 4.1 Recovery Procedures
```markdown
# Document recovery procedures for:
- Complete server failure
- Database corruption
- ZFS pool failure
- Network outage
- Data center failure
```

**Checklist:**
- [ ] Disaster recovery plan documented
- [ ] Recovery procedures tested
- [ ] Recovery time objectives (RTO) defined
- [ ] Recovery point objectives (RPO) defined
- [ ] Off-site backups configured
- [ ] Recovery team identified

---

## ⚡ Performance Optimization

### 1. Database Optimization

#### 1.1 PostgreSQL Configuration
```bash
# Review and optimize PostgreSQL settings
sudo vim /etc/postgresql/14/main/postgresql.conf
```

**Key Settings:**
```ini
# Memory settings (adjust based on available RAM)
shared_buffers = 4GB                    # 25% of RAM
effective_cache_size = 12GB             # 75% of RAM
maintenance_work_mem = 1GB
work_mem = 64MB

# Checkpoint settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB

# Query planner
random_page_cost = 1.1                   # For SSD
effective_io_concurrency = 200          # For SSD

# Connection settings
max_connections = 100
```

**Checklist:**
- [ ] PostgreSQL configuration optimized
- [ ] Settings appropriate for hardware
- [ ] Query performance analyzed
- [ ] Indexes created for frequently queried columns
- [ ] Vacuum and analyze scheduled

#### 1.2 Database Indexes
```sql
-- Review and create indexes as needed
CREATE INDEX IF NOT EXISTS idx_machines_status ON machines(status);
CREATE INDEX IF NOT EXISTS idx_images_type ON images(image_type);
CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs(timestamp);
```

**Checklist:**
- [ ] Indexes created for foreign keys
- [ ] Indexes created for frequently queried columns
- [ ] Index usage monitored
- [ ] Unused indexes removed

### 2. Application Optimization

#### 2.1 API Response Caching
```python
# Caching is configured in app/main.py
# Review cache settings
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

# Configure Redis cache (if using Redis)
```

**Checklist:**
- [ ] Caching enabled for appropriate endpoints
- [ ] Cache TTL configured
- [ ] Cache invalidation strategy defined
- [ ] Cache hit rate monitored

#### 2.2 Connection Pooling
```python
# Database connection pooling configured
# Review pool settings in app/backend/config/database.py
```

**Checklist:**
- [ ] Connection pool size appropriate
- [ ] Connection pool monitored
- [ ] Connection leaks prevented

### 3. Frontend Optimization

#### 3.1 Build Optimization
```bash
# Build production frontend with optimizations
cd /opt/ggnet2/app/frontend
npm run build

# Verify build size
du -sh dist/
```

**Checklist:**
- [ ] Production build optimized
- [ ] Bundle size minimized
- [ ] Code splitting implemented
- [ ] Lazy loading implemented
- [ ] Images optimized

#### 3.2 Nginx Optimization
```nginx
# Enable gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss;

# Enable caching
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

**Checklist:**
- [ ] Gzip compression enabled
- [ ] Static file caching configured
- [ ] Browser caching headers set
- [ ] CDN configured (if applicable)

---

## ✅ Production Readiness Checklist

### Pre-Production
- [ ] Security hardening completed
- [ ] All default passwords changed
- [ ] SSL/TLS configured
- [ ] Firewall configured
- [ ] Rate limiting enabled
- [ ] Input validation verified
- [ ] Security headers configured

### Monitoring & Logging
- [ ] Logging configured
- [ ] Log rotation configured
- [ ] Monitoring tools setup
- [ ] Alerts configured
- [ ] Dashboards created

### Backup & Recovery
- [ ] Database backup automated
- [ ] Configuration backup automated
- [ ] ZFS snapshots automated
- [ ] Backup restoration tested
- [ ] Disaster recovery plan documented

### Performance
- [ ] Database optimized
- [ ] Application optimized
- [ ] Frontend optimized
- [ ] Caching configured
- [ ] Performance tested

### Documentation
- [ ] Deployment guide reviewed
- [ ] Operations runbook created
- [ ] Troubleshooting guide available
- [ ] Team trained
- [ ] On-call procedures defined

---

## 📚 Additional Resources

- **Deployment Guide:** `docs/DEPLOYMENT_COMPLETE_GUIDE.md`
- **Security Guide:** `docs/SECURITY.md`
- **Performance Tuning:** `docs/PERFORMANCE_TUNING.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING.md`
- **API Documentation:** `http://your-domain.com/docs`

---

**Production Ready!** 🎉

