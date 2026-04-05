# Preporuke za Sve Module - ggNET2

**Datum:** 2025-01-XX  
**Verzija:** 1.0.0

---

## 📋 Sadržaj

1. [Executive Summary](#executive-summary)
2. [Backend Moduli - Preporuke](#backend-moduli---preporuke)
   - [Machines Modul](#1-machines-modul)
   - [Images Modul](#2-images-modul)
   - [VMs Modul](#3-vms-modul)
   - [Storage/Array Modul](#4-storagearray-modul)
   - [Network Modul](#5-network-modul)
   - [Clients Modul](#6-clients-modul)
   - [Settings Modul](#7-settings-modul)
   - [Config Modul](#8-config-modul)
3. [Frontend Moduli - Preporuke](#frontend-moduli---preporuke)
4. [Cross-Module Preporuke](#cross-module-preporuke)
5. [Prioritetizacija](#prioritetizacija)

---

## Executive Summary

Ovaj dokument sadrži **detaljne preporuke za svaki modul** u ggNET2 projektu, bazirane na analizi trenutne implementacije i planiranih funkcionalnosti.

### Ukupna Situacija

- **Backend:** ⚠️ **64% kompletan** - Osnovne funkcionalnosti postoje, napredne nedostaju
- **Frontend:** ⚠️ **54% kompletan** - Osnovni UI postoji, napredne funkcionalnosti nedostaju
- **Ukupno:** ⚠️ **59% kompletan**

### Top 5 Kritičnih Nedostataka

1. 🔴 **Security (0%)** - Authentication/Authorization potpuno nedostaje
2. 🔴 **Array Operacije (30%)** - Rebuild, TRIM, Drive Management nedostaju
3. 🔴 **Scheduler Modul (0%)** - Potpuno nedostaje
4. 🔴 **Structured Settings (40%)** - Generic settings postoje, structured nedostaju
5. 🔴 **Real-time Updates (30%)** - WebSocket eventi nedostaju

---

## Backend Moduli - Preporuke

### 1. Machines Modul

**Trenutna Ocena:** ⚠️ **70% kompletan**

#### ✅ Implementirano

- Osnovni CRUD operacije
- Image assignment
- Boot configuration
- Writeback management (osnovno)

#### ❌ Nedostaje

**Kritično (Prioritet: 🔴 Visok):**
1. **Bulk Operacije**
   - `bulk_restart()` - Bulk restart mašina
   - `bulk_shutdown()` - Bulk shutdown mašina
   - `bulk_wake()` - Bulk wake mašina
   - `bulk_turn_on()` - Bulk turn on mašina
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoints:** `POST /api/machines/bulk/restart`, `/shutdown`, `/wake`, `/turn-on`

**Srednji Prioritet (Prioritet: 🟡 Srednji):**
2. **Hardware Info**
   - `get_hardware_info()` - Hardware info (NIC, GPU, CPU, motherboard)
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoint:** `GET /api/machines/{id}/hardware`

3. **Advanced Settings**
   - `update_keep_writebacks()` - Keep Writebacks toggle
   - `update_snapshot_override()` - Snapshot override settings
   - `get_snapshot_state()` - Snapshot state metadata
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoints:** `PUT /api/machines/{id}/keep-writebacks`, `/snapshot-override`

**Niski Prioritet (Prioritet: 🟢 Nizak):**
4. **Writeback Management**
   - `list_writebacks()` - Lista svih writeback-a
   - `get_writeback_info()` - Detalji writeback-a
   - `delete_writeback()` - Brisanje writeback-a
   - **Vremenski Okvir:** 1 nedelja

#### 🔧 Tehničke Preporuke

1. **Refaktorisati `get_machine_info()`**
   - Metoda je dugačka (100+ linija)
   - Razdvojiti u manje metode
   - **Vremenski Okvir:** 2-3 dana

2. **Ukloniti Hardcoded Vrednosti**
   ```python
   # Trenutno:
   ip_address = machine.ip_address or "192.168.1.100"
   
   # Preporučeno:
   ip_address = machine.ip_address or settings.DEFAULT_MACHINE_IP
   ```
   - **Vremenski Okvir:** 1 dan

3. **Dodati Progress Tracking**
   - Bulk operacije treba da imaju progress tracking
   - WebSocket eventi za progress updates
   - **Vremenski Okvir:** 2-3 dana

#### 📊 Implementacioni Plan

**Faza 1 (1 nedelja):**
- [ ] Implementirati bulk operacije
- [ ] Dodati API endpoints
- [ ] Dodati progress tracking

**Faza 2 (1 nedelja):**
- [ ] Implementirati hardware info
- [ ] Implementirati advanced settings
- [ ] Refaktorisati `get_machine_info()`

**Faza 3 (1 nedelja):**
- [ ] Implementirati writeback management
- [ ] Ukloniti hardcoded vrednosti
- [ ] Dodati testove

---

### 2. Images Modul

**Trenutna Ocena:** ⚠️ **65% kompletan**

#### ✅ Implementirano

- Osnovni CRUD operacije
- Snapshot management (osnovno)
- Clone operations
- Dependency checking

#### ❌ Nedostaje

**Kritično (Prioritet: 🔴 Visok):**
1. **Snapshot Timeline**
   - `get_snapshot_timeline()` - Timeline snapshot-a sa metadata
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoint:** `GET /api/images/{id}/snapshots/timeline`

2. **Writeback Management**
   - `get_writeback_info()` - Writeback informacije za sliku
   - `apply_writebacks()` - Primena writeback-a za sliku
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoints:** `GET /api/images/{id}/writebacks`, `POST /api/images/{id}/writebacks/apply`

**Srednji Prioritet (Prioritet: 🟡 Srednji):**
3. **Snapshot Promotion**
   - `promote_snapshot()` - Promocija snapshot-a (make default)
   - `assign_snapshot_to_machine()` - Dodela snapshot-a mašini
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoints:** `POST /api/images/{id}/snapshots/{name}/promote`, `/assign`

4. **Bulk Operacije**
   - `bulk_delete_snapshots()` - Bulk brisanje snapshot-a
   - `bulk_change_default()` - Bulk promena default snapshot-a
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoints:** `POST /api/images/bulk/delete-snapshots`, `/change-default`

**Niski Prioritet (Prioritet: 🟢 Nizak):**
5. **Backup/Restore**
   - `backup_image()` - Backup slike (lokalni/remote)
   - `restore_image()` - Restore slike
   - `download_remote_image()` - Download remote slike
   - **Vremenski Okvir:** 2-3 nedelje
   - **API Endpoints:** `POST /api/images/{id}/backup`, `/restore`, `/download-remote`

#### 🔧 Tehničke Preporuke

1. **Refaktorisati `list_snapshots()`**
   - Kompleksna logika formatiranja
   - Razdvojiti parsiranje i formatiranje
   - **Vremenski Okvir:** 2-3 dana

2. **Dodati Snapshot Metadata**
   - Kreirati `Snapshot` database model
   - Store metadata (created_by, description, etc.)
   - **Vremenski Okvir:** 1 nedelja

3. **Implementirati Progress Tracking**
   - Backup/restore operacije treba da imaju progress
   - WebSocket eventi za progress updates
   - **Vremenski Okvir:** 2-3 dana

#### 📊 Implementacioni Plan

**Faza 1 (1 nedelja):**
- [ ] Implementirati snapshot timeline
- [ ] Implementirati writeback management
- [ ] Dodati API endpoints

**Faza 2 (1 nedelja):**
- [ ] Implementirati snapshot promotion
- [ ] Implementirati bulk operacije
- [ ] Refaktorisati `list_snapshots()`

**Faza 3 (2-3 nedelje):**
- [ ] Implementirati backup/restore
- [ ] Dodati Snapshot model
- [ ] Implementirati progress tracking

---

### 3. VMs Modul

**Trenutna Ocena:** ⚠️ **70% kompletan**

#### ✅ Implementirano

- Osnovni CRUD operacije
- VM lifecycle (start, stop, reset)
- Resource management (CPU, RAM)
- Libvirt integracija

#### ❌ Nedostaje

**Kritično (Prioritet: 🔴 Visok):**
1. **Remote Control**
   - `get_remote_control_url()` - Remote control URL generisanje (noVNC)
   - VNC token management
   - **Vremenski Okvir:** 1-2 nedelje
   - **API Endpoint:** `GET /api/vms/{id}/remote-control`

**Srednji Prioritet (Prioritet: 🟡 Srednji):**
2. **Host Info**
   - `get_host_info()` - Host info (CPU, RAM, storage)
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoint:** `GET /api/vms/host-info`

3. **Bridge Reconfiguration**
   - `reconfigure_bridge()` - Bridge rekonfiguracija
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoint:** `POST /api/vms/{id}/reconfigure-bridge`

4. **VM Console**
   - `get_vm_console()` - Console access
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoint:** `GET /api/vms/{id}/console`

**Niski Prioritet (Prioritet: 🟢 Nizak):**
5. **Advanced Features**
   - `migrate_vm()` - VM migracija
   - `snapshot_vm()` - VM snapshot
   - `get_vm_performance()` - Performance metrics
   - **Vremenski Okvir:** 2-3 nedelje

#### 🔧 Tehničke Preporuke

1. **Refaktorisati `_generate_domain_xml()`**
   - Metoda je dugačka (150+ linija)
   - Razdvojiti u manje metode po sekcijama
   - **Vremenski Okvir:** 2-3 dana

2. **Implementirati VNC Token Management**
   - Koristiti `VNC_TOKEN_DIR` iz settings
   - Generisati secure token-e
   - Validacija token-a
   - **Vremenski Okvir:** 1 nedelja

3. **Dodati Error Handling za Libvirt**
   - Bolje error messages
   - Graceful degradation
   - **Vremenski Okvir:** 2-3 dana

#### 📊 Implementacioni Plan

**Faza 1 (1-2 nedelje):**
- [ ] Implementirati remote control
- [ ] Implementirati VNC token management
- [ ] Dodati API endpoint

**Faza 2 (1 nedelja):**
- [ ] Implementirati host info
- [ ] Implementirati bridge reconfiguration
- [ ] Implementirati VM console

**Faza 3 (2-3 nedelje):**
- [ ] Implementirati advanced features
- [ ] Refaktorisati `_generate_domain_xml()`
- [ ] Poboljšati error handling

---

### 4. Storage/Array Modul

**Trenutna Ocena:** 🔴 **40% kompletan**

#### ✅ Implementirano

- Osnovne ZFS operacije (pool, dataset, snapshot, clone)
- Pool status (simplified)
- ARC stats
- IO stats
- Autotrim management

#### ❌ Nedostaje

**Kritično (Prioritet: 🔴 Visok):**
1. **Drive Detection & Management**
   - `get_pool_drives()` - Lista drive-ova u pool-u
   - `get_drive_info()` - Detalji drive-a (serial, model, SMART)
   - `identify_drive()` - Blink LED za drive
   - **Vremenski Okvir:** 1-2 nedelje
   - **API Endpoints:** `GET /api/storage/array/drives`, `/drives/{id}`, `POST /drives/{id}/identify`

2. **TRIM Operacija**
   - `pool_trim()` - Pool TRIM operacija (stvarna implementacija)
   - `get_trim_progress()` - Progress TRIM operacije
   - `get_trim_history()` - TRIM history
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoints:** `POST /api/storage/array/trim`, `GET /trim/status`, `/trim/history`

3. **Rebuild Operacije**
   - `pool_add()` - Dodavanje drive-a u pool
   - `pool_replace()` - Zamena drive-a
   - `pool_remove()` - Uklanjanje drive-a
   - `pool_online()` / `pool_offline()` - Drive online/offline
   - `get_rebuild_progress()` - Progress rebuild operacije
   - **Vremenski Okvir:** 2-3 nedelje
   - **API Endpoints:** `POST /api/storage/array/drives/add`, `/replace`, `/remove`, `/offline`, `/online`, `GET /rebuild/status`

**Srednji Prioritet (Prioritet: 🟡 Srednji):**
4. **Pool Status Parsing**
   - Detaljno parsiranje `zpool status` output-a
   - Vdev struktura
   - Errors/warnings
   - Rebuild progress parsing
   - **Vremenski Okvir:** 1 nedelja

5. **RAID Conversion**
   - `convert_raid()` - RAID konverzija (RAID0 ↔ RAID10)
   - Validacija preuslova
   - Step tracking
   - **Vremenski Okvir:** 2-3 nedelje
   - **API Endpoint:** `POST /api/storage/array/raid/convert`

**Niski Prioritet (Prioritet: 🟢 Nizak):**
6. **Forklift Upgrade**
   - `forklift_upgrade()` - Forklift storage upgrade workflow
   - Step-by-step tracking
   - State persistence
   - **Vremenski Okvir:** 2-3 nedelje
   - **API Endpoint:** `POST /api/storage/array/forklift/start`

#### 🔧 Tehničke Preporuke

1. **Poboljšati Pool Status Parsing**
   ```python
   # Trenutno: Simplified parsing
   if "ONLINE" in result.stdout:
       status["state"] = "online"
   
   # Preporučeno: Detaljno parsiranje
   # - Parse vdev struktura
   # - Parse drive lista
   # - Parse errors/warnings
   # - Parse rebuild progress
   ```
   - **Vremenski Okvir:** 1 nedelja

2. **Implementirati Progress Tracking**
   - Database model za ArrayOperation
   - WebSocket eventi za progress updates
   - State persistence
   - **Vremenski Okvir:** 1 nedelja

3. **Implementirati TRIM Operaciju**
   ```python
   # Trenutno: Placeholder
   def manual_trim(self, pool_name: Optional[str] = None) -> None:
       logger.info(f"Manual TRIM requested for pool: {pool_name}")
       # Note: zpool trim command would be executed here
   
   # Preporučeno: Stvarna implementacija
   def manual_trim(self, pool_name: Optional[str] = None) -> Dict[str, Any]:
       # Execute: zpool trim pool_name
       # Start background job
       # Return job ID for progress tracking
   ```
   - **Vremenski Okvir:** 1 nedelja

#### 📊 Implementacioni Plan

**Faza 1 (1-2 nedelje):**
- [ ] Implementirati drive detection
- [ ] Poboljšati pool status parsing
- [ ] Dodati API endpoints

**Faza 2 (1 nedelja):**
- [ ] Implementirati TRIM operaciju
- [ ] Implementirati progress tracking
- [ ] Dodati TRIM history

**Faza 3 (2-3 nedelje):**
- [ ] Implementirati rebuild operacije
- [ ] Implementirati drive management
- [ ] Dodati progress tracking

**Faza 4 (2-3 nedelje):**
- [ ] Implementirati RAID conversion
- [ ] Implementirati forklift upgrade
- [ ] Dodati testove

---

### 5. Network Modul

**Trenutna Ocena:** ✅ **80% kompletan**

#### ✅ Implementirano

- IP address detection
- Bridge management
- iPXE script generation
- DNS configuration
- IP forwarding

#### ❌ Nedostaje

**Srednji Prioritet (Prioritet: 🟡 Srednji):**
1. **Auto Bridge Configuration**
   - `auto_configure_bridge()` - Auto konfiguracija bridge-a
   - Status log-ovi
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoint:** `POST /api/network/bridge/auto-configure`

2. **Bridge Status**
   - `get_bridge_status()` - Status bridge-a (sa log-ovima)
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoint:** `GET /api/network/bridge/status`

3. **NIC Info**
   - `get_nic_info()` - NIC informacije (link speed, etc.)
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoint:** `GET /api/network/nics`

**Niski Prioritet (Prioritet: 🟢 Nizak):**
4. **iPXE Management**
   - `update_ipxe_script()` - Ažuriranje iPXE script-a
   - `get_boot_history()` - Boot history
   - `configure_dnsmasq()` - dnsmasq konfiguracija
   - **Vremenski Okvir:** 1-2 nedelje

#### 🔧 Tehničke Preporuke

1. **Dodati Bridge Status Logging**
   - Log bridge operacije
   - Store status history
   - **Vremenski Okvir:** 2-3 dana

2. **Implementirati dnsmasq Configuration**
   - Koristiti `dnsmasq_config` path iz settings
   - Auto-generisati konfiguraciju
   - **Vremenski Okvir:** 1 nedelja

#### 📊 Implementacioni Plan

**Faza 1 (1 nedelja):**
- [ ] Implementirati auto bridge configuration
- [ ] Implementirati bridge status
- [ ] Implementirati NIC info

**Faza 2 (1-2 nedelje):**
- [ ] Implementirati iPXE management
- [ ] Implementirati dnsmasq configuration
- [ ] Dodati testove

---

### 6. Clients Modul

**Trenutna Ocena:** ⚠️ **60% kompletan**

#### ✅ Implementirano

- Client info
- Message sending
- Broadcast messaging
- WebSocket connection management

#### ❌ Nedostaje

**Kritično (Prioritet: 🔴 Visok):**
1. **Real-time Eventi**
   - `machine_updated` - Machine update event
   - `image_updated` - Image update event
   - `array_updated` - Array update event
   - `rebuild_progress_updated` - Rebuild progress event
   - `trim_progress_updated` - TRIM progress event
   - **Vremenski Okvir:** 1-2 nedelje

2. **Progress Tracking Eventi**
   - Progress updates za dugotrajne operacije
   - WebSocket eventi za progress
   - **Vremenski Okvir:** 1 nedelja

**Srednji Prioritet (Prioritet: 🟡 Srednji):**
3. **Connection Management**
   - `register_client()` - Registracija novog klijenta
   - `unregister_client()` - Uklanjanje klijenta
   - Connection heartbeat
   - Reconnection handling
   - **Vremenski Okvir:** 1 nedelja

4. **Client History**
   - `get_client_history()` - Istorija klijenta
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoint:** `GET /api/clients/{id}/history`

#### 🔧 Tehničke Preporuke

1. **Implementirati Heartbeat Mehanizam**
   - Periodic ping/pong
   - Connection health monitoring
   - Auto-reconnection
   - **Vremenski Okvir:** 1 nedelja

2. **Dodati Event Broadcasting**
   - Integrisati sa manager klasama
   - Broadcast eventi na promene
   - **Vremenski Okvir:** 1 nedelja

#### 📊 Implementacioni Plan

**Faza 1 (1-2 nedelje):**
- [ ] Implementirati real-time eventi
- [ ] Implementirati progress tracking eventi
- [ ] Dodati event broadcasting

**Faza 2 (1 nedelja):**
- [ ] Implementirati connection management
- [ ] Implementirati heartbeat
- [ ] Implementirati client history

---

### 7. Settings Modul

**Trenutna Ocena:** 🔴 **40% kompletan**

#### ✅ Implementirano

- Generic settings CRUD
- Environment variable loading
- Type conversion

#### ❌ Nedostaje

**Kritično (Prioritet: 🔴 Visok):**
1. **Structured Settings Endpoints**
   - `get_general_settings()` - General settings
   - `update_general_settings()` - Update general settings
   - `get_network_settings()` - Network settings
   - `update_network_settings()` - Update network settings
   - `get_storage_settings()` - Storage settings
   - `update_storage_settings()` - Update storage settings
   - `get_security_settings()` - Security settings
   - `update_security_settings()` - Update security settings
   - **Vremenski Okvir:** 1-2 nedelje
   - **API Endpoints:** `GET/PUT /api/settings/general`, `/network`, `/storage`, `/security`

2. **RAM Allocation**
   - RAM allocation settings
   - Validation
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoint:** `GET/PUT /api/settings/ram-allocation`

3. **Retention Settings**
   - Snapshot retention
   - Writeback retention
   - Cleanup policies
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoint:** `GET/PUT /api/settings/retention`

**Srednji Prioritet (Prioritet: 🟡 Srednji):**
4. **Secure Boot Settings**
   - Certificate upload
   - Certificate management
   - **Vremenski Okvir:** 1 nedelja
   - **API Endpoint:** `GET/PUT /api/settings/secure-boot`

#### 🔧 Tehničke Preporuke

1. **Kreirati Settings Schema**
   ```python
   class GeneralSettings(BaseModel):
       server_name: str
       release_stream: str
       # ...
   
   class NetworkSettings(BaseModel):
       bridge_name: str
       bridge_ip: str
       # ...
   ```
   - **Vremenski Okvir:** 1 nedelja

2. **Dodati Validation**
   - Pydantic validacije
   - Business logic validacije
   - **Vremenski Okvir:** 1 nedelja

#### 📊 Implementacioni Plan

**Faza 1 (1-2 nedelje):**
- [ ] Implementirati structured settings endpoints
- [ ] Kreirati settings schema
- [ ] Dodati validation

**Faza 2 (1 nedelja):**
- [ ] Implementirati RAM allocation
- [ ] Implementirati retention settings
- [ ] Implementirati secure boot settings

---

### 8. Config Modul

**Trenutna Ocena:** ⚠️ **70% kompletan**

#### ✅ Implementirano

- Database setup
- SQLAlchemy models
- Alembic migrations
- Basic models (Image, Machine, VM, Client, Setting)

#### ❌ Nedostaje

**Srednji Prioritet (Prioritet: 🟡 Srednji):**
1. **Napredni Modeli**
   - `Snapshot` model - Snapshot metadata
   - `Writeback` model - Writeback metadata
   - `ScheduledJob` model - Scheduler jobs
   - `ActivityLog` model - Activity logging
   - `Drive` model - Array drive management
   - `ArrayOperation` model - Array operation tracking
   - **Vremenski Okvir:** 1-2 nedelje

2. **Database Migrations**
   - Migracije za nove modele
   - Data migrations
   - **Vremenski Okvir:** 1 nedelja

#### 🔧 Tehničke Preporuke

1. **Dodati Timestamps**
   - `created_at`, `updated_at` za sve modele
   - Auto-update `updated_at`
   - **Vremenski Okvir:** 2-3 dana

2. **Dodati Soft Delete**
   - `deleted_at` field
   - Soft delete support
   - **Vremenski Okvir:** 1 nedelja

#### 📊 Implementacioni Plan

**Faza 1 (1-2 nedelje):**
- [ ] Kreirati napredne modele
- [ ] Dodati migracije
- [ ] Dodati timestamps

**Faza 2 (1 nedelja):**
- [ ] Implementirati soft delete
- [ ] Dodati testove

---

## Frontend Moduli - Preporuke

### 1. Machines Page

**Trenutna Ocena:** ⚠️ **50% kompletan**

#### ❌ Nedostaje

**Kritično (Prioritet: 🔴 Visok):**
1. **Bulk Toolbar**
   - Bulk restart button
   - Bulk shutdown button
   - Bulk wake button
   - Bulk turn on button
   - **Vremenski Okvir:** 1 nedelja

2. **Status Ikonografija**
   - ggLeap badge (green/grey)
   - Warning badge (missing ggRock client)
   - Exclamation badge (missing image)
   - Link speed warning
   - Keep Writebacks icon
   - **Vremenski Okvir:** 1 nedelja

**Srednji Prioritet (Prioritet: 🟡 Srednji):**
3. **Hardware Tab**
   - NIC info
   - GPU info
   - CPU info
   - Motherboard info
   - **Vremenski Okvir:** 1 nedelja

4. **Advanced Tab**
   - Keep Writebacks toggle
   - Snapshot override settings
   - **Vremenski Okvir:** 1 nedelja

**Niski Prioritet (Prioritet: 🟢 Nizak):**
5. **Column Chooser**
   - Column chooser modal
   - Column visibility toggle
   - **Vremenski Okvir:** 1 nedelja

6. **Server-side Pagination**
   - Pagination component
   - Server-side filtering
   - **Vremenski Okvir:** 1 nedelja

#### 📊 Implementacioni Plan

**Faza 1 (1 nedelja):**
- [ ] Implementirati bulk toolbar
- [ ] Implementirati status ikonografiju
- [ ] Dodati API integraciju

**Faza 2 (1 nedelja):**
- [ ] Implementirati hardware tab
- [ ] Implementirati advanced tab
- [ ] Dodati testove

**Faza 3 (1 nedelja):**
- [ ] Implementirati column chooser
- [ ] Implementirati server-side pagination

---

### 2. Images Page

**Trenutna Ocena:** ⚠️ **50% kompletan**

#### ❌ Nedostaje

**Kritično (Prioritet: 🔴 Visok):**
1. **Snapshot Timeline**
   - Timeline komponenta
   - Snapshot metadata prikaz
   - **Vremenski Okvir:** 1 nedelja

2. **Writeback Management UI**
   - Writeback list
   - Apply writebacks workflow
   - Writeback filtering
   - **Vremenski Okvir:** 1 nedelja

**Srednji Prioritet (Prioritet: 🟡 Srednji):**
3. **Backup/Restore Workflow**
   - Backup wizard
   - Restore wizard
   - Progress tracking
   - **Vremenski Okvir:** 2-3 nedelje

4. **Bulk Operacije**
   - Bulk delete snapshots
   - Bulk change default
   - **Vremenski Okvir:** 1 nedelja

**Niski Prioritet (Prioritet: 🟢 Nizak):**
5. **Remote Image Download**
   - Download wizard
   - Progress tracking
   - **Vremenski Okvir:** 1-2 nedelje

#### 📊 Implementacioni Plan

**Faza 1 (1 nedelja):**
- [ ] Implementirati snapshot timeline
- [ ] Implementirati writeback management UI
- [ ] Dodati API integraciju

**Faza 2 (1 nedelja):**
- [ ] Implementirati bulk operacije
- [ ] Dodati testove

**Faza 3 (2-3 nedelje):**
- [ ] Implementirati backup/restore workflow
- [ ] Implementirati remote image download

---

### 3. VMs Page

**Trenutna Ocena:** ⚠️ **60% kompletan**

#### ❌ Nedostaje

**Kritično (Prioritet: 🔴 Visok):**
1. **Remote Control UI**
   - noVNC integracija
   - Remote control modal
   - Full-screen mode
   - **Vremenski Okvir:** 1-2 nedelje

**Srednji Prioritet (Prioritet: 🟡 Srednji):**
2. **Advanced Settings**
   - Advanced settings modal
   - Resource monitoring
   - **Vremenski Okvir:** 1 nedelja

3. **VM Console Access**
   - Console access button
   - Console modal
   - **Vremenski Okvir:** 1 nedelja

#### 📊 Implementacioni Plan

**Faza 1 (1-2 nedelje):**
- [ ] Implementirati remote control UI
- [ ] Integrisati noVNC
- [ ] Dodati API integraciju

**Faza 2 (1 nedelja):**
- [ ] Implementirati advanced settings
- [ ] Implementirati VM console access

---

### 4. Storage Page

**Trenutna Ocena:** 🔴 **30% kompletan**

#### ❌ Nedostaje

**Kritično (Prioritet: 🔴 Visok):**
1. **Array Dashboard**
   - Status LED (green/amber/red)
   - RAID type badge
   - Usage bar (Size/Used/Free/Reserved)
   - Warning threshold indicators
   - **Vremenski Okvir:** 1 nedelja

2. **Drive Grid**
   - Drive table (Device, Model/Serial, Role, Status, Temperature)
   - Drive actions (Details, Identify, Mark Failed, Replace, Remove, SMART)
   - Drive details modal
   - **Vremenski Okvir:** 1-2 nedelje

3. **Array Operacije UI**
   - Rebuild progress UI
   - TRIM progress UI
   - Drive management wizards
   - **Vremenski Okvir:** 2-3 nedelje

**Srednji Prioritet (Prioritet: 🟡 Srednji):**
4. **RAID Conversion Wizard**
   - Multi-step wizard
   - Progress tracking
   - **Vremenski Okvir:** 2-3 nedelje

5. **Forklift Upgrade Wizard**
   - Step-by-step guide
   - Progress tracking
   - **Vremenski Okvir:** 2-3 nedelje

#### 📊 Implementacioni Plan

**Faza 1 (1 nedelja):**
- [ ] Implementirati array dashboard
- [ ] Implementirati drive grid
- [ ] Dodati API integraciju

**Faza 2 (2-3 nedelje):**
- [ ] Implementirati array operacije UI
- [ ] Implementirati progress tracking
- [ ] Dodati testove

**Faza 3 (2-3 nedelje):**
- [ ] Implementirati RAID conversion wizard
- [ ] Implementirati forklift upgrade wizard

---

### 5. Settings Page

**Trenutna Ocena:** 🔴 **30% kompletan**

#### ❌ Nedostaje

**Kritično (Prioritet: 🔴 Visok):**
1. **Structured Settings API Integracija**
   - General settings tab
   - Network settings tab
   - Storage settings tab
   - Security settings tab
   - **Vremenski Okvir:** 1 nedelja

2. **RAM Allocation Sliders**
   - RAM allocation UI
   - Validation
   - **Vremenski Okvir:** 1 nedelja

3. **Retention Settings Controls**
   - Snapshot retention
   - Writeback retention
   - Cleanup policies
   - **Vremenski Okvir:** 1 nedelja

**Srednji Prioritet (Prioritet: 🟡 Srednji):**
4. **Network Bridge Auto-config**
   - Auto-config button
   - Status log-ovi
   - **Vremenski Okvir:** 1 nedelja

5. **Secure Boot Certificate Upload**
   - Certificate upload UI
   - Certificate management
   - **Vremenski Okvir:** 1 nedelja

**Niski Prioritet (Prioritet: 🟢 Nizak):**
6. **Unsaved Changes Detection**
   - Unsaved changes warning
   - Save/Cancel funkcionalnost
   - **Vremenski Okvir:** 1 nedelja

#### 📊 Implementacioni Plan

**Faza 1 (1 nedelja):**
- [ ] Implementirati structured settings API integraciju
- [ ] Implementirati RAM allocation sliders
- [ ] Implementirati retention settings controls

**Faza 2 (1 nedelja):**
- [ ] Implementirati network bridge auto-config
- [ ] Implementirati secure boot certificate upload
- [ ] Implementirati unsaved changes detection

---

### 6. Dashboard Page

**Trenutna Ocena:** ⚠️ **60% kompletan**

#### ❌ Nedostaje

**Srednji Prioritet (Prioritet: 🟡 Srednji):**
1. **Napredne Statistike**
   - Charts/graphs
   - Historical data
   - **Vremenski Okvir:** 1-2 nedelje

2. **Real-time Updates**
   - WebSocket integracija
   - Auto-refresh
   - **Vremenski Okvir:** 1 nedelja

3. **Activity Feed**
   - Activity log prikaz
   - Filtering
   - **Vremenski Okvir:** 1 nedelja

#### 📊 Implementacioni Plan

**Faza 1 (1 nedelja):**
- [ ] Implementirati real-time updates
- [ ] Dodati WebSocket integraciju

**Faza 2 (1-2 nedelje):**
- [ ] Implementirati napredne statistike
- [ ] Implementirati activity feed

---

## Cross-Module Preporuke

### 1. Security (Prioritet: 🔴 Visok)

**Status:** 🔴 **0% kompletan** - Potpuno nedostaje

#### Preporuke

1. **JWT Authentication**
   - Implementirati JWT token sistem
   - Login endpoint
   - Token refresh
   - **Vremenski Okvir:** 1-2 nedelje

2. **Role-based Authorization**
   - Admin, Operator, User roles
   - Permission system
   - **Vremenski Okvir:** 1-2 nedelje

3. **Secure Endpoints**
   - Protect sve endpointi
   - CSRF protection
   - **Vremenski Okvir:** 1 nedelja

#### 📊 Implementacioni Plan

**Faza 1 (1-2 nedelje):**
- [ ] Implementirati JWT authentication
- [ ] Implementirati login endpoint
- [ ] Dodati token refresh

**Faza 2 (1-2 nedelje):**
- [ ] Implementirati role-based authorization
- [ ] Implementirati permission system
- [ ] Protect sve endpointi

---

### 2. Real-time Updates (Prioritet: 🔴 Visok)

**Status:** ⚠️ **30% kompletan** - WebSocket postoji, eventi nedostaju

#### Preporuke

1. **WebSocket Client u Frontend-u**
   - React WebSocket hook
   - Connection management
   - Auto-reconnection
   - **Vremenski Okvir:** 1 nedelja

2. **Progress Tracking Eventi**
   - Rebuild progress
   - TRIM progress
   - Backup/restore progress
   - **Vremenski Okvir:** 1 nedelja

3. **Real-time Notifikacije**
   - Machine updates
   - Image updates
   - Array updates
   - **Vremenski Okvir:** 1 nedelja

#### 📊 Implementacioni Plan

**Faza 1 (1 nedelja):**
- [ ] Implementirati WebSocket client u frontend-u
- [ ] Dodati connection management

**Faza 2 (1 nedelja):**
- [ ] Implementirati progress tracking eventi
- [ ] Implementirati real-time notifikacije

---

### 3. Scheduler Modul (Prioritet: 🔴 Visok)

**Status:** 🔴 **0% kompletan** - Potpuno nedostaje

#### Preporuke

1. **Backend API**
   - Job CRUD operacije
   - Job execution
   - Job history
   - **Vremenski Okvir:** 2-3 nedelje

2. **Frontend UI**
   - Scheduler dashboard
   - Job creation/edit
   - Job history
   - **Vremenski Okvir:** 2-3 nedelje

#### 📊 Implementacioni Plan

**Faza 1 (2-3 nedelje):**
- [ ] Kreirati ScheduledJob model
- [ ] Implementirati backend API
- [ ] Implementirati job execution

**Faza 2 (2-3 nedelje):**
- [ ] Implementirati frontend UI
- [ ] Dodati testove

---

## Prioritetizacija

### Prioritet 1 (MVP - 4-6 nedelja)

**Kritično za MVP:**

1. **Security** (1-2 nedelje)
   - JWT authentication
   - Role-based authorization

2. **Array Operacije** (2-3 nedelje)
   - Drive detection
   - TRIM operacija
   - Rebuild operacije

3. **Bulk Operacije** (1 nedelja)
   - Machines bulk operacije
   - Images bulk operacije

4. **Structured Settings** (1-2 nedelje)
   - Structured endpoints
   - RAM allocation
   - Retention settings

5. **Real-time Updates** (1-2 nedelje)
   - WebSocket client
   - Progress tracking eventi

**Ukupno:** 6-10 nedelja

---

### Prioritet 2 (6-8 nedelja)

**Važno za production:**

1. **Scheduler Modul** (4-6 nedelja)
   - Backend API
   - Frontend UI

2. **Napredne Machines Funkcionalnosti** (2 nedelje)
   - Hardware info
   - Advanced settings

3. **Napredne Images Funkcionalnosti** (2-3 nedelje)
   - Snapshot timeline
   - Writeback management
   - Backup/restore

4. **VM Remote Control** (1-2 nedelje)
   - noVNC integracija

**Ukupno:** 9-13 nedelja

---

### Prioritet 3 (4-6 nedelja)

**Nice to have:**

1. **RAID Conversion** (2-3 nedelje)
2. **Forklift Upgrade** (2-3 nedelje)
3. **Advanced Dashboard** (1-2 nedelje)
4. **Code Quality Improvements** (1-2 nedelje)

**Ukupno:** 6-10 nedelja

---

## 📈 Ukupni Roadmap

### Q1 (12 nedelja)

**Faza 1: MVP (6-10 nedelja)**
- Security
- Array operacije
- Bulk operacije
- Structured settings
- Real-time updates

**Faza 2: Production Ready (2-4 nedelje)**
- Scheduler modul
- Napredne funkcionalnosti
- Testing & polish

### Q2 (12 nedelja)

**Faza 3: Advanced Features (6-8 nedelje)**
- RAID conversion
- Forklift upgrade
- Advanced dashboard
- Code quality improvements

**Faza 4: Optimization (4-6 nedelje)**
- Performance optimization
- Scalability improvements
- Documentation

---

## ✅ Zaključak

Preporuke su organizovane po modulima sa jasnim prioritetima i vremenskim okvirima. **Prioritet 1 (MVP)** je kritičan i treba biti implementiran prvo pre nego što se pređe na napredne funkcionalnosti.

**Ključni Fokus:**
1. 🔴 Security - **MORA** biti implementiran prvo
2. 🔴 Array Operacije - Kritične za storage management
3. 🔴 Real-time Updates - Potrebne za dobar UX
4. 🔴 Structured Settings - Potrebne za kompletnu funkcionalnost

**Ukupna Procena Vremena za MVP:** 6-10 nedelja

---

*Dokument kreiran na osnovu detaljne analize svih modula i planova*


