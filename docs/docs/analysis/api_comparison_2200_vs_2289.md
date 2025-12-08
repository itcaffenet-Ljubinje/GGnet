# API Uporedna Analiza - Verzija 2200 vs 2289

**Datum:** 2025-11-18  
**Status:** ✅ Kompletna

---

## 📊 Pregled

Ovaj dokument upoređuje API endpoint-e između verzija:
- **Verzija 2200:** Analizirana iz `ggrock_api_mapping.md` (prethodna analiza)
- **Verzija 2289:** Analizirana iz dekompajliranog `GgRock.Api.dll`

**Napomena:** Verzija 2200 nije direktno dekompajlirana, ali imamo dokumentaciju iz prethodne analize.

---

## 🎯 Glavne Razlike

### Novi Endpoint-i u Verziji 2289

#### 1. Batch Image Operations (`api/batchImageOperations`) ⭐ NOVO

**Verzija 2200:** ❌ Nije postojalo  
**Verzija 2289:** ✅ Implementirano

**Endpoint-i:**
- `GET /api/batchImageOperations/history`
- `POST /api/batchImageOperations/local/restore/images`
- `POST /api/batchImageOperations/remote/restore/images`
- `GET /api/batchImageOperations/local/backup/images`
- `GET /api/batchImageOperations/remote/backup/images`
- `POST /api/batchImageOperations/local/backup`
- `POST /api/batchImageOperations/remote/backup`
- `POST /api/batchImageOperations/local/restore`
- `POST /api/batchImageOperations/remote/restore`
- `POST /api/batchImageOperations/local/test`
- `POST /api/batchImageOperations/remote/test`

**Značenje:** Kompletan sistem za bulk operacije sa image-ima (backup, restore, test)

---

#### 2. Schedule API (`api/schedule`) ⭐ NOVO

**Verzija 2200:** ⚠️ Delimično (identifikovano kroz SignalR evente)  
**Verzija 2289:** ✅ Kompletan REST API

**Endpoint-i:**
- `GET /api/schedule/machineActions/{id:guid}/occurrences`
- `GET /api/schedule/machineActions`
- `GET /api/schedule/machineActions/{id:guid}`
- `POST /api/schedule/machineActions`
- `PUT /api/schedule/machineActions/{id:guid}`
- `DELETE /api/schedule/machineActions/{id:guid}/occurrences/{date}`
- `POST /api/schedule/machineActions/{id:guid}/occurrences/replaceSingle/{date}`
- `POST /api/schedule/machineActions/{id:guid}/occurrences/replaceAllFrom/{date}`
- `DELETE /api/schedule/machineActions/{id:guid}`
- `GET /api/schedule/machineBootStates/{id:guid}/occurrences`
- `GET /api/schedule/machineBootStates`
- `GET /api/schedule/machineBootStates/{id:guid}`
- `POST /api/schedule/machineBootStates`
- `PUT /api/schedule/machineBootStates/{id:guid}`
- `DELETE /api/schedule/machineBootStates/{id:guid}/occurrences/{date}`
- `POST /api/schedule/machineBootStates/{id:guid}/occurrences/replaceSingle/{date}`
- `POST /api/schedule/machineBootStates/{id:guid}/occurrences/replaceAllFrom/{date}`
- `DELETE /api/schedule/machineBootStates/{id:guid}`
- `POST /api/schedule/copyAllEntries`
- `GET /api/schedule/occurrences`
- `GET /api/schedule/executions`
- `GET /api/schedule/executions/nextScheduled`
- `GET /api/schedule/executions/closestForMachine/{machineId:guid}`
- `GET /api/schedule/config`
- `GET /api/schedule/config/default`
- `PATCH /api/schedule/config`
- `GET /api/schedule/behaviors`
- `GET /api/schedule/behaviors/{id:guid}`
- `POST /api/schedule/behaviors`
- `PATCH /api/schedule/behaviors/{id:guid}`
- `DELETE /api/schedule/behaviors/{id:guid}`

