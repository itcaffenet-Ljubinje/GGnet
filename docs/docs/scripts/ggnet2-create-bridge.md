# ggnet2-create-bridge Script

**Datum kreiranja:** 2025-01-26  
**Status:** 📋 Network Bridge Creation Script Documentation

---

## 📊 Pregled

`ggnet2-create-bridge` je Python skripta koja kreira network bridge za određeni network adapter i čuva nove postavke u `/etc/network/interfaces` fajl, ostavljajući originalni fajl sa `.bak` ekstenzijom.

---

## 🚀 Usage

### Basic Usage

```bash
sudo ggnet2-create-bridge <nic_name> <bridge_name>
```

### Parameters

- **`nic_name`**: Ime fizičkog network adaptera (npr. `eth0`, `enp3s0`)
- **`bridge_name`**: Ime bridge-a koji se kreira (npr. `vmbr0`)

### Example

```bash
# Create bridge vmbr0 for eth0
sudo ggnet2-create-bridge eth0 vmbr0
```

---

## 🔧 Kako Radi

### 1. Backup Creation

Skripta automatski kreira backup originalnog `/etc/network/interfaces` fajla:

```bash
/etc/network/interfaces.bak
```

### 2. Bridge Creation

1. **Proverava da li bridge već postoji:**
   - Ako postoji, ažurira opcije
   - Ako ne postoji, kreira novi

2. **Proverava da li NIC adapter postoji:**
   - Ako ne postoji, kreira ga sa DHCP konfiguracijom

3. **Konfiguriše bridge:**
   - Postavlja ime bridge-a
   - Postavlja `auto` na `true`
   - Postavlja `hotplug` na `false`
   - Konfiguriše bridge opcije:
     - `ports`: Ime fizičkog adaptera
     - `stp`: `off` (Spanning Tree Protocol)
     - `fd`: `0` (Forward Delay)

4. **Kreira fizički adapter:**
   - Uklanja prethodni NIC adapter
   - Kreira novi prazan fizički adapter sa `source: manual`

5. **Čuva konfiguraciju:**
   - Zapisuje u `/etc/network/interfaces`

---

## 📋 Requirements

### Python Dependencies

```bash
pip install debinterface
```

Ili koristite `requirements.txt`:

```bash
pip install -r requirements.txt
```

### System Requirements

- **Debian/Ubuntu** Linux
- **Root privileges** (sudo)
- **debinterface** Python biblioteka

---

## 🔒 Permissions

Skripta **mora** biti pokrenuta kao root:

```bash
sudo ggnet2-create-bridge eth0 vmbr0
```

---

## 📝 Example Output

```bash
$ sudo ggnet2-create-bridge eth0 vmbr0

Created backup: /etc/network/interfaces.bak
vmbr0 not found in interfaces, creating...
eth0 not found in interfaces, creating...
Successfully created bridge 'vmbr0' with NIC 'eth0'
Configuration saved to /etc/network/interfaces
Backup saved to /etc/network/interfaces.bak

Note: You may need to restart networking for changes to take effect:
  sudo systemctl restart networking
  # or
  sudo ifdown vmbr0 && sudo ifup vmbr0
```

---

## 🔄 Restart Networking

Nakon kreiranja bridge-a, možete restartovati networking:

### Option 1: Systemd (Debian/Ubuntu)

```bash
sudo systemctl restart networking
```

### Option 2: ifdown/ifup

```bash
sudo ifdown vmbr0 && sudo ifup vmbr0
```

### Option 3: NetworkManager (ako je instaliran)

```bash
sudo systemctl restart NetworkManager
```

---

## 📋 Generated Configuration

Skripta generiše sledeću konfiguraciju u `/etc/network/interfaces`:

```bash
# Physical adapter (required for bridge mode)
auto eth0
iface eth0 inet manual

# Bridge adapter
auto vmbr0
iface vmbr0 inet dhcp
    bridge_ports eth0
    bridge_stp off
    bridge_fd 0
```

---

## 🐛 Troubleshooting

### Error: debinterface module not found

**Problem:**
```
Error: debinterface module not found. Install it with:
  pip install debinterface
```

**Rešenje:**
```bash
pip install debinterface
# or
pip install -r requirements.txt
```

### Error: This script must be run as root

**Problem:**
```
Error: This script must be run as root (use sudo)
```

**Rešenje:**
```bash
sudo ggnet2-create-bridge eth0 vmbr0
```

### Error: Failed to write interfaces file

**Problem:**
```
Error: Failed to write interfaces file: Permission denied
```

**Rešenje:**
- Proverite da li ste pokrenuli skriptu sa `sudo`
- Proverite permissions na `/etc/network/interfaces`

### Bridge Not Working After Creation

**Problem:** Bridge je kreiran ali ne radi

**Rešenje:**
1. Restartujte networking:
   ```bash
   sudo systemctl restart networking
   ```

2. Proverite status:
   ```bash
   ip addr show vmbr0
   ```

3. Proverite da li je bridge up:
   ```bash
   sudo ip link set vmbr0 up
   ```

---

## 📚 Reference

- **Script Location:** `scripts/ggnet2-create-bridge.py`
- **debinterface Documentation:** https://pypi.org/project/debinterface/
- **Network Configuration:** `/etc/network/interfaces`
- **Backup File:** `/etc/network/interfaces.bak`

---

## ✅ Checklist

- [ ] `debinterface` instaliran (`pip install debinterface`)
- [ ] Skripta ima execute permissions (`chmod +x scripts/ggnet2-create-bridge.py`)
- [ ] Pokrenuta sa `sudo`
- [ ] Backup kreiran (`/etc/network/interfaces.bak`)
- [ ] Bridge kreiran u `/etc/network/interfaces`
- [ ] Networking restartovan
- [ ] Bridge radi (`ip addr show vmbr0`)

---

**ggnet2-create-bridge Script Complete!** ✅

