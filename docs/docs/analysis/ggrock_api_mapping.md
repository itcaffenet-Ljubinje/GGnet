# ggRock API Mapping & Gap Analysis

## Pregled

Ovaj dokument mapira originalni ggRock API (iz dekompajliranog `GgRock.Api.dll`) sa našim planovima i trenutnom implementacijom u ggNET2 projektu.

**Izvori:**
- Dekompajlirani `GgRock.Api.dll` (C:\Users\SERVER-PC\Desktop\GgRock_decompiled)
- `ANALIZA_FUNKCIONALNOSTI.md` - Analiza funkcionalnosti
- Naši frontend planovi u `docs/frontend/`
- Trenutna implementacija u `app/backend/api/`

---

## 1. Machines API (`/api/machines`)

### Originalni ggRock Endpoints

**Controller:** `bnZcCT3V8L9bxj4BEgd` (MachinesController)
**Autorizacija:** `[Authorize(Roles = "Admin")]`

| Endpoint | Metoda | Opis | Status u ggNET2 |
|----------|--------|------|-----------------|
| `/api/machines` | GET | Lista mašina | ✅ Implementirano |
| `/api/machines/{id}` | GET | Detalji mašine | ✅ Implementirano |
| `/api/machines` | POST | Kreiranje mašine | ✅ Implementirano |
| `/api/machines/{id}` | PUT | Ažuriranje mašine | ✅ Implementirano |
| `/api/machines/{id}` | DELETE | Brisanje mašine | ✅ Implementirano |
| `/api/machines/{id}/restart` | POST | Restart mašine | ✅ Implementirano |
| `/api/machines/restart` | POST | Bulk restart | ⚠️ **Nedostaje** |
| `/api/machines/{id}/shutdown` | POST | Shutdown mašine | ⚠️ **Nedostaje** |
| `/api/machines/shutdown` | POST | Bulk shutdown | ⚠️ **Nedostaje** |
| `/api/machines/{id}/wake` | POST | Wake mašine | ⚠️ **Nedostaje** |
| `/api/machines/{id}/turnOn` | POST | Turn on mašine | ⚠️ **Nedostaje** |
| `/api/machines/wake` | POST | Bulk wake | ⚠️ **Nedostaje** |
| `/api/machines/turnOn` | POST | Bulk turn on | ⚠️ **Nedostaje** |

### DTO Modeli

**MachineType Enum:**
- `PC` - Fizički računari
- `VM` - Virtuelne mašine

**MachineState Enum:**
- `Offline` - Mašina je offline
- `Booting` - Mašina se pokreće
- `Active` - Mašina je aktivna

**MachineAction Enum:**
- `Restart`
- `Shutdown`

### Gap Analysis

**Nedostaju:**
1. ✅ Bulk operacije (restart, shutdown, wake, turnOn) - **Planirano u `machines-implementation.md`**
2. ✅ Wake/Turn On funkcionalnost - **Planirano u `machines-implementation.md`**
3. ⚠️ Hardware info u DTO (NIC, GPU, CPU, motherboard) - **Planirano u `machines-implementation.md`**
4. ⚠️ Snapshot state metadata - **Planirano u `machines-implementation.md`**
5. ⚠️ Keep Writebacks toggle - **Planirano u `machines-implementation.md`**

**Prioritet:** Visok - Bulk operacije su kritične za UX

---

## 2. VMs API (`/api/vms`)

### Originalni ggRock Endpoints

**Controller:** `MFRdoM3L4Mb8R7RTxLe` (VMsController)
**Autorizacija:** `[Authorize(Roles = "Admin")]`

