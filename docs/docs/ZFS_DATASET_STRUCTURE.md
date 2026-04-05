# ZFS Dataset Structure

**Datum kreiranja:** 2025-01-26  
**Status:** 📋 ZFS Dataset Structure Documentation

---

## 📊 Pregled

Ovaj dokument opisuje kompletnu strukturu ZFS dataset-a koje ggNET2 koristi.

---

## 🗂️ Dataset Struktura

### Pool Structure

```
pool0/
└── ggnet2/
    ├── images/          # System images (zvol)
    ├── clones/          # VM/Machine clones (zvol)
    ├── clients/         # Machine disk volumes (zvol)
    ├── snapshots/       # Snapshot storage/backup
    ├── images_bin/      # Binary image files
    └── import/          # Temporary import operations
```

---

## 📋 Dataset Opis

### 1. `pool0/ggnet2/` (BASE_PATH)

**Tip:** Dataset  
**Svrha:** Base dataset za sve ggNET2 podatke  
**Properties:**
- `compression=lz4`
- `mountpoint=none`

**Kreiranje:**
```bash
zfs create pool0/ggnet2
zfs set compression=lz4 pool0/ggnet2
zfs set mountpoint=none pool0/ggnet2
```

---

### 2. `pool0/ggnet2/images` (IMAGES_PATH)

**Tip:** Dataset (sadrži zvol-ove)  
**Svrha:** System images (Windows, Linux, itd.)  
**Properties:**
- `compression=lz4`
- `mountpoint=none`

**Primer:**
```bash
# Create image volume
zfs create -V 100G pool0/ggnet2/images/win11

# Create base snapshot
zfs snapshot pool0/ggnet2/images/win11@base
```

**Kreiranje:**
```bash
zfs create pool0/ggnet2/images
zfs set compression=lz4 pool0/ggnet2/images
zfs set mountpoint=none pool0/ggnet2/images
```

---

### 3. `pool0/ggnet2/clones` (CLONES_PATH)

**Tip:** Dataset (sadrži zvol-ove)  
**Svrha:** VM i Machine clone-ovi  
**Properties:**
- `compression=lz4`
- `mountpoint=none`

**Primer:**
```bash
# Create VM clone
zfs clone pool0/ggnet2/images/win11@base pool0/ggnet2/clones/vm-001-system

# Create machine clone
zfs clone pool0/ggnet2/images/win11@base pool0/ggnet2/clones/machine-001-system
```

**Kreiranje:**
```bash
zfs create pool0/ggnet2/clones
zfs set compression=lz4 pool0/ggnet2/clones
zfs set mountpoint=none pool0/ggnet2/clones
```

---

### 4. `pool0/ggnet2/clients` (CLIENTS_PATH)

**Tip:** Dataset (sadrži zvol-ove)  
**Svrha:** Machine disk volumes (iSCSI targets)  
**Properties:**
- `compression=lz4`
- `mountpoint=none`

**Primer:**
```bash
# Create client disk volume
zfs create -V 500G pool0/ggnet2/clients/pc-100-disk-0

# Use as iSCSI target
# /dev/zvol/pool0/ggnet2/clients/pc-100-disk-0
```

**Kreiranje:**
```bash
zfs create pool0/ggnet2/clients
zfs set compression=lz4 pool0/ggnet2/clients
zfs set mountpoint=none pool0/ggnet2/clients
```

---

### 5. `pool0/ggnet2/snapshots` (SNAPSHOTS_PATH)

**Tip:** Dataset  
**Svrha:** Snapshot storage/backup  
**Properties:**
- `compression=lz4`
- `mountpoint=none`

**Primer:**
```bash
# Store snapshot backups
zfs send pool0/ggnet2/images/win11@base | \
  zfs receive pool0/ggnet2/snapshots/win11-base-backup
```

**Kreiranje:**
```bash
zfs create pool0/ggnet2/snapshots
zfs set compression=lz4 pool0/ggnet2/snapshots
zfs set mountpoint=none pool0/ggnet2/snapshots
```

---

### 6. `pool0/ggnet2/images_bin` (IMAGES_BIN_PATH)

**Tip:** Dataset  
**Svrha:** Binary image files (VHD, VMDK, QCOW2, itd.)  
**Properties:**
- `compression=lz4`
- `mountpoint=none`

**Primer:**
```bash
# Store binary image files
# Files are stored as regular files in the dataset
```

**Kreiranje:**
```bash
zfs create pool0/ggnet2/images_bin
zfs set compression=lz4 pool0/ggnet2/images_bin
zfs set mountpoint=none pool0/ggnet2/images_bin
```

