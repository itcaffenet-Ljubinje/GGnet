# Analiza migracije sa isc-dhcp-server na dnsmasq

## Pregled

Ovaj dokument analizira mogućnost prelaska sa `isc-dhcp-server` na `dnsmasq` za DHCP funkcionalnost u GGnet projektu.

## ✅ Migration Completed

**Datum migracije:** 2025-01-XX  
**Status:** Migracija je uspešno implementirana

### Implementirane izmene:

1. **DHCPAdapter klasa** (`backend/app/adapters/dhcp.py`):
   - Promenjen service name sa `isc-dhcp-server` na `dnsmasq`
   - Promenjen config path sa `/etc/dhcp/dhcpd.conf` na `/etc/dnsmasq.conf`
   - Modifikovane metode za dnsmasq format konfiguracije
   - Dodata podrška za machine-specific boot files sa tag-ovima

2. **Dockerfile** (`backend/Dockerfile`):
   - Zamenjen `isc-dhcp-server` sa `dnsmasq` u instalaciji

3. **Instalacione skripte**:
   - Kreiran `scripts/dnsmasq_config.sh` za instalaciju i konfiguraciju dnsmasq

4. **Preflight checks**:
   - Ažuriran `backend/app/routes/preflight.py` da proverava dnsmasq konfiguraciju
   - Ažuriran `backend/scripts/preflight.py` da proverava dnsmasq konfiguraciju

5. **Konfiguracioni template**:
   - Kreiran kompletan dnsmasq.conf template sa PXE boot podrškom

---

## 1. Trenutna situacija

### Gde se koristi `isc-dhcp-server`:

1. **Instalacija:**
   - `backend/Dockerfile` - linija 18
   - `scripts/install.sh` - linija 92
   - `scripts/dhcp_config.sh` - instalacija i konfiguracija

2. **Konfiguracija:**
   - `docker/dhcp/dhcpd.conf` - glavni konfiguracioni fajl
   - `infra/examples/dhcpd.conf` - primer konfiguracije
   - `/etc/dhcp/dhcpd.conf` - runtime konfiguracija

3. **Kod:**
   - `backend/app/adapters/dhcp.py` - DHCPAdapter klasa
   - `backend/app/routes/network_boot.py` - DHCP status endpoints
   - `backend/app/routes/preflight.py` - DHCP config check

4. **Service monitoring:**
   - `backend/app/utils/service_monitor.py` - monitoring servisa
   - Service name: `isc-dhcp-server`

---

## 2. Razlike između isc-dhcp-server i dnsmasq

### isc-dhcp-server

**Prednosti:**
- ✅ Moćniji za kompleksne DHCP scenarije
- ✅ Odlična podrška za PXE boot sa architecture detection
- ✅ Podrška za conditional boot file selection (`if option arch = 00:07`)
- ✅ Podrška za custom DHCP opcije (option 93, option 77)
- ✅ Bolja podrška za multiple subnets
- ✅ Detaljnije logging opcije
- ✅ Podrška za DHCP failover (high availability)

**Nedostaci:**
- ❌ Kompleksnija konfiguracija
- ❌ Veći resursi (memorija, CPU)
- ❌ Sporiji reload konfiguracije
- ❌ Kompleksniji syntax za konfiguraciju

### dnsmasq

**Prednosti:**
- ✅ Jednostavnija konfiguracija
- ✅ Manji resursi (lakši, brži)
- ✅ Brži reload konfiguracije
- ✅ Integrisan DNS server (bonus)
- ✅ Jednostavniji syntax
- ✅ Bolja podrška za Docker kontejnere
- ✅ Manje konflikata sa drugim servisima

**Nedostaci:**
- ❌ Ograničena podrška za advanced DHCP opcije
- ❌ Ograničena podrška za conditional boot file selection
- ❌ Manje fleksibilno za kompleksne scenarije
- ❌ Možda nedostaje podrška za neke advanced PXE opcije

---

## 3. Analiza funkcionalnosti

### Funkcionalnosti koje GGnet koristi:

#### ✅ Podržano u oba:

1. **Basic DHCP:**
   - IP address assignment
   - Static reservations (MAC → IP)
   - Lease time configuration
   - Gateway, DNS, subnet mask

2. **PXE Boot:**
   - `next-server` (TFTP server IP)
   - `filename` (boot file)
   - Basic PXE boot

#### ⚠️ Delimično podržano u dnsmasq:

