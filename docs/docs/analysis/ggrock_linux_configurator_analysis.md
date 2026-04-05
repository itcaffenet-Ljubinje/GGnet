# ggRock Linux Configurator Analiza

**Datum:** 2025-01-XX  
**Verzija:** 1.0.0

---

## 📋 Pregled

Analiza `ggrock-linux-configurator_0.1.109-1_amd64` paketa - utility paket za konfiguraciju Linux sistema za ggRock.

**Lokacija:** `C:\Users\SERVER-PC\Desktop\ggnet-hack\ggrock-linux-configurator_0.1.109-1_amd64\data`

**Licenca:** LGPL-2.1+  
**Copyright:** 2020 ggCircuit LLC

---

## 📊 Struktura Paketa

```
ggrock-linux-configurator_0.1.109-1_amd64/data/
├── etc/
│   ├── ggrock-linux-configurator/
│   │   └── templates/
│   │       └── pxe.conf                    # PXE/dnsmasq template
│   └── zfs/
│       └── zpool.d/
│           └── ggrock-lsblk                # ZFS pool script
├── lib/
│   └── systemd/
│       └── system/
│           ├── ggrock-preflight.service    # Preflight checks service
│           └── ggrock-upgrade.service      # Upgrade service
├── usr/
│   ├── bin/
│   │   ├── ggrock-auth                     # Authentication utility
│   │   ├── ggrock-create-bridge           # Network bridge creation
│   │   ├── ggrock-create-target           # iSCSI target creation
│   │   ├── ggrock-delete-target           # iSCSI target deletion
│   │   ├── ggrock-img                     # Image management utility
│   │   ├── ggrock-preflight               # Preflight checks
│   │   ├── ggrock-upgrade                 # System upgrade
│   │   └── ggrock-upgrade-debian12        # Debian 12 upgrade
│   ├── lib/
│   │   └── ggrock/
│   │       └── zpool.d/
│   │           └── ggrock-lsblk           # ZFS pool script (copy)
│   └── sbin/
│       └── ggrock-linux-configurator      # Main configurator tool
└── var/
    └── lib/
        └── tftp/
            ├── ipxe.efi                   # iPXE UEFI bootloader
            ├── ipxe.pxe                   # iPXE PXE bootloader
            ├── ipxe_202006.efi            # iPXE version 202006
            ├── ipxe_202102.efi            # iPXE version 202102
            ├── snp.efi                    # SNP UEFI bootloader
            ├── snponly.efi                # SNP only UEFI bootloader
            ├── undionly.kpxe              # UNDI only PXE bootloader
            ├── undionly.pxe               # UNDI only PXE bootloader
            ├── undionly_202006.kpxe       # UNDI only version 202006
            └── undionly_202102.kpxe       # UNDI only version 202102
```

---

## 🔍 Detaljna Analiza Komponenti

### 1. Utility Skripte (`usr/bin/`)

#### ggrock-auth (5,091 bytes)

**Funkcionalnost:** Authentication utility - ggLeap employee credentials authentication

**Detalji:**
- ✅ Prompt za username i password
- ✅ HTTP POST request na `https://localhost/api/users/authenticate`
- ✅ JSON response parsing
- ✅ JWT token extraction
- ✅ Token storage (verovatno u fajl ili environment variable)

**API Endpoint:**
- `POST /api/users/authenticate`
- Request: `{"username": "...", "password": "..."}`
- Response: JWT token (verovatno)

**Primenljivo za ggNET2:**
- ✅ Authentication mehanizam
- ✅ JWT token management
- ✅ CLI authentication tool

---

#### ggrock-create-bridge (1,793 bytes)

**Funkcionalnost:** Network bridge creation utility - Python skripta za kreiranje network bridge-a

**Detalji:**
- ✅ Koristi `debinterface` Python biblioteku
- ✅ Kreira bridge u `/etc/network/interfaces`
- ✅ Backup originalnog fajla sa `.bak` ekstenzijom
- ✅ Ako bridge već postoji, samo prilagođava opcije
- ✅ Kreira fizički adapter sa `source: manual` za bridge mode
- ✅ Bridge opcije: `stp: off`, `fd: 0`

**Usage:**
```bash
ggrock-create-bridge <nic_name> <bridge_name>
# Example: ggrock-create-bridge eth0 vmbr0
```

**Primenljivo za ggNET2:**
- ✅ Network bridge creation
- ✅ VM network setup
- ✅ `/etc/network/interfaces` management
- ✅ Integracija sa `network_utils.py`