---

### 7. `pool0/ggnet2/import` (IMPORT_PATH)

**Tip:** Dataset  
**Svrha:** Temporary import operations  
**Properties:**
- `compression=lz4`
- `mountpoint=none`

**Primer:**
```bash
# Temporary storage during image import
# Files are cleaned up after import completes
```

**Kreiranje:**
```bash
zfs create pool0/ggnet2/import
zfs set compression=lz4 pool0/ggnet2/import
zfs set mountpoint=none pool0/ggnet2/import
```

---

## 🔧 Setup

### Automatsko Kreiranje

Svi dataset-ovi se automatski kreiraju kada pokrenete `setup_zfs.sh`:

```bash
sudo bash scripts/setup_zfs.sh
```

### Ručno Kreiranje

```bash
# Base dataset
zfs create pool0/ggnet2
zfs set compression=lz4 pool0/ggnet2
zfs set mountpoint=none pool0/ggnet2

# Images
zfs create pool0/ggnet2/images
zfs set compression=lz4 pool0/ggnet2/images
zfs set mountpoint=none pool0/ggnet2/images

# Clones
zfs create pool0/ggnet2/clones
zfs set compression=lz4 pool0/ggnet2/clones
zfs set mountpoint=none pool0/ggnet2/clones

# Clients
zfs create pool0/ggnet2/clients
zfs set compression=lz4 pool0/ggnet2/clients
zfs set mountpoint=none pool0/ggnet2/clients

# Snapshots
zfs create pool0/ggnet2/snapshots
zfs set compression=lz4 pool0/ggnet2/snapshots
zfs set mountpoint=none pool0/ggnet2/snapshots

# Images Bin
zfs create pool0/ggnet2/images_bin
zfs set compression=lz4 pool0/ggnet2/images_bin
zfs set mountpoint=none pool0/ggnet2/images_bin

# Import
zfs create pool0/ggnet2/import
zfs set compression=lz4 pool0/ggnet2/import
zfs set mountpoint=none pool0/ggnet2/import
```

---

## 📊 Verifikacija

### Provera Dataset-a

```bash
# List all datasets
zfs list -r pool0/ggnet2

# Check specific dataset
zfs list pool0/ggnet2/images

# Check properties
zfs get all pool0/ggnet2/images
```

**Očekivani Output:**
```
NAME                      USED  AVAIL  REFER  MOUNTPOINT
pool0/ggnet2             500G   1.5T   128K  none
pool0/ggnet2/images      200G   1.5T   128K  none
pool0/ggnet2/clones      150G   1.5T   128K  none
pool0/ggnet2/clients     100G   1.5T   128K  none
pool0/ggnet2/snapshots    50G   1.5T   128K  none
pool0/ggnet2/images_bin   0G   1.5T   128K  none
pool0/ggnet2/import       0G   1.5T   128K  none
```

---

## 🔄 Korišćenje

### Images

```bash
# Create image
zfs create -V 100G pool0/ggnet2/images/win11
zfs snapshot pool0/ggnet2/images/win11@base

# List images
zfs list -t volume -r pool0/ggnet2/images
```

### Clones

```bash
# Create clone
zfs clone pool0/ggnet2/images/win11@base pool0/ggnet2/clones/vm-001-system

# List clones
zfs list -t volume -r pool0/ggnet2/clones
```

### Clients

```bash
# Create client disk
zfs create -V 500G pool0/ggnet2/clients/pc-100-disk-0

# Use as iSCSI target
targetcli /backstores/block create pc-100-disk-0 /dev/zvol/pool0/ggnet2/clients/pc-100-disk-0
```

---

## 📚 Reference

- **Setup Script:** `scripts/setup_zfs.sh`
- **Settings:** `app/backend/config/settings.py`
- **ZFS Utils:** `app/backend/storage/zfs_utils.py`

---

## ✅ Checklist

- [ ] Pool `pool0` kreiran
- [ ] Base dataset `pool0/ggnet2` kreiran
- [ ] Images dataset `pool0/ggnet2/images` kreiran
- [ ] Clones dataset `pool0/ggnet2/clones` kreiran
- [ ] Clients dataset `pool0/ggnet2/clients` kreiran
- [ ] Snapshots dataset `pool0/ggnet2/snapshots` kreiran
- [ ] Images bin dataset `pool0/ggnet2/images_bin` kreiran
- [ ] Import dataset `pool0/ggnet2/import` kreiran
- [ ] Svi dataset-i imaju `compression=lz4`
- [ ] Svi dataset-i imaju `mountpoint=none`

---

**ZFS Dataset Structure Complete!** ✅

