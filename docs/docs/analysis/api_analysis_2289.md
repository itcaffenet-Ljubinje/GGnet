# API Analiza - Verzija 2289

**Datum:** 2025-11-18  
**Verzija:** 0.1.2289.2303  
**Status:** ✅ Kompletna

---

## 📊 Statistika

- **API Endpoint-i:** 199
- **Kontroleri:** 26
- **SignalR Hub-ovi:** 5
- **DTO Modeli:** 5+ (obfuscated, ali route pattern-i su čitljivi)

**Napomena:** Kontroleri su obfuscated (imaju nasumična imena), ali route pattern-i su čitljivi i mogu se koristiti za identifikaciju funkcionalnosti.

---

## 🎯 API Kontroleri (Identifikovani po Route Pattern-u)

### 1. Server Management (`api/server`)

**Route:** `api/server`

**Endpoint-i:**
- `GET /api/server/ping` - Ping server
- `GET /api/server` - Server info
- `GET /api/server/public` - Public server info
- `GET /api/server/ram` - RAM info
- `PUT /api/server/ram` - Update RAM
- `GET /api/server/services` - List services
- `GET /api/server/services/{serviceId}` - Service info
- `POST /api/server/services/{serviceId}/restart` - Restart service
- `POST /api/server/reboot` - Reboot server

**Funkcionalnost:** Upravljanje serverom, servisima, RAM-om

---

### 2. Server Updates (`api/server/updates`)

**Route:** `api/server/updates`

**Endpoint-i:**
- `GET /api/server/updates` - List updates
- `POST /api/server/updates/{updateId}/install` - Install update
- `GET /api/server/updates/progress` - Update progress

**Funkcionalnost:** Upravljanje server update-ima

---

### 3. Server Commands (`api/server/commands`)

**Route:** `api/server/commands`

**Endpoint-i:**
- `GET /api/server/commands` - List commands
- `GET /api/server/commands/lastExecution` - Last execution
- `POST /api/server/commands/run` - Run command
- `POST /api/server/commands/cancel` - Cancel command

**Funkcionalnost:** Izvršavanje server komandi

---

### 4. Release Streams (`api/server/releaseStreams`)

**Route:** `api/server/releaseStreams`

**Endpoint-i:**
- `GET /api/server/releaseStreams` - List release streams
- `POST /api/server/releaseStreams/{name}/select` - Select release stream

**Funkcionalnost:** Upravljanje release stream-ovima

---

### 5. Machines (`api/machines`)

**Route:** `api/machines`

**Endpoint-i:**
- `GET /api/machines` - List machines
- `GET /api/machines/client` - Client machines
- `POST /api/machines/batch` - Batch operations
- `PUT /api/machines/{id}` - Update machine
- `DELETE /api/machines/{id}` - Delete machine
- `POST /api/machines/{id}/restart` - Restart machine
- `POST /api/machines/restart` - Restart multiple machines
- `POST /api/machines/{id}/shutdown` - Shutdown machine
- `POST /api/machines/shutdown` - Shutdown multiple machines
- `POST /api/machines/wake` - Wake machines
- `POST /api/machines/turnOn` - Turn on machines
- `POST /api/machines/{id}/wake` - Wake machine
- `POST /api/machines/{id}/turnOn` - Turn on machine
- `GET /api/machines/{machineId}/hardware` - Hardware info
- `POST /api/machines/{machineId}/hardware/displaysettings` - Update display settings
- `GET /api/machines/{machineId}/hardware/displaysettings` - Get display settings
- `POST /api/machines/displaysettings` - Update display settings (bulk)
- `POST /api/machines/{id}/writebacks/{writebackPath}/keep` - Keep writeback
- `POST /api/machines/{id}/writebacks/keep` - Keep all writebacks
- `DELETE /api/machines/{id}/writebacks/{writebackPath}` - Delete writeback
- `PUT /api/machines/{id:guid}/scheduledBehavior/{behaviorId:guid}` - Set scheduled behavior
- `DELETE /api/machines/{id:guid}/scheduledBehavior` - Remove scheduled behavior

**Funkcionalnost:** Upravljanje fizičkim mašinama, hardware, writeback-ovi, scheduled behaviors

---

### 6. Images (`api/images`)

**Route:** `api/images`

