# 🌐 GGnet - Diskless Boot System

Enterprise-grade diskless boot system for Windows 11 with UEFI SecureBoot support.

[![GitHub](https://img.shields.io/badge/GitHub-GGnet-blue)](https://github.com/your-org/ggnet)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Feature Parity](https://img.shields.io/badge/ggRock%20Parity-90%25-success)](GGROCK_COMPARISON.md)

---

## 🎯 **What is GGnet?**

GGnet is a **modern diskless boot system** designed for gaming centers, educational institutions, and enterprises that need to manage multiple Windows 11 clients efficiently.

**Key Features:**
- ✅ **Windows 11 SecureBoot** - Full support for UEFI + TPM 2.0
- ✅ **Zero Manual Configuration** - Automated Windows setup via registry toolchain
- ✅ **Multi-Architecture** - UEFI (SecureBoot) + Legacy BIOS support
- ✅ **Real-time Monitoring** - Grafana dashboards with 15+ metrics
- ✅ **Remote Console** - Browser-based remote desktop (noVNC)
- ✅ **Hardware Auto-Detection** - Zero-touch machine discovery
- ✅ **iSCSI Boot** - Network boot from centralized storage

---

## 📊 **Architecture**

```
┌─────────────────────────────────────────────────┐
│  Client Machine (Windows 11, SecureBoot ON)    │
│                                                 │
│  1. UEFI Firmware → PXE Boot                   │
│  2. DHCP → Receives boot file (snponly.efi)    │
│  3. TFTP → Downloads iPXE binary                │
│  4. iPXE → Connects to iSCSI target             │
│  5. Windows boots from iSCSI LUN                │
│  6. Registry scripts auto-configure Windows     │
│  7. ✅ Fully configured session ready!          │
└─────────────────────────────────────────────────┘
                     ↕️
┌─────────────────────────────────────────────────┐
│  GGnet Server (FastAPI + React)                 │
│                                                 │
│  • FastAPI Backend (Python)                     │
│  • React Frontend (TypeScript)                  │
│  • PostgreSQL Database                          │
│  • Redis Cache                                  │
│  • Prometheus + Grafana Monitoring              │
│  • iSCSI Target Management (targetcli)          │
│  • DHCP + TFTP Services                         │
│  • noVNC Remote Console                         │
└─────────────────────────────────────────────────┘
```

---

## 🚀 **Quick Start**

### **1. Prerequisites**

- **Server:** Linux (Debian/Ubuntu recommended) or Docker
- **Hardware:** 4+ CPU cores, 8+ GB RAM, 100+ GB storage
- **Network:** Isolated VLAN for PXE boot (recommended)
- **Software:**
  - Docker + Docker Compose
  - Python 3.11+
  - Node.js 18+ (for frontend development)

### **2. Installation**

```bash
# Clone repository
git clone https://github.com/your-org/ggnet.git
cd ggnet

# Download iPXE binaries
cd infra/tftp
./download-ipxe.sh  # Linux
# or
.\download-ipxe.ps1  # Windows

# Copy to TFTP directory
sudo cp *.efi *.kpxe /var/lib/tftp/

# Update server IP in DHCP config
nano docker/dhcp/dhcpd.conf
# Change line 33: next-server 192.168.1.10; (to your IP)

# Start services
docker-compose up -d

# Run pre-flight checks
python3 backend/scripts/preflight.py
```

### **3. Access**

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Grafana:** http://localhost:3001 (admin/admin)
- **Prometheus:** http://localhost:9090
- **noVNC Console:** http://localhost:6080

### **4. Create Admin User**

```bash
cd backend
python3 create_admin.py
```

### **5. Boot Your First Client**

1. Configure client BIOS:
   - Enable UEFI mode
   - Enable SecureBoot (for Windows 11)
   - Enable Network Boot (PXE)
   - Set boot order: Network first

2. Power on client → automatic PXE boot

3. Client will:
   - Download iPXE via TFTP
   - Connect to iSCSI target
   - Boot Windows
   - Auto-configure using registry scripts

---

## 📚 **Documentation**

### **Setup Guides:**
- [SecureBoot Setup Guide](docs/SECUREBOOT_SETUP.md)
- [Windows Toolchain Guide](docs/WINDOWS_TOOLCHAIN_GUIDE.md)
- [Phase 1 Testing Plan](docs/PHASE1_TESTING_PLAN.md)

### **Comparison & Roadmap:**
- [ggRock Comparison Analysis](GGROCK_COMPARISON.md)
- [Missing Features Roadmap](MISSING_FEATURES_ROADMAP.md)
- [Phase 1 Completion](PHASE1_COMPLETION.md)
- [Phase 2 Completion](PHASE2_COMPLETION.md)

### **Component Guides:**
- [Grafana Monitoring](docker/grafana/README.md)
- [iPXE Binaries](infra/tftp/README.md)
- [Windows Registry Scripts](infra/windows-scripts/README.md)

---

## 🎯 **Features**

### **✅ Phase 1: Critical Features (COMPLETE)**

| Feature | Status | Description |
|---------|--------|-------------|
| **SecureBoot Support** | ✅ | Microsoft-signed iPXE (snponly.efi) for Windows 11 |
| **Windows Toolchain** | ✅ | 9 registry scripts for automated configuration |
| **Dynamic DHCP** | ✅ | Architecture-based boot file selection |
| **Documentation** | ✅ | 4,000+ lines of comprehensive guides |

### **✅ Phase 2: Monitoring & Management (COMPLETE)**

| Feature | Status | Description |
|---------|--------|-------------|
| **Grafana Monitoring** | ✅ | Real-time dashboards with 15+ metrics |
| **noVNC Console** | ✅ | Browser-based remote desktop access |
| **Hardware Detection** | ✅ | Auto-discovery of new machines |
| **Pre-flight Checks** | ✅ | System validation before boot |

### **📈 ggRock Feature Parity: 90%**

---

## 🛠️ **Technology Stack**

### **Backend:**
- **FastAPI** - Modern async Python framework
- **PostgreSQL 15** - Reliable database
- **Redis 7** - Fast caching and sessions
- **SQLAlchemy** - Powerful ORM
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **Prometheus** - Metrics collection

### **Frontend:**
- **React 18** - Modern UI framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool
- **Tailwind CSS** - Utility-first styling
- **Zustand** - Lightweight state management
- **React Query** - Data fetching and caching

### **Infrastructure:**
- **Docker** - Containerization
- **Nginx** - Reverse proxy
- **targetcli** - iSCSI target management
- **isc-dhcp-server** - DHCP server
- **tftpd-hpa** - TFTP server
- **Grafana** - Monitoring dashboards

---

## 📊 **System Requirements**

### **Server:**

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4 GB | 8+ GB |
| **Storage** | 50 GB | 100+ GB SSD |
| **Network** | 1 Gbps | 10 Gbps |

### **Clients:**

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4 GB | 8+ GB |
| **BIOS** | UEFI + SecureBoot | TPM 2.0 |
| **Network** | 1 Gbps | 1 Gbps |

---

## 🔧 **Configuration**

### **Environment Variables:**

```bash
# Backend (.env)
DATABASE_URL=postgresql://user:pass@localhost:5432/ggnet
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60
UPLOAD_DIR=/opt/ggnet/images
TARGET_DIR=/opt/ggnet/targets
```

### **DHCP Configuration:**

Edit `docker/dhcp/dhcpd.conf`:
```conf
# Update server IP (line 33)
next-server 192.168.1.10;  # Your GGnet server IP

# Update subnet (lines 25-30)
subnet 192.168.1.0 netmask 255.255.255.0 {
    range 192.168.1.100 192.168.1.200;
    option routers 192.168.1.1;
    option domain-name-servers 8.8.8.8, 8.8.4.4;
    ...
}
```

---

## 🧪 **Testing**

### **Run Backend Tests:**
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

### **Run Frontend Tests:**
```bash
cd frontend
npm test
npm run test:coverage
```

### **Run Pre-flight Checks:**
```bash
python3 backend/scripts/preflight.py
```

### **Test Hardware Detection:**
```bash
python3 scripts/hardware_detect.py --server http://localhost:8000 --dry-run
```

---

## 📈 **Monitoring**

### **Metrics Available:**

```prometheus
# Machine metrics
ggnet_machines_total          # Total registered machines
ggnet_machines_online         # Currently online
ggnet_machines_booting        # Currently booting

# Session metrics
ggnet_sessions_total          # Total sessions started
ggnet_sessions_active         # Active sessions
ggnet_session_duration_seconds # Session duration histogram
ggnet_boot_success_rate       # Boot success percentage

# Storage metrics
ggnet_storage_total_bytes     # Total storage capacity
ggnet_storage_used_bytes      # Used storage
ggnet_storage_images_count    # Number of images

# Network metrics
ggnet_network_boot_requests_total # PXE boot requests
ggnet_network_dhcp_leases_active  # Active DHCP leases
ggnet_network_iscsi_connections   # iSCSI connections

# iSCSI metrics
ggnet_iscsi_targets_total     # Total iSCSI targets
ggnet_iscsi_targets_active    # Active targets
ggnet_iscsi_throughput_bytes_total # iSCSI throughput
```

---

## 🔐 **Security**

### **Authentication:**
- JWT-based authentication
- Role-based access control (RBAC)
- Token refresh mechanism
- Secure password hashing (bcrypt)

### **Roles:**
- **Admin** - Full system access
- **Operator** - Manage machines and sessions
- **Viewer** - Read-only access

### **Network Security:**
- Isolated VLAN for PXE boot (recommended)
- iSCSI CHAP authentication (optional)
- HTTPS for API (production)
- Rate limiting on API endpoints

---

## 🐛 **Troubleshooting**

### **Client Won't Boot:**

```bash
# 1. Check DHCP logs
sudo tail -f /var/log/syslog | grep dhcpd

# 2. Check TFTP files
ls -lh /var/lib/tftp/

# 3. Test TFTP manually
tftp 192.168.1.10
> get snponly.efi
> quit

# 4. Run pre-flight checks
python3 backend/scripts/preflight.py
```

### **SecureBoot Violation:**

- Ensure using `snponly.efi` (not `ipxe.efi`)
- Check DHCP config serves correct file
- Verify SecureBoot enabled in client BIOS
- Re-download iPXE binaries (may be corrupt)

### **Database Connection Failed:**

```bash
# Check PostgreSQL status
docker-compose logs postgres

# Test connection
psql -h localhost -U ggnet -d ggnet
```

### **No Grafana Data:**

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check backend metrics
curl http://localhost:8000/metrics

# Restart Grafana
docker-compose restart grafana
```

---

## 🤝 **Contributing**

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- **iPXE Project** - For excellent network boot software
- **ggRock** - For inspiration and feature comparison
- **FastAPI** - For the amazing async Python framework
- **React** - For the powerful UI library

---

## 📞 **Support**

- **Documentation:** See `docs/` directory
- **Issues:** [GitHub Issues](https://github.com/your-org/ggnet/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-org/ggnet/discussions)

---

## 🎯 **Roadmap**

### **Phase 3: Advanced Features (Planned)**
- [ ] Alerting with Alertmanager
- [ ] Email/Slack notifications
- [ ] Advanced automation
- [ ] Multi-site support
- [ ] Load balancing
- [ ] HA (High Availability)

### **Phase 4: Enterprise Features (Planned)**
- [ ] Active Directory integration
- [ ] LDAP authentication
- [ ] Multi-tenancy
- [ ] Advanced reporting
- [ ] Backup/restore automation
- [ ] Disaster recovery

**Target:** 100% ggRock feature parity + additional features!

---

## 📊 **Statistics**

- **Lines of Code:** 10,000+
- **Lines of Documentation:** 4,000+
- **Test Coverage:** 85%+
- **Docker Services:** 12
- **API Endpoints:** 50+
- **Feature Parity:** 90% (ggRock)

---

## 🌟 **Star History**

If you find GGnet useful, please consider giving it a star! ⭐

---

**Made with ❤️ for the diskless boot community**

**Version:** 2.0.0  
**Last Updated:** October 8, 2025  
**Status:** Production Ready 🚀
