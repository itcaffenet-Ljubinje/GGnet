# ggnet2-upgrade-debian12 Script

**Datum kreiranja:** 2025-01-26  
**Status:** 📋 Debian 12 Upgrade Script Documentation

---

## 📊 Pregled

`ggnet2-upgrade-debian12` je bash skripta koja upgrade-uje Debian 11 (Bullseye) na Debian 12 (Bookworm). Ovo je **major system upgrade** koji zahteva pažljivo planiranje.

---

## ⚠️ WARNING

**Ovo je major system upgrade koji:**
- Menja sve package sources sa Bullseye na Bookworm
- Upgrade-uje sve instalirane pakete
- **Reboot-uje server** nakon završetka
- Može trajati dugo vremena (30+ minuta)

**Preporučeno:**
- Napravite backup sistema pre upgrade-a
- Planirajte maintenance window
- Testirajte na test serveru prvo

---

## 🚀 Usage

### Basic Usage

```bash
sudo ggnet2-upgrade-debian12
```

**Interaktivni proces:**
1. Proverava da li je OS Debian 11 (Bullseye)
2. Prikazuje upozorenje i traži potvrdu
3. Update-uje package sources
4. Upgrade-uje sve pakete
5. Reboot-uje server

---

## 🔧 Kako Radi

### 1. OS Verification

Skripta proverava da li je OS Debian 11 (Bullseye):

```bash
if [ "$VERSION_CODENAME" != "bullseye" ]; then
    echo "Your OS must be Debian 11 (Bullseye) to run this script."
    exit 1
fi
```

### 2. Package Sources Update

Ažurira sve package sources:

```bash
# Update /etc/apt/sources.list
sed -i 's/bullseye/bookworm/g' /etc/apt/sources.list

# Update all files in /etc/apt/sources.list.d/
sed -i 's/bullseye/bookworm/g' /etc/apt/sources.list.d/*
```

### 3. Add non-free-firmware Component

Dodaje `non-free-firmware` component (zahteva Debian 12):

```bash
sed -i 's/non-free/non-free non-free-firmware/g' /etc/apt/sources.list
sed -i 's/non-free/non-free non-free-firmware/g' /etc/apt/sources.list.d/*
```

### 4. Full System Upgrade

Pokreće full system upgrade:

```bash
DEBIAN_FRONTEND=noninteractive apt-get -y update
DEBIAN_FRONTEND=noninteractive apt -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" full-upgrade
```

**Opcije:**
- `--force-confdef`: Koristi default konfiguraciju za konflikte
- `--force-confold`: Zadržava postojeću konfiguraciju gde je moguće

### 5. Reboot

Nakon upgrade-a, server se automatski reboot-uje:

```bash
reboot
```

---

## 📋 Requirements

### System Requirements

- **Debian 11 (Bullseye)** - Skripta ne radi na drugim verzijama
- **Root privileges** (sudo)
- **Stable network connection**
- **Sufficient disk space** (preporučeno 10GB+ slobodnog prostora)

### Pre-Upgrade Checklist

- [ ] Backup sistema (npr. ZFS snapshot)
- [ ] Backup database (`pg_dump`)
- [ ] Backup konfiguracije (`/etc/nginx`, `/etc/ggnet2`, itd.)
- [ ] Proverite disk space (`df -h`)
- [ ] Planirajte maintenance window
- [ ] Obavestite korisnike o downtime-u

---

## 🔄 Upgrade Process

### Step 1: Pre-Upgrade

```bash
# Backup database
sudo -u postgres pg_dump ggnet2 > /backup/ggnet2_pre_upgrade.sql

# Backup configuration
sudo tar -czf /backup/ggnet2_config_pre_upgrade.tar.gz /etc/ggnet2 /etc/nginx/conf.d/ggnet2.conf

# Check disk space
df -h
```

### Step 2: Run Upgrade

```bash
sudo ggnet2-upgrade-debian12
```

### Step 3: Post-Upgrade

Nakon reboot-a, proverite:

```bash
# Check OS version
cat /etc/os-release

# Check services
sudo systemctl status ggnet2
sudo systemctl status nginx
sudo systemctl status postgresql

# Check application
curl https://localhost/api/health
```

---

## 🐛 Troubleshooting

### Error: OS must be Debian 11 (Bullseye)

**Problem:**
```
Your OS must be Debian 11 (Bullseye) to run this script.
```

**Rešenje:**
- Skripta radi samo na Debian 11 (Bullseye)
- Za Debian 12 upgrade, koristite standardni `apt full-upgrade`

### Upgrade Fails Midway

**Problem:** Upgrade pada tokom procesa

**Rešenje:**
1. Ne reboot-ujte server
2. Proverite logove:
   ```bash
   tail -f /var/log/apt/history.log
   ```
3. Pokušajte da popravite:
   ```bash
   sudo apt-get -f install
   sudo dpkg --configure -a
   ```
4. Nastavite upgrade:
   ```bash
   sudo apt full-upgrade
   ```

### Services Not Starting After Reboot

**Problem:** Servisi se ne pokreću nakon reboot-a

**Rešenje:**
1. Proverite status:
   ```bash
   sudo systemctl status ggnet2
   ```
2. Proverite logove:
   ```bash
   sudo journalctl -u ggnet2 -n 50
   ```
3. Restart servisa:
   ```bash
   sudo systemctl restart ggnet2
   ```

---

## 📚 Reference

- **Script Location:** `scripts/ggnet2-upgrade-debian12`
- **Debian Upgrade Guide:** https://www.debian.org/releases/bookworm/amd64/release-notes/ch-upgrading.en.html
- **Backup Guide:** `docs/DEPLOYMENT_COMPLETE_GUIDE.md`

---

## ✅ Checklist

- [ ] Backup sistema kreiran
- [ ] Backup database kreiran
- [ ] Disk space proveren (10GB+ slobodno)
- [ ] Maintenance window planiran
- [ ] Korisnici obavešteni
- [ ] Skripta pokrenuta sa `sudo`
- [ ] Upgrade završen uspešno
- [ ] Server reboot-ovan
- [ ] Servisi rade nakon reboot-a
- [ ] Aplikacija radi nakon upgrade-a

---

**ggnet2-upgrade-debian12 Script Complete!** ✅

