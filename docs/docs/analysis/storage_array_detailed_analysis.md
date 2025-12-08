# Detaljna Analiza Storage/Array Modula - ggNET2

**Datum:** 2025-01-XX  
**Verzija:** 0.1.0

---

## 📋 Executive Summary

Storage/Array modul je kritičan za funkcionisanje sistema, ali trenutno ima samo **osnovne funkcionalnosti**. Nedostaju **kritične napredne operacije** poput rebuild-a, TRIM-a, drive management-a, i RAID konverzije koje su neophodne za production-ready sistem.

**Ukupna Ocena:** 🔴 **40% kompletan**

---

## 🏗️ Arhitektura Modula

### Struktura

```
app/backend/storage/
├── __init__.py
├── zfs_utils.py           # 655 linija - Low-level ZFS operacije
├── storage_manager.py     # 268 linija - High-level storage management
├── arc_monitor.py         # 93 linije - ARC statistike
└── iostat_reader.py       # 134 linije - IO statistike

app/backend/api/
└── storage.py             # 259 linija - API endpoints

app/frontend/src/
├── pages/Storage.jsx      # 296 linija - Frontend stranica
└── services/storageAPI.js # 67 linija - API service
```

### Komponente

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Storage.jsx)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Array Dashboard (Placeholder data)                  │  │
│  │  - Pool status                                       │  │
│  │  - Stripes table (hardcoded)                          │  │
│  │  - Trim button                                       │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              Backend API (storage.py)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  GET /api/storage/pool          ✅                   │  │
│  │  GET /api/storage/arc           ✅                   │  │
│  │  GET /api/storage/iostat        ✅                   │  │
│  │  POST /api/storage/pool/trim    ⚠️ (placeholder)     │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│         StorageManager (storage_manager.py)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Pool Management      ✅ (osnovno)                    │  │
│  │  Dataset Management   ✅                              │  │
│  │  ARC Stats            ✅                              │  │
│  │  IO Stats             ✅                              │  │
│  │  TRIM                 ⚠️ (placeholder)                │  │
│  │  Rebuild              ❌                              │  │
│  │  Drive Management     ❌                              │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│            ZFSUtils (zfs_utils.py)                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Pool Ops            ✅ (list, status, create, etc.)  │  │
│  │  Dataset Ops         ✅                               │  │
│  │  Snapshot Ops        ✅                               │  │
│  │  Clone Ops           ✅                               │  │
│  │  Volume Ops          ✅                               │  │
│  │  Drive Ops           ❌                              │  │
│  │  Rebuild Ops         ❌                              │  │
│  │  TRIM Ops            ❌                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Detaljna Analiza Komponenti

### 1. ZFSUtils (`zfs_utils.py`)

#### ✅ Implementirane Funkcionalnosti

**Pool Operacije:**
- ✅ `pool_list()` - Lista svih pool-ova
- ✅ `pool_status()` - Status pool-a (simplified parsing)
- ✅ `pool_exists()` - Provera postojanja
- ✅ `pool_create()` - Kreiranje pool-a (stripe, mirror, raidz)
- ✅ `pool_import()` - Import pool-a
- ✅ `pool_export()` - Export pool-a
- ✅ `pool_scrub()` - Pokretanje scrub operacije

**Dataset Operacije:**
- ✅ `dataset_list()` - Lista dataset-a
- ✅ `dataset_create()` - Kreiranje dataset-a
- ✅ `dataset_destroy()` - Brisanje dataset-a
- ✅ `dataset_exists()` - Provera postojanja
- ✅ `dataset_get_property()` - Čitanje property-ja
- ✅ `dataset_set_property()` - Postavljanje property-ja

**Snapshot Operacije:**
- ✅ `snapshot_create()` - Kreiranje snapshot-a
- ✅ `snapshot_list()` - Lista snapshot-a
- ✅ `snapshot_destroy()` - Brisanje snapshot-a
- ✅ `snapshot_exists()` - Provera postojanja

**Clone Operacije:**
- ✅ `clone_create()` - Kreiranje clone-a
- ✅ `clone_promote()` - Promocija clone-a (writeback)

**Volume Operacije:**
- ✅ `volume_create()` - Kreiranje zvol-a
- ✅ `volume_get_size()` - Čitanje veličine
- ✅ `volume_set_size()` - Promena veličine

