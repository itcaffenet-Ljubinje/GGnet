# GGnet Diskless Server

A complete open-source diskless server solution similar to ggRock, built with FastAPI, React, and modern web technologies. GGnet enables you to boot Windows and Linux clients over the network using iSCSI and PXE boot.

## 🚀 Features

### Core Functionality
- **Network Boot**: PXE boot with iPXE for UEFI and legacy BIOS clients
- **iSCSI Targets**: Dynamic iSCSI target creation and management
- **Image Management**: Upload, convert, and manage VHD/VHDX disk images
- **Session Monitoring**: Real-time monitoring of active diskless sessions
- **Machine Management**: Complete CRUD operations for client machines

### Web Interface
- **Modern React UI**: Polished, responsive web interface
- **Drag & Drop Upload**: Easy image file upload with progress tracking
- **Real-time Updates**: WebSocket-based live session monitoring
- **Dark Mode**: Built-in dark/light theme support
- **Mobile Responsive**: Works on desktop, tablet, and mobile devices

### Server Components
- **DHCP Server**: Automatic IP assignment and PXE boot configuration
- **TFTP Server**: iPXE boot files distribution
- **iSCSI Target**: High-performance block storage over network
- **Nginx Reverse Proxy**: Secure web interface and API gateway
- **Redis Cache**: Fast session storage and caching
- **PostgreSQL**: Reliable data persistence

## 📋 Requirements

### System Requirements
- **OS**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+ / RHEL 8+
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: Minimum 100GB, Recommended 500GB+
- **Network**: Gigabit Ethernet recommended
- **CPU**: x86_64 architecture

### Software Dependencies
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+
- Nginx 1.18+
- ISC DHCP Server
- TFTP Server
- iSCSI Target (targetcli)

## 🛠️ Installation

### Quick Install (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/ggnet.git
   cd ggnet
   ```

2. **Run the installation script**:
```bash
   sudo chmod +x install.sh
   sudo ./install.sh
   ```

3. **Access the web interface**:
   Open your browser and navigate to `http://your-server-ip`

4. **Login with default credentials**:
   - Username: `admin`
   - Password: `admin123`

### Manual Installation

If you prefer manual installation, follow these steps:

#### 1. Install System Dependencies

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install -y python3 python3-pip nodejs npm nginx postgresql redis-server
sudo apt install -y isc-dhcp-server tftpd-hpa targetcli-fb python3-rtslib-fb
sudo apt install -y qemu-utils git curl wget build-essential
```

**CentOS/RHEL**:
```bash
sudo yum update -y
sudo yum install -y python3 python3-pip nodejs npm nginx postgresql redis
sudo yum install -y dhcp tftp-server targetcli qemu-img git curl wget
sudo yum groupinstall -y "Development Tools"
```

#### 2. Configure Database

```bash
sudo -u postgres psql
CREATE DATABASE ggnet;
CREATE USER ggnet WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ggnet TO ggnet;
\q
```

#### 3. Install Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Install Frontend

```bash
cd frontend
npm install
npm run build
```

#### 5. Configure Services

Run the individual configuration scripts:
```bash
sudo ./scripts/dhcp_config.sh
sudo ./scripts/tftp_config.sh
sudo ./scripts/iscsi_config.sh
```

## 🔧 Configuration

### Network Configuration

#### DHCP Configuration
The DHCP server is automatically configured with these settings:
- **Subnet**: 192.168.1.0/24
- **Range**: 192.168.1.100-200
- **Gateway**: 192.168.1.1
- **DNS**: 8.8.8.8, 8.8.4.4
- **TFTP Server**: 192.168.1.1
- **PXE Filename**: ipxe.efi

#### TFTP Configuration
- **Directory**: /opt/ggnet/tftp
- **iPXE Files**: ipxe.efi, ipxe.lkrn, undionly.kpxe
- **Configuration**: ipxe.cfg

#### iSCSI Configuration
- **Base IQN**: iqn.2024.ggnet.local
- **Portal**: 0.0.0.0:3260
- **Target Directory**: /opt/ggnet/targets

### Application Configuration

#### Backend Configuration
Edit `backend/app/core/config.py`:
```python
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://ggnet:password@localhost/ggnet"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    SECRET_KEY: str = "your-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # File Upload
    MAX_FILE_SIZE: int = 50 * 1024 * 1024 * 1024  # 50GB
    UPLOAD_DIR: str = "/opt/ggnet/images"