**Značenje:** Kompletan scheduling sistem sa machine actions, boot states, behaviors, occurrences, i executions

---

#### 3. Server Updates (`api/server/updates`) ⭐ NOVO

**Verzija 2200:** ❌ Nije postojalo  
**Verzija 2289:** ✅ Implementirano

**Endpoint-i:**
- `GET /api/server/updates`
- `POST /api/server/updates/{updateId}/install`
- `GET /api/server/updates/progress`

**Značenje:** Upravljanje server update-ima

---

#### 4. Server Commands (`api/server/commands`) ⭐ NOVO

**Verzija 2200:** ❌ Nije postojalo  
**Verzija 2289:** ✅ Implementirano

**Endpoint-i:**
- `GET /api/server/commands`
- `GET /api/server/commands/lastExecution`
- `POST /api/server/commands/run`
- `POST /api/server/commands/cancel`

**Značenje:** Izvršavanje server komandi

---

#### 5. Release Streams (`api/server/releaseStreams`) ⭐ NOVO

**Verzija 2200:** ❌ Nije postojalo  
**Verzija 2289:** ✅ Implementirano

**Endpoint-i:**
- `GET /api/server/releaseStreams`
- `POST /api/server/releaseStreams/{name}/select`

**Značenje:** Upravljanje release stream-ovima

---

#### 6. Activity Log (`api/activityLog`) ⭐ NOVO

**Verzija 2200:** ❌ Nije postojalo  
**Verzija 2289:** ✅ Implementirano

**Endpoint-i:**
- `GET /api/activityLog`
- `GET /api/activityLog/export`
- `GET /api/activityLog/actions`

**Značenje:** Activity logging i audit trail

---

#### 7. Features (`api/features`) ⭐ NOVO

**Verzija 2200:** ❌ Nije postojalo  
**Verzija 2289:** ✅ Implementirano

**Endpoint-i:**
- `GET /api/features`

**Značenje:** Feature flags

---

#### 8. Grafana (`api/grafana`) ⭐ NOVO

**Verzija 2200:** ❌ Nije postojalo  
**Verzija 2289:** ✅ Implementirano

**Endpoint-i:**
- `GET /api/grafana/jwt`

**Značenje:** Grafana integracija

---

#### 9. SSL Certificates (`api/certificates/ssl`) ⭐ NOVO

**Verzija 2200:** ❌ Nije postojalo  
**Verzija 2289:** ✅ Implementirano

**Endpoint-i:**
- `GET /api/certificates/ssl/addresses`
- `POST /api/certificates/ssl`
- `GET /api/certificates/ssl/script`

**Značenje:** SSL certificate management

---

#### 10. Subscription (`api/subscription`) ⭐ NOVO

**Verzija 2200:** ❌ Nije postojalo  
**Verzija 2289:** ✅ Implementirano

**Endpoint-i:**
- `GET /api/subscription`
- `GET /api/subscription/public`
- `GET /api/subscription/usage`

**Značenje:** Subscription management

---

#### 11. Productboard (`api/productboard`) ⭐ NOVO

**Verzija 2200:** ❌ Nije postojalo  
**Verzija 2289:** ✅ Implementirano

**Endpoint-i:**
- `GET /api/productboard`

**Značenje:** Productboard integracija

---

### Prošireni Endpoint-i u Verziji 2289

#### 1. Machines API (`api/machines`)

**Verzija 2200:**
- `GET /api/machines`
- `GET /api/machines/{id}`
- `POST /api/machines`
- `PUT /api/machines/{id}`
- `DELETE /api/machines/{id}`
- `POST /api/machines/{id}/restart`
- `POST /api/machines/restart` (bulk)
- `POST /api/machines/{id}/shutdown`
- `POST /api/machines/shutdown` (bulk)
- `POST /api/machines/{id}/wake`
- `POST /api/machines/{id}/turnOn`
- `POST /api/machines/wake` (bulk)
- `POST /api/machines/turnOn` (bulk)