#### ❌ Nedostajuće Funkcionalnosti

**Pool Operacije:**
- ❌ `pool_trim()` - TRIM operacija na pool-u
- ❌ `pool_replace()` - Zamena drive-a
- ❌ `pool_attach()` - Dodavanje drive-a
- ❌ `pool_detach()` - Uklanjanje drive-a
- ❌ `pool_online()` - Online drive-a
- ❌ `pool_offline()` - Offline drive-a
- ❌ `pool_remove()` - Uklanjanje drive-a iz pool-a
- ❌ `pool_add()` - Dodavanje drive-a u pool
- ❌ `pool_get_drives()` - Lista drive-ova u pool-u
- ❌ `pool_get_rebuild_status()` - Status rebuild-a/resilver-a

**Drive Operacije:**
- ❌ `get_drive_info()` - Informacije o drive-u (serial, model, SMART)
- ❌ `identify_drive()` - Blink LED za drive
- ❌ `mark_drive_failed()` - Označavanje drive-a kao failed
- ❌ `get_drive_temperature()` - Temperatura drive-a
- ❌ `get_drive_smart()` - SMART podaci

#### 🔍 Detaljna Analiza Koda

**Jake Strane:**
- ✅ Dobra struktura klasa
- ✅ Dobro error handling (ZFSError)
- ✅ Logging implementiran
- ✅ Subprocess execution sa timeout-om (5 minuta)
- ✅ Dobra validacija input-a

**Problemi:**

1. **Simplified Status Parsing:**
   ```python
   # pool_status() samo parsira "ONLINE", "DEGRADED", etc.
   # Ne parsira detaljne informacije o drive-ovima, vdev-ovima, errors
   ```
   **Problem:** Nedostaju detaljne informacije potrebne za drive grid

2. **Nedostaje Drive Detection:**
   ```python
   # Nema metoda za detekciju drive-ova u pool-u
   # Nema parsiranja "zpool status" output-a za drive informacije
   ```
   **Problem:** Frontend ne može prikazati drive grid

3. **Nedostaje Rebuild Progress:**
   ```python
   # Nema parsiranja rebuild/resilver progress-a
   # Nema metoda za praćenje dugotrajnih operacija
   ```
   **Problem:** Nema progress tracking za rebuild operacije

4. **TRIM Nedostaje:**
   ```python
   # Nema pool_trim() metode
   # ZFS podržava "zpool trim" komandu
   ```
   **Problem:** TRIM operacija nije implementirana

**Ocena:** ⚠️ **60% kompletan** - Osnovne ZFS operacije postoje, napredne nedostaju

---

### 2. StorageManager (`storage_manager.py`)

#### ✅ Implementirane Funkcionalnosti

- ✅ `get_pool_status()` - Status pool-a
- ✅ `create_pool()` - Kreiranje pool-a
- ✅ `import_pool()` - Import pool-a
- ✅ `start_scrub()` - Pokretanje scrub-a
- ✅ `enable_autotrim()` / `disable_autotrim()` - Autotrim management
- ✅ `get_autotrim_status()` - Status autotrim-a
- ✅ `manual_trim()` - **PLACEHOLDER** (samo loguje)
- ✅ `create_base_datasets()` - Kreiranje base dataset-a
- ✅ `get_arc_stats()` - ARC statistike
- ✅ `get_pool_iostat()` - IO statistike

#### ❌ Nedostajuće Funkcionalnosti

**Array Operacije:**
- ❌ `rebuild_array()` - Rebuild array operacija
- ❌ `trim_array()` - TRIM operacija (samo placeholder)
- ❌ `get_drives()` - Lista drive-ova
- ❌ `add_drive()` - Dodavanje drive-a
- ❌ `remove_drive()` - Uklanjanje drive-a
- ❌ `replace_drive()` - Zamena drive-a
- ❌ `convert_raid()` - RAID konverzija (RAID0 ↔ RAID10)
- ❌ `forklift_upgrade()` - Forklift storage upgrade
- ❌ `get_rebuild_progress()` - Progress rebuild operacije
- ❌ `get_trim_progress()` - Progress TRIM operacije
- ❌ `get_space_threshold_status()` - Space threshold monitoring