| Endpoint | Metoda | Opis | Status u ggNET2 |
|----------|--------|------|-----------------|
| `/api/vms` | GET | Lista VM-ova | ✅ Implementirano |
| `/api/vms/{machineId}` | GET | Detalji VM-a | ✅ Implementirano |
| `/api/vms/{machineId}` | PUT | Ažuriranje VM-a | ✅ Implementirano |
| `/api/vms/{machineId}/start` | POST | Start VM-a | ✅ Implementirano |
| `/api/vms/{machineId}/stop` | POST | Stop VM-a | ✅ Implementirano |
| `/api/vms/{machineId}/reset` | POST | Reset VM-a | ✅ Implementirano |
| `/api/vms/{machineId}/remote` | POST | Remote control URL | ⚠️ **Nedostaje** |
| `/api/vms/host` | GET | Host info | ⚠️ **Nedostaje** |
| `/api/vms/bridge` | POST | Bridge reconfiguration | ⚠️ **Nedostaje** |

### Gap Analysis

**Nedostaju:**
1. ✅ Remote control URL generisanje (noVNC) - **Planirano u `virtual-machines-advanced.md`**
2. ✅ Bridge reconfiguration - **Planirano u `virtual-machines-advanced.md`**
3. ⚠️ Host info endpoint - **Koristi se za resource monitoring**

**Prioritet:** Srednji - Remote control je važan za UX

---

## 3. Images API (`/api/images`)

### Originalni ggRock Endpoints

**Controller:** `j2SNtvV48GCChTJF4pV` (ImagesController)
**Autorizacija:** `[Authorize(Roles = "Admin")]`

| Endpoint | Metoda | Opis | Status u ggNET2 |
|----------|--------|------|-----------------|
| `/api/images` | GET | Lista slika | ✅ Implementirano |
| `/api/images/{id}` | GET | Detalji slike | ✅ Implementirano |
| `/api/images` | POST | Kreiranje slike | ✅ Implementirano |
| `/api/images/{id}` | PUT | Ažuriranje slike | ✅ Implementirano |
| `/api/images/{id}` | DELETE | Brisanje slike | ✅ Implementirano |
| `/api/images/remote` | GET | Remote images list | ⚠️ **Nedostaje** |
| `/api/images/remote/{imageUuid}/download` | POST | Download remote image | ⚠️ **Nedostaje** |

### DTO Modeli

**GgImageBootMode Enum:**
- `Legacy = 0`
- `Uefi = 10`

### Gap Analysis

**Nedostaju:**
1. ✅ Remote image download - **Planirano u `images-implementation.md`**
2. ⚠️ Snapshot timeline endpoint - **Planirano u `images-implementation.md`**
3. ⚠️ Writeback management endpoint - **Planirano u `images-implementation.md`**
4. ⚠️ Backup/restore endpoints - **Planirano u `images-implementation.md`**
5. ⚠️ Bulk operations - **Planirano u `images-implementation.md`**

**Prioritet:** Visok - Snapshot i writeback management su kritični

---

## 4. Array API (`/api/array`)

### Originalni ggRock Endpoints

**Controller:** `hI7MjWV2HTERV83Cy14` (ArrayController)
**Autorizacija:** `[Authorize(Roles = "Admin")]`

| Endpoint | Metoda | Opis | Status u ggNET2 |
|----------|--------|------|-----------------|
| `/api/array` | GET | Array status | ⚠️ **Djelomično** (storage API) |
| `/api/array/rebuild` | POST | Rebuild array | ⚠️ **Nedostaje** |
| `/api/array/trim` | POST | TRIM operation | ⚠️ **Nedostaje** |
| `/api/array/drives` | GET | Lista drive-ova | ⚠️ **Nedostaje** |
| `/api/array/drives/{id}/add` | POST | Add drive | ⚠️ **Nedostaje** |
| `/api/array/drives/{id}/remove` | POST | Remove drive | ⚠️ **Nedostaje** |
| `/api/array/drives/{id}/replace` | POST | Replace drive | ⚠️ **Nedostaje** |
| `/api/array/raid/convert` | POST | RAID conversion | ⚠️ **Nedostaje** |

### Gap Analysis

**Nedostaju:**
1. ✅ Array rebuild operacije - **Planirano u `array-advanced.md`**
2. ✅ TRIM operacije - **Planirano u `trim-management.md`**
3. ✅ Drive management (add/remove/replace) - **Planirano u `array-advanced.md`**
4. ✅ RAID conversion - **Planirano u `array-advanced.md`**
5. ⚠️ Progress tracking za rebuild/trim - **Planirano u `array-advanced.md`**
6. ⚠️ Space threshold monitoring - **Planirano u `array-automation.md`**