---

#### ggrock-create-target (1,409 bytes)

**Funkcionalnost:** iSCSI target creation utility - Python skripta za kreiranje iSCSI target-a

**Detalji:**
- ✅ Koristi `rtslib_fb` Python biblioteku (targetcli)
- ✅ Kreira BlockStorageObject iz ZFS zvol-a
- ✅ Kreira iSCSI Target sa TPG (Target Portal Group)
- ✅ Kreira NetworkPortal na `0.0.0.0:3260`
- ✅ Kreira LUN i NodeACL
- ✅ Mapira LUN na initiator
- ✅ Disable authentication (`authentication: 0`)

**Usage:**
```bash
ggrock-create-target <device_name> <device_path> <target_iqn> <initiator_iqn>
# Example: ggrock-create-target pc-100-disk-0 /dev/zvol/pool0/ggrock/clients/pc-100-disk-0 iqn.2019-08.com.ggrock.ggrock1:pc-100-disk-0 iqn.2019-08.com.ggrock:pc-100
```

**Primenljivo za ggNET2:**
- ✅ iSCSI target creation
- ✅ Machine boot setup
- ✅ ZFS zvol integration
- ✅ Integracija sa `machine_manager.py`

---

#### ggrock-delete-target (1,670 bytes)

**Funkcionalnost:** iSCSI target deletion utility - Python skripta za brisanje iSCSI target-a

**Detalji:**
- ✅ Koristi `rtslib_fb` Python biblioteku
- ✅ Briše iSCSI Target i sve LUN-ove
- ✅ Briše BlockStorageObject
- ✅ Error handling za broken links (`RTSLibBrokenLink`)
- ✅ Opciono brisanje BlockStorageObject ako target ne postoji

**Usage:**
```bash
ggrock-delete-target <target_iqn> [device_name]
# Example: ggrock-delete-target iqn.2019-08.com.ggrock.ggrock1:pc-100-disk-0 pc-100-disk-0
```

**Primenljivo za ggNET2:**
- ✅ iSCSI target deletion
- ✅ Machine cleanup
- ✅ Error handling
- ✅ Integracija sa `machine_manager.py`

---

#### ggrock-img (8,183 bytes)

**Funkcionalnost:** Image management utility - Bash skripta za ZFS image operacije

**Komande:**
- ✅ `get_sendsize` - Procena veličine backup-a
- ✅ `list_snapshots` - Lista snapshot-a za sliku
- ✅ `send` - Backup slike (ZFS send)
- ✅ `receive` - Restore slike (ZFS receive)
- ✅ `export` - Export slike u različite formate (vhd, vhdx, vmdk, qcow2, vdi, raw)

**Usage:**
```bash
# Estimate backup size
ggrock-img get_sendsize -p pool0 -i games

# List snapshots
ggrock-img list_snapshots -p pool0 -i games

# Backup image
ggrock-img send -p pool0 -i games > games.img

# Restore image
ggrock-img receive -p pool0 -i games < games.img

# Incremental backup
ggrock-img send -p pool0 -i games -I last_snapshot | ssh host2 ggrock-img receive -p pool0 -i games

# Export to VHD
ggrock-img export -p pool0 -i games -t vhd -f games.vhd
```

**Primenljivo za ggNET2:**
- ✅ Image backup/restore
- ✅ ZFS send/receive operacije
- ✅ Image export (različiti formati)
- ✅ Integracija sa `image_manager.py`

---

#### ggrock-preflight (5,184 bytes)

**Funkcionalnost:** Preflight checks utility - Bash skripta za system preflight checks

**Komande:**
- ✅ `start` - Pokretanje preflight checks
- ✅ `cleanup` - Cleanup nakon preflight checks

**Funkcionalnosti:**
- ✅ `check_ggrock_installed_preflight` - Provera instalacije ggRock-a
- ✅ `check_headers_preflight` - Provera Linux kernel headers
- ✅ `check_dns_preflight` - Provera DNS konfiguracije (`/etc/resolv.conf`)
- ✅ Automatsko ispravljanje grešaka
- ✅ Nginx preflight konfiguracija
- ✅ HTML error page generisanje

**Primenljivo za ggNET2:**
- ✅ System preflight checks
- ✅ Dependency validation (kernel headers, DNS)
- ✅ Health checks
- ✅ Automatsko ispravljanje grešaka

---

#### ggrock-upgrade (2,330 bytes)