**Verzija 2289:** ✅ Sve iz verzije 2200 +:
- `GET /api/machines/client` ⭐ NOVO
- `POST /api/machines/batch` ⭐ NOVO
- `GET /api/machines/{machineId}/hardware` ⭐ NOVO
- `POST /api/machines/{machineId}/hardware/displaysettings` ⭐ NOVO
- `GET /api/machines/{machineId}/hardware/displaysettings` ⭐ NOVO
- `POST /api/machines/displaysettings` ⭐ NOVO (bulk)
- `POST /api/machines/{id}/writebacks/{writebackPath}/keep` ⭐ NOVO
- `POST /api/machines/{id}/writebacks/keep` ⭐ NOVO
- `DELETE /api/machines/{id}/writebacks/{writebackPath}` ⭐ NOVO
- `PUT /api/machines/{id:guid}/scheduledBehavior/{behaviorId:guid}` ⭐ NOVO
- `DELETE /api/machines/{id:guid}/scheduledBehavior` ⭐ NOVO

**Značenje:** Prošireno sa hardware info, display settings, writeback management, i scheduled behaviors

---

#### 2. Images API (`api/images`)

**Verzija 2200:**
- `GET /api/images`
- `GET /api/images/{id}`
- `POST /api/images`
- `PUT /api/images/{id}`
- `DELETE /api/images/{id}`
- `GET /api/images/remote`
- `POST /api/images/remote/{imageUuid}/download`

**Verzija 2289:** ✅ Sve iz verzije 2200 +:
- `GET /api/images/{path}` ⭐ NOVO (path-based)
- `PUT /api/images/{path}` ⭐ NOVO (path-based)
- `DELETE /api/images/{path}` ⭐ NOVO (path-based)
- `POST /api/images/{path}/snapshots/{snapshotPath}/default` ⭐ NOVO
- `POST /api/images/{path}/snapshots/{snapshotPath}/lock` ⭐ NOVO
- `DELETE /api/images/{path}/snapshots/{snapshotPath}` ⭐ NOVO
- `GET /api/images/imported` ⭐ NOVO
- `POST /api/images/imported/{importId}/cancel` ⭐ NOVO
- `POST /api/images/imported/{importId}/finish` ⭐ NOVO
- `POST /api/images/import/vhd` ⭐ NOVO
- `POST /api/images/import` ⭐ NOVO
- `POST /api/images/{sourceSnapshotPath}/copy` ⭐ NOVO
- `DELETE /api/images/{path}/writebacks` ⭐ NOVO

**Značenje:** Prošireno sa snapshot management, import/export, writeback management

---

#### 3. Storage Array (`api/array`)

**Verzija 2200:**
- `GET /api/array`
- `POST /api/array/rebuild`
- `POST /api/array/trim`
- `GET /api/array/drives`
- `POST /api/array/drives/{id}/add`
- `POST /api/array/drives/{id}/remove`
- `POST /api/array/drives/{id}/replace`

**Verzija 2289:** ✅ Sve iz verzije 2200 +:
- `POST /api/array` ⭐ NOVO (create array)
- `POST /api/array/extend` ⭐ NOVO
- `POST /api/array/drives/{driveUuid}/online` ⭐ NOVO
- `POST /api/array/drives/{driveUuid}/offline` ⭐ NOVO
- `POST /api/array/drives` ⭐ NOVO (add drives)
- `POST /api/array/drives/{oldDriveUuid}/replace` ⭐ NOVO
- `DELETE /api/array/drives/{driveUuid}` ⭐ NOVO
- `POST /api/array/export` ⭐ NOVO
- `DELETE /api/array` ⭐ NOVO (delete array)
- `GET /api/array/stripes/lookup` ⭐ NOVO
- `POST /api/array/trim/resume` ⭐ NOVO
- `POST /api/array/trim/suspend` ⭐ NOVO
- `POST /api/array/trim/run` ⭐ NOVO
- `POST /api/array/trim/cancel` ⭐ NOVO

