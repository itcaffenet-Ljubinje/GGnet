# Prioriteti Implementacije za ggNET2

**Datum:** 2025-11-18  
**Bazirano na:** Analiza verzije 2289 i trenutnog stanja ggNET2  
**Status:** 📋 Plan Implementacije

---

## 📊 Executive Summary

Ovaj dokument identifikuje prioritete za implementaciju funkcionalnosti u ggNET2 na osnovu:
- Analize verzije 2289 (199 endpoint-a, 26 kontrolera)
- Trenutnog stanja ggNET2 (osnovni CRUD operacije)
- Gap analize između verzija 2200 i 2289

**Ključni nalazi:**
- **Trenutno implementirano:** ~30% osnovnih funkcionalnosti
- **Nedostaje za MVP:** Bulk operations, Scheduling, Writebacks, Array operations
- **Nedostaje za Production:** Authentication, Activity logging, Progress tracking

---

## 🎯 Kategorizacija Prioriteta

### P0 - Kritično za MVP (Must Have)
**Vreme:** 4-6 nedelja  
**Opis:** Funkcionalnosti bez kojih sistem ne može biti korišćen u produkciji

### P1 - Visok Prioritet (Should Have)
**Vreme:** 6-8 nedelja  
**Opis:** Funkcionalnosti koje značajno poboljšavaju UX i funkcionalnost

### P2 - Srednji Prioritet (Nice to Have)
**Vreme:** 8-12 nedelja  
**Opis:** Funkcionalnosti koje su korisne ali nisu kritične

### P3 - Nizak Prioritet (Future)
**Vreme:** 12+ nedelja  
**Opis:** Funkcionalnosti koje mogu biti implementirane kasnije

---

## 🔴 P0 - Kritično za MVP

### 1. Authentication & Authorization ⚠️ KRITIČNO

**Status:** ❌ Nedostaje  
**Prioritet:** 🔴 P0 - Kritično  
**Vreme:** 2-3 nedelje

**Funkcionalnosti:**
- JWT token-based authentication
- Role-based access control (RBAC)
- User management (Admin, User roles)
- Password management
- Session management

**Endpoint-i (iz verzije 2289):**
- `POST /api/users/authenticate`
- `POST /api/users/forceChangePassword`
- `GET /api/users/permissions`
- `GET /api/users/current`
- `GET /api/users/local`
- `POST /api/clients/authenticate`

**Dependencies:**
- PostgreSQL schema za users i roles
- JWT library (python-jose)
- Password hashing (bcrypt)

**Implementacija:**
```
app/backend/
├── auth/
│   ├── __init__.py
│   ├── jwt_handler.py
│   ├── password_manager.py
│   ├── rbac.py
│   └── dependencies.py
├── api/
│   └── users.py (novi)
└── config/
    └── models.py (User, Role models)
```

**Test Plan:**
- Unit testovi za JWT generisanje i validaciju
- Integration testovi za authentication flow
- Security testovi (SQL injection, XSS)

---

### 2. Bulk Operations - Machines ⚠️ KRITIČNO

**Status:** ❌ Nedostaje  
**Prioritet:** 🔴 P0 - Kritično  
**Vreme:** 1 nedelja

**Funkcionalnosti:**
- Bulk restart machines
- Bulk shutdown machines
- Bulk wake machines
- Bulk turn on machines
- Batch operations sa progress tracking

**Endpoint-i (iz verzije 2289):**
- `POST /api/machines/batch` - Batch operations
- `POST /api/machines/restart` - Bulk restart
- `POST /api/machines/shutdown` - Bulk shutdown
- `POST /api/machines/wake` - Bulk wake
- `POST /api/machines/turnOn` - Bulk turn on

**Dependencies:**
- Machines API (već postoji)
- WebSocket za progress tracking

**Implementacija:**
```python
# app/backend/api/machines.py
@router.post("/batch")
async def batch_operations(
    request: BatchOperationRequest,
    db: Session = Depends(get_db)
):
    """Batch operations sa progress tracking"""
    pass

@router.post("/restart")
async def bulk_restart(
    request: BulkActionRequest,
    db: Session = Depends(get_db)
):
    """Bulk restart machines"""
    pass
```

**Test Plan:**
- Testovi za bulk operacije sa 10+ machines
- Progress tracking testovi
- Error handling testovi

---

### 3. Bulk Operations - Images ⚠️ KRITIČNO

**Status:** ❌ Nedostaje  
**Prioritet:** 🔴 P0 - Kritično  
**Vreme:** 2 nedelje