**Prioritet:** Visok - Array operacije su kritične za storage management

---

## 5. Settings API (`/api/settings`)

### Originalni ggRock Endpoints

**Controller:** N/A (različiti kontroleri)
**Autorizacija:** `[Authorize(Roles = "Admin")]`

| Endpoint | Metoda | Opis | Status u ggNET2 |
|----------|--------|------|-----------------|
| `/api/settings` | GET | Lista postavki | ✅ Implementirano |
| `/api/settings/{key}` | GET | Get postavka | ✅ Implementirano |
| `/api/settings/{key}` | PUT | Update postavka | ✅ Implementirano |
| `/api/settings/general` | GET/PUT | General settings | ⚠️ **Nedostaje** |
| `/api/settings/network` | GET/PUT | Network settings | ⚠️ **Nedostaje** |
| `/api/settings/storage` | GET/PUT | Storage settings | ⚠️ **Nedostaje** |
| `/api/settings/security` | GET/PUT | Security settings | ⚠️ **Nedostaje** |

### Gap Analysis

**Nedostaju:**
1. ✅ Structured settings endpoints - **Planirano u `settings-implementation.md`**
2. ⚠️ RAM allocation endpoint - **Planirano u `settings-implementation.md`**
3. ⚠️ Network bridge auto-config - **Planirano u `settings-implementation.md`**
4. ⚠️ Retention settings - **Planirano u `settings-implementation.md`**
5. ⚠️ Secure boot settings - **Planirano u `settings-implementation.md`**

**Prioritet:** Visok - Settings su kritični za konfiguraciju sistema

---

## 6. Toolchain API (`/api/toolchain`)

### Originalni ggRock Endpoints

**Controller:** `dhbRQW3Ci9OuJaKLjlt` (ToolchainController)
**Autorizacija:** `[Authorize(Roles = "Admin")]`

| Endpoint | Metoda | Opis | Status u ggNET2 |
|----------|--------|------|-----------------|
| `/api/toolchain/setup/{imagePath}` | POST | Setup toolchain | ❌ **Nije relevantno** |
| `/api/toolchain/injectNic` | POST | Inject NIC drivers | ❌ **Nije relevantno** |
| `/api/toolchain/networkDrivers` | POST | Network drivers | ❌ **Nije relevantno** |
| `/api/toolchain/options` | GET | Toolchain options | ❌ **Nije relevantno** |
| `/api/toolchain/nic` | GET | NIC info | ❌ **Nije relevantno** |
| `/api/toolchain/state` | GET | Toolchain state | ❌ **Nije relevantno** |
| `/api/toolchain/version` | GET | Toolchain version | ❌ **Nije relevantno** |
| `/api/toolchain/config` | GET | Toolchain config | ❌ **Nije relevantno** |

**Napomena:** Toolchain API je specifičan za Windows client deployment i nije relevantan za naš Linux-based sistem.

---

## 7. Scheduler API (`/api/scheduler`)

### Originalni ggRock Endpoints

**Controller:** N/A (identifikovan kroz SignalR evente)
**Autorizacija:** `[Authorize(Roles = "Admin")]`

| Endpoint | Metoda | Opis | Status u ggNET2 |
|----------|--------|------|-----------------|
| `/api/scheduler/jobs` | GET | Lista job-ova | ⚠️ **Nedostaje** |
| `/api/scheduler/jobs` | POST | Kreiranje job-a | ⚠️ **Nedostaje** |
| `/api/scheduler/jobs/{id}` | GET | Detalji job-a | ⚠️ **Nedostaje** |
| `/api/scheduler/jobs/{id}` | PUT | Ažuriranje job-a | ⚠️ **Nedostaje** |
| `/api/scheduler/jobs/{id}` | DELETE | Brisanje job-a | ⚠️ **Nedostaje** |
| `/api/scheduler/jobs/{id}/run` | POST | Run job now | ⚠️ **Nedostaje** |
| `/api/scheduler/history` | GET | Job history | ⚠️ **Nedostaje** |