**Drive Management:**
- ❌ `get_drive_details()` - Detalji drive-a
- ❌ `identify_drive()` - Blink LED
- ❌ `mark_drive_failed()` - Označavanje failed
- ❌ `take_drive_offline()` - Offline drive-a
- ❌ `bring_drive_online()` - Online drive-a
- ❌ `get_drive_smart()` - SMART podaci

#### 🔍 Detaljna Analiza Koda

**Problemi:**

1. **TRIM je Placeholder:**
   ```python
   def manual_trim(self, pool_name: Optional[str] = None) -> None:
       # Manual TRIM is done via zpool trim command
       # This is a simplified version - can be enhanced
       logger.info(f"Manual TRIM requested for pool: {pool_name}")
       # Note: zpool trim command would be executed here
       # For now, we'll just log it
   ```
   **Problem:** TRIM operacija se ne izvršava, samo se loguje

2. **Nedostaje Drive Management:**
   - Nema metoda za upravljanje drive-ovima
   - Nema parsiranja drive informacija iz `zpool status`

3. **Nedostaje Rebuild Management:**
   - Nema metoda za rebuild operacije
   - Nema progress tracking-a

**Ocena:** ⚠️ **50% kompletan** - Osnovne operacije postoje, napredne nedostaju

---

### 3. ARCMonitor (`arc_monitor.py`)

#### ✅ Implementirane Funkcionalnosti

- ✅ `get_arc_stats()` - Čitanje ARC statistika iz `/proc/spl/kstat/zfs/arcstats`
- ✅ Parsiranje ARC metrika (size, hits, misses, hit_rate, miss_rate)
- ✅ Fallback ako ARC stats file ne postoji

#### 🔍 Detaljna Analiza

**Jake Strane:**
- ✅ Dobro parsiranje ARC stats
- ✅ Fallback handling
- ✅ Permission error handling

**Problemi:**
- ⚠️ Zavisnost od `/proc/spl/kstat/zfs/arcstats` (može ne postojati na nekim sistemima)

**Ocena:** ✅ **90% kompletan** - Dobro implementirano

---

### 4. IOStatReader (`iostat_reader.py`)

#### ✅ Implementirane Funkcionalnosti

- ✅ `get_pool_iostat()` - Čitanje IO statistika preko `zpool iostat`
- ✅ Parsiranje read/write ops i bandwidth

#### 🔍 Detaljna Analiza

**Problemi:**

1. **Simplified Parsing:**
   ```python
   # Parsiranje je pojednostavljeno
   # Ne parsira detaljne per-vdev statistike
   ```
   **Problem:** Nedostaju detaljne per-drive statistike

**Ocena:** ⚠️ **70% kompletan** - Osnovne IO stats postoje, detaljne nedostaju

---

### 5. Storage API (`storage.py`)

#### ✅ Implementirani Endpoints

| Endpoint | Metoda | Status | Kompletnost |
|----------|--------|--------|-------------|
| `/api/storage/pool` | GET | ✅ | 80% |
| `/api/storage/pools` | GET | ✅ | 80% |
| `/api/storage/pool` | POST | ✅ | 80% |
| `/api/storage/pool/import` | POST | ✅ | 80% |
| `/api/storage/pool/{name}/scrub` | POST | ✅ | 80% |
| `/api/storage/pool/{name}/autotrim` | GET | ✅ | 80% |
| `/api/storage/pool/{name}/autotrim/enable` | POST | ✅ | 80% |
| `/api/storage/pool/{name}/autotrim/disable` | POST | ✅ | 80% |
| `/api/storage/pool/{name}/trim` | POST | ⚠️ | 20% (placeholder) |
| `/api/storage/arc` | GET | ✅ | 90% |
| `/api/storage/iostat` | GET | ✅ | 70% |

#### ❌ Nedostajući Endpoints

