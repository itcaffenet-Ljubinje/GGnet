# ggNET2 Linux Configurator - Plan Implementacije

**Datum:** 2025-01-XX  
**Verzija:** 1.0.0

---

## 📋 Pregled

Plan za implementaciju `ggnet2_linux_configurator` funkcionalnosti na osnovu analize `ggrock-linux-configurator` paketa.

---

## 🏗️ Preporučena Struktura

### Opcija 1: Odvojeni Folder u `scripts/` (PREPORUČENO)

```
ggnet2/
├── scripts/
│   ├── ggnet2_linux_configurator/      # Utility skripte
│   │   ├── ggnet2-auth                 # CLI authentication
│   │   ├── ggnet2-create-bridge        # Bridge creation wrapper
│   │   ├── ggnet2-create-target       # iSCSI target creation wrapper
│   │   ├── ggnet2-delete-target       # iSCSI target deletion wrapper
│   │   ├── ggnet2-img                 # Image management CLI
│   │   ├── ggnet2-preflight           # Preflight checks CLI
│   │   ├── ggnet2-upgrade             # Upgrade automation CLI
│   │   └── ggnet2-linux-configurator  # Main configurator tool
│   ├── systemd/                       # Systemd service fajlovi
│   │   ├── ggnet2-preflight.service
│   │   └── ggnet2-upgrade.service
│   └── templates/                     # Konfiguracija template-i
│       └── dnsmasq/
│           └── pxe.conf
├── app/
│   └── backend/
│       ├── network/
│       │   ├── network_utils.py        # Bridge creation (ažurirati)
│       │   ├── dnsmasq_manager.py     # NOVO - dnsmasq konfiguracija
│       │   └── iscsi_manager.py        # NOVO - iSCSI target management
│       └── system/                     # NOVO - System utilities
│           ├── __init__.py
│           ├── preflight.py            # NOVO - Preflight checks
│           ├── upgrade.py              # NOVO - Upgrade automation
│           └── auth.py                 # NOVO - Authentication CLI
```

**Prednosti:**
- ✅ Jasna organizacija - utility skripte su odvojene
- ✅ Lako instalirati kao paket
- ✅ CLI wrapperi mogu pozivati Python module
- ✅ Systemd service fajlovi su odvojeni

**Nedostaci:**
- ⚠️ Dodatni folder u strukturi

---

### Opcija 2: Integrisano u `app/backend/`

```
ggnet2/
├── app/
│   └── backend/
│       ├── network/
│       │   ├── network_utils.py
│       │   ├── dnsmasq_manager.py
│       │   └── iscsi_manager.py
│       └── system/
│           ├── __init__.py
│           ├── preflight.py
│           ├── upgrade.py
│           └── auth.py
├── scripts/
│   └── systemd/
│       ├── ggnet2-preflight.service
│       └── ggnet2-upgrade.service
```

**Prednosti:**
- ✅ Sve u jednom mestu
- ✅ Python moduli su direktno dostupni

**Nedostaci:**
- ⚠️ CLI wrapperi bi morali biti u `scripts/` ili kao entry points
- ⚠️ Manje jasna organizacija

---

## ✅ Preporuka: Opcija 1

**Razlog:** 
- Utility skripte su CLI tool-ovi koji treba da budu dostupni u PATH-u
- Python moduli su backend logika
- Systemd service fajlovi su deployment konfiguracija
- Jasna separacija concerns

---

## 📦 Komponente za Implementaciju

### 1. Python Backend Moduli (`app/backend/system/`)

#### `preflight.py` - Preflight Checks

**Funkcionalnosti:**
- ✅ `check_ggnet2_installed()` - Provera instalacije ggNET2-a
- ✅ `check_kernel_headers()` - Provera Linux kernel headers
- ✅ `check_dns_config()` - Provera DNS konfiguracije
- ✅ `fix_kernel_headers()` - Automatska instalacija headers
- ✅ `fix_dns_config()` - Automatska DNS konfiguracija
- ✅ `run_preflight_checks()` - Glavna funkcija

**API:**
```python
from app.backend.system.preflight import PreflightChecker

checker = PreflightChecker()
results = checker.run_all_checks()
if results.has_failures():
    checker.fix_failures(results)
```

---

#### `upgrade.py` - Upgrade Automation

**Funkcionalnosti:**
- ✅ `read_upgrade_config()` - Čitanje `/etc/ggnet2/upgrade_env`
- ✅ `run_dist_upgrade()` - Full system upgrade
- ✅ `upgrade_package(package, version)` - Upgrade specifičnog paketa
- ✅ `run_migration(migration_name)` - Database migration
- ✅ `backup_database()` - Database backup pre migracije
- ✅ `run_upgrade()` - Glavna funkcija

**API:**
```python
from app.backend.system.upgrade import UpgradeManager

manager = UpgradeManager()
manager.run_upgrade()
```

