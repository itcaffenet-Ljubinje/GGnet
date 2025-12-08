# ggnet2-lsblk Script

**Datum kreiranja:** 2025-01-26  
**Status:** 📋 ZFS zpool.d Custom lsblk Script Documentation

---

## 📊 Pregled

`ggnet2-lsblk` je custom `lsblk` skripta za ZFS `zpool.d` sistem. Koristi se za formatiranje output-a disk informacija u `zpool status` komandama.

---

## 🔧 Kako Radi

### ZFS zpool.d Integration

ZFS automatski koristi skripte iz `/etc/zfs/zpool.d/` direktorijuma za formatiranje output-a:

1. **ZFS poziva skriptu** sa device path-om kao argumentom
2. **Skripta poziva `lsblk`** sa formatiranim output-om
3. **ZFS integriše output** u status display

### Default Output

Kada se pozove kao `ggnet2-lsblk`, prikazuje:
- **SIZE**: Veličina diska (bytes format sa `-b` flag)
- **MODEL**: Model diska
- **SERIAL**: Serijski broj diska

### Custom Columns

Ako se symlink-uje sa drugim imenom (lowercase), koristi se to ime kao column name:

```bash
# Symlink za 'type' column
ln -s ggnet2-lsblk /etc/zfs/zpool.d/type

# ZFS će koristiti 'type' kao output column
```

---

## 📋 Installation

### Option 1: Via setup_zfs.sh

Skripta se automatski kreira kada pokrenete `setup_zfs.sh`:

```bash
sudo bash scripts/setup_zfs.sh
```

### Option 2: Manual Installation

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

## 🚀 Usage

### Direct Usage

```bash
# Show help
ggnet2-lsblk -h

# Show size, model, serial for a device
VDEV_UPATH=/dev/sda ggnet2-lsblk
```

**Output:**
```
size=2000398934016
model=ST2000DM001-1ER164
serial=Z1Z8P8ZX
```

### ZFS Integration

ZFS automatski koristi skriptu kada prikazuje pool status:

```bash
# ZFS will use custom lsblk output
zpool status pool0
```

**Example Output:**
```
  pool: pool0
 state: ONLINE
  scan: none requested
config:

        NAME        SIZE  MODEL                SERIAL
        sda         1.8T  ST2000DM001-1ER164  Z1Z8P8ZX
        sdb         1.8T  ST2000DM001-1ER164  Z1Z8P8ZY
```

---

## 📋 Available Columns

Skripta podržava sve `lsblk` output kolone:

- `NAME` - Device name
- `KNAME` - Internal kernel device name
- `MAJ:MIN` - Major:minor device number
- `FSTYPE` - Filesystem type
- `MOUNTPOINT` - Mount point
- `LABEL` - Filesystem label
- `UUID` - Filesystem UUID
- `MODEL` - Device model
- `SIZE` - Device size
- `STATE` - Device state
- `SERIAL` - Device serial number
- `ROTA` - Rotational device (0=SSD, 1=HDD)
- `TYPE` - Device type
- ... i više

---

## 🔧 Customization

### Modify Default Columns

Uredite skriptu da koristi druge kolone:

```bash
sudo nano /usr/lib/ggnet2/zpool.d/ggnet2-lsblk
```

**Primer:** Dodajte `ROTA` kolonu:

```bash
if [ "$script" = "ggnet2-lsblk" ]; then
    list="size model serial rota"
else
    list=$(echo "$script" | tr '[:upper:]' '[:lower:]')
fi
```

### Add Custom Columns

Kreirajte symlink za custom kolonu:

```bash
# Create symlink for 'rota' column
sudo ln -s /usr/lib/ggnet2/zpool.d/ggnet2-lsblk /etc/zfs/zpool.d/rota

# ZFS će sada prikazati ROTA kolonu
```

---

## 🐛 Troubleshooting

### Script Not Found

**Problem:** ZFS ne koristi custom skriptu

**Rešenje:**
1. Proverite da li postoji symlink:
   ```bash
   ls -la /etc/zfs/zpool.d/ggnet2-lsblk
   ```

2. Proverite da li je skripta executable:
   ```bash
   chmod +x /usr/lib/ggnet2/zpool.d/ggnet2-lsblk
   ```

3. Proverite da li ZFS vidi skriptu:
   ```bash
   zpool status pool0
   ```

### lsblk Command Not Found

**Problem:**
```
lsblk: command not found
```

**Rešenje:**
```bash
sudo apt-get install -y util-linux
```

### SERIAL Column Empty

**Problem:** SERIAL kolona je prazna

**Rešenje:**
- Neki stariji disk-ovi nemaju SERIAL informaciju
- Proverite sa `lsblk -o SERIAL /dev/sda` direktno
- Ako je prazno, disk možda ne podržava SERIAL

---

## 📚 Reference

- **Script Location:** `scripts/ggnet2-lsblk`
- **ZFS Setup:** `docs/scripts/setup_zfs.md`
- **ZFS zpool.d Documentation:** `man zpool`

---

## ✅ Checklist

- [ ] Skripta instalirana (`/usr/lib/ggnet2/zpool.d/ggnet2-lsblk`)
- [ ] Symlink kreiran (`/etc/zfs/zpool.d/ggnet2-lsblk`)
- [ ] Skripta executable (`chmod +x`)
- [ ] `lsblk` komanda dostupna
- [ ] ZFS koristi custom output (`zpool status`)

---

**ggnet2-lsblk Script Complete!** ✅