```

#### Frontend Configuration
Edit `frontend/src/lib/api.ts`:
```typescript
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://your-domain.com/api' 
  : 'http://localhost:8000'
```

## 📖 Usage

### Getting Started

1. **Upload Images**:
   - Navigate to the Images section
   - Drag and drop VHD/VHDX files
   - Wait for conversion to complete

2. **Create Machines**:
   - Go to the Machines section
   - Click "Add Machine"
   - Enter MAC address and machine details
   - Assign an image to the machine

3. **Create iSCSI Targets**:
   - Go to the Storage section
   - Click "Add Array"
   - Configure target settings
   - Link machine to target

4. **Boot Clients**:
   - Configure client BIOS for network boot
   - Power on client machine
   - Monitor boot progress in Sessions section

### Web Interface Guide

#### Dashboard
- **System Overview**: CPU, memory, disk usage
- **Active Sessions**: Real-time session monitoring
- **Recent Activity**: System events and logs
- **Quick Actions**: Common tasks and shortcuts

#### Machines
- **Machine List**: View all registered machines
- **Machine Details**: Hardware info, boot status, location
- **Bulk Operations**: Manage multiple machines
- **Search & Filter**: Find machines quickly

#### Images
- **Image Library**: All available disk images
- **Upload Manager**: Drag & drop file upload
- **Conversion Status**: Track image processing
- **Storage Usage**: Monitor disk space

#### Sessions
- **Active Sessions**: Live session monitoring
- **Session History**: Past session records
- **Boot Progress**: Real-time boot status
- **Session Control**: Start/stop sessions

#### Storage
- **Array Configuration**: Disk array management
- **iSCSI Targets**: Target creation and management
- **Storage Statistics**: Usage and performance
- **Reserved Settings**: Disk reservation options

#### Monitoring
- **Performance Metrics**: CPU, memory, network usage
- **System Health**: Service status and alerts
- **Logs**: System and application logs
- **Charts**: Historical performance data

### Command Line Tools

#### GGnet Management
```bash
# Service management
ggnet start          # Start all services
ggnet stop           # Stop all services
ggnet restart        # Restart all services
ggnet status         # Check service status
ggnet logs           # View backend logs