**Endpoint-i:**
- `GET /api/images` - List images
- `GET /api/images/{path}` - Get image
- `POST /api/images` - Create image
- `PUT /api/images/{path}` - Update image
- `DELETE /api/images/{path}` - Delete image
- `POST /api/images/{path}/snapshots/{snapshotPath}/default` - Set default snapshot
- `POST /api/images/{path}/snapshots/{snapshotPath}/lock` - Lock snapshot
- `DELETE /api/images/{path}/snapshots/{snapshotPath}` - Delete snapshot
- `GET /api/images/imported` - List imported images
- `POST /api/images/imported/{importId}/cancel` - Cancel import
- `POST /api/images/imported/{importId}/finish` - Finish import
- `POST /api/images/import/vhd` - Import VHD
- `POST /api/images/import` - Import image
- `POST /api/images/{sourceSnapshotPath}/copy` - Copy image
- `DELETE /api/images/{path}/writebacks` - Delete writebacks
- `GET /api/images/remote` - List remote images
- `POST /api/images/remote/{imageUuid}/download` - Download remote image

**Funkcionalnost:** Upravljanje image-ima, snapshot-ovi, import/export, remote images

---

### 7. Batch Image Operations (`api/batchImageOperations`)

**Route:** `api/batchImageOperations`

**Endpoint-i:**
- `GET /api/batchImageOperations/history` - Operation history
- `POST /api/batchImageOperations/local/restore/images` - Local restore images
- `POST /api/batchImageOperations/remote/restore/images` - Remote restore images
- `GET /api/batchImageOperations/local/backup/images` - Local backup images
- `GET /api/batchImageOperations/remote/backup/images` - Remote backup images
- `POST /api/batchImageOperations/local/backup` - Local backup
- `POST /api/batchImageOperations/remote/backup` - Remote backup
- `POST /api/batchImageOperations/local/restore` - Local restore
- `POST /api/batchImageOperations/remote/restore` - Remote restore
- `POST /api/batchImageOperations/local/test` - Local test
- `POST /api/batchImageOperations/remote/test` - Remote test

**Funkcionalnost:** Bulk operacije sa image-ima (backup, restore, test)

---

### 8. VMs (`api/vms`)

**Route:** `api/vms`

**Endpoint-i:**
- `GET /api/vms/host` - VM host info
- `POST /api/vms/{machineId}/reset` - Reset VM
- `POST /api/vms/{machineId}/start` - Start VM
- `POST /api/vms/{machineId}/stop` - Stop VM
- `POST /api/vms` - Create VM
- `GET /api/vms/{machineId}/info` - VM info
- `PUT /api/vms/{machineId}` - Update VM
- `POST /api/vms/{machineId}/remote` - Remote access
- `POST /api/vms/bridge` - Create bridge

**Funkcionalnost:** Upravljanje virtuelnim mašinama

---

### 9. Storage Array (`api/array`)

**Route:** `api/array`

**Endpoint-i:**
- `GET /api/array` - Array info
- `POST /api/array` - Create array
- `POST /api/array/extend` - Extend array
- `POST /api/array/drives/{driveUuid}/online` - Drive online
- `POST /api/array/drives/{driveUuid}/offline` - Drive offline
- `POST /api/array/drives` - Add drives
- `POST /api/array/drives/{oldDriveUuid}/replace` - Replace drive
- `DELETE /api/array/drives/{driveUuid}` - Remove drive
- `POST /api/array/export` - Export array
- `DELETE /api/array` - Delete array
- `GET /api/array/stripes/lookup` - Lookup stripes
- `POST /api/array/trim/resume` - Resume TRIM
- `POST /api/array/trim/suspend` - Suspend TRIM
- `POST /api/array/trim/run` - Run TRIM
- `POST /api/array/trim/cancel` - Cancel TRIM

**Funkcionalnost:** Upravljanje ZFS storage array-om, drive-ovi, TRIM operacije

---

### 10. Drives (`api/drives`)

**Route:** `api/drives`

**Endpoint-i:**
- `GET /api/drives/{driveName}/smart` - SMART data
- `GET /api/drives/free` - Free drives

**Funkcionalnost:** Upravljanje fizičkim drive-ovima

---

### 11. Partitions (`api/partitions`)

**Route:** `api/partitions`

**Endpoint-i:**
- `GET /api/partitions` - List partitions
- `GET /api/partitions/{partitionName}/vhds` - Partition VHDs

**Funkcionalnost:** Upravljanje particijama

---

### 12. Schedule (`api/schedule`)

**Route:** `api/schedule`

