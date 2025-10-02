# GGnet Diskless Server - Installation Guide

## Overview

This guide covers the installation and configuration of GGnet Diskless Server on Ubuntu/Debian systems.

## Prerequisites

### System Requirements

- **OS**: Ubuntu 20.04+ or Debian 11+
- **CPU**: 4+ cores (8+ recommended)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Storage**: 100GB+ for system, additional storage for images
- **Network**: Gigabit Ethernet (10Gb recommended for production)

### Network Requirements

- Static IP address for the server
- DHCP server access (for PXE boot configuration)
- Firewall access for required ports

### Required Ports

| Port | Protocol | Service | Description |
|------|----------|---------|-------------|
| 80   | TCP      | HTTP    | Web interface |
| 443  | TCP      | HTTPS   | Secure web interface |
| 3260 | TCP      | iSCSI   | iSCSI target portal |
| 69   | UDP      | TFTP    | Boot file serving |
| 67   | UDP      | DHCP    | Network boot (if running DHCP) |

## Quick Installation

### Automated Installation (Recommended)

```bash
# Download and run the installation script
curl -fsSL https://raw.githubusercontent.com/ggnet/diskless-server/main/scripts/install.sh | sudo bash
```

### Manual Installation

#### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y \
    python3.11 python3.11-venv python3.11-dev python3-pip \
    nodejs npm \
    postgresql postgresql-contrib \
    redis-server \
    nginx \
    targetcli-fb open-iscsi qemu-utils \
    tftpd-hpa isc-dhcp-server \
    git curl wget unzip build-essential libpq-dev
```

#### 2. Create User and Directories

```bash
# Create system user
sudo useradd --system --shell /bin/bash --home-dir /opt/ggnet --create-home ggnet

# Create directories
sudo mkdir -p /opt/ggnet/{backend,frontend,scripts}
sudo mkdir -p /etc/ggnet
sudo mkdir -p /var/log/ggnet
sudo mkdir -p /var/lib/ggnet/{uploads,images,backups}

# Set permissions
sudo chown -R ggnet:ggnet /opt/ggnet /var/log/ggnet /var/lib/ggnet
```

#### 3. Setup Database

```bash
# Start PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE USER ggnet WITH PASSWORD 'ggnet_password';
CREATE DATABASE ggnet OWNER ggnet;
GRANT ALL PRIVILEGES ON DATABASE ggnet TO ggnet;
\q
EOF
```

#### 4. Install Backend

```bash
# Clone repository
git clone https://github.com/ggnet/diskless-server.git
cd diskless-server