**Funkcionalnosti:**
- Batch image operations (backup, restore, test)
- Local i remote backup/restore
- Progress tracking za batch operacije

**Endpoint-i (iz verzije 2289):**
- `GET /api/batchImageOperations/history`
- `POST /api/batchImageOperations/local/backup`
- `POST /api/batchImageOperations/remote/backup`
- `POST /api/batchImageOperations/local/restore`
- `POST /api/batchImageOperations/remote/restore`
- `POST /api/batchImageOperations/local/test`
- `POST /api/batchImageOperations/remote/test`

**Dependencies:**
- Images API (već postoji)
- ZFS snapshot operations
- WebSocket za progress tracking

**Implementacija:**
```
app/backend/
├── images/
│   └── batch_operations.py (novi)
└── api/
    └── batch_image_operations.py (novi)
```

**Test Plan:**
- Testovi za batch backup/restore
- Progress tracking testovi
- Error recovery testovi

---

### 4. Writebacks Management ⚠️ KRITIČNO

**Status:** ⚠️ Delimično (WritebackManager postoji)  
**Prioritet:** 🔴 P0 - Kritično  
**Vreme:** 1 nedelja

**Funkcionalnosti:**
- Keep writeback (single i bulk)
- Delete writeback
- Writeback state management

**Endpoint-i (iz verzije 2289):**
- `POST /api/machines/{id}/writebacks/{writebackPath}/keep`
- `POST /api/machines/{id}/writebacks/keep`
- `DELETE /api/machines/{id}/writebacks/{writebackPath}`
- `DELETE /api/images/{path}/writebacks`

**Dependencies:**
- WritebackManager (već postoji)
- Machines API
- Images API

**Implementacija:**
```python
# app/backend/api/machines.py
@router.post("/{id}/writebacks/{writebackPath}/keep")
async def keep_writeback(...):
    """Keep single writeback"""
    pass

@router.post("/{id}/writebacks/keep")
async def keep_all_writebacks(...):
    """Keep all writebacks"""
    pass
```

**Test Plan:**
- Testovi za keep/delete operacije
- State management testovi

---

### 5. Array Operations - Drive Management ⚠️ KRITIČNO

**Status:** ❌ Nedostaje  
**Prioritet:** 🔴 P0 - Kritično  
**Vreme:** 2 nedelje

**Funkcionalnosti:**
- Drive detection i listing
- Drive online/offline
- Drive add/remove/replace
- Array extend
- Array export/delete

**Endpoint-i (iz verzije 2289):**
- `GET /api/drives/free` - Free drives
- `GET /api/drives/{driveName}/smart` - SMART data
- `POST /api/array/drives/{driveUuid}/online`
- `POST /api/array/drives/{driveUuid}/offline`
- `POST /api/array/drives` - Add drives
- `POST /api/array/drives/{oldDriveUuid}/replace`
- `DELETE /api/array/drives/{driveUuid}`
- `POST /api/array/extend`
- `POST /api/array/export`
- `DELETE /api/array`

**Dependencies:**
- Storage API (već postoji)
- ZFS utilities
- SMART monitoring (smartctl)

**Implementacija:**
```
app/backend/
├── storage/
│   ├── drive_manager.py (novi)
│   └── array_operations.py (novi)
└── api/
    └── array.py (novi, ili proširiti storage.py)
```

**Test Plan:**
- Drive detection testovi
- Array operations testovi
- Error handling testovi

---

### 6. Array Operations - TRIM Management ⚠️ KRITIČNO

**Status:** ❌ Nedostaje  
**Prioritet:** 🔴 P0 - Kritično  
**Vreme:** 1 nedelja

**Funkcionalnosti:**
- TRIM resume/suspend/run/cancel
- TRIM progress tracking
- TRIM configuration

**Endpoint-i (iz verzije 2289):**
- `POST /api/array/trim/resume`
- `POST /api/array/trim/suspend`
- `POST /api/array/trim/run`
- `POST /api/array/trim/cancel`
- `GET /api/settings/trim`
- `PUT /api/settings/trim`

**Dependencies:**
- Storage API
- ZFS TRIM operations

**Implementacija:**
```python
# app/backend/storage/trim_manager.py
class TrimManager:
    def resume_trim(self, pool_name: str):
        """Resume TRIM operation"""
        pass
    
    def suspend_trim(self, pool_name: str):
        """Suspend TRIM operation"""
        pass
```

**Test Plan:**
- TRIM operations testovi
- Progress tracking testovi