**Značenje:** Prošireno sa kompletnim drive management-om, TRIM operacijama, array export/delete

---

#### 4. Server API (`api/server`)

**Verzija 2200:** ⚠️ Nije dokumentovano  
**Verzija 2289:** ✅ Kompletan API:
- `GET /api/server/ping`
- `GET /api/server`
- `GET /api/server/public`
- `GET /api/server/ram`
- `PUT /api/server/ram`
- `GET /api/server/services`
- `GET /api/server/services/{serviceId}`
- `POST /api/server/services/{serviceId}/restart`
- `POST /api/server/reboot`

**Značenje:** Kompletan server management API

---

#### 5. Settings API (`api/settings`)

**Verzija 2200:** ⚠️ Nije detaljno dokumentovano  
**Verzija 2289:** ✅ Kompletan API:
- `GET /api/settings/images`
- `PUT /api/settings/images`
- `GET /api/settings/trim`
- `PUT /api/settings/trim`
- `GET /api/settings/network`
- `PUT /api/settings/network`
- `GET /api/settings/boot`
- `PUT /api/settings/boot`
- `GET /api/settings/auth`
- `PATCH /api/settings/auth`

**Značenje:** Strukturisani settings API sa kategorijama

---

#### 6. Clients API (`api/clients`)

**Verzija 2200:** ⚠️ Nije dokumentovano  
**Verzija 2289:** ✅ Implementirano:
- `POST /api/clients/authenticate`
- `GET /api/clients/config`
- `POST /api/clients/ad-joined`

**Značenje:** Client authentication i konfiguracija

---

#### 7. Users API (`api/users`)

**Verzija 2200:** ⚠️ Nije dokumentovano  
**Verzija 2289:** ✅ Implementirano:
- `POST /api/users/authenticate`
- `POST /api/users/forceChangePassword`
- `GET /api/users/permissions`
- `GET /api/users/current`
- `POST /api/users/owner`
- `GET /api/users/local`

**Značenje:** User management i autentifikacija

---

## 📊 Statistika

| Kategorija | Verzija 2200 | Verzija 2289 | Razlika |
|-----------|--------------|--------------|---------|
| **API Kontroleri** | ~15 | 26 | +11 |
| **API Endpoint-i** | ~80 | 199 | +119 |
| **Novi Moduli** | - | 11 | +11 |
| **Prošireni Moduli** | - | 7 | +7 |

---

## 🔍 Detaljna Uporedba po Modulima

### Machines API

| Endpoint | Verzija 2200 | Verzija 2289 | Status |
|----------|--------------|--------------|--------|
| `GET /api/machines` | ✅ | ✅ | Identično |
| `GET /api/machines/{id}` | ✅ | ✅ | Identično |
| `POST /api/machines` | ✅ | ✅ | Identično |
| `PUT /api/machines/{id}` | ✅ | ✅ | Identično |
| `DELETE /api/machines/{id}` | ✅ | ✅ | Identično |
| `POST /api/machines/{id}/restart` | ✅ | ✅ | Identično |
| `POST /api/machines/restart` | ✅ | ✅ | Identično |
| `POST /api/machines/{id}/shutdown` | ✅ | ✅ | Identično |
| `POST /api/machines/shutdown` | ✅ | ✅ | Identično |
| `POST /api/machines/{id}/wake` | ✅ | ✅ | Identično |
| `POST /api/machines/{id}/turnOn` | ✅ | ✅ | Identično |
| `POST /api/machines/wake` | ✅ | ✅ | Identično |
| `POST /api/machines/turnOn` | ✅ | ✅ | Identično |
| `GET /api/machines/client` | ❌ | ✅ | **NOVO** |
| `POST /api/machines/batch` | ❌ | ✅ | **NOVO** |
| `GET /api/machines/{machineId}/hardware` | ❌ | ✅ | **NOVO** |
| `POST /api/machines/{machineId}/hardware/displaysettings` | ❌ | ✅ | **NOVO** |
| `GET /api/machines/{machineId}/hardware/displaysettings` | ❌ | ✅ | **NOVO** |
| `POST /api/machines/displaysettings` | ❌ | ✅ | **NOVO** |
| `POST /api/machines/{id}/writebacks/{writebackPath}/keep` | ❌ | ✅ | **NOVO** |
| `POST /api/machines/{id}/writebacks/keep` | ❌ | ✅ | **NOVO** |
| `DELETE /api/machines/{id}/writebacks/{writebackPath}` | ❌ | ✅ | **NOVO** |
| `PUT /api/machines/{id:guid}/scheduledBehavior/{behaviorId:guid}` | ❌ | ✅ | **NOVO** |
| `DELETE /api/machines/{id:guid}/scheduledBehavior` | ❌ | ✅ | **NOVO** |

