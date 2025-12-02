# 🚀 GGnet - Production Deployment Guide

**Version:** 2.1.0  
**Date:** October 8, 2025  
**Status:** Production Ready ✅

---

## 📋 **Quick Reference**

| Component | URL/Port | Credentials |
|-----------|----------|-------------|
| **Frontend** | http://SERVER_IP:3000 | Created admin user |
| **Backend API** | http://SERVER_IP:8000 | JWT tokens |
| **API Docs** | http://SERVER_IP:8000/docs | Public |
| **Grafana** | http://SERVER_IP:3001 | admin/admin |
| **Prometheus** | http://SERVER_IP:9090 | Public |
| **noVNC Console** | http://SERVER_IP:6080 | Per-session |

---

## 🎯 **Deployment Options**

Choose ONE of these deployment methods:

### **Option 1: Docker Compose (Recommended for Testing)**
- ✅ Easiest setup
- ✅ All services in containers
- ✅ Great for development
- ⚠️ May need privileged mode for iSCSI

### **Option 2: Native Installation (Recommended for Production)**
- ✅ Best performance
- ✅ Direct hardware access
- ✅ Easier iSCSI/DHCP/TFTP config
- ⚠️ More complex initial setup

### **Option 3: Hybrid (Docker + Native Services)**
- ✅ Backend/Frontend in Docker
- ✅ DHCP/TFTP/iSCSI native
- ✅ Best of both worlds
- ⚠️ Requires manual service coordination

---

## 🐳 **OPTION 1: Docker Compose Deployment**

### **Prerequisites:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin
```

### **Installation:**

```bash
# 1. Clone repository
git clone https://github.com/itcaffenet-Ljubinje/GGnet.git
cd GGnet

# 2. Download iPXE binaries
cd infra/tftp
chmod +x download-ipxe.sh
./download-ipxe.sh
cd ../..