# Copy backend files
sudo cp -r backend/* /opt/ggnet/backend/

# Create virtual environment
sudo -u ggnet python3.11 -m venv /opt/ggnet/venv

# Install dependencies
sudo -u ggnet /opt/ggnet/venv/bin/pip install -r /opt/ggnet/backend/requirements.txt

# Copy and configure environment
sudo cp env.example /etc/ggnet/backend.env
sudo chown ggnet:ggnet /etc/ggnet/backend.env
sudo chmod 640 /etc/ggnet/backend.env

# Update configuration
sudo sed -i 's|DATABASE_URL=.*|DATABASE_URL=postgresql://ggnet:ggnet_password@localhost:5432/ggnet|g' /etc/ggnet/backend.env
sudo sed -i 's|UPLOAD_DIR=.*|UPLOAD_DIR=/var/lib/ggnet/uploads|g' /etc/ggnet/backend.env
sudo sed -i 's|IMAGES_DIR=.*|IMAGES_DIR=/var/lib/ggnet/images|g' /etc/ggnet/backend.env

# Run database migrations
cd /opt/ggnet/backend
sudo -u ggnet /opt/ggnet/venv/bin/alembic upgrade head
```

#### 5. Install Frontend

```bash
# Copy frontend files
sudo cp -r frontend/* /opt/ggnet/frontend/

# Install and build
cd /opt/ggnet/frontend
sudo -u ggnet npm install
sudo -u ggnet npm run build

# Copy to nginx
sudo rm -rf /var/www/html/*
sudo cp -r /opt/ggnet/frontend/dist/* /var/www/html/
```

#### 6. Setup Services

```bash
# Copy systemd service files
sudo cp systemd/*.service /etc/systemd/system/

# Reload and enable services
sudo systemctl daemon-reload
sudo systemctl enable ggnet-backend ggnet-worker
sudo systemctl start ggnet-backend ggnet-worker
```

#### 7. Configure Nginx

```bash
# Backup original config
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup

# Copy our configuration
sudo cp docker/nginx/nginx.conf /etc/nginx/nginx.conf

# Test and restart
sudo nginx -t
sudo systemctl restart nginx
```

## Configuration

### Environment Variables

Edit `/etc/ggnet/backend.env`:

```bash
# Database
DATABASE_URL=postgresql://ggnet:ggnet_password@localhost:5432/ggnet

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Storage
UPLOAD_DIR=/var/lib/ggnet/uploads
IMAGES_DIR=/var/lib/ggnet/images
MAX_UPLOAD_SIZE=10737418240

# iSCSI
ISCSI_TARGET_PREFIX=iqn.2025.ggnet
ISCSI_PORTAL_IP=192.168.1.100
ISCSI_PORTAL_PORT=3260

# Network Boot
TFTP_ROOT=/var/lib/tftpboot
```

### DHCP Configuration

Configure your DHCP server to support PXE boot:

```bash
# Example dhcpd.conf snippet
subnet 192.168.1.0 netmask 255.255.255.0 {
    range 192.168.1.100 192.168.1.200;
    option routers 192.168.1.1;
    option domain-name-servers 8.8.8.8;
    
    # PXE boot configuration
    next-server 192.168.1.100;  # GGnet server IP
    
    if option arch = 00:07 {
        filename "EFI/BOOT/bootx64.efi";  # UEFI x64
    } else {
        filename "pxelinux.0";            # Legacy BIOS
    }
}
```

### TFTP Server Setup

```bash
# Configure TFTP
sudo tee /etc/default/tftpd-hpa << EOF
TFTP_USERNAME="tftp"
TFTP_DIRECTORY="/var/lib/tftpboot"
TFTP_ADDRESS="0.0.0.0:69"
TFTP_OPTIONS="--secure"
EOF

# Create directory structure
sudo mkdir -p /var/lib/tftpboot/EFI/BOOT
sudo chown -R tftp:tftp /var/lib/tftpboot

# Restart TFTP service
sudo systemctl restart tftpd-hpa
```

## Initial Setup

### 1. Access Web Interface

Open your browser and navigate to:
- HTTP: `http://your-server-ip`
- HTTPS: `https://your-server-ip` (if SSL configured)

### 2. Login

Use the default credentials:
- **Username**: `admin`
- **Password**: `admin123`

**⚠️ Important**: Change the default password immediately after first login!

### 3. Change Admin Password

1. Go to Settings → Security
2. Click "Change Password"
3. Enter current password: `admin123`
4. Set a strong new password
5. Click "Update Password"

### 4. Configure System Settings

1. Go to Settings → System
2. Update configuration as needed:
   - Default boot timeout
   - Maximum upload size
   - Storage paths

### 5. Configure Network Settings

1. Go to Settings → Network
2. Update network configuration:
   - Server IP address
   - iSCSI portal settings
   - TFTP root directory

## First Boot Setup

### 1. Upload Disk Image

1. Go to Images page
2. Click "Upload Image"
3. Select your VHD/VHDX file
4. Wait for upload and processing to complete

### 2. Add Client Machine

1. Go to Machines page
2. Click "Add Machine"
3. Enter machine details:
   - Name (e.g., "LAB-PC-01")
   - MAC address
   - IP address (optional)
   - Boot mode (UEFI recommended)
   - Enable Secure Boot if needed

### 3. Create iSCSI Target

1. Go to Targets page
2. Click "Create Target"
3. Select machine and system image
4. Optionally add extra disk for games/data
5. Click "Create Target"

### 4. Start Boot Session

1. Go to Sessions page
2. Click "Start Session"
3. Select the target you created
4. The system will prepare the iSCSI target

### 5. Boot Client Machine

1. Ensure client machine is configured for PXE/network boot
2. Power on the client machine
3. It should boot from the network and load your disk image

## Troubleshooting

### Service Status

Check service status:

```bash
# Backend service
sudo systemctl status ggnet-backend

# Worker service
sudo systemctl status ggnet-worker

# Nginx
sudo systemctl status nginx

# PostgreSQL
sudo systemctl status postgresql

# Redis
sudo systemctl status redis-server

# TFTP
sudo systemctl status tftpd-hpa
```

### Log Files

Check log files for errors:

```bash
# Backend logs
sudo journalctl -u ggnet-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Application logs
sudo tail -f /var/log/ggnet/error.log
sudo tail -f /var/log/ggnet/audit.log
```

### Common Issues

#### 1. Backend Service Won't Start

```bash
# Check configuration
sudo -u ggnet /opt/ggnet/venv/bin/python -c "from app.core.config import get_settings; print('Config OK')"

# Check database connection
sudo -u ggnet /opt/ggnet/venv/bin/python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

#### 2. Upload Fails

- Check disk space: `df -h`
- Check permissions: `ls -la /var/lib/ggnet/uploads`
- Check nginx client_max_body_size in `/etc/nginx/nginx.conf`

#### 3. iSCSI Target Creation Fails

- Check if running as root: `sudo targetcli ls`
- Check if targetcli is installed: `which targetcli`
- Check system logs: `sudo journalctl -u ggnet-backend`

#### 4. Client Won't Boot

- Check DHCP configuration
- Check TFTP service: `sudo systemctl status tftpd-hpa`
- Check boot files exist: `ls -la /var/lib/tftpboot/`
- Check network connectivity

### Performance Tuning

#### Database Optimization

```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/13/main/postgresql.conf

# Recommended settings for GGnet:
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
```

#### Storage Performance

- Use SSD storage for best performance
- Consider RAID 10 for redundancy and performance
- Separate OS, database, and image storage if possible

## Security Considerations

### Firewall Configuration

```bash
# Allow required ports
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 3260/tcp  # iSCSI
sudo ufw allow 69/udp    # TFTP

# Enable firewall
sudo ufw enable
```

### SSL/TLS Setup

1. Obtain SSL certificate (Let's Encrypt recommended)
2. Configure Nginx for HTTPS
3. Update firewall rules
4. Test SSL configuration

### Regular Maintenance

- Update system packages regularly
- Monitor log files for suspicious activity
- Backup database and configuration files
- Review user accounts and permissions

## Backup and Recovery

### Database Backup

```bash
# Create backup
sudo -u postgres pg_dump ggnet > /var/lib/ggnet/backups/ggnet_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
sudo -u postgres psql ggnet < /var/lib/ggnet/backups/ggnet_backup.sql
```

### Configuration Backup

```bash
# Backup configuration
sudo tar -czf /var/lib/ggnet/backups/config_$(date +%Y%m%d_%H%M%S).tar.gz \
    /etc/ggnet/ \
    /etc/nginx/nginx.conf \
    /etc/default/tftpd-hpa
```

### Image Backup

```bash
# Backup images (adjust path as needed)
sudo rsync -av /var/lib/ggnet/images/ /backup/location/images/
```

## Support

For support and documentation:

- GitHub Issues: https://github.com/ggnet/diskless-server/issues
- Documentation: https://docs.ggnet.local
- Community Forum: https://community.ggnet.local

## License

This project is licensed under the MIT License. See LICENSE file for details.