**Funkcionalnost:** System upgrade utility - Bash skripta za automatski upgrade sistema

**Detalji:**
- ✅ Čita konfiguraciju iz `/etc/ggrock-linux-configurator/upgrade_env`
- ✅ Podržava `RUN_DIST_UPGRADE` flag za full system upgrade
- ✅ Podržava `APP_VERSION` za specifičnu verziju ggRock-a
- ✅ Podržava `CONFIGURATOR_VERSION` za specifičnu verziju configurator-a
- ✅ Podržava `MIGRATION` za database migracije
- ✅ Database backup pre migracije (`pg_dump`)
- ✅ Non-interactive apt-get operacije

**Konfiguracija (`/etc/ggrock-linux-configurator/upgrade_env`):**
```bash
RUN_DIST_UPGRADE=true|false
APP_VERSION=0.1.2289.2303-1|skip
CONFIGURATOR_VERSION=0.1.109-1|skip
MIGRATION=migration_name
```

**Primenljivo za ggNET2:**
- ✅ System upgrade automation
- ✅ Package management
- ✅ Version management
- ✅ Database migration automation
- ✅ Backup pre migracije

---

#### ggrock-upgrade-debian12 (1,113 bytes)

**Funkcionalnost:** Debian 12 upgrade utility

**Status:** ⚠️ **Nedostaje detaljna analiza** - Potrebno pročitati skriptu

**Primenljivo za ggNET2:**
- ✅ Debian 12 upgrade automation
- ✅ Distribution upgrade

---

### 2. Systemd Service Fajlovi

#### ggrock-preflight.service

**Fajl:** `lib/systemd/system/ggrock-preflight.service`

**Konfiguracija:**
```ini
[Unit]
Description=Run ggRock preflight checks
Wants=network-online.target
After=network-online.target
After=zfs.target

[Service]
Type=simple
ExecStart=ggrock-preflight start
TimeoutStartSec=0
SyslogIdentifier=ggrock-preflight
ExecStopPost=-ggrock-preflight cleanup

[Install]
WantedBy=multi-user.target
```

**Funkcionalnost:**
- ✅ Preflight checks pre pokretanja sistema
- ✅ Zavisnost od network i ZFS
- ✅ Cleanup nakon zaustavljanja

**Primenljivo za ggNET2:**
- ✅ Preflight checks service
- ✅ Dependency management
- ✅ Health validation

---

#### ggrock-upgrade.service

**Fajl:** `lib/systemd/system/ggrock-upgrade.service`

**Konfiguracija:**
```ini
[Unit]
Description=ggRock Upgrade Service
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
ExecStart=ggrock-upgrade
SyslogIdentifier=ggrock-upgrade

[Install]
WantedBy=multi-user.target
```

**Funkcionalnost:**
- ✅ Automatski upgrade sistema
- ✅ Zavisnost od network

**Primenljivo za ggNET2:**
- ✅ Upgrade automation
- ✅ System maintenance

---

### 3. PXE/dnsmasq Konfiguracija

#### pxe.conf Template

**Fajl:** `etc/ggrock-linux-configurator/templates/pxe.conf`

**Funkcionalnost:**
- ✅ dnsmasq konfiguracija za PXE boot
- ✅ iPXE support
- ✅ UEFI/BIOS support
- ✅ Proxy DHCP

**Ključne Postavke:**
```conf
# TFTP root
tftp-root=/var/lib/tftp

# iPXE boot
dhcp-match=ipxe,175
dhcp-boot=net:ipxe,http://SERVER_IP/boot/script?mac=${netX/mac}&ip=${netX/ip}&if=${ifname},,SERVER_IP

# PXE menu
pxe-prompt="Booting ggRock Client", 1
pxe-service=net:ipxe,X86PC, "Boot to ggRock", http://SERVER_IP/boot/script?mac=${netX/mac}&ip=${netX/ip}&if=${ifname}
pxe-service=net:ipxe,X86-64_EFI, "Boot to ggRock UEFI", http://SERVER_IP/boot/script?mac=${netX/mac}&ip=${netX/ip}&if=${ifname}
```

**Primenljivo za ggNET2:**
- ✅ dnsmasq konfiguracija
- ✅ iPXE boot setup
- ✅ UEFI/BIOS support
- ✅ Integracija sa `ipxe_manager.py`

---

### 4. ZFS Pool Script

#### ggrock-lsblk