| Endpoint | Metoda | Prioritet | Plan |
|----------|--------|-----------|------|
| `/api/storage/array` | GET | 🔴 Visok | `array.md` |
| `/api/storage/array/drives` | GET | 🔴 Visok | `array.md` |
| `/api/storage/array/drives/{id}` | GET | 🔴 Visok | `array.md` |
| `/api/storage/array/drives/add` | POST | 🔴 Visok | `array-advanced.md` |
| `/api/storage/array/drives/{id}/replace` | POST | 🔴 Visok | `array-advanced.md` |
| `/api/storage/array/drives/{id}/remove` | POST | 🔴 Visok | `array-advanced.md` |
| `/api/storage/array/drives/{id}/offline` | POST | 🔴 Visok | `array-advanced.md` |
| `/api/storage/array/drives/{id}/online` | POST | 🔴 Visok | `array-advanced.md` |
| `/api/storage/array/drives/{id}/identify` | POST | 🟡 Srednji | `array.md` |
| `/api/storage/array/drives/{id}/smart` | GET | 🟡 Srednji | `array.md` |
| `/api/storage/array/rebuild` | POST | 🔴 Visok | `array-advanced.md` |
| `/api/storage/array/rebuild/status` | GET | 🔴 Visok | `array-advanced.md` |
| `/api/storage/array/trim` | POST | 🔴 Visok | `trim-management.md` |
| `/api/storage/array/trim/status` | GET | 🔴 Visok | `trim-management.md` |
| `/api/storage/array/trim/history` | GET | 🟡 Srednji | `trim-management.md` |
| `/api/storage/array/raid/convert` | POST | 🟡 Srednji | `array-advanced.md` |
| `/api/storage/array/forklift/start` | POST | 🟢 Nizak | `array-forklift.md` |
| `/api/storage/array/metrics` | GET | 🔴 Visok | `array.md` |

**Ocena:** ⚠️ **40% kompletan** - Samo osnovni endpointi, napredni nedostaju

---

### 6. Frontend Storage Page (`Storage.jsx`)

#### ✅ Implementirano

- ✅ Osnovni layout (header, stripes table)
- ✅ Pool status prikaz (hardcoded placeholder data)
- ✅ Stripes table (hardcoded placeholder data)
- ✅ Trim button (poziva API)
- ✅ Refresh button (sinkronizacija sa backend-om)

#### ❌ Nedostaje

**Array Dashboard:**
- ❌ Status LED (green/amber/red)
- ❌ RAID type badge
- ❌ Usage bar (Size/Used/Free/Reserved)
- ❌ Warning threshold indicators
- ❌ Real-time pool metrics

**Drive Grid:**
- ❌ Drive table (Device, Model/Serial, Role, Status, Temperature)
- ❌ Drive actions (Details, Identify, Mark Failed, Replace, Remove, SMART)
- ❌ Drive details modal
- ❌ Rebuild progress indicators

**Drive Management:**
- ❌ Add Drive wizard
- ❌ Replace Drive wizard
- ❌ Remove Drive dialog
- ❌ Take Offline / Bring Online dialogs

**Array Operacije:**
- ❌ Rebuild operacija UI
- ❌ TRIM operacija UI (samo button postoji)
- ❌ RAID conversion wizard
- ❌ Forklift upgrade wizard

**Automation:**
- ❌ Snapshot/writeback automation panel
- ❌ TRIM scheduler panel
- ❌ Cleanup schedule preview

**Alerts:**
- ❌ DEGRADED/FAULTED banners
- ❌ Threshold breach toasts
- ❌ Rebuild warnings

#### 🔍 Detaljna Analiza Koda

**Problemi:**

1. **Hardcoded Placeholder Data:**
   ```javascript
   const [poolStatus, setPoolStatus] = useState({
     name: 'pool0',
     size: 2 * 1024 * 1024 * 1024 * 1024,  // Hardcoded
     allocated: 256 * 1024 * 1024 * 1024,  // Hardcoded
     free: 1.75 * 1024 * 1024 * 1024 * 1024,  // Hardcoded
   })
   const [stripes, setStripes] = useState([...])  // Hardcoded placeholder
   ```
   **Problem:** Frontend koristi placeholder data umesto realnih podataka

2. **Nedostaje API Integracija:**
   - `handleRefresh()` poziva API ali ne parsira drive informacije
   - Nema integracije sa drive management endpoint-ima

3. **TODO Komentari:**
   ```javascript
   // TODO: Implement save configuration
   // TODO: Implement cancel configuration
   ```

**Ocena:** 🔴 **30% kompletan** - Samo osnovni layout, funkcionalnost nedostaje

---

### 7. Frontend Storage API Service (`storageAPI.js`)

#### ✅ Implementirano