---

## 🟠 P1 - Visok Prioritet

### 7. Scheduling System

**Status:** ❌ Nedostaje  
**Prioritet:** 🟠 P1 - Visok  
**Vreme:** 3-4 nedelje

**Funkcionalnosti:**
- Machine actions scheduling
- Boot states scheduling
- Behaviors management
- Occurrences management
- Executions tracking

**Endpoint-i (iz verzije 2289):**
- `GET /api/schedule/machineActions`
- `POST /api/schedule/machineActions`
- `GET /api/schedule/machineBootStates`
- `POST /api/schedule/machineBootStates`
- `GET /api/schedule/behaviors`
- `POST /api/schedule/behaviors`
- `GET /api/schedule/executions`
- `GET /api/schedule/executions/nextScheduled`

**Dependencies:**
- PostgreSQL schema za scheduling
- Background task scheduler (APScheduler ili Celery)
- Machines API

**Implementacija:**
```
app/backend/
├── scheduler/
│   ├── __init__.py
│   ├── scheduler_manager.py
│   ├── behavior_manager.py
│   └── execution_tracker.py
└── api/
    └── schedule.py (novi)
```

**Test Plan:**
- Scheduling testovi
- Execution tracking testovi
- Timezone handling testovi

---

### 8. Progress Tracking - WebSocket Events

**Status:** ⚠️ Delimično (WebSocket postoji)  
**Prioritet:** 🟠 P1 - Visok  
**Vreme:** 2 nedelje

**Funkcionalnosti:**
- Real-time progress tracking za sve dugotrajne operacije
- Array rebuild/trim progress
- Image import/backup progress
- Batch operations progress

**Event-i (iz verzije 2289):**
- `array_rebuild_progress_updated`
- `array_trim_progress_updated`
- `image_import_progress_updated`
- `image_backup_restore_progress_updated`
- `batch_operation_progress_updated`

**Dependencies:**
- WebSocket hub (već postoji)
- Background tasks

**Implementacija:**
```python
# app/backend/websocket/hub.py
async def send_progress_update(
    operation_id: str,
    progress: float,
    status: str
):
    """Send progress update via WebSocket"""
    pass
```

**Test Plan:**
- WebSocket connection testovi
- Progress update testovi
- Multiple client testovi

---

### 9. Activity Logging & Audit Trail

**Status:** ❌ Nedostaje  
**Prioritet:** 🟠 P1 - Visok  
**Vreme:** 1-2 nedelje

**Funkcionalnosti:**
- Activity log kreiranje
- Activity log export
- Action tracking
- Audit trail

**Endpoint-i (iz verzije 2289):**
- `GET /api/activityLog`
- `GET /api/activityLog/export`
- `GET /api/activityLog/actions`

**Dependencies:**
- PostgreSQL schema za activity logs
- User authentication

**Implementacija:**
```
app/backend/
├── activity/
│   ├── __init__.py
│   ├── activity_logger.py
│   └── audit_trail.py
└── api/
    └── activity_log.py (novi)
```

**Test Plan:**
- Logging testovi
- Export testovi
- Performance testovi

---

### 10. Server Management API

**Status:** ❌ Nedostaje  
**Prioritet:** 🟠 P1 - Visok  
**Vreme:** 1 nedelja

**Funkcionalnosti:**
- Server info
- RAM management
- Services management
- Server reboot

**Endpoint-i (iz verzije 2289):**
- `GET /api/server/ping`
- `GET /api/server`
- `GET /api/server/public`
- `GET /api/server/ram`
- `PUT /api/server/ram`
- `GET /api/server/services`
- `POST /api/server/services/{serviceId}/restart`
- `POST /api/server/reboot`

**Dependencies:**
- System utilities (psutil, systemd)

**Implementacija:**
```
app/backend/
├── server/
│   ├── __init__.py
│   ├── server_manager.py
│   └── service_manager.py
└── api/
    └── server.py (novi)
```

**Test Plan:**
- Server info testovi
- Service management testovi

---

### 11. Image Snapshot Management

**Status:** ⚠️ Delimično (osnovni snapshot operacije)  
**Prioritet:** 🟠 P1 - Visok  
**Vreme:** 1 nedelja

**Funkcionalnosti:**
- Set default snapshot
- Lock snapshot
- Delete snapshot
- Snapshot timeline

**Endpoint-i (iz verzije 2289):**
- `POST /api/images/{path}/snapshots/{snapshotPath}/default`
- `POST /api/images/{path}/snapshots/{snapshotPath}/lock`
- `DELETE /api/images/{path}/snapshots/{snapshotPath}`

