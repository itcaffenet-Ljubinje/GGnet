# GGnet Production Deployment Guide

## 🚀 **IMMEDIATE NEXT STEP: Deploy GGnet v2.0.0**

This guide will walk you through deploying GGnet to a production environment step by step.

---

## 📋 **Pre-Deployment Checklist**

### **System Requirements**
- [ ] **OS**: Ubuntu 22.04 LTS, Debian 12, or CentOS 9
- [ ] **CPU**: 4+ cores, 3.0+ GHz
- [ ] **RAM**: 8+ GB
- [ ] **Storage**: 100+ GB SSD
- [ ] **Network**: Gigabit Ethernet
- [ ] **Root Access**: sudo privileges required

### **Network Requirements**
- [ ] **Ports**: 80, 443, 8000, 3260, 69, 67/68
- [ ] **Domain**: Optional but recommended
- [ ] **SSL Certificate**: Let's Encrypt or commercial
- [ ] **Firewall**: Configured for required ports

---

## 🏗️ **DEPLOYMENT OPTIONS**

### **Option 1: Automated Installation (Recommended)**

#### **Step 1: Download and Prepare**
```bash
# Clone the repository
git clone https://github.com/itcaffenet-Ljubinje/GGnet.git
cd GGnet

# Make installation script executable
sudo chmod +x install.sh

# Review the installation script (optional)
cat install.sh
```

#### **Step 2: Run Automated Installation**
```bash
# Run the installation script
sudo ./install.sh

# The script will:
# - Install all dependencies
# - Configure services
# - Set up database
# - Configure network services
# - Start all services
```

#### **Step 3: Verify Installation**
```bash
# Check service status
sudo systemctl status ggnet-backend
sudo systemctl status ggnet-worker
sudo systemctl status redis-server
sudo systemctl status postgresql
sudo systemctl status nginx

# Check if services are running
curl http://localhost:8000/health/
```

### **Option 2: Docker Deployment**

#### **Step 1: Install Docker**
```bash
# Install Docker and Docker Compose
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

#### **Step 2: Deploy with Docker**
```bash
# Navigate to infra directory
cd infra

# Start services with Docker Compose
docker compose up -d --build

# Check container status
docker compose ps
```

#### **Step 3: Verify Deployment**
```bash
# Check if containers are running
docker compose logs -f

# Test health endpoint
curl http://localhost:8000/health/
```

### **Option 3: Manual Installation**

#### **Step 1: Install Dependencies**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-venv python3-pip \
    postgresql postgresql-contrib redis-server \
    nginx qemu-utils targetcli-fb tftpd-hpa isc-dhcp-server \
    git curl wget
```

#### **Step 2: Setup Database**
```bash
# Create database and user
sudo -u postgres psql -c "CREATE DATABASE ggnet;"
sudo -u postgres psql -c "CREATE USER ggnet WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ggnet TO ggnet;"
```

#### **Step 3: Setup Application**
```bash
# Create application user
sudo useradd -r -m -d /opt/ggnet -s /usr/sbin/nologin ggnet

# Create directories
sudo mkdir -p /opt/ggnet/{backend,logs,backups}
sudo mkdir -p /var/lib/ggnet/{images,uploads}
sudo mkdir -p /var/lib/tftpboot

# Copy application files
sudo cp -r backend/* /opt/ggnet/backend/
sudo chown -R ggnet:ggnet /opt/ggnet
sudo chown -R ggnet:ggnet /var/lib/ggnet
sudo chown -R tftp:tftp /var/lib/tftpboot
```

#### **Step 4: Install Python Dependencies**
```bash
# Create virtual environment
sudo -u ggnet python3 -m venv /opt/ggnet/venv

# Install dependencies
sudo -u ggnet /opt/ggnet/venv/bin/pip install -r /opt/ggnet/backend/requirements.txt
```

#### **Step 5: Configure Services**
```bash
# Copy systemd services
sudo cp infra/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Copy nginx configuration
sudo cp infra/nginx/ggnet.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/ggnet.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### **Step 6: Initialize Database**
```bash
# Run database migrations
sudo -u ggnet /opt/ggnet/venv/bin/alembic upgrade head

# Create admin user
sudo -u ggnet /opt/ggnet/venv/bin/python /opt/ggnet/backend/create_admin.py
```

#### **Step 7: Start Services**
```bash
# Start and enable services
sudo systemctl start postgresql redis-server nginx
sudo systemctl start ggnet-backend ggnet-worker
sudo systemctl enable ggnet-backend ggnet-worker
```

---

## 🔧 **POST-DEPLOYMENT CONFIGURATION**

### **Step 1: Configure SSL (Recommended)**
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### **Step 2: Configure Firewall**
```bash
# Install and configure UFW
sudo apt install -y ufw

# Allow required ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # API (if needed externally)
sudo ufw allow 3260/tcp  # iSCSI
sudo ufw allow 69/udp    # TFTP
sudo ufw allow 67:68/udp # DHCP

# Enable firewall
sudo ufw enable
```

### **Step 3: Configure Network Services**

#### **DHCP Configuration**
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

# Restart DHCP service
sudo systemctl restart isc-dhcp-server
```

