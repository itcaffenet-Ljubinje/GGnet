# Analiza ggRock Dependencies - GGnet Projekt

## Pregled

Ovaj dokument analizira dependencies iz ggRock sistema i određuje koje su potrebne za GGnet projekt.

**ggRock paket verzija:** 0.1.2315.0-1  
**ggrock-linux-configurator verzija:** 0.1.109-1

---

## 1. ggRock Paket Dependencies

### System Libraries (Standardne - već u sistemu)

| Paket | Status | Objašnjenje |
|-------|--------|-------------|
| `libc6` (>= 2.14) | ✅ **Već postoji** | Standard C library - uvek prisutna u Linux sistemima |
| `libgcc1` (>= 1:3.0) | ✅ **Već postoji** | GCC support library - uvek prisutna |
| `libstdc++6` (>= 4.8) | ✅ **Već postoji** | Standard C++ library - uvek prisutna |
| `zlib1g` (>= 1:1.1.4) | ✅ **Već postoji** | Compression library - uvek prisutna |
| `libpam0g` (>= 0.99.7.1) | ✅ **Već postoji** | PAM library - uvek prisutna |

### Potrebni za GGnet

| Paket | Status u GGnet | Prioritet | Objašnjenje |
|-------|----------------|-----------|-------------|
| `nginx` | ✅ **Postoji** | 🔴 **Kritično** | Web server - koristi se za frontend i reverse proxy |
| `postgresql-12` | ✅ **Postoji** (postgresql) | 🔴 **Kritično** | Database - koristi se za glavnu bazu podataka |
| `libcurl4` (>= 7.16.2) | ✅ **Već postoji** | 🟡 **Važno** | HTTP client library - koristi se za HTTP zahteve |
| `libgssapi-krb5-2` | ⚠️ **Nedostaje** | 🟢 **Opciono** | Kerberos library - potrebno samo ako koristimo Kerberos autentifikaciju |

### Monitoring (Opciono)

| Paket | Status u GGnet | Prioritet | Objašnjenje |
|-------|----------------|-----------|-------------|
| `prometheus` | ❌ **Nedostaje** | 🟡 **Važno** | Monitoring sistem - korisno za production monitoring |
| `grafana` | ❌ **Nedostaje** | 🟡 **Važno** | Monitoring dashboards - korisno za vizualizaciju metrika |

**Napomena:** GGnet trenutno koristi `psutil` za monitoring, ali Prometheus/Grafana bi bili korisni za production.

### Remote Access & VNC

| Paket | Status u GGnet | Prioritet | Objašnjenje |
|-------|----------------|-----------|-------------|
| `websockify` | ❌ **Nedostaje** | 🟡 **Važno** | WebSocket proxy za VNC - potrebno za noVNC funkcionalnost |
| `novnc` | ❌ **Nedostaje** | 🟡 **Važno** | VNC web client - potrebno za browser-based remote desktop |

**Napomena:** GGnet ima VNC console endpoint (`/api/v1/vnc-console`), ali možda nedostaje noVNC integracija.

### Hardware Detection

| Paket | Status u GGnet | Prioritet | Objašnjenje |
|-------|----------------|-----------|-------------|
| `lshw` | ⚠️ **Nedostaje** | 🟡 **Važno** | Hardware detection - koristi se u `scripts/hardware_detect.py` ali možda nije instaliran |
| `dmidecode` | ⚠️ **Nedostaje** | 🟡 **Važno** | BIOS/DMI information - koristi se u `scripts/hardware_detect.py` ali možda nije instaliran |

**Napomena:** GGnet ima hardware detection skriptu koja koristi `lshw` i `dmidecode`, ali paketi možda nisu eksplicitno navedeni u instalacionim skriptama.

### Disk & Storage Utilities

| Paket | Status u GGnet | Prioritet | Objašnjenje |
|-------|----------------|-----------|-------------|
| `parted` | ❌ **Nedostaje** | 🟢 **Opciono** | Disk partitioning - korisno za advanced disk management |
| `unzip` | ✅ **Postoji** | 🟡 **Važno** | Archive extraction - već u `install.sh` |

### Windows Utilities

| Paket | Status u GGnet | Prioritet | Objašnjenje |
|-------|----------------|-----------|-------------|
| `chntpw` | ❌ **Nedostaje** | 🟡 **Važno** | Windows password reset - korisno za Windows image management |
| `wakeonlan` | ❌ **Nedostaje** | 🟢 **Opciono** | Wake-on-LAN - korisno za remote machine wake-up |