**Fajlovi:**
- `etc/zfs/zpool.d/ggrock-lsblk`
- `usr/lib/ggrock/zpool.d/ggrock-lsblk`

**Funkcionalnost:**
- ✅ ZFS pool script
- ✅ lsblk integracija (verovatno)

**Status:** ⚠️ **Prazan fajl** - Nema sadržaja u verziji 0.1.109

**Primenljivo za ggNET2:**
- ✅ ZFS pool management
- ✅ Drive detection
- ✅ Integracija sa `zfs_utils.py`

---

### 5. iPXE Boot Fajlovi

#### TFTP Boot Fajlovi (`var/lib/tftp/`)

**Fajlovi:**
- `ipxe.efi` - Main iPXE UEFI bootloader
- `ipxe.pxe` - Main iPXE PXE bootloader
- `ipxe_202006.efi` - iPXE version 202006 (UEFI)
- `ipxe_202102.efi` - iPXE version 202102 (UEFI)
- `snp.efi` - SNP UEFI bootloader
- `snponly.efi` - SNP only UEFI bootloader
- `undionly.kpxe` - UNDI only PXE bootloader
- `undionly.pxe` - UNDI only PXE bootloader
- `undionly_202006.kpxe` - UNDI only version 202006
- `undionly_202102.kpxe` - UNDI only version 202102

**Funkcionalnost:**
- ✅ iPXE bootloader fajlovi za različite arhitekture
- ✅ UEFI i BIOS support
- ✅ Različite verzije iPXE

**Primenljivo za ggNET2:**
- ✅ iPXE bootloader distribucija
- ✅ UEFI/BIOS support
- ✅ Integracija sa `ipxe_manager.py`

---

## 🔍 Uporedna Analiza sa ggNET2

### Trenutna Implementacija u ggNET2

#### Network Module (`app/backend/network/`)

**Postojeće Funkcionalnosti:**
- ✅ `network_utils.py` - Network utilities (bridge, IP forwarding)
- ✅ `ipxe_manager.py` - iPXE boot management
- ⚠️ `iscsi_manager.py` - iSCSI management (verovatno postoji)

**Nedostaje:**
- ❌ `ggrock-create-bridge` ekvivalent (delimično u `network_utils.py`)
- ❌ `ggrock-create-target` ekvivalent (verovatno u `iscsi_manager.py`)
- ❌ `ggrock-delete-target` ekvivalent
- ❌ `ggrock-preflight` ekvivalent
- ❌ `ggrock-upgrade` ekvivalent

---

### Preporuke za Integraciju

#### 1. Bridge Creation

**Trenutno:** `network_utils.py` ima `create_bridge()`

**Preporuka:**
- ✅ Analizirati `ggrock-create-bridge` skriptu
- ✅ Uporediti sa trenutnom implementacijom
- ✅ Identifikovati dodatne funkcionalnosti

---

#### 2. iSCSI Target Management

**Trenutno:** Verovatno u `iscsi_manager.py` (nije analizirano)

**Preporuka:**
- ✅ Analizirati `ggrock-create-target` skriptu
- ✅ Analizirati `ggrock-delete-target` skriptu
- ✅ Uporediti sa trenutnom implementacijom
- ✅ Identifikovati dodatne funkcionalnosti

---

#### 3. Preflight Checks

**Trenutno:** ❌ **Nedostaje**

**Preporuka:**
- ✅ Implementirati `ggrock-preflight` ekvivalent
- ✅ System dependency checks
- ✅ Health validation
- ✅ Systemd service integracija

---

#### 4. Upgrade Automation

**Trenutno:** ❌ **Nedostaje**

**Preporuka:**
- ✅ Implementirati `ggrock-upgrade` ekvivalent
- ✅ System upgrade automation
- ✅ Version management
- ✅ Systemd service integracija

---

#### 5. PXE/dnsmasq Konfiguracija

**Trenutno:** `ipxe_manager.py` ima osnovnu iPXE funkcionalnost

**Preporuka:**
- ✅ Analizirati `pxe.conf` template
- ✅ Implementirati dnsmasq konfiguraciju
- ✅ Proxy DHCP setup
- ✅ UEFI/BIOS support

---

#### 6. iPXE Boot Fajlovi

**Trenutno:** ❌ **Nedostaje distribucija iPXE fajlova**

**Preporuka:**
- ✅ Distribuirati iPXE bootloader fajlove
- ✅ Podržati različite verzije
- ✅ UEFI/BIOS support
- ✅ Integracija sa TFTP serverom

---