#### **TFTP Configuration**
```bash
# Configure TFTP
sudo nano /etc/default/tftpd-hpa

# Set configuration
TFTP_DIRECTORY="/var/lib/tftpboot"
TFTP_ADDRESS="0.0.0.0:69"
TFTP_OPTIONS="--secure"

# Copy boot files
sudo cp /usr/lib/ipxe/ipxe.efi /var/lib/tftpboot/bootx64.efi
sudo cp /usr/lib/ipxe/undionly.kpxe /var/lib/tftpboot/

# Set permissions
sudo chown -R tftp:tftp /var/lib/tftpboot
sudo chmod -R 755 /var/lib/tftpboot

# Restart TFTP service
sudo systemctl restart tftpd-hpa
```

### **Step 4: Create Initial Configuration**
```bash
# Copy environment configuration
sudo cp env.example /opt/ggnet/backend/.env

# Edit configuration
sudo nano /opt/ggnet/backend/.env

# Update with your settings:
# DATABASE_URL=postgresql://ggnet:your_password@localhost:5432/ggnet
# SECRET_KEY=your-secret-key-change-in-production
# REDIS_URL=redis://localhost:6379/0
```

---

## ✅ **VERIFICATION & TESTING**

### **Step 1: Health Checks**
```bash
# Check all services
sudo systemctl status ggnet-backend ggnet-worker redis-server postgresql nginx

# Test API endpoints
curl http://localhost:8000/health/
curl http://localhost:8000/health/detailed

# Test web interface
curl http://localhost:8000/
```

### **Step 2: Create Test User**
```bash
# Access the web interface
# Navigate to: http://your-server-ip:8000
# Default credentials: admin / admin123

# Or create new user via API
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User",
    "role": "operator",
    "password": "testpassword"
  }'
```

### **Step 3: Test Core Functionality**
```bash
# Test machine creation
curl -X POST http://localhost:8000/machines \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "name": "Test Machine",
    "mac_address": "00:11:22:33:44:55",
    "ip_address": "192.168.1.100",
    "boot_mode": "UEFI",
    "description": "Test machine for verification"
  }'

# Test image upload (if you have a test image)
curl -X POST http://localhost:8000/images/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/test-image.vhdx" \
  -F "name=Test Image" \
  -F "image_type=SYSTEM"
```

---

## 🔍 **TROUBLESHOOTING**

### **Common Issues**

#### **Service Won't Start**
```bash
# Check service logs
sudo journalctl -u ggnet-backend -f
sudo journalctl -u ggnet-worker -f

# Check configuration
sudo -u ggnet /opt/ggnet/venv/bin/python -c "
from app.core.config import get_settings
print(get_settings())
"
```

#### **Database Connection Issues**
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

#### **Redis Connection Issues**
```bash
# Test Redis connection
redis-cli ping

# Check Redis status
sudo systemctl status redis-server

# Check Redis logs
sudo journalctl -u redis-server -f
```

#### **Network Issues**
```bash
# Check if ports are listening
sudo netstat -tlnp | grep -E "(8000|3260|69|67|68)"

# Check firewall status
sudo ufw status

# Test network connectivity
telnet localhost 8000
```

---

## 📊 **MONITORING SETUP**

### **Step 1: Configure Logging**
```bash
# Check log files
sudo tail -f /opt/ggnet/logs/app.log
sudo tail -f /opt/ggnet/logs/error.log
sudo tail -f /opt/ggnet/logs/audit.log

# Configure log rotation
sudo nano /etc/logrotate.d/ggnet
```

### **Step 2: Setup Monitoring**
```bash
# Check health endpoints
curl http://localhost:8000/health/
curl http://localhost:8000/health/detailed
curl http://localhost:8000/metrics/

# Monitor system resources
htop
df -h
free -h
```

### **Step 3: Setup Alerts**
```bash
# Create monitoring script
sudo nano /opt/ggnet/scripts/monitor.sh

#!/bin/bash
# Health check script
if ! curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
    echo "GGnet health check failed" | mail -s "GGnet Alert" admin@example.com
fi

# Add to crontab
echo "*/5 * * * * /opt/ggnet/scripts/monitor.sh" | sudo crontab -
```

---

## 🎯 **NEXT STEPS AFTER DEPLOYMENT**

### **Immediate Actions**
1. **Test with Real Clients**: Boot a test machine from network
2. **Create User Accounts**: Set up user accounts for your team
3. **Upload Images**: Upload your first disk images
4. **Configure Machines**: Add your client machines
5. **Test Sessions**: Start and monitor test sessions

### **Configuration Tasks**
1. **Network Configuration**: Configure DHCP and TFTP for your network
2. **Image Management**: Upload and convert your disk images
3. **User Management**: Create user accounts and set permissions
4. **Monitoring Setup**: Configure monitoring and alerting
5. **Backup Setup**: Configure automated backups

### **Training & Documentation**
1. **User Training**: Train your team on using GGnet
2. **Documentation Review**: Review all documentation
3. **Support Procedures**: Establish support procedures
4. **Best Practices**: Document best practices for your environment

---

## 🎉 **DEPLOYMENT COMPLETE**

Once you've completed these steps, GGnet will be fully deployed and ready for production use!

### **Access Points**
- **Web Interface**: http://your-server-ip:8000
- **API Documentation**: http://your-server-ip:8000/docs
- **Health Check**: http://your-server-ip:8000/health/
- **Metrics**: http://your-server-ip:8000/metrics/

### **Default Credentials**
- **Username**: admin
- **Password**: admin123
- **⚠️ Change these immediately after first login!**

### **Support Resources**
- **Documentation**: README.md, RUNBOOK.md, UPGRADE.md
- **GitHub**: https://github.com/itcaffenet-Ljubinje/GGnet
- **Issues**: Report bugs and request features
- **Community**: GitHub Discussions for support

**GGnet is now ready for production use!** 🚀
