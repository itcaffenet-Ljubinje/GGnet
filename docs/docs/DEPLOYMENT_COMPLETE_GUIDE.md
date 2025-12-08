# Kompletan Deployment Guide za ggNET2

**Datum kreiranja:** 2025-01-26  
**Status:** 📋 Kompletan Deployment Guide

---

## 📊 Pregled

Ovaj dokument sadrži kompletan vodič za deployment ggNET2 sistema na production server. Pokriva sve korake od server pripreme do production readiness.

---

## 🔧 Server Preparation

### 1. System Requirements

#### Minimum Requirements
- **OS:** Debian 11/12 ili Ubuntu 20.04/22.04 LTS
- **CPU:** 4+ cores
- **RAM:** 8GB minimum (16GB recommended)
- **Storage:** 100GB+ za OS i aplikaciju, dodatni storage za ZFS pool
- **Network:** Gigabit Ethernet

#### Recommended Requirements
- **OS:** Debian 12 ili Ubuntu 22.04 LTS
- **CPU:** 8+ cores
- **RAM:** 32GB+
- **Storage:** SSD za OS, HDD/SSD za ZFS pool
- **Network:** 10 Gigabit Ethernet (za production)

### 2. Initial Server Setup

#### 2.1 OS Installation
```bash
# Install Debian/Ubuntu minimal
# During installation:
# - Set hostname: ggnet2-server
# - Configure network (static IP recommended)
# - Create admin user (not root)
# - Enable SSH
```

#### 2.2 Update System
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y curl wget git vim
```

#### 2.3 Configure Network
```bash
# Edit /etc/network/interfaces or use netplan (Ubuntu)
# Set static IP address
# Configure DNS servers
# Test connectivity
ping -c 4 8.8.8.8
```

#### 2.4 Configure SSH
```bash
# Edit /etc/ssh/sshd_config
# - Disable root login
# - Use key-based authentication
# - Change default port (optional)
sudo systemctl restart sshd
```

#### 2.5 Prepare Storage for ZFS
```bash
# Install ZFS
sudo apt install -y zfsutils-linux

# Identify available drives
lsblk

# Note: ZFS pool creation will be done during installation
```

---

## 📦 Installation

### 1. Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/ggnet2
sudo chown $USER:$USER /opt/ggnet2

# Clone repository
cd /opt/ggnet2
git clone <repository-url> .

# Or if using existing repository
cd /opt/ggnet2
git pull origin main
```

### 2. Install Dependencies

#### 2.1 System Dependencies
```bash
# Install required system packages
sudo apt install -y \
  python3.11 python3.11-venv python3-pip \
  postgresql postgresql-contrib \
  nginx \
  nodejs npm \
  build-essential \
  libpq-dev \
  zfsutils-linux \
  smartmontools \
  util-linux \
  wakeonlan
```

**Alternativno - koristite installation script:**
```bash
# Make script executable
chmod +x scripts/install_system_utilities.sh

# Run installation script (instalira util-linux, smartmontools, wakeonlan)
sudo ./scripts/install_system_utilities.sh
```

**Napomena:** Ovi utilities su potrebni za:
- **util-linux**: Drive management (`lsblk` komanda)
- **smartmontools**: SMART data reading (`smartctl` komanda)
- **wakeonlan**: Wake-on-LAN funkcionalnost (opciono)

Više informacija: `docs/SYSTEM_UTILITIES.md`

#### 2.2 Python Virtual Environment
```bash
# Create virtual environment
cd /opt/ggnet2
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2.3 Node.js Dependencies
```bash
# Install Node.js dependencies
cd /opt/ggnet2/app/frontend
npm install
```

### 3. Configure Environment Variables (OPTIONAL)

**Zero-Config Setup (Preporučeno):**

Aplikacija može raditi **bez `.env` fajla**! Automatski:
- ✅ Detektuje server IP adresu
- ✅ Generiše JWT secret key
- ✅ Konfiguriše CORS origins
- ✅ Koristi default database URL (localhost)

**Za custom konfiguraciju:**

```bash
# Create .env file (opciono)
cd /opt/ggnet2
cp .env.example .env
vim .env
```

**Napomena:** 
- Zero-config setup je preporučen za development i brzu instalaciju
- `.env` fajl je opciono - koristite ga samo ako želite custom konfiguraciju
- Više informacija: `docs/ZERO_CONFIG_SETUP.md`

**Required Environment Variables:**

Pogledajte `.env.example` fajl u root direktorijumu za kompletan template sa svim varijablama.

**Ključne varijable koje MORATE postaviti:**
```env
# Database (MORATE PROMENITI!)
DATABASE_URL=postgresql://ggnet2:your_secure_password@localhost:5432/ggnet2