- ✅ `getPoolStatus()` - Pool status
- ✅ `listPools()` - Lista pool-ova
- ✅ `createPool()` - Kreiranje pool-a
- ✅ `importPool()` - Import pool-a
- ✅ `startScrub()` - Scrub operacija
- ✅ `getAutotrimStatus()` - Autotrim status
- ✅ `enableAutotrim()` / `disableAutotrim()` - Autotrim management
- ✅ `manualTrim()` - Manual TRIM (poziva placeholder endpoint)
- ✅ `getARCStats()` - ARC statistike
- ✅ `getIOStats()` - IO statistike

#### ❌ Nedostaje

- ❌ `getArrayStatus()` - Array status
- ❌ `getDrives()` - Lista drive-ova
- ❌ `getDriveDetails()` - Detalji drive-a
- ❌ `addDrive()` - Dodavanje drive-a
- ❌ `replaceDrive()` - Zamena drive-a
- ❌ `removeDrive()` - Uklanjanje drive-a
- ❌ `offlineDrive()` / `onlineDrive()` - Drive online/offline
- ❌ `identifyDrive()` - Blink LED
- ❌ `getDriveSMART()` - SMART podaci
- ❌ `rebuildArray()` - Rebuild operacija
- ❌ `getRebuildStatus()` - Rebuild status
- ❌ `trimArray()` - TRIM operacija
- ❌ `getTrimStatus()` - TRIM status
- ❌ `getTrimHistory()` - TRIM history
- ❌ `convertRAID()` - RAID konverzija

**Ocena:** ⚠️ **50% kompletan** - Osnovni API servisi postoje, napredni nedostaju

---

## 📊 Gap Analysis

### Backend Gap Analysis

#### Kritični Nedostaci

1. **🔴 Drive Management - 0%**
   - Nema detekcije drive-ova u pool-u
   - Nema parsiranja `zpool status` za drive informacije
   - Nema metoda za add/remove/replace/offline/online
   - **Impact:** Frontend ne može prikazati drive grid

2. **🔴 Rebuild Operacije - 0%**
   - Nema rebuild operacije
   - Nema progress tracking-a
   - Nema status monitoring-a
   - **Impact:** Nemoguće dodati/zameniti drive-ove

3. **🔴 TRIM Operacije - 20%**
   - `manual_trim()` je samo placeholder
   - Nema stvarnog izvršavanja `zpool trim`
   - Nema progress tracking-a
   - Nema history tracking-a
   - **Impact:** TRIM se ne izvršava

4. **🔴 Pool Status Parsing - 40%**
   - `pool_status()` samo parsira osnovne state-ove
   - Ne parsira drive informacije
   - Ne parsira vdev informacije
   - Ne parsira errors/warnings
   - **Impact:** Nedostaju detaljne informacije za UI

#### Srednji Nedostaci

1. **🟡 RAID Conversion - 0%**
   - Nema metode za RAID konverziju
   - Nema validacije preuslova
   - **Impact:** Nemoguće konvertovati RAID0 ↔ RAID10

2. **🟡 Forklift Upgrade - 0%**
   - Nema forklift upgrade workflow-a
   - Nema step tracking-a
   - **Impact:** Nemoguće izvršiti forklift upgrade

3. **🟡 SMART Data - 0%**
   - Nema čitanja SMART podataka
   - Nema temperature monitoring-a
   - **Impact:** Nedostaju drive health informacije

### Frontend Gap Analysis

#### Kritični Nedostaci

1. **🔴 Array Dashboard - 30%**
   - Nema status LED
   - Nema usage bar
   - Nema warning indicators
   - Koristi placeholder data
   - **Impact:** Korisnik ne vidi realno stanje array-a

2. **🔴 Drive Grid - 0%**
   - Nema drive table
   - Nema drive actions
   - Nema drive details modal
   - **Impact:** Nemoguće upravljati drive-ovima

3. **🔴 Drive Management Wizards - 0%**
   - Nema Add Drive wizard-a
   - Nema Replace Drive wizard-a
   - Nema Remove Drive dialog-a
   - **Impact:** Nemoguće dodati/zameniti/ukloniti drive-ove

4. **🔴 Rebuild UI - 0%**
   - Nema rebuild progress UI
   - Nema rebuild status monitoring
   - **Impact:** Nemoguće pratiti rebuild operacije