**Konfiguracija (`/etc/ggnet2/upgrade_env`):**
```bash
RUN_DIST_UPGRADE=true|false
APP_VERSION=0.1.0|skip
CONFIGURATOR_VERSION=0.1.0|skip
MIGRATION=migration_name
```

---

#### `auth.py` - Authentication CLI

**Funkcionalnosti:**
- ✅ `authenticate(username, password)` - HTTP POST na `/api/users/authenticate`
- ✅ `get_token()` - JWT token extraction
- ✅ `save_token(token)` - Token storage
- ✅ `load_token()` - Token loading

**API:**
```python
from app.backend.system.auth import AuthCLI

auth = AuthCLI()
token = auth.authenticate("username", "password")
auth.save_token(token)
```

---

### 2. Network Moduli (`app/backend/network/`)

#### `dnsmasq_manager.py` - dnsmasq Konfiguracija

**Funkcionalnosti:**
- ✅ `generate_pxe_config(server_ip, nbp_version)` - Generisanje `pxe.conf`
- ✅ `update_dnsmasq_config()` - Ažuriranje dnsmasq konfiguracije
- ✅ `restart_dnsmasq()` - Restart dnsmasq servisa
- ✅ `set_nbp_version(version)` - Postavljanje NBP verzije

**API:**
```python
from app.backend.network.dnsmasq_manager import DNSMasqManager

manager = DNSMasqManager()
manager.generate_pxe_config("192.168.1.10", "latest")
manager.update_dnsmasq_config()
```

---

#### `iscsi_manager.py` - iSCSI Target Management

**Funkcionalnosti:**
- ✅ `create_target(device_name, device_path, target_iqn, initiator_iqn)` - Kreiranje iSCSI target-a
- ✅ `delete_target(target_iqn, device_name)` - Brisanje iSCSI target-a
- ✅ `list_targets()` - Lista svih target-a

**API:**
```python
from app.backend.network.iscsi_manager import ISCSIManager

manager = ISCSIManager()
manager.create_target(
    device_name="pc-100-disk-0",
    device_path="/dev/zvol/pool0/ggnet2/clients/pc-100-disk-0",
    target_iqn="iqn.2019-08.com.ggnet2.ggnet2-1:pc-100-disk-0",
    initiator_iqn="iqn.2019-08.com.ggnet2:pc-100"
)
```

**Zavisnosti:**
- `rtslib-fb` Python biblioteka
- `targetcli` sistem utility

---

### 3. CLI Utility Skripte (`scripts/ggnet2_linux_configurator/`)

#### `ggnet2-auth` - Authentication CLI

**Funkcionalnost:**
- ✅ Prompt za username i password
- ✅ Poziva `app.backend.system.auth.AuthCLI`
- ✅ Čuva JWT token

**Usage:**
```bash
ggnet2-auth
# Username: admin
# Password: ****
```

---

#### `ggnet2-create-bridge` - Bridge Creation

**Funkcionalnost:**
- ✅ Wrapper za `app.backend.network.network_utils.create_bridge()`
- ✅ Backup `/etc/network/interfaces`
- ✅ Restart networking service

**Usage:**
```bash
ggnet2-create-bridge eth0 vmbr0
```

---

#### `ggnet2-create-target` - iSCSI Target Creation

**Funkcionalnost:**
- ✅ Wrapper za `app.backend.network.iscsi_manager.create_target()`

**Usage:**
```bash
ggnet2-create-target pc-100-disk-0 /dev/zvol/pool0/ggnet2/clients/pc-100-disk-0 iqn.2019-08.com.ggnet2.ggnet2-1:pc-100-disk-0 iqn.2019-08.com.ggnet2:pc-100
```

---

#### `ggnet2-delete-target` - iSCSI Target Deletion

**Funkcionalnost:**
- ✅ Wrapper za `app.backend.network.iscsi_manager.delete_target()`

**Usage:**
```bash
ggnet2-delete-target iqn.2019-08.com.ggnet2.ggnet2-1:pc-100-disk-0 pc-100-disk-0
```

---

#### `ggnet2-img` - Image Management CLI

**Funkcionalnost:**
- ✅ Wrapper za `app.backend.images.image_manager` operacije
- ✅ ZFS send/receive
- ✅ Image export (vhd, vhdx, vmdk, qcow2, vdi, raw)

**Usage:**
```bash
ggnet2-img get_sendsize -p pool0 -i games
ggnet2-img list_snapshots -p pool0 -i games
ggnet2-img send -p pool0 -i games > games.img
ggnet2-img receive -p pool0 -i games < games.img
ggnet2-img export -p pool0 -i games -t vhd -f games.vhd
```

---

#### `ggnet2-preflight` - Preflight Checks CLI

**Funkcionalnost:**
- ✅ Wrapper za `app.backend.system.preflight.PreflightChecker`
- ✅ Komande: `start`, `cleanup`