---

### Images API

| Endpoint | Verzija 2200 | Verzija 2289 | Status |
|----------|--------------|--------------|--------|
| `GET /api/images` | ✅ | ✅ | Identično |
| `GET /api/images/{id}` | ✅ | ✅ | Identično (path-based u 2289) |
| `POST /api/images` | ✅ | ✅ | Identično |
| `PUT /api/images/{id}` | ✅ | ✅ | Identično (path-based u 2289) |
| `DELETE /api/images/{id}` | ✅ | ✅ | Identično (path-based u 2289) |
| `GET /api/images/remote` | ✅ | ✅ | Identično |
| `POST /api/images/remote/{imageUuid}/download` | ✅ | ✅ | Identično |
| `POST /api/images/{path}/snapshots/{snapshotPath}/default` | ❌ | ✅ | **NOVO** |
| `POST /api/images/{path}/snapshots/{snapshotPath}/lock` | ❌ | ✅ | **NOVO** |
| `DELETE /api/images/{path}/snapshots/{snapshotPath}` | ❌ | ✅ | **NOVO** |
| `GET /api/images/imported` | ❌ | ✅ | **NOVO** |
| `POST /api/images/imported/{importId}/cancel` | ❌ | ✅ | **NOVO** |
| `POST /api/images/imported/{importId}/finish` | ❌ | ✅ | **NOVO** |
| `POST /api/images/import/vhd` | ❌ | ✅ | **NOVO** |
| `POST /api/images/import` | ❌ | ✅ | **NOVO** |
| `POST /api/images/{sourceSnapshotPath}/copy` | ❌ | ✅ | **NOVO** |
| `DELETE /api/images/{path}/writebacks` | ❌ | ✅ | **NOVO** |

---

### Storage Array API

| Endpoint | Verzija 2200 | Verzija 2289 | Status |
|----------|--------------|--------------|--------|
| `GET /api/array` | ✅ | ✅ | Identično |
| `POST /api/array/rebuild` | ✅ | ⚠️ | Nije eksplicitno u 2289 |
| `POST /api/array/trim` | ✅ | ⚠️ | Prošireno u 2289 |
| `GET /api/array/drives` | ✅ | ⚠️ | Prošireno u 2289 |
| `POST /api/array/drives/{id}/add` | ✅ | ⚠️ | Prošireno u 2289 |
| `POST /api/array/drives/{id}/remove` | ✅ | ⚠️ | Prošireno u 2289 |
| `POST /api/array/drives/{id}/replace` | ✅ | ✅ | Identično |
| `POST /api/array` | ❌ | ✅ | **NOVO** (create) |
| `POST /api/array/extend` | ❌ | ✅ | **NOVO** |
| `POST /api/array/drives/{driveUuid}/online` | ❌ | ✅ | **NOVO** |
| `POST /api/array/drives/{driveUuid}/offline` | ❌ | ✅ | **NOVO** |
| `POST /api/array/drives` | ❌ | ✅ | **NOVO** (add) |
| `DELETE /api/array/drives/{driveUuid}` | ❌ | ✅ | **NOVO** |
| `POST /api/array/export` | ❌ | ✅ | **NOVO** |
| `DELETE /api/array` | ❌ | ✅ | **NOVO** |
| `GET /api/array/stripes/lookup` | ❌ | ✅ | **NOVO** |
| `POST /api/array/trim/resume` | ❌ | ✅ | **NOVO** |
| `POST /api/array/trim/suspend` | ❌ | ✅ | **NOVO** |
| `POST /api/array/trim/run` | ❌ | ✅ | **NOVO** |
| `POST /api/array/trim/cancel` | ❌ | ✅ | **NOVO** |