5. **🔴 TRIM UI - 10%**
   - Samo button postoji
   - Nema progress tracking
   - Nema scheduler UI
   - Nema history view
   - **Impact:** TRIM funkcionalnost nedostaje

---

## 🔧 Tehnički Detalji

### 1. ZFS Pool Status Parsing

#### Trenutna Implementacija

```python
def pool_status(self, pool_name: str) -> Dict[str, Any]:
    result = self._run_command([self.zpool_cmd, "status", pool_name])
    status = {
        "name": pool_name,
        "status": "unknown",
        "state": "unknown",
        "output": result.stdout,  # Raw output
    }
    
    # Simplified parsing
    if "ONLINE" in result.stdout:
        status["state"] = "online"
    elif "DEGRADED" in result.stdout:
        status["state"] = "degraded"
    # ...
```

#### Problem

- Ne parsira drive informacije
- Ne parsira vdev strukturu
- Ne parsira errors/warnings
- Ne parsira rebuild progress

#### Potrebno Poboljšanje

```python
def pool_status(self, pool_name: str) -> Dict[str, Any]:
    # Treba parsirati:
    # - Pool state (ONLINE, DEGRADED, FAULTED, OFFLINE)
    # - Vdev struktura (stripe, mirror, raidz)
    # - Drive lista sa statusom
    # - Errors/warnings
    # - Rebuild/resilver progress
    # - Capacity informacije
```

**Prioritet:** 🔴 **Visok** - Potrebno za drive grid

---

### 2. Drive Detection

#### Trenutna Implementacija

**NEDOSTAJE** - Nema drive detection metode

#### Potrebna Implementacija

```python
def get_pool_drives(self, pool_name: str) -> List[Dict[str, Any]]:
    """
    Get list of drives in pool
    
    Returns:
        List of drive dictionaries with:
        - device: /dev/sda
        - role: data, cache, spare
        - status: ONLINE, DEGRADED, FAULTED, OFFLINE
        - serial: drive serial number
        - model: drive model
        - size: drive size
        - temperature: drive temperature (if available)
        - errors: read/write/checksum errors
    """
    # Parse "zpool status -v" output
    # Extract drive information
    # Get SMART data (optional)
    # Get temperature (optional)
```

**Prioritet:** 🔴 **Visok** - Potrebno za drive grid

---

### 3. TRIM Operacija

#### Trenutna Implementacija

```python
def manual_trim(self, pool_name: Optional[str] = None) -> None:
    logger.info(f"Manual TRIM requested for pool: {pool_name}")
    # Note: zpool trim command would be executed here
    # For now, we'll just log it
```

#### Problem

- TRIM se ne izvršava
- Nema progress tracking-a
- Nema history tracking-a

#### Potrebna Implementacija

```python
def manual_trim(self, pool_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform manual TRIM operation
    
    Returns:
        TRIM job information with:
        - job_id: Unique job ID
        - status: running, completed, failed
        - progress: 0-100
        - estimated_completion: ETA
    """
    # Execute: zpool trim pool_name
    # Start background job
    # Return job ID for progress tracking
    # Store in database for history
```

**Prioritet:** 🔴 **Visok** - TRIM je kritičan za SSD performanse

---

### 4. Rebuild Operacija

#### Trenutna Implementacija

**NEDOSTAJE** - Nema rebuild operacije

#### Potrebna Implementacija

```python
def rebuild_array(
    self,
    pool_name: str,
    operation: str,  # "add", "replace", "remove"
    drive_path: str,
    new_drive_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Rebuild array operation
    
    Returns:
        Rebuild job information with:
        - job_id: Unique job ID
        - status: queued, running, completed, failed
        - progress: 0-100
        - estimated_completion: ETA
        - speed: MB/s
    """
    # Execute appropriate zpool command:
    # - zpool add (for add)
    # - zpool replace (for replace)
    # - zpool remove (for remove)
    # Start background job
    # Monitor progress via "zpool status"
    # Return job ID for progress tracking
```

**Prioritet:** 🔴 **Visok** - Potrebno za drive management

---

### 5. Progress Tracking

#### Trenutna Implementacija

**NEDOSTAJE** - Nema progress tracking sistema

#### Potrebna Implementacija