# Maintenance
ggnet update         # Update GGnet
ggnet backup         # Create backup
```

#### iSCSI Management
```bash
# Target management
ggnet-iscsi create windows11 /opt/ggnet/images/windows11.vhd
ggnet-iscsi list
ggnet-iscsi start windows11
ggnet-iscsi stop windows11
ggnet-iscsi delete windows11
```

#### TFTP Management
```bash
# Script management
ggnet-tftp list
ggnet-tftp create machine01
ggnet-tftp delete machine01
ggnet-tftp status
```

## 🔒 Security

### Authentication
- **JWT Tokens**: Secure API authentication
- **Refresh Tokens**: Automatic token renewal
- **Role-based Access**: Admin, operator, viewer roles
- **Session Management**: Secure session handling

### Network Security
- **Firewall**: Configured for required ports only
- **SSL/TLS**: HTTPS support (configure certificates)
- **iSCSI Authentication**: Optional CHAP authentication
- **Network Isolation**: VLAN support recommended

### Data Protection
- **Database Encryption**: PostgreSQL encryption
- **File Permissions**: Restricted file access
- **Backup Encryption**: Encrypted backups
- **Audit Logging**: Complete activity logging

## 🚨 Troubleshooting

### Common Issues

#### PXE Boot Fails
1. **Check DHCP Configuration**:
   ```bash
   sudo systemctl status isc-dhcp-server
   sudo tail -f /var/log/syslog | grep dhcp
   ```

2. **Verify TFTP Server**:
   ```bash
   sudo systemctl status tftpd-hpa
   sudo netstat -ulnp | grep :69
   ```

3. **Test TFTP Manually**:
   ```bash
   tftp localhost -c get ipxe.efi
   ```

#### iSCSI Connection Issues
1. **Check Target Status**:
   ```bash
   ggnet-iscsi status
   targetcli ls /iscsi
   ```

2. **Verify Network Connectivity**:
   ```bash
   telnet server-ip 3260
   ```

3. **Check Client iSCSI Initiator**:
   ```bash
   iscsiadm -m discovery -t st -p server-ip
   iscsiadm -m session -P 3
   ```

#### Performance Issues
1. **Monitor System Resources**:
   ```bash
   htop
   iostat -x 1
   ```

2. **Check Network Usage**:
   ```bash
   iftop
   nethogs
   ```

3. **Review Logs**:
   ```bash
   journalctl -u ggnet-backend -f
   tail -f /var/log/nginx/error.log
   ```

### Log Locations
- **Backend Logs**: `journalctl -u ggnet-backend`
- **Frontend Logs**: `journalctl -u ggnet-frontend`
- **Nginx Logs**: `/var/log/nginx/`
- **DHCP Logs**: `/var/log/syslog`
- **iSCSI Logs**: `journalctl -u target`
- **Application Logs**: `/opt/ggnet/logs/`

## 📊 Monitoring

### System Monitoring
- **CPU Usage**: Real-time CPU monitoring
- **Memory Usage**: RAM and swap usage
- **Disk I/O**: Storage performance metrics
- **Network I/O**: Bandwidth utilization

### Application Monitoring
- **Active Sessions**: Live session count
- **Boot Times**: Average boot duration
- **Error Rates**: Failed boot attempts
- **Storage Usage**: Image and cache usage

### Alerting
- **Email Notifications**: System alerts
- **Webhook Integration**: Custom notifications
- **SNMP Support**: Network monitoring
- **Log Aggregation**: Centralized logging

## 🔄 Backup & Recovery

### Backup Strategy
1. **Database Backup**:
   ```bash
   pg_dump -U ggnet ggnet > backup.sql
   ```

2. **Configuration Backup**:
   ```bash
   tar -czf config-backup.tar.gz /etc/ggnet/
   ```

3. **Image Backup**:
   ```bash
   rsync -av /opt/ggnet/images/ /backup/images/
   ```

### Recovery Procedures
1. **Database Recovery**:
   ```bash
   psql -U ggnet ggnet < backup.sql
   ```

2. **Configuration Recovery**:
   ```bash
   tar -xzf config-backup.tar.gz -C /
   systemctl restart ggnet-backend
   ```

3. **Full System Recovery**:
   ```bash
   sudo ./install.sh
   # Restore backups
   # Reconfigure settings
   ```

## 🤝 Contributing

### Development Setup
1. **Clone Repository**:
   ```bash
   git clone https://github.com/your-org/ggnet.git
   cd ggnet
   ```

2. **Backend Development**:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

3. **Frontend Development**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Code Style
- **Python**: Black, isort, flake8
- **TypeScript**: ESLint, Prettier
- **Commits**: Conventional commits
- **Documentation**: Docstrings and comments

### Testing
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **iPXE**: Network boot firmware
- **targetcli**: iSCSI target management
- **FastAPI**: Modern Python web framework
- **React**: Frontend framework
- **Tailwind CSS**: Utility-first CSS framework

## 📞 Support

### Documentation
- **Wiki**: [GitHub Wiki](https://github.com/your-org/ggnet/wiki)
- **API Docs**: Available at `/docs` endpoint
- **Examples**: [Examples Directory](examples/)

### Community
- **Issues**: [GitHub Issues](https://github.com/your-org/ggnet/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/ggnet/discussions)
- **Discord**: [Community Server](https://discord.gg/ggnet)

### Professional Support
- **Email**: support@ggnet.local
- **Commercial License**: Available for enterprise use
- **Training**: Custom training sessions available

---

**GGnet Diskless Server** - Empowering network boot solutions with modern technology.