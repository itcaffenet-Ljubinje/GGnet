# ggNET2 Scripts Summary

**Datum kreiranja:** 2025-01-26  
**Status:** 📋 Complete Scripts Summary

---

## 📊 Pregled

Ovaj dokument sumira sve skripte koje ggNET2 koristi, bazirane na ggRock skriptama.

---

## 🔧 Utility Scripts

### 1. `ggnet2-cert-mgr`
**Lokacija:** `scripts/ggnet2-cert-mgr`  
**Funkcionalnost:** SSL certificate management  
**Usage:**
```bash
sudo ggnet2-cert-mgr generate [dns_addresses] [ip_addresses]
```
**Dokumentacija:** `docs/scripts/ggnet2-cert-mgr.md`

---

### 2. `ggnet2-create-bridge`
**Lokacija:** 
- `scripts/ggnet2-create-bridge.py` (Python, preporučeno)
- `scripts/ggnet2_linux_configurator/ggnet2-create-bridge` (Bash wrapper)

**Funkcionalnost:** Network bridge creation  
**Usage:**
```bash
# Python script
sudo python3 scripts/ggnet2-create-bridge.py eth0 vmbr0

# Bash wrapper
sudo ggnet2-create-bridge vmbr0 eth0
```
**Dokumentacija:** `docs/scripts/ggnet2-create-bridge.md`

---

### 3. `ggnet2-create-target`
**Lokacija:** `scripts/ggnet2_linux_configurator/ggnet2-create-target`  
**Funkcionalnost:** iSCSI target creation  
**Usage:**
```bash
ggnet2-create-target <device_name> <device_path> <target_iqn> <initiator_iqn>
```

---

### 4. `ggnet2-delete-target`
**Lokacija:** `scripts/ggnet2_linux_configurator/ggnet2-delete-target`  
**Funkcionalnost:** iSCSI target deletion  
**Usage:**
```bash
ggnet2-delete-target <target_iqn> [device_name]
```

---

### 5. `ggnet2-img`
**Lokacija:** `scripts/ggnet2_linux_configurator/ggnet2-img`  
**Funkcionalnost:** Image management CLI  
**Usage:**
```bash
ggnet2-img <command> [arguments]
```

---

### 6. `ggnet2-lsblk`
**Lokacija:** `scripts/ggnet2-lsblk`  
**Funkcionalnost:** ZFS zpool.d custom lsblk script  
**Usage:**
```bash
# Direct usage
VDEV_UPATH=/dev/sda ggnet2-lsblk

# ZFS automatically uses it
zpool status pool0
```
**Dokumentacija:** `docs/scripts/ggnet2-lsblk.md`

---

### 7. `ggnet2-auth`
**Lokacija:** `scripts/ggnet2_linux_configurator/ggnet2-auth`  
**Funkcionalnost:** Interactive authentication CLI  
**Usage:**
```bash
ggnet2-auth [--save-token]
```

---

### 8. `ggnet2-preflight`
**Lokacija:** `scripts/ggnet2_linux_configurator/ggnet2-preflight`  
**Funkcionalnost:** Preflight checks and fixes  
**Usage:**
```bash
ggnet2-preflight {start|cleanup}
```

---

### 9. `ggnet2-upgrade`
**Lokacija:** `scripts/ggnet2_linux_configurator/ggnet2-upgrade`  
**Funkcionalnost:** System upgrade automation  
**Usage:**
```bash
ggnet2-upgrade
```

---

### 10. `ggnet2-upgrade-debian12`
**Lokacija:** `scripts/ggnet2-upgrade-debian12`  
**Funkcionalnost:** Debian 11 → Debian 12 upgrade  
**Usage:**
```bash
sudo ggnet2-upgrade-debian12
```
**Dokumentacija:** `docs/scripts/ggnet2-upgrade-debian12.md`

---

### 11. `ggnet2-linux-configurator`
**Lokacija:** `scripts/ggnet2_linux_configurator/ggnet2-linux-configurator`  
**Funkcionalnost:** Main interactive configurator tool  
**Usage:**
```bash
ggnet2-linux-configurator
```

---

## 📋 Setup Scripts

### 1. `install.sh`
**Lokacija:** `scripts/install.sh`  
**Funkcionalnost:** Main installation script  
**Usage:**
```bash
sudo bash scripts/install.sh
```

---

### 2. `setup_zfs.sh`
**Lokacija:** `scripts/setup_zfs.sh`  
**Funkcionalnost:** ZFS pool and dataset setup  
**Usage:**
```bash
sudo bash scripts/setup_zfs.sh
```

---

### 3. `setup_nginx.sh`
**Lokacija:** `scripts/setup_nginx.sh`  
**Funkcionalnost:** Nginx reverse proxy setup  
**Usage:**
```bash
sudo bash scripts/setup_nginx.sh
```

---

### 4. `setup_pxe.sh` / `setup_ipxe.sh`
**Lokacija:** `scripts/setup_pxe.sh`, `scripts/setup_ipxe.sh`  
**Funkcionalnost:** PXE/iPXE boot server setup  
**Usage:**
```bash
sudo bash scripts/setup_pxe.sh
```