```python
# Database model
class ArrayOperation(Base):
    id = Column(Integer, primary_key=True)
    operation_type = Column(String)  # "rebuild", "trim", "scrub"
    pool_name = Column(String)
    status = Column(String)  # "queued", "running", "completed", "failed"
    progress = Column(Integer)  # 0-100
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    # ...

# Manager method
def get_operation_status(self, job_id: int) -> Dict[str, Any]:
    """
    Get operation status
    
    Returns:
        Operation status with progress, ETA, etc.
    """
    # Query database
    # Parse zpool status for real-time progress
    # Return status
```

**Prioritet:** 🔴 **Visok** - Potrebno za real-time updates

---

## 📋 Implementacioni Plan

### Faza 1: Drive Detection & Parsing (Prioritet: 🔴 Visok)

**Cilj:** Omogućiti prikaz drive grid-a u frontend-u

**Backend Tasks:**
1. Implementirati `pool_status()` detaljno parsiranje
   - Parsirati vdev strukturu
   - Parsirati drive listu
   - Parsirati errors/warnings
   - Parsirati rebuild progress

2. Implementirati `get_pool_drives()` metodu
   - Detektovati drive-ove u pool-u
   - Ekstraktovati serial, model, size
   - Detektovati role (data, cache, spare)
   - Detektovati status (ONLINE, DEGRADED, etc.)

3. Implementirati `get_drive_info()` metodu
   - Detaljne informacije o drive-u
   - SMART podaci (opciono)
   - Temperatura (opciono)

**Frontend Tasks:**
1. Implementirati drive grid komponentu
2. Integrisati sa backend API-jem
3. Prikazati drive informacije

**Vremenski Okvir:** 1-2 nedelje

---

### Faza 2: TRIM Operacija (Prioritet: 🔴 Visok)

**Cilj:** Implementirati funkcionalnu TRIM operaciju

**Backend Tasks:**
1. Implementirati `pool_trim()` u ZFSUtils
   - Izvršiti `zpool trim` komandu
   - Start background job
   - Return job ID

2. Implementirati `trim_array()` u StorageManager
   - Wrapper za pool_trim
   - Job tracking
   - Error handling

3. Implementirati progress tracking
   - Database model za TRIM jobs
   - Status monitoring
   - History tracking

4. Implementirati TRIM scheduler
   - Cron job ili background task
   - Schedule management
   - Run history

**Frontend Tasks:**
1. Implementirati TRIM scheduler UI
2. Implementirati progress tracking
3. Implementirati history view

**Vremenski Okvir:** 1-2 nedelje

---

### Faza 3: Rebuild Operacije (Prioritet: 🔴 Visok)

**Cilj:** Omogućiti add/remove/replace drive operacije

**Backend Tasks:**
1. Implementirati `pool_add()` u ZFSUtils
   - `zpool add` komanda
   - Validacija
   - Error handling

2. Implementirati `pool_replace()` u ZFSUtils
   - `zpool replace` komanda
   - Validacija
   - Error handling

3. Implementirati `pool_remove()` u ZFSUtils
   - `zpool remove` komanda
   - Validacija (RAID level check)
   - Error handling

4. Implementirati rebuild progress tracking
   - Parsiranje `zpool status` za progress
   - Job tracking
   - ETA calculation

5. Implementirati `rebuild_array()` u StorageManager
   - Wrapper za pool operacije
   - Job orchestration
   - Progress monitoring

**Frontend Tasks:**
1. Implementirati Add Drive wizard
2. Implementirati Replace Drive wizard
3. Implementirati Remove Drive dialog
4. Implementirati rebuild progress UI

**Vremenski Okvir:** 2-3 nedelje

---

### Faza 4: Array Dashboard (Prioritet: 🟡 Srednji)

**Cilj:** Kompletan array dashboard sa real-time metrics

**Backend Tasks:**
1. Implementirati `get_array_metrics()` endpoint
   - Pool capacity
   - Used/Free/Reserved
   - Warning thresholds
   - Drive health summary

2. Implementirati WebSocket eventi
   - `array_updated`
   - `array_rebuild_progress_updated`
   - `array_trim_progress_updated`
   - `array_space_threshold_reached`

**Frontend Tasks:**
1. Implementirati status LED
2. Implementirati usage bar
3. Implementirati warning indicators
4. Implementirati real-time updates

**Vremenski Okvir:** 1-2 nedelje

---

### Faza 5: Napredne Operacije (Prioritet: 🟡 Srednji)

