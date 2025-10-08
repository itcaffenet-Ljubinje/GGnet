# 🎉 GGnet v2.1.0 - Production Release

**Release Date:** October 8, 2025  
**Status:** ✅ Production Ready  
**Feature Parity:** 95% ggRock (for pre-configured images)

---

## 🎯 **What's Included**

### **Core Features:**
- ✅ Windows 11 SecureBoot support (snponly.efi)
- ✅ Multi-architecture boot (UEFI + Legacy BIOS)
- ✅ Automated Windows configuration (9 registry scripts)
- ✅ iSCSI target management (targetcli integration)
- ✅ Image upload & conversion (VHDX/QCOW2/RAW)
- ✅ Session orchestration (start/stop/monitor)
- ✅ Real-time monitoring (Grafana + Prometheus)
- ✅ Remote console (noVNC)
- ✅ Hardware auto-detection
- ✅ Pre-flight system checks
- ✅ CLI tools (ggnet, ggnet-iscsi)
- ✅ Automated installer (install.sh)

---

## 🚀 **Quick Start**

### **Docker Deployment:**
```bash
git clone https://github.com/itcaffenet-Ljubinje/GGnet.git
cd GGnet
cd infra/tftp && ./download-ipxe.sh && cd ../..
docker-compose up -d
docker exec -it ggnet-backend python3 create_admin.py
open http://localhost:3000
```

### **Native Installation:**
```bash
wget https://raw.githubusercontent.com/itcaffenet-Ljubinje/GGnet/main/install.sh
sudo bash install.sh
sudo ggnet start
```

---

## 📊 **System Requirements**

### **Server:**
- CPU: 4+ cores
- RAM: 8+ GB
- Storage: 100+ GB SSD
- OS: Debian 11+ / Ubuntu 20.04+

### **Network:**
- 1 Gbps network minimum
- Static IP for server
- Isolated VLAN (recommended)

---

## ✅ **What Works**

### **Tested Scenarios:**
- ✅ Boot Windows 11 with SecureBoot from pre-configured VHDX
- ✅ Boot Windows 10 from VHDX/QCOW2
- ✅ Legacy BIOS boot
- ✅ Auto-configuration via registry scripts
- ✅ Real-time monitoring
- ✅ Remote console access
- ✅ Hardware auto-discovery

### **Supported Formats:**
- ✅ VHDX (Windows Hyper-V)
- ✅ QCOW2 (QEMU/KVM)
- ✅ RAW (dd images)

---

## ⚠️ **Known Limitations**

### **v2.1.0 Requires:**
- Pre-configured Windows images (VHDX/QCOW2)
- Windows already installed and sysprepped
- Drivers pre-installed in image

### **Not Included:**
- ❌ WinPE for fresh Windows installation
- ❌ Automated driver injection
- ❌ Network bridging automation
- ❌ KVM/libvirt virtualization

**These will be added in v2.2.0 and v3.0.0**

---

## 📚 **Documentation**

- [README.md](README.md) - Main documentation
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production deployment
- [GGROCK_PARITY_FINAL.md](GGROCK_PARITY_FINAL.md) - Feature comparison
- [docs/SECUREBOOT_SETUP.md](docs/SECUREBOOT_SETUP.md) - SecureBoot guide
- [docs/WINDOWS_TOOLCHAIN_GUIDE.md](docs/WINDOWS_TOOLCHAIN_GUIDE.md) - Windows automation

---

## 🐛 **Bug Fixes**

- Fixed import error in hardware.py
- Optimized repository (removed 82 legacy files)
- Updated .gitignore for cache files

---

## 🎯 **Roadmap**

### **v2.2.0 (Next - Quick Enhancements):**
- Add missing utilities (chntpw, cifs-utils, bridge-utils, pv)
- Network bridging script (ggnet-create-bridge)
- Legacy iPXE versions for old hardware
- Enhanced CLI tools

### **v3.0.0 (Future - WinPE & Full Automation):**
- WinPE boot environment
- Fresh Windows installation
- Driver injection system
- Disk partitioning automation
- Software deployment
- 100% ggRock feature parity

---

## 🙏 **Acknowledgments**

- iPXE Project
- ggRock (for inspiration)
- FastAPI community
- React community

---

**Download:** [GGnet v2.1.0](https://github.com/itcaffenet-Ljubinje/GGnet/releases/tag/v2.1.0)

**Install:** See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

**Support:** [GitHub Issues](https://github.com/itcaffenet-Ljubinje/GGnet/issues)

---

**GGnet v2.1.0 - Production Ready!** 🚀