**Usage:**
```bash
ggnet2-preflight start
ggnet2-preflight cleanup
```

---

#### `ggnet2-upgrade` - Upgrade Automation CLI

**Funkcionalnost:**
- ✅ Wrapper za `app.backend.system.upgrade.UpgradeManager`
- ✅ Čita `/etc/ggnet2/upgrade_env`

**Usage:**
```bash
ggnet2-upgrade
```

---

#### `ggnet2-linux-configurator` - Main Configurator Tool

**Funkcionalnost:**
- ✅ Interactive UI za konfiguraciju sistema
- ✅ Package installation
- ✅ Repository setup
- ✅ Bridge configuration
- ✅ IP forwarding
- ✅ dnsmasq configuration
- ✅ NBP version management

**Usage:**
```bash
ggnet2-linux-configurator
ggnet2-linux-configurator --verbose
ggnet2-linux-configurator nbp list
ggnet2-linux-configurator nbp get
ggnet2-linux-configurator nbp set latest
```

---

### 4. Systemd Service Fajlovi (`scripts/systemd/`)

#### `ggnet2-preflight.service`

```ini
[Unit]
Description=Run ggNET2 preflight checks
Wants=network-online.target
After=network-online.target
After=zfs.target

[Service]
Type=simple
ExecStart=/usr/local/bin/ggnet2-preflight start
TimeoutStartSec=0
SyslogIdentifier=ggnet2-preflight
ExecStopPost=-/usr/local/bin/ggnet2-preflight cleanup

[Install]
WantedBy=multi-user.target
```

---

#### `ggnet2-upgrade.service`

```ini
[Unit]
Description=ggNET2 Upgrade Service
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/ggnet2-upgrade
SyslogIdentifier=ggnet2-upgrade

[Install]
WantedBy=multi-user.target
```

---

## 📋 Implementacioni Plan

### Faza 1: Backend Moduli (Prioritet 1)

1. ✅ Kreirati `app/backend/system/` folder
2. ✅ Implementirati `preflight.py`
3. ✅ Implementirati `upgrade.py`
4. ✅ Implementirati `auth.py`
5. ✅ Implementirati `dnsmasq_manager.py`
6. ✅ Implementirati `iscsi_manager.py`

### Faza 2: CLI Utility Skripte (Prioritet 2)

1. ✅ Kreirati `scripts/ggnet2_linux_configurator/` folder
2. ✅ Implementirati `ggnet2-auth`
3. ✅ Implementirati `ggnet2-create-bridge`
4. ✅ Implementirati `ggnet2-create-target`
5. ✅ Implementirati `ggnet2-delete-target`
6. ✅ Implementirati `ggnet2-img`
7. ✅ Implementirati `ggnet2-preflight`
8. ✅ Implementirati `ggnet2-upgrade`
9. ✅ Implementirati `ggnet2-linux-configurator`

### Faza 3: Systemd Services (Prioritet 2)

1. ✅ Kreirati `scripts/systemd/` folder
2. ✅ Implementirati `ggnet2-preflight.service`
3. ✅ Implementirati `ggnet2-upgrade.service`
4. ✅ Ažurirati `setup_systemd.sh` da instalira nove service fajlove

### Faza 4: iPXE Boot Fajlovi (Prioritet 1)

1. ✅ Ažurirati `setup_ipxe.sh` da distribuira iPXE fajlove
2. ✅ Dodati iPXE fajlove u `scripts/templates/ipxe/`

### Faza 5: Dokumentacija (Prioritet 3)

1. ✅ Kreirati `docs/scripts/ggnet2_linux_configurator.md`
2. ✅ Ažurirati `docs/backend/system.md`
3. ✅ Ažurirati `docs/backend/network.md`

---

## 🔧 Zavisnosti

### Python Paketi

```python
# requirements.txt dodatak
rtslib-fb>=2.1.0  # iSCSI target management
debinterface>=0.1.0  # Network interfaces management (ili custom implementacija)
```

### Sistem Paketi

```bash
# Debian/Ubuntu
apt-get install -y targetcli-fb  # iSCSI target CLI
apt-get install -y dnsmasq       # DHCP/DNS server
apt-get install -y dialog        # Interactive UI (za ggnet2-linux-configurator)
```

---

## ✅ Zaključak

**Preporučena Struktura:** Opcija 1 - Odvojeni folder `scripts/ggnet2_linux_configurator/`

**Razlog:**
- ✅ Jasna organizacija
- ✅ CLI utility skripte su odvojene od backend logike
- ✅ Lako instalirati kao paket
- ✅ Systemd service fajlovi su odvojeni

**Sledeći Koraci:**
1. Kreirati strukturu foldera
2. Implementirati Python backend module
3. Implementirati CLI utility skripte
4. Kreirati systemd service fajlove
5. Ažurirati setup skripte

---

*Plan kreiran na osnovu analize `ggrock-linux-configurator_0.1.109-1_amd64` paketa*