# Security (MORATE PROMENITI!)
SECRET_KEY=your_very_secure_secret_key_minimum_32_characters
JWT_SECRET_KEY=your_very_secure_secret_key_minimum_32_characters

# Admin User (MORATE PROMENITI!)
ADMIN_PASSWORD=change_this_password
```

**Više informacija:** `docs/ENVIRONMENT_VARIABLES.md`

### 4. Setup PostgreSQL

```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE USER ggnet2 WITH PASSWORD 'your_secure_password';
CREATE DATABASE ggnet2 OWNER ggnet2;
GRANT ALL PRIVILEGES ON DATABASE ggnet2 TO ggnet2;
\q
EOF

# Test connection
psql -U ggnet2 -d ggnet2 -h localhost
```

### 5. Initialize Database

```bash
# Activate virtual environment
cd /opt/ggnet2
source venv/bin/activate

# Run migrations
alembic upgrade head

# Initialize default data (roles, permissions, admin user)
python -m app.backend.auth.init_default_data
```

### 6. Build Frontend

```bash
# Build production frontend
cd /opt/ggnet2/app/frontend
npm run build

# The build output will be in app/frontend/dist/
```

### 7. Setup Nginx Reverse Proxy

```bash
# Create Nginx configuration
sudo vim /etc/nginx/sites-available/ggnet2
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /opt/ggnet2/app/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ggnet2 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 8. Setup Systemd Services

#### 8.1 Backend Service
```bash
# Create systemd service file
sudo vim /etc/systemd/system/ggnet2-backend.service
```

**Service File:**
```ini
[Unit]
Description=ggNET2 Backend API
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

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ggnet2-backend
sudo systemctl start ggnet2-backend
sudo systemctl status ggnet2-backend
```

#### 8.2 Frontend Service (if needed)
```bash
# If serving frontend separately (not via Nginx)
sudo vim /etc/systemd/system/ggnet2-frontend.service
```

**Service File:**
```ini
[Unit]
Description=ggNET2 Frontend
After=network.target

[Service]
Type=simple
User=ggnet2
Group=ggnet2
WorkingDirectory=/opt/ggnet2/app/frontend
ExecStart=/usr/bin/npm run preview
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 🔧 Post-Installation Configuration

### 1. Configure ZFS Pool

```bash
# Create ZFS pool (adjust drive names as needed)
sudo zpool create -f pool0 mirror /dev/sda /dev/sdb

# Create datasets
sudo zfs create pool0/images
sudo zfs create pool0/clones

# Set properties
sudo zfs set compression=lz4 pool0
sudo zfs set dedup=off pool0
sudo zfs set atime=off pool0

# Verify
zpool status
zfs list
```

### 2. Configure Network Bridge

```bash
# Install bridge utilities
sudo apt install -y bridge-utils

# Configure bridge (edit /etc/network/interfaces or use netplan)
# Example for /etc/network/interfaces:
auto br0
iface br0 inet static
    address 192.168.1.100
    netmask 255.255.255.0
    gateway 192.168.1.1
    bridge_ports eth0
    bridge_stp off
    bridge_fd 0
    bridge_maxwait 0
```

### 3. Configure Firewall

```bash
# Install UFW
sudo apt install -y ufw

# Configure firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Verify
sudo ufw status
```

### 4. Setup SSL/TLS (Optional but Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### 5. Verify All Services

```bash
# Check backend service
sudo systemctl status ggnet2-backend

# Check Nginx
sudo systemctl status nginx

# Check PostgreSQL
sudo systemctl status postgresql

# Check ZFS pool
zpool status

# Test API
curl http://localhost:8000/api/v1/ping

# Test frontend
curl http://localhost/
```

---

## ✅ Verification Checklist

### Backend Verification
- [ ] Backend API responding on `http://localhost:8000`
- [ ] API documentation accessible at `http://localhost:8000/docs`
- [ ] Database connection working
- [ ] All migrations applied
- [ ] Default data initialized (roles, permissions, admin user)

### Frontend Verification
- [ ] Frontend accessible at `http://your-domain.com`
- [ ] All pages load correctly
- [ ] API calls working
- [ ] WebSocket connections working

### Authentication Verification
- [ ] Login page accessible
- [ ] Can login with admin credentials
- [ ] Token stored correctly
- [ ] Protected routes require authentication
- [ ] Logout works correctly

### Services Verification
- [ ] All systemd services running
- [ ] Services auto-start on boot
- [ ] Logs accessible
- [ ] No errors in logs

### Network Verification
- [ ] Network bridge configured
- [ ] Firewall rules correct
- [ ] SSL/TLS working (if configured)
- [ ] External access working

---

## 🔒 Production Readiness

### 1. Security Hardening

#### 1.1 Change Default Passwords
```bash
# Change admin password via UI or API
# Change PostgreSQL password
# Change JWT secret key
```