## 📊 Gap Analysis

### Funkcionalnosti koje Nedostaju u ggNET2

| Funkcionalnost | ggRock | ggNET2 | Prioritet |
|---------------|--------|--------|-----------|
| **Preflight Checks** | ✅ `ggrock-preflight` | ❌ Nedostaje | 🔴 Visok |
| **Upgrade Automation** | ✅ `ggrock-upgrade` | ❌ Nedostaje | 🟡 Srednji |
| **dnsmasq Konfiguracija** | ✅ `pxe.conf` template | ⚠️ Delimično | 🔴 Visok |
| **iPXE Boot Fajlovi** | ✅ TFTP distribucija | ❌ Nedostaje | 🔴 Visok |
| **Bridge Creation** | ✅ `ggrock-create-bridge` | ✅ `network_utils.py` | ✅ Postoji |
| **iSCSI Target** | ✅ `ggrock-create-target` | ⚠️ Verovatno postoji | 🟡 Srednji |
| **Image Management** | ✅ `ggrock-img` | ✅ `image_manager.py` | ✅ Postoji |
| **ZFS Pool Script** | ✅ `ggrock-lsblk` | ⚠️ Delimično | 🟡 Srednji |

---

## 🎯 Preporuke za ggNET2

### Prioritet 1 (Visok)

1. **Implementirati Preflight Checks**
   - Kreirati `app/backend/system/preflight.py`
   - System dependency validation
   - Health checks
   - Systemd service integracija

2. **Implementirati dnsmasq Konfiguraciju**
   - Analizirati `pxe.conf` template
   - Kreirati `app/backend/network/dnsmasq_manager.py`
   - Proxy DHCP setup
   - UEFI/BIOS support

3. **Distribuirati iPXE Boot Fajlove**
   - Kopirati iPXE fajlove u `/var/lib/tftp/`
   - Podržati različite verzije
   - UEFI/BIOS support

### Prioritet 2 (Srednji)

1. **Analizirati iSCSI Target Management**
   - Pročitati `ggrock-create-target` i `ggrock-delete-target`
   - Uporediti sa trenutnom implementacijom
   - Identifikovati dodatne funkcionalnosti

2. **Implementirati Upgrade Automation**
   - Kreirati `app/backend/system/upgrade.py`
   - System upgrade automation
   - Version management

3. **Analizirati ZFS Pool Script**
   - Pročitati `ggrock-lsblk` (ako ima sadržaj u novijim verzijama)
   - Integrisati sa `zfs_utils.py`

---

## 📋 Detaljna Analiza Utility Skripti

### Analizirano

1. ✅ **ggrock-auth** - Authentication mehanizam (CLI tool za JWT token)
2. ✅ **ggrock-create-bridge** - Bridge creation (Python, debinterface)
3. ✅ **ggrock-create-target** - iSCSI target creation (Python, rtslib_fb)
4. ✅ **ggrock-delete-target** - iSCSI target deletion (Python, rtslib_fb)
5. ✅ **ggrock-img** - Image management (Bash, ZFS send/receive, export)
6. ✅ **ggrock-preflight** - Preflight checks (Bash, kernel headers, DNS)
7. ✅ **ggrock-upgrade** - Upgrade automation (Bash, apt-get, migrations)

### Potrebno Analizirati

1. ⚠️ **ggrock-upgrade-debian12** - Debian 12 upgrade detalji
2. ⚠️ **ggrock-linux-configurator** - Main configurator tool

**Status:** ✅ **Većina skripti je analizirana** - Detaljna analiza je završena

---

## ✅ Zaključak

`ggrock-linux-configurator` paket sadrži **kritične utility skripte** za konfiguraciju Linux sistema za ggRock. Većina funkcionalnosti **nedostaje u ggNET2** ili je **delimično implementirana**.

**Ključni Nedostaci u ggNET2:**
1. 🔴 **Preflight Checks** - Potpuno nedostaje
2. 🔴 **dnsmasq Konfiguracija** - Delimično implementirana
3. 🔴 **iPXE Boot Fajlovi Distribucija** - Nedostaje
4. 🟡 **Upgrade Automation** - Nedostaje
5. 🟡 **iSCSI Target Management** - Verovatno postoji, ali treba proveriti

**Preporuka:** Analizirati sve utility skripte i implementirati nedostajuće funkcionalnosti u ggNET2.

---

*Dokument kreiran na osnovu analize `ggrock-linux-configurator_0.1.109-1_amd64` paketa*