---

## 🎯 Ključne Razlike

### 1. Bulk Operations ✅

**Verzija 2200:** ⚠️ Delimično (samo machines)  
**Verzija 2289:** ✅ Kompletan sistem za machines i images

**Novi Endpoint-i:**
- `POST /api/machines/batch`
- `POST /api/batchImageOperations/*` (11 endpoint-a)

---

### 2. Scheduling ✅

**Verzija 2200:** ⚠️ Identifikovano kroz SignalR evente  
**Verzija 2289:** ✅ Kompletan REST API (30+ endpoint-a)

**Novi Endpoint-i:**
- Machine actions management
- Boot states management
- Behaviors management
- Occurrences management
- Executions tracking

---

### 3. Writebacks Management ✅

**Verzija 2200:** ⚠️ Nije dokumentovano  
**Verzija 2289:** ✅ Kompletan API

**Novi Endpoint-i:**
- `POST /api/machines/{id}/writebacks/{writebackPath}/keep`
- `POST /api/machines/{id}/writebacks/keep`
- `DELETE /api/machines/{id}/writebacks/{writebackPath}`
- `DELETE /api/images/{path}/writebacks`

---

### 4. Array Operations ✅

**Verzija 2200:** ⚠️ Osnovne operacije  
**Verzija 2289:** ✅ Kompletan drive management i TRIM operacije

**Novi Endpoint-i:**
- Drive online/offline
- Array extend/export/delete
- TRIM resume/suspend/run/cancel
- Stripes lookup

---

### 5. Server Management ✅

**Verzija 2200:** ⚠️ Nije dokumentovano  
**Verzija 2289:** ✅ Kompletan API

**Novi Endpoint-i:**
- Server info, RAM, services
- Server updates
- Server commands
- Release streams

---

### 6. Activity Logging ✅

**Verzija 2200:** ❌ Nije postojalo  
**Verzija 2289:** ✅ Implementirano

**Novi Endpoint-i:**
- `GET /api/activityLog`
- `GET /api/activityLog/export`
- `GET /api/activityLog/actions`

---

### 7. User Management ✅

**Verzija 2200:** ⚠️ Nije dokumentovano  
**Verzija 2289:** ✅ Kompletan API

**Novi Endpoint-i:**
- User authentication
- Password management
- Permissions
- Owner management

---

## 📝 Preporuke za ggNET2

### Visok Prioritet

1. **Bulk Operations** - Kritično za produkciju
2. **Scheduling** - Kompletan sistem
3. **Writebacks Management** - Writeback operacije
4. **Array Operations** - Drive management, TRIM

### Srednji Prioritet

1. **Activity Logging** - Audit trail
2. **Server Management** - Server info, updates, commands
3. **User Management** - User authentication i permissions

### Nizak Prioritet

1. **Subscription** - Subscription management
2. **Productboard** - Productboard integracija
3. **Grafana** - Grafana integracija
4. **SSL Certificates** - SSL certificate management

---

## ✅ Zaključak

**Verzija 2289 ima značajno više funkcionalnosti** od verzije 2200:
- **+119 novih endpoint-a**
- **+11 novih modula**
- **Kompletan scheduling sistem**
- **Bulk operations za machines i images**
- **Kompletan server management**
- **Activity logging i audit trail**

**Preporuka:** Koristiti verziju 2289 kao referencu za ggNET2 projekat, jer sadrži najnovije funkcionalnosti i bug fix-ove.

---

*Uporedna analiza kreirana na osnovu dokumentacije verzije 2200 i dekompajliranog DLL-a verzije 2289.*