#### 1.2 Review RBAC Permissions
- [ ] Review all roles and permissions
- [ ] Ensure least privilege principle
- [ ] Test permission enforcement

#### 1.3 Configure Rate Limiting
- [ ] Verify rate limiting enabled
- [ ] Test rate limit enforcement
- [ ] Adjust limits as needed

#### 1.4 Input Validation
- [ ] Verify all API endpoints validate input
- [ ] Test SQL injection prevention
- [ ] Test XSS prevention

### 2. Monitoring & Logging

#### 2.1 Setup Logging
```bash
# Configure log rotation
sudo vim /etc/logrotate.d/ggnet2

# Example configuration:
/opt/ggnet2/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

#### 2.2 Setup Monitoring (Optional)
- [ ] Install monitoring tools (Prometheus, Grafana)
- [ ] Configure alerts
- [ ] Setup performance monitoring

### 3. Backup Strategy

#### 3.1 Database Backup
```bash
# Create backup script
sudo vim /opt/ggnet2/scripts/backup_db.sh
```

**Backup Script:**
```bash
#!/bin/bash
BACKUP_DIR="/opt/ggnet2/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U ggnet2 -d ggnet2 > $BACKUP_DIR/db_$DATE.sql

# Compress
gzip $BACKUP_DIR/db_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
```

```bash
# Make executable
chmod +x /opt/ggnet2/scripts/backup_db.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /opt/ggnet2/scripts/backup_db.sh
```

#### 3.2 Configuration Backup
```bash
# Backup configuration files
sudo tar -czf /opt/ggnet2/backups/config_$(date +%Y%m%d).tar.gz \
  /opt/ggnet2/.env \
  /etc/nginx/sites-available/ggnet2 \
  /etc/systemd/system/ggnet2-*.service
```

#### 3.3 ZFS Snapshot Strategy
```bash
# Create ZFS snapshots
sudo zfs snapshot pool0@backup_$(date +%Y%m%d)

# List snapshots
zfs list -t snapshot

# Restore from snapshot (if needed)
sudo zfs rollback pool0@backup_20250126
```

### 4. Performance Optimization

#### 4.1 Database Optimization
```bash
# Review PostgreSQL configuration
sudo vim /etc/postgresql/14/main/postgresql.conf

# Key settings:
# - shared_buffers
# - effective_cache_size
# - maintenance_work_mem
# - checkpoint_completion_target
```

#### 4.2 Frontend Optimization
- [ ] Verify production build
- [ ] Enable gzip compression in Nginx
- [ ] Setup CDN (if needed)
- [ ] Optimize images

#### 4.3 API Optimization
- [ ] Verify caching enabled
- [ ] Review query performance
- [ ] Optimize slow queries

---

## 🚨 Troubleshooting

### Common Issues

#### Backend Not Starting
```bash
# Check logs
sudo journalctl -u ggnet2-backend -n 50

# Check virtual environment
source /opt/ggnet2/venv/bin/activate
python -c "import app.main"

# Check database connection
psql -U ggnet2 -d ggnet2 -h localhost
```

#### Frontend Not Loading
```bash
# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Verify build exists
ls -la /opt/ggnet2/app/frontend/dist

# Test Nginx configuration
sudo nginx -t
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -U ggnet2 -d ggnet2 -h localhost

# Review .env file
cat /opt/ggnet2/.env | grep DATABASE
```

#### ZFS Pool Issues
```bash
# Check pool status
zpool status

# Check for errors
zpool status -v

# Import pool (if needed)
sudo zpool import pool0
```

---

## 📚 Additional Resources

- **API Documentation:** `http://your-domain.com/docs`
- **Backend Documentation:** `docs/backend/`
- **Frontend Documentation:** `docs/frontend/`
- **Troubleshooting Guide:** `docs/TROUBLESHOOTING.md`
- **Security Guide:** `docs/SECURITY.md`
- **Performance Tuning:** `docs/PERFORMANCE_TUNING.md`

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] Server prepared (OS, network, storage)
- [ ] All dependencies installed
- [ ] Environment variables configured
- [ ] Database created and initialized
- [ ] Frontend built

### Deployment
- [ ] Repository cloned/updated
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Database migrations applied
- [ ] Default data initialized
- [ ] Nginx configured
- [ ] Systemd services created
- [ ] Services started

### Post-Deployment
- [ ] ZFS pool configured
- [ ] Network bridge configured
- [ ] Firewall configured
- [ ] SSL/TLS configured (if needed)
- [ ] All services verified
- [ ] Login tested
- [ ] Basic functionality tested

### Production Readiness
- [ ] Security hardened
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Performance optimized
- [ ] Documentation reviewed
- [ ] Team trained

---

**Deployment Complete!** 🎉