**Cilj:** RAID conversion i forklift upgrade

**Backend Tasks:**
1. Implementirati `convert_raid()` metodu
   - RAID0 → RAID10
   - RAID10 → RAID0
   - Validacija preuslova
   - Step tracking

2. Implementirati `forklift_upgrade()` workflow
   - Step-by-step tracking
   - State persistence
   - Health checks

**Frontend Tasks:**
1. Implementirati RAID conversion wizard
2. Implementirati forklift upgrade wizard

**Vremenski Okvir:** 2-3 nedelje

---

## 🐛 Identifikovani Problemi

### Kritični Problemi

1. **🔴 TRIM Ne Radi**
   - `manual_trim()` je samo placeholder
   - TRIM se ne izvršava
   - **Fix:** Implementirati `zpool trim` execution

2. **🔴 Nema Drive Detection**
   - Frontend ne može prikazati drive grid
   - **Fix:** Implementirati `get_pool_drives()` i detaljno parsiranje

3. **🔴 Nema Rebuild Operacije**
   - Nemoguće dodati/zameniti drive-ove
   - **Fix:** Implementirati rebuild operacije sa progress tracking-om

4. **🔴 Nema Progress Tracking**
   - Nema praćenja dugotrajnih operacija
   - **Fix:** Implementirati job tracking sistem

### Srednji Problemi

1. **🟡 Simplified Status Parsing**
   - `pool_status()` ne parsira detaljne informacije
   - **Fix:** Poboljšati parsiranje `zpool status` output-a

2. **🟡 Placeholder Data u Frontend-u**
   - Frontend koristi hardcoded data
   - **Fix:** Integrisati sa realnim API podacima

3. **🟡 Nema SMART Data**
   - Nedostaju drive health informacije
   - **Fix:** Implementirati SMART data čitanje

---

## 📈 Preporuke

### Prioritet 1 (MVP - 2-3 nedelje)

1. **Implementirati Drive Detection**
   - `get_pool_drives()` metoda
   - Detaljno parsiranje `zpool status`
   - Drive grid u frontend-u

2. **Implementirati TRIM Operaciju**
   - `pool_trim()` metoda
   - Job tracking
   - Progress monitoring

3. **Implementirati Rebuild Operacije**
   - `pool_add()`, `pool_replace()`, `pool_remove()`
   - Progress tracking
   - Add/Replace wizards u frontend-u

### Prioritet 2 (1-2 nedelje)

1. **Poboljšati Status Parsing**
   - Detaljno parsiranje `zpool status`
   - Vdev struktura
   - Errors/warnings

2. **Implementirati Array Dashboard**
   - Status LED
   - Usage bar
   - Real-time metrics

### Prioritet 3 (2-3 nedelje)

1. **Implementirati RAID Conversion**
   - `convert_raid()` metoda
   - Conversion wizard

2. **Implementirati Forklift Upgrade**
   - `forklift_upgrade()` workflow
   - Step tracking

---

## 📊 Metrije

### Backend

- **Ukupno Linija Koda:** ~1,200 linija
- **Implementirane Metode:** 25+
- **Nedostajuće Metode:** 30+
- **Code Coverage:** N/A (nema testova)

### Frontend

- **Ukupno Linija Koda:** ~360 linija
- **Komponente:** 1 stranica (Storage.jsx)
- **Nedostajuće Komponente:** 10+ (wizards, dialogs, grids)

---

## ✅ Zaključak

Storage/Array modul ima **solidnu osnovu** sa dobrim ZFS integracijama, ali **nedostaju kritične funkcionalnosti** za production-ready sistem:

1. **🔴 Drive Management** - Potpuno nedostaje (0%)
2. **🔴 Rebuild Operacije** - Potpuno nedostaje (0%)
3. **🔴 TRIM Operacija** - Samo placeholder (20%)
4. **🔴 Progress Tracking** - Potpuno nedostaje (0%)
5. **🔴 Array Dashboard** - Djelomično (30%)

**Ukupna Ocena:** 🔴 **40% kompletan**

**Preporuka:** Fokusirati se na **Prioritet 1 (MVP)** - Drive Detection, TRIM, i Rebuild operacije su kritične za funkcionalnost sistema.

---

*Dokument kreiran na osnovu detaljne analize Storage/Array modula*