3. **Architecture Detection:**
   - `isc-dhcp-server`: Full podrška za `option arch` (option 93)
   - `dnsmasq`: Ograničena podrška, možda zahteva dodatnu konfiguraciju

4. **Conditional Boot File Selection:**
   - `isc-dhcp-server`: `if option arch = 00:07 { filename "..." }`
   - `dnsmasq`: Možda zahteva `pxe-service` sa architecture codes

5. **iPXE Detection:**
   - `isc-dhcp-server`: `if exists user-class and option user-class = "iPXE"`
   - `dnsmasq`: Možda zahteva `pxe-service` sa user-class matching

#### ❌ Možda nedostaje u dnsmasq:

6. **Complex DHCP Options:**
   - Custom option spaces (PXE option space)
   - Multiple conditional statements
   - Advanced logging

---

## 4. Konfiguracija uporedba

### isc-dhcp-server (trenutno):

```dhcpd.conf
# Architecture detection
option arch code 93 = unsigned integer 16;
option user-class code 77 = string;

# Conditional boot file selection
if option arch = 00:07 {
    if exists user-class and option user-class = "iPXE" {
        filename "http://192.168.1.10:8000/boot/script.ipxe";
    } else {
        filename "snponly.efi";
    }
} elsif option arch = 00:09 {
    # UEFI with HTTP boot
    filename "snponly.efi";
} else {
    filename "pxelinux.0";
}

# Static host entries
host client01 {
    hardware ethernet 00:11:22:33:44:55;
    fixed-address 192.168.1.101;
    option host-name "client01";
    next-server 192.168.1.10;
    filename "machines/00-11-22-33-44-55.ipxe";
}
```

### dnsmasq (ekvivalent):

```dnsmasq.conf
# Basic DHCP
dhcp-range=192.168.1.100,192.168.1.200,255.255.255.0,12h
dhcp-option=3,192.168.1.1  # Gateway
dhcp-option=6,8.8.8.8,8.8.4.4  # DNS

# TFTP server
dhcp-boot=snponly.efi,192.168.1.10,192.168.1.10

# PXE boot services (architecture-based)
pxe-service=x86PC,"Legacy BIOS",pxelinux.0
pxe-service=x86-64_EFI,"UEFI x64",snponly.efi,192.168.1.10
pxe-service=BC_EFI,"UEFI x64 HTTP",snponly.efi,192.168.1.10

# Static host entries
dhcp-host=00:11:22:33:44:55,192.168.1.101,client01,12h
dhcp-boot=tag:client01,machines/00-11-22-33-44-55.ipxe,192.168.1.10

# iPXE detection (možda zahteva dodatnu konfiguraciju)
# dnsmasq nema direktnu podršku za user-class conditional
```

**Problem:** dnsmasq nema direktnu podršku za conditional boot file selection baziran na `user-class` (iPXE detection).

---

## 5. Mogućnost migracije

### ✅ Moguće je migrirati, ALI:

#### Prednosti migracije:
1. **Jednostavnija konfiguracija** - lakše održavanje
2. **Manji resursi** - bolje za Docker kontejnere
3. **Brži reload** - brže ažuriranje konfiguracije
4. **Integrisan DNS** - bonus funkcionalnost
5. **ggRock koristi dnsmasq** - bolja kompatibilnost

#### Izazovi migracije:
1. **iPXE Detection** - dnsmasq možda ne podržava conditional boot baziran na user-class
2. **Architecture Detection** - dnsmasq koristi drugačiji pristup (`pxe-service`)
3. **Kod promene** - potrebno promeniti:
   - `DHCPAdapter` klasu
   - Konfiguracioni format
   - Service name
   - Reload komande
   - Config validation

#### Rešenja za izazove:

**Problem 1: iPXE Detection**
- **Rešenje:** Koristiti različite boot fajlove ili HTTP boot direktno
- **Alternativa:** Koristiti `pxe-service` sa tag-ovima

**Problem 2: Architecture Detection**
- **Rešenje:** Koristiti `pxe-service` sa architecture codes
- **Primer:** `pxe-service=x86-64_EFI,"UEFI x64",snponly.efi`

**Problem 3: Machine-specific boot files**
- **Rešenje:** Koristiti `dhcp-host` sa `dhcp-boot` tag-ovima
- **Primer:** `dhcp-host=mac,ip,name,tag:tag1` + `dhcp-boot=tag:tag1,filename,server`