### Gap Analysis

**Nedostaju:**
1. ✅ Scheduler API - **Planirano u `scheduler-implementation.md`**
2. ⚠️ Job CRUD operacije - **Planirano u `scheduler-implementation.md`**
3. ⚠️ Job execution - **Planirano u `scheduler-implementation.md`**
4. ⚠️ History tracking - **Planirano u `scheduler-implementation.md`**

**Prioritet:** Srednji - Scheduler je važan ali nije kritičan za MVP

---

## 8. SignalR Hubs

### Originalni ggRock Hubs

| Hub | Route | Autorizacija | Status u ggNET2 |
|-----|-------|--------------|------------------|
| Admin Hub | `/hubs/admin` | `[Authorize(Roles = "Admin")]` | ⚠️ **Djelomično** (WebSocket hub) |
| Machine Hub | `/hubs/machine` | `[Authorize(Roles = "Machine")]` | ⚠️ **Djelomično** (WebSocket hub) |

### SignalR Eventi

**Machine Events:**
- `machine_updated` - ✅ Implementirano
- `machine_client_connection_updated` - ⚠️ **Nedostaje**
- `machine_boot_failed` - ⚠️ **Nedostaje**

**Image Events:**
- `image_updated` - ✅ Implementirano
- `image_import_updated` - ⚠️ **Nedostaje**
- `image_import_progress_updated` - ⚠️ **Nedostaje**
- `image_backup_restore_progress_updated` - ⚠️ **Nedostaje**
- `image_backup_restore_updated` - ⚠️ **Nedostaje**
- `image_download_progress_updated` - ⚠️ **Nedostaje**

**Array Events:**
- `array_updated` - ⚠️ **Nedostaje**
- `array_rebuild_progress_updated` - ⚠️ **Nedostaje**
- `array_trim_progress_updated` - ⚠️ **Nedostaje**
- `array_space_threshold_reached` - ⚠️ **Nedostaje**

**VM Events:**
- `vm_info_updated` - ⚠️ **Nedostaje**

**Writeback Events:**
- `writeback_info_updated` - ⚠️ **Nedostaje**
- `writeback_states_updated` - ⚠️ **Nedostaje**

**System Events:**
- `server_ram_updated` - ⚠️ **Nedostaje**
- `version_info_updated` - ⚠️ **Nedostaje**
- `subscription_updated` - ❌ **Nije relevantno**
- `features_updated` - ⚠️ **Nedostaje**
- `activity_log_created` - ⚠️ **Nedostaje**

**Scheduler Events:**
- `scheduled_machine_actions` - ⚠️ **Nedostaje**
- `scheduled_machine_boot_states` - ⚠️ **Nedostaje**
- `managed_machine_action_executions` - ⚠️ **Nedostaje**
- `next_managed_machine_action_executions` - ⚠️ **Nedostaje**

**Toolchain Events:**
- `toolchain_download_progress_updated` - ❌ **Nije relevantno**
- `toolchain_state_updated` - ❌ **Nije relevantno**
- `toolchain_version_updated` - ❌ **Nije relevantno**

**Shell Events:**
- `shell_command_execution_progress` - ⚠️ **Nedostaje**

### Gap Analysis

**Nedostaju:**
1. ✅ Progress tracking eventi - **Planirano u planovima**
2. ⚠️ Real-time array updates - **Planirano u `array-advanced.md`**
3. ⚠️ Real-time VM updates - **Planirano u `virtual-machines-advanced.md`**
4. ⚠️ Activity logging events - **Koristi se za audit trail**

**Prioritet:** Visok - Real-time updates su kritični za UX

---

## 9. Server Commands API (`/api/server/commands`)

### Originalni ggRock Endpoints

**Controller:** `DKAyn03ewySI3YXhiju` (ServerCommandsController)
**Autorizacija:** `[Authorize(Roles = "Admin")]`

