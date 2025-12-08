# System Utilities Installation Guide

**Datum kreiranja:** 2025-01-26  
**Status:** 📋 System Utilities Documentation

---

## 📊 Pregled

Ovaj dokument opisuje system utilities koje su potrebne za ggNET2 sistem i kako ih instalirati.

---

## 🔧 Potrebni System Utilities

### 1. util-linux

**Paket:** `util-linux`  
**Komande:** `lsblk`, `fdisk`, `blkid`, `findmnt`, itd.

**Zašto je potreban:**
- `lsblk` - Koristi se za listanje blok uređaja (drive-ova)
- `fdisk` - Za particionisanje diskova
- `blkid` - Za identifikaciju blok uređaja

**Gde se koristi:**
- `app/backend/storage/drive_manager.py` - Za listanje drive-ova
- Drive detection i enumeration

**Instalacija:**
```bash
sudo apt-get install -y util-linux
```

**Verifikacija:**
```bash
lsblk --version
# Output: lsblk from util-linux 2.37.2
```

---

### 2. smartmontools

**Paket:** `smartmontools`  
**Komande:** `smartctl`

**Zašto je potreban:**
- `smartctl` - Koristi se za čitanje SMART podataka sa drive-ova
- Health monitoring drive-ova
- Temperature, error rates, wear leveling, itd.

**Gde se koristi:**
- `app/backend/storage/drive_manager.py` - Za čitanje SMART podataka
- Drive health monitoring
- Drive details API endpoint

**Instalacija:**
```bash
sudo apt-get install -y smartmontools
```

**Verifikacija:**
```bash
smartctl --version
# Output: smartmontools release 7.2 ...
```

**Test:**
```bash
# Read SMART data from a drive (replace /dev/sda with your drive)
sudo smartctl -a /dev/sda
```

---

### 3. wakeonlan

**Paket:** `wakeonlan`  
**Komande:** `wakeonlan`

**Zašto je potreban:**
- `wakeonlan` - Koristi se za Wake-on-LAN funkcionalnost
- Udaljeno paljenje mašina preko mreže
- Opciono - sistem može raditi i bez njega (Python implementacija)

**Gde se koristi:**
- `app/backend/machines/machine_manager.py` - Za Wake-on-LAN operacije
- Bulk operations - Wake machines

**Instalacija:**
```bash
sudo apt-get install -y wakeonlan
```

**Verifikacija:**
```bash
wakeonlan --version
# Output: wakeonlan 0.41 ...
```

**Napomena:**
- Ovo je opcioni utility
- Ako nije instaliran, sistem će koristiti Python implementaciju
- Preporučeno je instalirati za bolju kompatibilnost

---

## 📦 Automatska Instalacija

### Korišćenje Installation Script-a

```bash
# Make script executable
chmod +x scripts/install_system_utilities.sh

# Run as root or with sudo
sudo ./scripts/install_system_utilities.sh
```

**Šta script radi:**
1. Proverava da li je pokrenut kao root/sudo
2. Ažurira package list
3. Instalira `util-linux` (ako nije već instaliran)
4. Instalira `smartmontools` (ako nije već instaliran)
5. Instalira `wakeonlan` (ako nije već instaliran)
6. Verifikuje da su sve komande dostupne
7. Prikazuje status instalacije

---

## 🔍 Verifikacija Instalacije

### Provera svih utilities

```bash
# Check util-linux
lsblk --version

# Check smartmontools
smartctl --version

# Check wakeonlan (optional)
wakeonlan --version 2>/dev/null || echo "wakeonlan not installed (optional)"
```

### Test funkcionalnosti

```bash
# Test lsblk (list drives)
lsblk

# Test smartctl (read SMART data - requires sudo)
sudo smartctl -a /dev/sda

# Test wakeonlan (send WOL packet - requires MAC address)
wakeonlan 00:11:22:33:44:55
```

---

## 🐛 Troubleshooting

### Problem: `lsblk: command not found`

**Rešenje:**
```bash
sudo apt-get update
sudo apt-get install -y util-linux
```

### Problem: `smartctl: command not found`

**Rešenje:**
```bash
sudo apt-get update
sudo apt-get install -y smartmontools
```

### Problem: `wakeonlan: command not found`

**Rešenje:**
```bash
sudo apt-get update
sudo apt-get install -y wakeonlan
```

**Napomena:** Ovo je opcioni utility. Sistem će raditi i bez njega.

### Problem: Permission denied za smartctl

**Rešenje:**
```bash
# smartctl zahteva sudo pristup
sudo smartctl -a /dev/sda

# Ili dodati korisnika u disk grupu (ne preporučuje se)
# sudo usermod -aG disk $USER
```

---

## 📝 Integration sa Deployment Guide

Ovi utilities su uključeni u `docs/DEPLOYMENT_COMPLETE_GUIDE.md` u sekciji "Install Dependencies":

```bash
sudo apt install -y \
  python3.11 python3.11-venv python3-pip \
  postgresql postgresql-contrib \
  nginx \
  nodejs npm \
  build-essential \
  libpq-dev \
  zfsutils-linux \
  smartmontools \
  util-linux \
  wakeonlan
```

---

## ✅ Checklist

- [ ] `util-linux` instaliran
- [ ] `lsblk` komanda dostupna
- [ ] `smartmontools` instaliran
- [ ] `smartctl` komanda dostupna
- [ ] `wakeonlan` instaliran (opciono)
- [ ] `wakeonlan` komanda dostupna (opciono)
- [ ] Svi utilities testirani
- [ ] Dokumentacija pročitana

---

## 📚 Reference

- **Deployment Guide:** `docs/DEPLOYMENT_COMPLETE_GUIDE.md`
- **Drive Manager:** `app/backend/storage/drive_manager.py`
- **Machine Manager:** `app/backend/machines/machine_manager.py`
- **util-linux Documentation:** https://www.kernel.org/pub/linux/utils/util-linux/
- **smartmontools Documentation:** https://www.smartmontools.org/
- **wakeonlan Documentation:** https://github.com/jpoliv/wakeonlan

---

**System Utilities Installation Complete!** ✅