---

## 6. Preporuka

### 🟡 Preporučeno: Migrirati na dnsmasq

**Razlozi:**
1. ✅ ggRock koristi `dnsmasq` - bolja kompatibilnost
2. ✅ Jednostavnija konfiguracija - lakše održavanje
3. ✅ Manji resursi - bolje za Docker
4. ✅ Brži reload - bolje performanse
5. ✅ Integrisan DNS - bonus funkcionalnost

**Uslovi:**
- Potrebno je prilagoditi kod za dnsmasq konfiguraciju
- Možda zahteva promene u PXE boot logici
- Potrebno testirati sa različitim klijentima

---

## 7. Plan migracije

### Faza 1: Priprema
1. Kreirati `dnsmasq.conf` template
2. Dokumentovati razlike u konfiguraciji
3. Testirati dnsmasq konfiguraciju ručno

### Faza 2: Kod promene
4. Kreirati `DnsmasqAdapter` klasu (ili modifikovati `DHCPAdapter`)
5. Promeniti konfiguracioni format
6. Promeniti service name i reload komande
7. Ažurirati config validation

### Faza 3: Instalacija
8. Ažurirati `install.sh` - zameniti `isc-dhcp-server` sa `dnsmasq`
9. Ažurirati `Dockerfile` - zameniti paket
10. Ažurirati `dhcp_config.sh` - promeniti u `dnsmasq_config.sh`

### Faza 4: Dokumentacija
11. Ažurirati `docs/installation.md`
12. Kreirati migration guide
13. Ažurirati primere konfiguracije

### Faza 5: Testiranje
14. Testirati basic DHCP funkcionalnost
15. Testirati PXE boot sa različitim arhitekturama
16. Testirati static host entries
17. Testirati reload funkcionalnost

---

## 8. Primer dnsmasq konfiguracije za GGnet

```conf
# /etc/dnsmasq.conf
# GGnet Diskless System - dnsmasq Configuration

# Basic settings
port=0  # Disable DNS (if not needed)
interface=eth0
bind-interfaces

# DHCP Range
dhcp-range=192.168.1.100,192.168.1.200,255.255.255.0,12h

# Network options
dhcp-option=3,192.168.1.1  # Gateway
dhcp-option=6,8.8.8.8,8.8.4.4  # DNS servers
dhcp-option=15,ggnet.local  # Domain name

# TFTP Server
enable-tftp
tftp-root=/var/lib/tftpboot

# PXE Boot Services
# Format: pxe-service=<arch>,"<description>",<filename>,<server>
pxe-service=x86PC,"Legacy BIOS",undionly.kpxe,192.168.1.10
pxe-service=x86-64_EFI,"UEFI x64",snponly.efi,192.168.1.10
pxe-service=BC_EFI,"UEFI x64 HTTP",snponly.efi,192.168.1.10

# Default boot file
dhcp-boot=snponly.efi,192.168.1.10,192.168.1.10

# Static host entries (dodaju se dinamički)
# Format: dhcp-host=<mac>,<ip>,<hostname>,<lease-time>,<tag>
# dhcp-host=00:11:22:33:44:55,192.168.1.101,client01,12h,ggnet-client

# Machine-specific boot files (dodaju se dinamički)
# Format: dhcp-boot=tag:<tag>,<filename>,<server>
# dhcp-boot=tag:ggnet-client,machines/00-11-22-33-44-55.ipxe,192.168.1.10

# Logging
log-dhcp
log-queries

# Additional options
dhcp-authoritative
dhcp-rapid-commit
```

---

## 9. Zaključak

**Da, možemo preći sa `isc-dhcp-server` na `dnsmasq`**, ali zahteva:

1. ✅ **Kod promene** - modifikacija `DHCPAdapter` klase
2. ✅ **Konfiguracija** - novi format konfiguracionog fajla
3. ✅ **Instalacija** - ažuriranje instalacionih skripti
4. ⚠️ **Testiranje** - potrebno testirati sa različitim klijentima

**Preporuka:** Migrirati na `dnsmasq` zbog:
- Kompatibilnosti sa ggRock sistemom
- Jednostavnije konfiguracije
- Manjih resursa
- Bržeg reload-a

**Rizici:** 
- Možda zahteva prilagođavanje PXE boot logike
- Potrebno testirati architecture detection
- Potrebno testirati iPXE detection (ako je kritično)