**Dependencies:**
- Images API
- ZFS snapshot operations

**Implementacija:**
```python
# app/backend/api/images.py
@router.post("/{path}/snapshots/{snapshotPath}/default")
async def set_default_snapshot(...):
    """Set default snapshot"""
    pass
```

**Test Plan:**
- Snapshot operations testovi
- Lock/unlock testovi

---

### 12. Image Import/Export

**Status:** ⚠️ Delimično  
**Prioritet:** 🟠 P1 - Visok  
**Vreme:** 2 nedelje

**Funkcionalnosti:**
- Image import (VHD, raw)
- Image export
- Import progress tracking
- Remote image download

**Endpoint-i (iz verzije 2289):**
- `GET /api/images/imported`
- `POST /api/images/imported/{importId}/cancel`
- `POST /api/images/imported/{importId}/finish`
- `POST /api/images/import/vhd`
- `POST /api/images/import`
- `POST /api/images/{sourceSnapshotPath}/copy`
- `GET /api/images/remote`
- `POST /api/images/remote/{imageUuid}/download`

**Dependencies:**
- Images API
- ZFS send/receive operations
- Background tasks

**Implementacija:**
```
app/backend/
├── images/
│   └── import_export.py (novi)
└── api/
    └── images.py (proširiti)
```

**Test Plan:**
- Import/export testovi
- Progress tracking testovi
- Error recovery testovi

---

## 🟡 P2 - Srednji Prioritet

### 13. Machines Hardware Info

**Status:** ❌ Nedostaje  
**Prioritet:** 🟡 P2 - Srednji  
**Vreme:** 1 nedelja

**Funkcionalnosti:**
- Hardware info (NIC, GPU, CPU, motherboard)
- Display settings management

**Endpoint-i (iz verzije 2289):**
- `GET /api/machines/{machineId}/hardware`
- `POST /api/machines/{machineId}/hardware/displaysettings`
- `GET /api/machines/{machineId}/hardware/displaysettings`
- `POST /api/machines/displaysettings` (bulk)

**Dependencies:**
- Machines API
- Hardware detection utilities

---

### 14. Scheduled Behaviors Integration

**Status:** ❌ Nedostaje  
**Prioritet:** 🟡 P2 - Srednji  
**Vreme:** 1 nedelja

**Funkcionalnosti:**
- Set scheduled behavior na machine
- Remove scheduled behavior

**Endpoint-i (iz verzije 2289):**
- `PUT /api/machines/{id:guid}/scheduledBehavior/{behaviorId:guid}`
- `DELETE /api/machines/{id:guid}/scheduledBehavior`

**Dependencies:**
- Scheduling system (P1)
- Machines API

---

### 15. Server Updates Management

**Status:** ❌ Nedostaje  
**Prioritet:** 🟡 P2 - Srednji  
**Vreme:** 1-2 nedelje

**Funkcionalnosti:**
- List updates
- Install updates
- Update progress tracking

**Endpoint-i (iz verzije 2289):**
- `GET /api/server/updates`
- `POST /api/server/updates/{updateId}/install`
- `GET /api/server/updates/progress`

**Dependencies:**
- Server Management API (P1)
- Package manager integration

---

### 16. Server Commands

**Status:** ❌ Nedostaje  
**Prioritet:** 🟡 P2 - Srednji  
**Vreme:** 1 nedelja

**Funkcionalnosti:**
- Run shell commands
- Command history
- Command cancellation

**Endpoint-i (iz verzije 2289):**
- `GET /api/server/commands`
- `GET /api/server/commands/lastExecution`
- `POST /api/server/commands/run`
- `POST /api/server/commands/cancel`

**Dependencies:**
- Server Management API (P1)
- Security considerations

---

### 17. Structured Settings API

**Status:** ⚠️ Delimično (osnovni settings)  
**Prioritet:** 🟡 P2 - Srednji  
**Vreme:** 1 nedelja

**Funkcionalnosti:**
- Structured settings endpoints (images, trim, network, boot, auth)
- Settings validation
- Settings defaults

**Endpoint-i (iz verzije 2289):**
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

**Dependencies:**
- Settings API (već postoji)

---

## 🟢 P3 - Nizak Prioritet

### 18. Release Streams

**Status:** ❌ Nedostaje  
**Prioritet:** 🟢 P3 - Nizak  
**Vreme:** 1 nedelja