### Network Utilities

| Paket | Status u GGnet | Prioritet | Objašnjenje |
|-------|----------------|-----------|-------------|
| `sshpass` | ❌ **Nedostaje** | 🟢 **Opciono** | SSH password authentication - korisno za automated SSH skripte |
| `xmlstarlet` | ❌ **Nedostaje** | 🟢 **Opciono** | XML processing - korisno za XML konfiguracije |

---

## 2. ggrock-linux-configurator Dependencies

### Package Management

| Paket | Status u GGnet | Prioritet | Objašnjenje |
|-------|----------------|-----------|-------------|
| `apt-transport-https` | ⚠️ **Možda nedostaje** | 🟡 **Važno** | HTTPS transport za apt - potrebno za secure package repos |
| `software-properties-common` | ✅ **Postoji** | 🟡 **Važno** | Software properties management - već u `install.sh` |
| `wget` | ✅ **Postoji** | 🟡 **Važno** | File downloader - već u `install.sh` |
| `dialog` | ❌ **Nedostaje** | 🟢 **Opciono** | Dialog boxes - korisno za interaktivne instalacije |

### Network Services

| Paket | Status u GGnet | Prioritet | Objašnjenje |
|-------|----------------|-----------|-------------|
| `dnsmasq` | ❌ **Nedostaje** | 🟡 **Važno** | DNS/DHCP server - alternativni DHCP server (GGnet koristi isc-dhcp-server) |
| `isc-dhcp-server` | ✅ **Postoji** | 🔴 **Kritično** | DHCP server - već u `install.sh` i `Dockerfile` |

**Napomena:** ggRock koristi `dnsmasq`, GGnet koristi `isc-dhcp-server`. Oba rade, ali možda treba podrška za oba.

### iSCSI & Storage

| Paket | Status u GGnet | Prioritet | Objašnjenje |
|-------|----------------|-----------|-------------|
| `targetcli-fb` | ✅ **Postoji** | 🔴 **Kritično** | iSCSI target CLI - već u `install.sh` i `Dockerfile` |
| `qemu-utils` | ✅ **Postoji** | 🔴 **Kritično** | QEMU utilities - već u `install.sh` i `Dockerfile` |

### Monitoring

| Paket | Status u GGnet | Prioritet | Objašnjenje |
|-------|----------------|-----------|-------------|
| `prometheus-node-exporter` | ❌ **Nedostaje** | 🟡 **Važno** | Node metrics exporter - korisno za Prometheus monitoring |

### File Systems & Network Storage

| Paket | Status u GGnet | Prioritet | Objašnjenje |
|-------|----------------|-----------|-------------|
| `cifs-utils` | ❌ **Nedostaje** | 🟢 **Opciono** | CIFS/SMB utilities - korisno za SMB share pristup |
| `pv` | ❌ **Nedostaje** | 🟢 **Opciono** | Pipe viewer - korisno za progress bar u skriptama |

### Virtualization

| Paket | Status u GGnet | Prioritet | Objašnjenje |
|-------|----------------|-----------|-------------|
| `qemu-kvm` | ❌ **Nedostaje** | 🟡 **Važno** | KVM virtualization - potrebno za VM management (ako koristimo VMs) |
| `libvirt-clients` | ❌ **Nedostaje** | 🟡 **Važno** | Libvirt client tools - potrebno za VM management |
| `libvirt-daemon-system` | ❌ **Nedostaje** | 🟡 **Važno** | Libvirt daemon - potrebno za VM management |
| `virtinst` | ❌ **Nedostaje** | 🟡 **Važno** | VM installation tools - korisno za VM kreiranje |

**Napomena:** GGnet ima VM management (`/api/v1/vms`), ali možda nedostaju ovi paketi za full funkcionalnost.

### Network Management

| Paket | Status u GGnet | Prioritet | Objašnjenje |
|-------|----------------|-----------|-------------|
| `bridge-utils` | ❌ **Nedostaje** | 🟡 **Važno** | Network bridge utilities - potrebno za network bridge management |
| `ifenslave` | ❌ **Nedostaje** | 🟢 **Opciono** | Bonding utilities - korisno za network bonding |

### Web Management

| Paket | Status u GGnet | Prioritet | Objašnjenje |
|-------|----------------|-----------|-------------|
| `cockpit` | ❌ **Nedostaje** | 🟢 **Opciono** | Web-based server management - alternativni web UI za server management |

### Python