# 3. Copy iPXE files to Docker volume
mkdir -p docker/tftp
cp infra/tftp/*.efi infra/tftp/*.kpxe docker/tftp/

# 4. Configure DHCP (update server IP)
nano docker/dhcp/dhcpd.conf
# Change line 33: next-server YOUR_SERVER_IP;

# 5. Start all services
docker-compose up -d

# 6. Wait for services to be ready
docker-compose logs -f backend
# Wait for "Application startup complete"
# Press Ctrl+C to exit logs

# 7. Create admin user
docker exec -it ggnet-backend python3 create_admin.py
# Enter username: admin
# Enter password: (your secure password)

# 8. Verify services
docker-compose ps
# All services should show "Up"

# 9. Run pre-flight checks
docker exec -it ggnet-backend python3 scripts/preflight.py
```

### **Access:**
```bash
# Get server IP
ip addr show | grep inet

# Access Frontend
open http://YOUR_IP:3000

# Access Grafana
open http://YOUR_IP:3001
# Login: admin / admin
```

---

## 💻 **OPTION 2: Native Installation (Production)**

### **Prerequisites:**
```bash
# Debian/Ubuntu 20.04+
sudo apt-get update
sudo apt-get install -y git curl wget
```

### **Automated Installation:**

```bash
# 1. Download and run installer
wget https://raw.githubusercontent.com/itcaffenet-Ljubinje/GGnet/main/install.sh
sudo bash install.sh

# 2. Create admin user
cd /opt/ggnet/backend
python3 create_admin.py

# 3. Start services
sudo ggnet start

# 4. Check status
ggnet status

# 5. Run pre-flight checks
ggnet check
```

### **What install.sh Does:**

1. ✅ Installs system dependencies (PostgreSQL, Redis, nginx, targetcli, qemu-utils, etc.)
2. ✅ Creates ggnet user and directories
3. ✅ Copies application files to /opt/ggnet
4. ✅ Sets up Python virtual environment
5. ✅ Configures PostgreSQL database
6. ✅ Downloads iPXE binaries
7. ✅ Configures DHCP/TFTP/nginx
8. ✅ Installs systemd services
9. ✅ Starts all services
10. ✅ Installs CLI tools (ggnet, ggnet-iscsi)

---

## 🔧 **Post-Installation Configuration**

### **1. Configure Network Settings**

Edit DHCP config:
```bash
sudo nano /etc/dhcp/dhcpd.conf
```

Update these values:
```conf
subnet 192.168.1.0 netmask 255.255.255.0 {
    range 192.168.1.100 192.168.1.200;  # Your DHCP range
    option routers 192.168.1.1;          # Your gateway
    option domain-name-servers 8.8.8.8;  # Your DNS
    next-server 192.168.1.10;            # YOUR SERVER IP
}
```

Restart DHCP:
```bash
sudo systemctl restart isc-dhcp-server
```

---

### **2. Upload Windows 11 Image**

**Via Web UI:**
1. Login to http://YOUR_IP:3000
2. Go to **Images** page
3. Click **Upload Image**
4. Select Windows 11 VHDX file
5. Wait for upload + conversion

**Via CLI:**
```bash
# Copy image to server
scp windows11.vhdx admin@YOUR_IP:/opt/ggnet/images/

# Or via API
curl -X POST http://YOUR_IP:8000/api/images/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@windows11.vhdx"
```

---

### **3. Create Machine Entry**

**Via Web UI:**
1. Go to **Machines** page
2. Click **Add Machine**
3. Fill in details:
   - Name: Gaming-PC-01
   - MAC Address: 00:11:22:33:44:55
   - Hostname: pc-01
   - IP: 192.168.1.101 (static or leave empty for DHCP)
4. Click **Save**

**Via CLI:**
```bash
curl -X POST http://YOUR_IP:8000/api/machines/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gaming-PC-01",
    "mac_address": "00:11:22:33:44:55",
    "hostname": "pc-01",
    "ip_address": "192.168.1.101"
  }'
```

---

### **4. Start Session (Boot Client)**

**Via Web UI:**
1. Go to **Sessions** page
2. Click **Start Session**
3. Select Machine and Image
4. Click **Start**
5. Boot client via PXE

**Via CLI:**
```bash
curl -X POST http://YOUR_IP:8000/api/v1/sessions/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "machine_id": 1,
    "image_id": 1
  }'
```

---

## 🖥️ **Client Boot Configuration**

### **BIOS/UEFI Settings:**

1. **Enter BIOS** (usually F2, Del, F12 during boot)

2. **Enable Network Boot:**
   - Boot → Network Boot: **Enabled**
   - Or: Advanced → Integrated Devices → NIC: **Enabled with PXE**

3. **For Windows 11 (SecureBoot):**
   - Security → Secure Boot: **Enabled**
   - Boot → Boot Mode: **UEFI**
   - Security → TPM 2.0: **Enabled**

4. **For Older Windows (No SecureBoot):**
   - Security → Secure Boot: **Disabled**
   - Boot → Boot Mode: **UEFI** or **Legacy**

5. **Set Boot Order:**
   - 1st: Network Boot (PXE)
   - 2nd: Hard Disk (fallback)

6. **Save & Reboot**

### **Expected Boot Flow:**

```
[00:00] Power on
[00:05] PXE boot starts
        >> Start PXE over IPv4
        >> DHCP: 192.168.1.101
        >> TFTP: Downloading snponly.efi...

[00:10] iPXE loads
        iPXE (http://ipxe.org)
        >> dhcp net0... ok
        >> Connecting to iSCSI...

[00:15] Windows boot
        [Windows logo]

[01:00] Registry config applied
        [Auto-configuring Windows...]

[01:30] Auto-login
        [Desktop appears]

[02:00] ✅ Ready to use!
```

---

## 📊 **Monitoring**

### **Grafana Dashboards:**

Access: `http://YOUR_IP:3001`

**Default Dashboard:**
- Total Machines
- Machines Online
- Active Sessions
- Boot Success Rate
- Storage Capacity

**Custom Dashboards:**
- Add JSON files to `docker/grafana/dashboards/`
- Restart Grafana

### **Prometheus Metrics:**

Access: `http://YOUR_IP:9090`

**Key Metrics:**
```
ggnet_machines_total
ggnet_machines_online
ggnet_sessions_active
ggnet_boot_success_rate
ggnet_storage_used_bytes
ggnet_iscsi_targets_active
```

---

## 🔧 **Management Commands**

### **Service Management:**

```bash
# Start all services
sudo ggnet start

# Stop all services
sudo ggnet stop

# Restart services
sudo ggnet restart

# Check status
ggnet status
```

### **iSCSI Management:**

```bash
# Create iSCSI target
sudo ggnet-iscsi create <machine-id> <image-path>

# Example:
sudo ggnet-iscsi create 1 /opt/ggnet/images/windows11.vhdx

# List targets
sudo ggnet-iscsi list

# Delete target
sudo ggnet-iscsi delete <machine-id>
```

### **System Checks:**

```bash
# Run pre-flight checks
ggnet check

# View logs
ggnet logs backend
ggnet logs worker

# Create backup
sudo ggnet backup all
sudo ggnet backup database
sudo ggnet backup config
```

---

## 🔒 **Security Hardening**

### **1. Change Default Passwords:**

```bash
# Grafana
# Login to http://YOUR_IP:3001
# Profile → Change Password

# Database (if exposed)
sudo -u postgres psql
ALTER USER ggnet WITH PASSWORD 'NEW_SECURE_PASSWORD';

# Update backend/.env
nano /opt/ggnet/backend/.env
# DATABASE_URL=postgresql://ggnet:NEW_PASSWORD@...
```

### **2. Enable HTTPS:**

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d ggnet.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### **3. Configure Firewall:**

```bash
# Allow required ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 69/udp    # TFTP
sudo ufw allow 3260/tcp  # iSCSI
sudo ufw allow 3000/tcp  # Frontend (optional, use nginx proxy)
sudo ufw allow 8000/tcp  # Backend API (optional, use nginx proxy)

# Enable firewall
sudo ufw enable
```

---

## 🧪 **Testing**

### **Smoke Test:**

```bash
# 1. Check all services running
ggnet status

# 2. Test API
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

# 3. Test Frontend
curl http://localhost:3000
# Should return HTML

# 4. Test Grafana
curl http://localhost:3001/api/health
# Should return: {"commit":"...","database":"ok"}

# 5. Test TFTP
tftp localhost
> get snponly.efi
> quit
ls -lh snponly.efi
# Should be ~1.2 MB
```

### **Full Integration Test:**

```bash
# 1. Create test machine via API
# 2. Upload test image
# 3. Start session
# 4. Boot client
# 5. Verify Windows boots
# 6. Check Grafana metrics
# 7. Test noVNC console
```

---

## 📈 **Performance Tuning**

### **Database Optimization:**

```sql
-- PostgreSQL tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '16MB';
SELECT pg_reload_conf();
```

### **Redis Optimization:**

```bash
# Edit redis config
sudo nano /etc/redis/redis.conf

# Add:
maxmemory 512mb
maxmemory-policy allkeys-lru
```

### **Backend Optimization:**

```bash
# Use production ASGI server (already configured)
# Uvicorn with 4 workers

# Edit systemd service
sudo nano /etc/systemd/system/ggnet-backend.service

# Set workers:
ExecStart=/opt/ggnet/backend/venv/bin/uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-config logging.ini
```

---

## 🔍 **Troubleshooting**

### **Services Won't Start:**

```bash
# Check logs
sudo journalctl -u ggnet-backend -n 50
sudo journalctl -u ggnet-worker -n 50

# Check dependencies
ggnet check

# Verify database
sudo systemctl status postgresql
psql -U ggnet -d ggnet -c "SELECT 1;"
```

### **Client Won't Boot:**

```bash
# 1. Check DHCP logs
sudo tail -f /var/log/syslog | grep dhcpd

# 2. Check TFTP files
ls -lh /var/lib/tftp/

# 3. Test TFTP manually
tftp YOUR_SERVER_IP
> get snponly.efi
> quit

# 4. Check iSCSI targets
sudo targetcli ls

# 5. Run pre-flight
ggnet check
```

### **API Errors:**

```bash
# Check backend logs
ggnet logs backend

# Test API health
curl http://localhost:8000/health

# Check database connection
curl http://localhost:8000/health/readiness
```

---

## 📊 **Monitoring & Maintenance**

### **Daily Checks:**

```bash
# Service status
ggnet status

# System health
ggnet check

# View metrics
curl http://localhost:8000/metrics
```

### **Weekly Maintenance:**

```bash
# Database backup
sudo ggnet backup database

# Config backup
sudo ggnet backup config

# Check disk space
df -h /opt/ggnet

# Review logs
ggnet logs backend | tail -100
```

### **Monthly Tasks:**

```bash
# Full backup
sudo ggnet backup all

# Update system
sudo ggnet update

# Review Grafana dashboards
# Check for anomalies or trends

# Update iPXE binaries (if new versions)
cd /opt/ggnet/infra/tftp
./download-ipxe.sh
sudo cp *.efi *.kpxe /var/lib/tftp/
```

---

## 🎯 **Production Checklist**

### **Before Going Live:**

- [ ] Server has static IP
- [ ] Firewall configured
- [ ] HTTPS enabled (certbot)
- [ ] Strong admin password set
- [ ] Database password changed
- [ ] Grafana password changed
- [ ] Backup strategy configured
- [ ] Monitoring alerts configured
- [ ] Documentation reviewed
- [ ] Team trained on UI
- [ ] Emergency contact list ready

### **Day 1:**

- [ ] Monitor logs continuously
- [ ] Watch Grafana dashboards
- [ ] Be ready for quick rollback
- [ ] Document any issues
- [ ] Collect user feedback

### **Week 1:**

- [ ] Review performance metrics
- [ ] Optimize based on actual usage
- [ ] Adjust resource allocation
- [ ] Fine-tune DHCP/TFTP settings
- [ ] Update documentation with learnings

---

## 🚨 **Emergency Procedures**

### **Service Down:**

```bash
# Restart specific service
sudo systemctl restart ggnet-backend

# Or restart all
sudo ggnet restart

# Check what's wrong
ggnet check
ggnet logs backend
```

### **Database Issues:**

```bash
# Restore from backup
sudo tar -xzf /var/backups/ggnet/ggnet_db_*.tar.gz
sudo -u postgres psql ggnet < backup.sql

# Or rollback migration
cd /opt/ggnet/backend
source venv/bin/activate
alembic downgrade -1
```

### **Complete Rollback:**

```bash
# Stop services
sudo ggnet stop

# Restore from full backup
sudo tar -xzf /var/backups/ggnet/ggnet_full_*.tar.gz -C /opt/

# Restart
sudo ggnet start
```

---

## 📞 **Support Resources**

- **Documentation:** `docs/` directory
- **GitHub Issues:** https://github.com/itcaffenet-Ljubinje/GGnet/issues
- **Community:** GitHub Discussions
- **Email:** (your support email)

---

## 🎓 **Training Materials**

### **For Administrators:**
- [SecureBoot Setup Guide](docs/SECUREBOOT_SETUP.md)
- [Windows Toolchain Guide](docs/WINDOWS_TOOLCHAIN_GUIDE.md)
- [Phase 1 Testing Plan](docs/PHASE1_TESTING_PLAN.md)

### **For Users:**
- How to boot a client
- How to manage sessions
- How to upload images

---

## ✅ **Success Metrics**

Monitor these KPIs:

- **Boot Success Rate:** > 95%
- **Average Boot Time:** < 3 minutes
- **Session Uptime:** > 99%
- **Storage Usage:** < 80%
- **API Response Time:** < 100ms
- **Active Sessions:** Track peak usage

---

**GGnet v2.1.0 is READY for PRODUCTION!** 🚀

Deploy with confidence!