**Endpoint-i:**
- `GET /api/server/releaseStreams`
- `POST /api/server/releaseStreams/{name}/select`

---

### 19. Features API

**Status:** ❌ Nedostaje  
**Prioritet:** 🟢 P3 - Nizak  
**Vreme:** 1 nedelja

**Endpoint-i:**
- `GET /api/features`

---

### 20. Grafana Integration

**Status:** ❌ Nedostaje  
**Prioritet:** 🟢 P3 - Nizak  
**Vreme:** 1 nedelja

**Endpoint-i:**
- `GET /api/grafana/jwt`

---

### 21. SSL Certificates Management

**Status:** ❌ Nedostaje  
**Prioritet:** 🟢 P3 - Nizak  
**Vreme:** 1-2 nedelje

**Endpoint-i:**
- `GET /api/certificates/ssl/addresses`
- `POST /api/certificates/ssl`
- `GET /api/certificates/ssl/script`

---

### 22. Subscription Management

**Status:** ❌ Nedostaje  
**Prioritet:** 🟢 P3 - Nizak  
**Vreme:** 1 nedelja

**Endpoint-i:**
- `GET /api/subscription`
- `GET /api/subscription/public`
- `GET /api/subscription/usage`

---

### 23. Productboard Integration

**Status:** ❌ Nedostaje  
**Prioritet:** 🟢 P3 - Nizak  
**Vreme:** 1 nedelja

**Endpoint-i:**
- `GET /api/productboard`

---

## 📅 Vremenski Plan

### Faza 1: MVP (P0) - 6-8 nedelja

**Nedelja 1-2:**
- Authentication & Authorization
- Bulk Operations - Machines

**Nedelja 3-4:**
- Bulk Operations - Images
- Writebacks Management

**Nedelja 5-6:**
- Array Operations - Drive Management
- Array Operations - TRIM Management

**Nedelja 7-8:**
- Testing & Bug Fixes
- Documentation

---

### Faza 2: Production Ready (P1) - 8-10 nedelja

**Nedelja 9-12:**
- Scheduling System

**Nedelja 13-14:**
- Progress Tracking - WebSocket Events
- Activity Logging & Audit Trail

**Nedelja 15-16:**
- Server Management API
- Image Snapshot Management

**Nedelja 17-18:**
- Image Import/Export
- Testing & Bug Fixes

---

### Faza 3: Nice to Have (P2) - 6-8 nedelja

**Nedelja 19-22:**
- Machines Hardware Info
- Scheduled Behaviors Integration
- Server Updates Management
- Server Commands
- Structured Settings API

---

### Faza 4: Future (P3) - 4-6 nedelja

**Nedelja 23-28:**
- Release Streams
- Features API
- Grafana Integration
- SSL Certificates Management
- Subscription Management
- Productboard Integration

---

## 🔗 Dependencies Graph

```
Authentication (P0)
    ↓
Activity Logging (P1)
    ↓
All other APIs

Scheduling System (P1)
    ↓
Scheduled Behaviors (P2)

Server Management (P1)
    ↓
Server Updates (P2)
    ↓
Server Commands (P2)

Array Operations (P0)
    ↓
TRIM Management (P0)

Bulk Operations (P0)
    ↓
Progress Tracking (P1)
```

---

## 📊 Statistika

| Prioritet | Broj Funkcionalnosti | Vreme | Status |
|-----------|---------------------|-------|--------|
| **P0 - Kritično** | 6 | 6-8 nedelja | ❌ Nedostaje |
| **P1 - Visok** | 6 | 8-10 nedelja | ❌ Nedostaje |
| **P2 - Srednji** | 5 | 6-8 nedelja | ❌ Nedostaje |
| **P3 - Nizak** | 6 | 4-6 nedelja | ❌ Nedostaje |
| **UKUPNO** | **23** | **24-32 nedelje** | |

---

## ✅ Preporuke

### Odmah (P0)
1. **Authentication & Authorization** - Bez ovoga sistem nije siguran
2. **Bulk Operations** - Kritično za UX
3. **Array Operations** - Kritično za storage management

### Kratkoročno (P1)
1. **Scheduling System** - Važno za automatizaciju
2. **Progress Tracking** - Kritično za UX
3. **Activity Logging** - Važno za audit

### Dugoročno (P2-P3)
1. **Hardware Info** - Korisno ali nije kritično
2. **Server Updates** - Korisno za maintenance
3. **Integracije** - Grafana, SSL, Subscription

---

*Dokument kreiran na osnovu analize verzije 2289 i trenutnog stanja ggNET2.*