---

### 5. `setup_systemd.sh`
**Lokacija:** `scripts/setup_systemd.sh`  
**Funkcionalnost:** Systemd service setup  
**Usage:**
```bash
sudo bash scripts/setup_systemd.sh
```

---

### 6. `setup_ssl.sh`
**Lokacija:** `scripts/setup_ssl.sh`  
**Funkcionalnost:** SSL certificate setup  
**Usage:**
```bash
sudo bash scripts/setup_ssl.sh
```

---

### 7. `setup_prometheus.sh`
**Lokacija:** `scripts/setup_prometheus.sh`  
**Funkcionalnost:** Prometheus monitoring setup  
**Usage:**
```bash
sudo bash scripts/setup_prometheus.sh
```

---

### 8. `setup_grafana.sh`
**Lokacija:** `scripts/setup_grafana.sh`  
**Funkcionalnost:** Grafana monitoring setup  
**Usage:**
```bash
sudo bash scripts/setup_grafana.sh
```

---

### 9. `install_system_utilities.sh`
**Lokacija:** `scripts/install_system_utilities.sh`  
**Funkcionalnost:** Install system utilities (util-linux, smartmontools, wakeonlan)  
**Usage:**
```bash
sudo bash scripts/install_system_utilities.sh
```

---

## 📊 Comparison: ggRock vs ggNET2

| ggRock Script | ggNET2 Script | Status |
|---------------|---------------|--------|
| `ggrock-cert-mgr` | `ggnet2-cert-mgr` | ✅ Implemented |
| `ggrock-create-bridge` | `ggnet2-create-bridge.py` | ✅ Implemented |
| `ggrock-create-target` | `ggnet2-create-target` | ✅ Implemented |
| `ggrock-delete-target` | `ggnet2-delete-target` | ✅ Implemented |
| `ggrock-img` | `ggnet2-img` | ✅ Implemented |
| `ggrock-lsblk` | `ggnet2-lsblk` | ✅ Implemented |
| `ggrock-auth` | `ggnet2-auth` | ✅ Implemented |
| `ggrock-preflight` | `ggnet2-preflight` | ✅ Implemented |
| `ggrock-upgrade` | `ggnet2-upgrade` | ✅ Implemented |
| `ggrock-upgrade-debian12` | `ggnet2-upgrade-debian12` | ✅ Implemented |
| `ggrock-linux-configurator` | `ggnet2-linux-configurator` | ✅ Implemented |

---

## 📚 Documentation

Sve skripte imaju dokumentaciju u `docs/scripts/` direktorijumu:

- `docs/scripts/ggnet2-cert-mgr.md`
- `docs/scripts/ggnet2-create-bridge.md`
- `docs/scripts/ggnet2-lsblk.md`
- `docs/scripts/ggnet2-upgrade-debian12.md`
- `docs/scripts/install.md`
- `docs/scripts/setup_zfs.md`
- `docs/scripts/setup_nginx.md`
- `docs/scripts/setup_pxe.md`
- `docs/scripts/setup_systemd.md`
- `docs/scripts/setup_ssl.md`
- `docs/scripts/setup_prometheus.md`
- `docs/scripts/setup_grafana.md`

---

## ✅ Installation

### Install All Utility Scripts

```bash
# Copy scripts to /usr/local/bin/
sudo cp scripts/ggnet2_linux_configurator/ggnet2-* /usr/local/bin/
sudo cp scripts/ggnet2-cert-mgr /usr/local/bin/
sudo cp scripts/ggnet2-upgrade-debian12 /usr/local/bin/
sudo cp scripts/ggnet2-lsblk /usr/local/bin/

# Make executable
sudo chmod +x /usr/local/bin/ggnet2-*
```

### Install ZFS lsblk Script

```bash
# Create directories
sudo mkdir -p /usr/lib/ggnet2/zpool.d
sudo mkdir -p /etc/zfs/zpool.d

# Copy script
sudo cp scripts/ggnet2-lsblk /usr/lib/ggnet2/zpool.d/
sudo chmod +x /usr/lib/ggnet2/zpool.d/ggnet2-lsblk

# Create symlink
sudo ln -sf /usr/lib/ggnet2/zpool.d/ggnet2-lsblk /etc/zfs/zpool.d/ggnet2-lsblk
```

---

## 🎯 Quick Reference

### Certificate Management
```bash
sudo ggnet2-cert-mgr generate "ggnet2.local" "192.168.1.100"
```

### Network Bridge
```bash
sudo python3 scripts/ggnet2-create-bridge.py eth0 vmbr0
```

### iSCSI Target
```bash
ggnet2-create-target pc-100-disk-0 /dev/zvol/pool0/ggnet2/clients/pc-100-disk-0 \
  iqn.2019-08.com.ggnet2.ggnet2-1:pc-100-disk-0 \
  iqn.2019-08.com.ggnet2:pc-100
```

### Image Management
```bash
ggnet2-img list_snapshots pool0/ggnet2/images/win11
```

### System Upgrade
```bash
sudo ggnet2-upgrade-debian12
```

---

**ggNET2 Scripts Summary Complete!** ✅