| Paket | Status u GGnet | Prioritet | Objašnjenje |
|-------|----------------|-----------|-------------|
| `python3-pip` | ✅ **Postoji** | 🔴 **Kritično** | Python package manager - već u `install.sh` |

---

## 3. Sažetak - Nedostajući Paketi

### 🔴 Kritično - Potrebno dodati

**Nema kritičnih nedostajućih paketa** - svi kritični paketi već postoje u projektu.

### 🟡 Važno - Preporučeno dodati

1. **Monitoring:**
   - `prometheus` - Za production monitoring
   - `grafana` - Za monitoring dashboards
   - `prometheus-node-exporter` - Za node metrics

2. **VNC/Remote Access:**
   - `websockify` - Za VNC WebSocket proxy
   - `novnc` - Za browser-based VNC client

3. **Hardware Detection:**
   - `lshw` - Za hardware detection (već se koristi u kodu)
   - `dmidecode` - Za BIOS/DMI info (već se koristi u kodu)

4. **Virtualization (ako koristimo VMs):**
   - `qemu-kvm` - Za KVM virtualization
   - `libvirt-clients` - Za libvirt CLI tools
   - `libvirt-daemon-system` - Za libvirt daemon
   - `virtinst` - Za VM installation tools

5. **Network:**
   - `bridge-utils` - Za network bridge management
   - `apt-transport-https` - Za secure package repos

6. **Windows Utilities:**
   - `chntpw` - Za Windows password reset

### 🟢 Opciono - Može biti korisno

1. `parted` - Disk partitioning
2. `wakeonlan` - Wake-on-LAN
3. `sshpass` - SSH password auth
4. `xmlstarlet` - XML processing
5. `cifs-utils` - SMB/CIFS utilities
6. `pv` - Pipe viewer
7. `dialog` - Dialog boxes
8. `ifenslave` - Network bonding
9. `cockpit` - Web-based server management
10. `dnsmasq` - Alternativni DHCP server (ako želimo opciju)

---

## 4. Preporuke za GGnet

### Prioritet 1: Dodati u install.sh

```bash
# Monitoring
prometheus
grafana
prometheus-node-exporter

# VNC/Remote Access
websockify
novnc

# Hardware Detection (već se koristi u kodu)
lshw
dmidecode

# Virtualization (ako koristimo VMs)
qemu-kvm
libvirt-clients
libvirt-daemon-system
virtinst

# Network
bridge-utils
apt-transport-https

# Windows Utilities
chntpw
```

### Prioritet 2: Razmotriti dodavanje

- `parted` - Za advanced disk management
- `wakeonlan` - Za remote machine wake-up
- `cifs-utils` - Za SMB share pristup

### Prioritet 3: Nije potrebno

- `dnsmasq` - Već koristimo `isc-dhcp-server`
- `cockpit` - Već imamo web UI
- `dialog` - Ne koristimo interaktivne instalacije
- `sshpass` - Možemo koristiti SSH keys
- `xmlstarlet` - Možemo koristiti Python XML parsere
- `ifenslave` - Network bonding nije kritično

---

## 5. Instalacioni Komandi

### Dodati u `scripts/install.sh`:

```bash
# Dodati u install_dependencies() funkciju
apt-get install -y \
    # ... postojeći paketi ...
    # Monitoring
    prometheus \
    grafana \
    prometheus-node-exporter \
    # VNC/Remote Access
    websockify \
    novnc \
    # Hardware Detection
    lshw \
    dmidecode \
    # Virtualization
    qemu-kvm \
    libvirt-clients \
    libvirt-daemon-system \
    virtinst \
    # Network
    bridge-utils \
    apt-transport-https \
    # Windows Utilities
    chntpw
```

### Dodati u `backend/Dockerfile` (ako je potrebno):

```dockerfile
RUN apt-get update && apt-get install -y \
    # ... postojeći paketi ...
    lshw \
    dmidecode \
    bridge-utils \
    && rm -rf /var/lib/apt/lists/*
```

**Napomena:** Prometheus, Grafana, websockify, novnc su obično instalirani na host sistemu, ne u Docker kontejneru.

---

## 6. Zaključak

**Ukupno nedostaje:** ~15 paketa  
**Kritično nedostaje:** 0 paketa  
**Važno nedostaje:** ~12 paketa  
**Opciono nedostaje:** ~8 paketa

**Preporuka:** Dodati pakete iz "Prioritet 1" sekcije u `install.sh` za kompletnu funkcionalnost koja odgovara ggRock sistemu.