**Endpoint-i:**
- `GET /api/schedule/machineActions/{id:guid}/occurrences` - Machine action occurrences
- `GET /api/schedule/machineActions` - List machine actions
- `GET /api/schedule/machineActions/{id:guid}` - Get machine action
- `POST /api/schedule/machineActions` - Create machine action
- `PUT /api/schedule/machineActions/{id:guid}` - Update machine action
- `DELETE /api/schedule/machineActions/{id:guid}/occurrences/{date}` - Delete occurrence
- `POST /api/schedule/machineActions/{id:guid}/occurrences/replaceSingle/{date}` - Replace single occurrence
- `POST /api/schedule/machineActions/{id:guid}/occurrences/replaceAllFrom/{date}` - Replace all from date
- `DELETE /api/schedule/machineActions/{id:guid}` - Delete machine action
- `GET /api/schedule/machineBootStates/{id:guid}/occurrences` - Machine boot state occurrences
- `GET /api/schedule/machineBootStates` - List machine boot states
- `GET /api/schedule/machineBootStates/{id:guid}` - Get machine boot state
- `POST /api/schedule/machineBootStates` - Create machine boot state
- `PUT /api/schedule/machineBootStates/{id:guid}` - Update machine boot state
- `DELETE /api/schedule/machineBootStates/{id:guid}/occurrences/{date}` - Delete occurrence
- `POST /api/schedule/machineBootStates/{id:guid}/occurrences/replaceSingle/{date}` - Replace single occurrence
- `POST /api/schedule/machineBootStates/{id:guid}/occurrences/replaceAllFrom/{date}` - Replace all from date
- `DELETE /api/schedule/machineBootStates/{id:guid}` - Delete machine boot state
- `POST /api/schedule/copyAllEntries` - Copy all entries
- `GET /api/schedule/occurrences` - List occurrences
- `GET /api/schedule/executions` - List executions
- `GET /api/schedule/executions/nextScheduled` - Next scheduled execution
- `GET /api/schedule/executions/closestForMachine/{machineId:guid}` - Closest execution for machine
- `GET /api/schedule/config` - Get config
- `GET /api/schedule/config/default` - Get default config
- `PATCH /api/schedule/config` - Update config
- `GET /api/schedule/behaviors` - List behaviors
- `GET /api/schedule/behaviors/{id:guid}` - Get behavior
- `POST /api/schedule/behaviors` - Create behavior
- `PATCH /api/schedule/behaviors/{id:guid}` - Update behavior
- `DELETE /api/schedule/behaviors/{id:guid}` - Delete behavior

**Funkcionalnost:** Scheduling sistem - machine actions, boot states, behaviors, executions

---

### 13. Toolchain (`api/toolchain`)

**Route:** `api/toolchain`

**Endpoint-i:**
- `POST /api/toolchain/setup/{imagePath}` - Setup toolchain
- `POST /api/toolchain/injectNic` - Inject NIC
- `POST /api/toolchain/networkDrivers` - Network drivers
- `GET /api/toolchain/options` - Toolchain options
- `GET /api/toolchain/nic` - NIC info
- `GET /api/toolchain/state` - Toolchain state
- `POST /api/toolchain/cancel` - Cancel toolchain
- `POST /api/toolchain/finish` - Finish toolchain
- `POST /api/toolchain/save` - Save toolchain
- `POST /api/toolchain/fail` - Fail toolchain
- `POST /api/toolchain/logs` - Toolchain logs
- `GET /api/toolchain/version` - Toolchain version
- `GET /api/toolchain/config` - Get config
- `PATCH /api/toolchain/config` - Update config

**Funkcionalnost:** Toolchain setup i upravljanje

---

### 14. Boot (`boot`)

**Route:** `boot`

**Endpoint-i:**
- `GET /boot/script` - Boot script

**Funkcionalnost:** iPXE boot script generation

---

### 15. Settings (`api/settings`)

**Route:** `api/settings`

**Endpoint-i:**
- `GET /api/settings/images` - Image settings
- `PUT /api/settings/images` - Update image settings
- `GET /api/settings/trim` - TRIM settings
- `PUT /api/settings/trim` - Update TRIM settings
- `GET /api/settings/network` - Network settings
- `PUT /api/settings/network` - Update network settings
- `GET /api/settings/boot` - Boot settings
- `PUT /api/settings/boot` - Update boot settings
- `GET /api/settings/auth` - Auth settings
- `PATCH /api/settings/auth` - Update auth settings

**Funkcionalnost:** System settings (images, TRIM, network, boot, auth)

---

### 16. Clients (`api/clients`)

**Route:** `api/clients`

**Endpoint-i:**
- `POST /api/clients/authenticate` - Authenticate client
- `GET /api/clients/config` - Client config
- `POST /api/clients/ad-joined` - AD joined status

**Funkcionalnost:** Client authentication i konfiguracija

---

### 17. Users (`api/users`)

**Route:** `api/users`

**Endpoint-i:**
- `POST /api/users/authenticate` - Authenticate user
- `POST /api/users/forceChangePassword` - Force password change
- `GET /api/users/permissions` - User permissions
- `GET /api/users/current` - Current user
- `POST /api/users/owner` - Set owner
- `GET /api/users/local` - Local users

**Funkcionalnost:** User management i autentifikacija

---

### 18. Activity Log (`api/activityLog`)

**Route:** `api/activityLog`