| Endpoint | Metoda | Opis | Status u ggNET2 |
|----------|--------|------|-----------------|
| `/api/server/commands/lastExecution` | GET | Last command execution | ⚠️ **Nedostaje** |
| `/api/server/commands/run` | POST | Run shell command | ⚠️ **Nedostaje** |
| `/api/server/commands/cancel` | POST | Cancel command | ⚠️ **Nedostaje** |

**Napomena:** Shell command execution je koristan za debugging i maintenance, ali nije kritičan za MVP.

---

## 10. Users API (`/api/users`)

### Originalni ggRock Endpoints

**Controller:** `zixghZ3Bi7oTf0x79Z9` (UsersController)
**Autorizacija:** `[Authorize]`

| Endpoint | Metoda | Opis | Status u ggNET2 |
|----------|--------|------|-----------------|
| `/api/users` | GET | Lista korisnika | ⚠️ **Nedostaje** |
| `/api/users` | POST | Kreiranje korisnika | ⚠️ **Nedostaje** |
| `/api/users/{id}` | GET | Detalji korisnika | ⚠️ **Nedostaje** |
| `/api/users/{id}` | PUT | Ažuriranje korisnika | ⚠️ **Nedostaje** |
| `/api/users/{id}` | DELETE | Brisanje korisnika | ⚠️ **Nedostaje** |

**Napomena:** User management koristi ASP.NET Core Identity. Za naš sistem, možemo implementirati jednostavniji pristup ili koristiti postojeći authentication sistem.

---

## Prioriteti Implementacije

### Visok Prioritet (MVP)

1. **Machines API - Bulk operacije**
   - `/api/machines/restart` (POST)
   - `/api/machines/shutdown` (POST)
   - `/api/machines/wake` (POST)
   - `/api/machines/turnOn` (POST)

2. **Machines API - Hardware info**
   - Proširiti DTO sa hardware informacijama
   - Snapshot state metadata

3. **Images API - Snapshot & Writeback management**
   - Snapshot timeline endpoint
   - Writeback management endpoint
   - Bulk operations

4. **Array API - Core operacije**
   - `/api/array/rebuild` (POST)
   - `/api/array/trim` (POST)
   - `/api/array/drives` (GET)
   - Progress tracking

5. **Settings API - Structured endpoints**
   - `/api/settings/general` (GET/PUT)
   - `/api/settings/network` (GET/PUT)
   - `/api/settings/storage` (GET/PUT)
   - `/api/settings/security` (GET/PUT)

6. **SignalR - Progress tracking**
   - Array rebuild/trim progress
   - Image import/backup progress
   - VM operations progress

### Srednji Prioritet

1. **VMs API - Remote control**
   - `/api/vms/{machineId}/remote` (POST)
   - `/api/vms/bridge` (POST)

2. **Scheduler API**
   - Job CRUD operacije
   - Job execution
   - History tracking

3. **Activity Logging**
   - Activity log endpoint
   - Real-time activity events

### Nizak Prioritet

1. **Server Commands API**
   - Shell command execution
   - Command history

2. **Users API**
   - User management (ako je potrebno)

---

## Preporuke

1. **Fokus na MVP funkcionalnosti** - Implementirati visok prioritet endpointe prvo
2. **Real-time updates** - SignalR eventi su kritični za dobar UX
3. **Progress tracking** - Sve dugotrajne operacije trebaju progress tracking
4. **Bulk operacije** - Korisnici očekuju bulk operacije za efficiency
5. **Structured settings** - Settings API treba biti strukturiran prema frontend planovima

---

## Reference

- `ANALIZA_FUNKCIONALNOSTI.md` - Kompletna analiza originalnog ggRock API-ja
- `docs/frontend/machines-implementation.md` - Machines implementation plan
- `docs/frontend/images-implementation.md` - Images implementation plan
- `docs/frontend/settings-implementation.md` - Settings implementation plan
- `docs/frontend/array-advanced.md` - Array advanced operations plan
- `docs/frontend/scheduler-implementation.md` - Scheduler implementation plan

---

*Dokument kreiran na osnovu dekompajliranog `GgRock.Api.dll` i naših frontend planova*