**Endpoint-i:**
- `GET /api/activityLog` - List activity logs
- `GET /api/activityLog/export` - Export activity logs
- `GET /api/activityLog/actions` - List actions

**Funkcionalnost:** Activity logging i audit trail

---

### 19. Features (`api/features`)

**Route:** `api/features`

**Endpoint-i:**
- `GET /api/features` - List features

**Funkcionalnost:** Feature flags

---

### 20. Grafana (`api/grafana`)

**Route:** `api/grafana`

**Endpoint-i:**
- `GET /api/grafana/jwt` - Grafana JWT token

**Funkcionalnost:** Grafana integracija

---

### 21. SSL Certificates (`api/certificates/ssl`)

**Route:** `api/certificates/ssl`

**Endpoint-i:**
- `GET /api/certificates/ssl/addresses` - SSL addresses
- `POST /api/certificates/ssl` - Create SSL certificate
- `GET /api/certificates/ssl/script` - SSL script

**Funkcionalnost:** SSL certificate management

---

### 22. Subscription (`api/subscription`)

**Route:** `api/subscription`

**Endpoint-i:**
- `GET /api/subscription` - Subscription info
- `GET /api/subscription/public` - Public subscription info
- `GET /api/subscription/usage` - Subscription usage

**Funkcionalnost:** Subscription management

---

### 23. Productboard (`api/productboard`)

**Route:** `api/productboard`

**Endpoint-i:**
- `GET /api/productboard` - Productboard info

**Funkcionalnost:** Productboard integracija

---

## 🔌 SignalR Hub-ovi

Pronađeno **5 SignalR hub-ova** (obfuscated imena, ali funkcionalnost je verovatno):
- Real-time updates
- Progress tracking
- Client notifications
- Machine status updates
- Image operation progress

---

## 📊 Ključne Funkcionalnosti

### 1. Bulk Operacije ✅

- `POST /api/machines/batch` - Batch machine operations
- `POST /api/batchImageOperations/*` - Batch image operations
- `POST /api/machines/restart` - Bulk restart
- `POST /api/machines/shutdown` - Bulk shutdown

### 2. Scheduling ✅

- Kompletan scheduling sistem sa:
  - Machine actions
  - Boot states
  - Behaviors
  - Occurrences
  - Executions

### 3. Remote Images ✅

- `GET /api/images/remote` - List remote images
- `POST /api/images/remote/{imageUuid}/download` - Download remote image

### 4. Writebacks ✅

- `POST /api/machines/{id}/writebacks/{writebackPath}/keep` - Keep writeback
- `POST /api/machines/{id}/writebacks/keep` - Keep all writebacks
- `DELETE /api/machines/{id}/writebacks/{writebackPath}` - Delete writeback

### 5. Array Operations ✅

- Drive management (online/offline/replace)
- TRIM operations (resume/suspend/run/cancel)
- Array extend/export/delete

### 6. Toolchain ✅

- Toolchain setup i upravljanje
- NIC injection
- Network drivers
- State management

---

## 🔍 Uporedba sa ggNET2

### Implementirano u ggNET2

- ✅ Machines API (osnovno)
- ✅ Images API (osnovno)
- ✅ VMs API (osnovno)
- ✅ Storage Array API (osnovno)
- ✅ Settings API (osnovno)

### Nedostaje u ggNET2

- ❌ **Bulk Operations** - Batch operacije za machines i images
- ❌ **Scheduling** - Kompletan scheduling sistem
- ❌ **Remote Images** - Remote image download
- ❌ **Writebacks Management** - Writeback keep/delete operacije
- ❌ **Array Operations** - Drive management, TRIM operations
- ❌ **Toolchain** - Toolchain setup i upravljanje
- ❌ **Activity Log** - Activity logging i audit trail
- ❌ **Subscription** - Subscription management
- ❌ **Productboard** - Productboard integracija
- ❌ **Grafana** - Grafana integracija
- ❌ **SSL Certificates** - SSL certificate management
- ❌ **Server Commands** - Server command execution
- ❌ **Release Streams** - Release stream management
- ❌ **Server Updates** - Update management

---

## 📝 Preporuke

### Visok Prioritet

1. **Bulk Operations** - Kritično za produkciju
2. **Scheduling** - Kompletan sistem
3. **Array Operations** - Drive management, TRIM
4. **Writebacks Management** - Writeback operacije

### Srednji Prioritet

1. **Remote Images** - Remote image download
2. **Activity Log** - Audit trail
3. **Toolchain** - Toolchain setup
4. **Server Updates** - Update management

### Nizak Prioritet

1. **Subscription** - Subscription management
2. **Productboard** - Productboard integracija
3. **Grafana** - Grafana integracija
4. **SSL Certificates** - SSL certificate management

---

*Analiza je kreirana na osnovu dekompajliranog DLL-a iz verzije 2289.*

