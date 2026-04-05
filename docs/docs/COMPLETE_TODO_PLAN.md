# Kompletan TODO Plan za ggNET2

**Datum kreiranja:** 2025-11-26  
**Bazirano na:** Analiza svih `.md` fajlova u projektu (170+ fajlova)  
**Status:** 📋 Master TODO Lista - Kompletan Pregled

---

## 📊 Pregled

Ovaj dokument sadrži kompletan TODO plan izvučen iz:
- **170+ `.md` fajlova** u projektu
- **`docs/` folder** - sve dokumentacije (backend, frontend, architecture, scripts, windows_client, analysis)
- **Root folder** - status dokumenti, deployment guides, next steps plans
- **Implementation plans** - svi planovi implementacije
- **Code-level TODOs** - TODO komentari direktno u kodu
- **Testing checklists** - svi test planovi
- **Deployment guides** - deployment i production readiness

Organizovan po prioritetima (P0-P3) i kategorijama (Backend, Frontend, Testing, Deployment, Dokumentacija).

### 📋 Sadržaj Dokumenta

1. **P0 - Kritično za MVP** (6 funkcionalnosti, ~80 TODO stavki)
2. **P1 - Visok Prioritet** (6 funkcionalnosti, ~60 TODO stavki)
3. **P2 - Srednji Prioritet** (5 funkcionalnosti, ~40 TODO stavki)
4. **P3 - Nizak Prioritet** (6 funkcionalnosti, ~20 TODO stavki)
5. **Frontend Tasks** (T-Array, T-Images, T-Settings, T-Shared, ~150 TODO stavki)
6. **Advanced Frontend** (Array Advanced, VM Advanced, Scheduler Advanced, ~80 TODO stavki)
7. **Implementation Checklists** (~120 TODO stavki)
8. **Code-Level TODOs** (~5 TODO stavki)
9. **Testing & Validation** (~100 TODO stavki)
10. **Deployment & Production** (~50 TODO stavki)
11. **Dokumentacija** (~10 TODO stavki)
12. **System Setup** (~15 TODO stavki)

### Statistika

- **P0 (Kritično):** 6 funkcionalnosti
- **P1 (Visok):** 6 funkcionalnosti  
- **P2 (Srednji):** 5 funkcionalnosti
- **P3 (Nizak):** 6 funkcionalnosti
- **Frontend Tasks:** 5 glavnih taskova
- **Dokumentacija:** 5 TODO stavki

**Ukupno:** 28+ funkcionalnosti + frontend tasks + dokumentacija + testing + deployment

**Ukupno TODO Stavki:** ~720+

### Kategorije TODO Stavki

1. **P0 - Kritično (Backend + Frontend):** ~80 stavki
2. **P1 - Visok Prioritet:** ~60 stavki
3. **P2 - Srednji Prioritet:** ~40 stavki
4. **P3 - Nizak Prioritet:** ~20 stavki
5. **Frontend Tasks (T-Array, T-Images, T-Settings, T-Shared):** ~150 stavki
6. **Advanced Frontend (Array Advanced, VM Advanced, Scheduler Advanced):** ~80 stavki
7. **Implementation Checklists:** ~120 stavki
8. **Code-Level TODOs:** ~5 stavki
9. **Testing & Validation:** ~100 stavki
10. **Deployment & Production:** ~50 stavki
11. **Dokumentacija:** ~10 stavki
12. **System Setup:** ~15 stavki

**Ukupno:** ~720+ TODO stavki

---

## 🔴 P0 - Kritično za MVP (Must Have)

### 1. Authentication & Authorization ⚠️ KRITIČNO

**Status:** ✅ Implementacija kompletna (osim migracija)  
**Prioritet:** 🔴 P0  
**Vreme:** 2-3 nedelje

#### TODO Stavke:

- [ ] **Database Migrations**
  - [ ] Kreirati Alembic migration za auth tabele
  - [ ] Proveriti migration fajl (`alembic/versions/XXXX_add_p0_modules.py`)
  - [ ] Proveriti da li su sve tabele uključene:
    - [ ] `users`, `roles`, `permissions`
    - [ ] `user_roles`, `role_permissions`
  - [ ] Proveriti foreign keys i indexes
  - [ ] Primena migracije: `alembic upgrade head`
  - [ ] Backup baze pre migracije

- [ ] **Inicijalizacija Default Podataka**
  - [ ] Pokrenuti `python -m app.backend.auth.init_default_data`
  - [ ] Proveriti da li su kreirani default roles (admin, operator, viewer)
  - [ ] Proveriti da li su kreirani default permissions
  - [ ] Kreirati prvi admin user (admin/admin123)

- [ ] **API Testing**
  - [ ] Test login endpoint: `POST /api/users/login`
  - [ ] Test protected endpoints sa tokenom
  - [ ] Test RBAC permissions
  - [ ] Security testovi (SQL injection, XSS)

- [ ] **Frontend Integration**
  - [ ] Login page
  - [ ] Token storage (localStorage/sessionStorage)
  - [ ] Protected routes
  - [ ] User menu/profile
  - [ ] Role-based UI restrictions

**Dokumentacija:** `docs/backend/auth_implementation_plan.md`, `docs/backend/AUTH_IMPLEMENTATION_STATUS.md`

---

### 2. Bulk Operations - Machines ⚠️ KRITIČNO

**Status:** ✅ Backend implementacija kompletna  
**Prioritet:** 🔴 P0  
**Vreme:** 1 nedelja

#### TODO Stavke:

- [ ] **Backend Testing**
  - [ ] Test `POST /api/machines/batch` endpoint
  - [ ] Test `POST /api/machines/restart` (bulk)
  - [ ] Test `POST /api/machines/shutdown` (bulk)
  - [ ] Test `POST /api/machines/wake` (bulk)
  - [ ] Test `POST /api/machines/turnOn` (bulk)
  - [ ] Test progress tracking preko WebSocket-a
  - [ ] Test error handling za bulk operacije

- [ ] **Frontend Integration**
  - [ ] Bulk action buttons (Machines page)
  - [ ] Batch operation status modal
  - [ ] Progress indicators
  - [ ] WebSocket integration za real-time updates
  - [ ] Multi-select checkbox functionality

**Dokumentacija:** `docs/backend/bulk_operations_machines_plan.md`, `docs/backend/BULK_OPERATIONS_IMPLEMENTATION_STATUS.md`

---

### 3. Bulk Operations - Images ⚠️ KRITIČNO

**Status:** ✅ Backend implementacija kompletna  
**Prioritet:** 🔴 P0  
**Vreme:** 2 nedelje

#### TODO Stavke:

- [ ] **Backend Testing**
  - [ ] Test `GET /api/batchImageOperations/history`
  - [ ] Test `POST /api/batchImageOperations/local/backup`
  - [ ] Test `POST /api/batchImageOperations/remote/backup`
  - [ ] Test `POST /api/batchImageOperations/local/restore`
  - [ ] Test `POST /api/batchImageOperations/remote/restore`
  - [ ] Test `POST /api/batchImageOperations/local/test`
  - [ ] Test `POST /api/batchImageOperations/remote/test`
  - [ ] Test progress tracking

- [ ] **Frontend Integration**
  - [ ] Batch operations UI za images
  - [ ] Progress tracking modal
  - [ ] Local/remote backup selection
  - [ ] Restore workflow UI

**Dokumentacija:** `docs/backend/bulk_operations_images_plan.md`, `docs/backend/BULK_IMAGE_OPERATIONS_IMPLEMENTATION_STATUS.md`

---

### 4. Writebacks Management ⚠️ KRITIČNO

**Status:** ✅ Backend implementacija kompletna  
**Prioritet:** 🔴 P0  
**Vreme:** 1 nedelja

#### TODO Stavke:

- [ ] **Backend Testing**
  - [ ] Test `POST /api/machines/{id}/writebacks/{writebackPath}/keep`
  - [ ] Test `POST /api/machines/{id}/writebacks/keep`
  - [ ] Test `DELETE /api/machines/{id}/writebacks/{writebackPath}`
  - [ ] Test `DELETE /api/images/{path}/writebacks`

- [ ] **Frontend Integration**
  - [ ] Keep writeback button per machine
  - [ ] Keep all writebacks button
  - [ ] Delete writeback confirmation
  - [ ] Writeback state display

**Dokumentacija:** `docs/backend/writebacks_management_plan.md`, `docs/backend/WRITEBACKS_IMPLEMENTATION_STATUS.md`

---

### 5. Array Operations - Drive Management ⚠️ KRITIČNO

**Status:** ✅ Backend implementacija kompletna  
**Prioritet:** 🔴 P0  
**Vreme:** 2 nedelje

#### TODO Stavke:

- [ ] **Backend Testing**
  - [ ] Test `GET /api/drives/free`
  - [ ] Test `GET /api/drives/{driveName}/smart`
  - [ ] Test `POST /api/array/drives/{driveUuid}/online`
  - [ ] Test `POST /api/array/drives/{driveUuid}/offline`
  - [ ] Test `POST /api/array/drives` (Add drives)
  - [ ] Test `POST /api/array/drives/{oldDriveUuid}/replace`
  - [ ] Test `DELETE /api/array/drives/{driveUuid}`
  - [ ] Test `POST /api/array/extend`
  - [ ] Test `POST /api/array/export`
  - [ ] Test `DELETE /api/array`

- [ ] **Frontend Integration**
  - [ ] Drives list page
  - [ ] Drive details (SMART data)
  - [ ] Array creation wizard
  - [ ] Drive add/remove/replace UI
  - [ ] Drive action menu (Details, Identify, Mark Failed, Replace, Remove, View SMART)

**Dokumentacija:** `docs/backend/array_drive_management_plan.md`, `docs/backend/ARRAY_DRIVE_MANAGEMENT_IMPLEMENTATION_STATUS.md`

---

### 6. Array Operations - TRIM Management ⚠️ KRITIČNO

**Status:** ✅ Backend implementacija kompletna  
**Prioritet:** 🔴 P0  
**Vreme:** 1 nedelja

#### TODO Stavke:

- [ ] **Backend Testing**
  - [ ] Test `POST /api/array/trim/resume`
  - [ ] Test `POST /api/array/trim/suspend`
  - [ ] Test `POST /api/array/trim/run`
  - [ ] Test `POST /api/array/trim/cancel`
  - [ ] Test `GET /api/array/trim/status`
  - [ ] Test `GET /api/array/{pool_name}/rebuild/status` (novi endpoint)

- [ ] **Frontend Integration**
  - [ ] TRIM status display
  - [ ] TRIM control buttons (resume/suspend/cancel)
  - [ ] TRIM progress indicator
  - [ ] TRIM settings page
  - [ ] TRIM scheduler UI

**Dokumentacija:** `docs/backend/array_trim_management_plan.md`, `docs/backend/ARRAY_TRIM_MANAGEMENT_IMPLEMENTATION_STATUS.md`

---

## 🟠 P1 - Visok Prioritet (Should Have)

### 7. Scheduling System

**Status:** ❌ Nedostaje  
**Prioritet:** 🟠 P1  
**Vreme:** 3-4 nedelje

#### TODO Stavke:

- [ ] **Backend Implementation**
  - [ ] Kreirati `app/backend/scheduler/` modul
  - [ ] Database schema za scheduling (machineActions, machineBootStates, behaviors, executions)
  - [ ] Implementirati `SchedulerManager`
  - [ ] Implementirati `BehaviorManager`
  - [ ] Implementirati `ExecutionTracker`
  - [ ] Background task scheduler (APScheduler ili Celery)
  - [ ] API endpoints:
    - [ ] `GET /api/schedule/machineActions`
    - [ ] `POST /api/schedule/machineActions`
    - [ ] `GET /api/schedule/machineBootStates`
    - [ ] `POST /api/schedule/machineBootStates`
    - [ ] `GET /api/schedule/behaviors`
    - [ ] `POST /api/schedule/behaviors`
    - [ ] `GET /api/schedule/executions`
    - [ ] `GET /api/schedule/executions/nextScheduled`

- [ ] **Frontend Integration**
  - [ ] Scheduler tab u Settings
  - [ ] Machine actions scheduling UI
  - [ ] Boot states scheduling UI
  - [ ] Behaviors management UI
  - [ ] Executions tracking UI

**Dokumentacija:** `docs/analysis/implementation_priorities_ggnet2.md`

---

### 8. Progress Tracking - WebSocket Events

**Status:** ⚠️ Delimično (WebSocket postoji)  
**Prioritet:** 🟠 P1  
**Vreme:** 2 nedelje

#### TODO Stavke:

- [ ] **Backend Implementation**
  - [ ] Real-time progress tracking za sve dugotrajne operacije
  - [ ] Array rebuild/trim progress events
  - [ ] Image import/backup progress events
  - [ ] Batch operations progress events
  - [ ] WebSocket events:
    - [ ] `array_rebuild_progress_updated`
    - [ ] `array_trim_progress_updated`
    - [ ] `image_import_progress_updated`
    - [ ] `image_backup_restore_progress_updated`
    - [ ] `batch_operation_progress_updated`

- [ ] **Frontend Integration**
  - [ ] WebSocket client integration
  - [ ] Progress bars za sve operacije
  - [ ] Real-time updates u UI

**Dokumentacija:** `docs/analysis/implementation_priorities_ggnet2.md`

---

### 9. Activity Logging & Audit Trail

**Status:** ❌ Nedostaje  
**Prioritet:** 🟠 P1  
**Vreme:** 1-2 nedelje

#### TODO Stavke:

- [ ] **Backend Implementation**
  - [ ] Kreirati `app/backend/activity/` modul
  - [ ] Database schema za activity logs
  - [ ] Implementirati `ActivityLogger`
  - [ ] Implementirati `AuditTrail`
  - [ ] API endpoints:
    - [ ] `GET /api/activityLog`
    - [ ] `GET /api/activityLog/export`
    - [ ] `GET /api/activityLog/actions`

- [ ] **Frontend Integration**
  - [ ] Activity log viewer
  - [ ] Export functionality
  - [ ] Filter by action type

**Dokumentacija:** `docs/analysis/implementation_priorities_ggnet2.md`

---

### 10. Server Management API

**Status:** ❌ Nedostaje  
**Prioritet:** 🟠 P1  
**Vreme:** 1 nedelja

#### TODO Stavke:

- [ ] **Backend Implementation**
  - [ ] Kreirati `app/backend/server/` modul
  - [ ] Implementirati `ServerManager`
  - [ ] Implementirati `ServiceManager`
  - [ ] API endpoints:
    - [ ] `GET /api/server/ping`
    - [ ] `GET /api/server`
    - [ ] `GET /api/server/public`
    - [ ] `GET /api/server/ram`
    - [ ] `PUT /api/server/ram`
    - [ ] `GET /api/server/services`
    - [ ] `POST /api/server/services/{serviceId}/restart`
    - [ ] `POST /api/server/reboot`

- [ ] **Frontend Integration**
  - [ ] Server info display
  - [ ] RAM management UI
  - [ ] Services management UI

**Dokumentacija:** `docs/analysis/implementation_priorities_ggnet2.md`

---

### 11. Image Snapshot Management

**Status:** ⚠️ Delimično (osnovni snapshot operacije)  
**Prioritet:** 🟠 P1  
**Vreme:** 1 nedelja

#### TODO Stavke:

- [ ] **Backend Implementation**
  - [ ] API endpoints:
    - [ ] `POST /api/images/{path}/snapshots/{snapshotPath}/default`
    - [ ] `POST /api/images/{path}/snapshots/{snapshotPath}/lock`
    - [ ] `DELETE /api/images/{path}/snapshots/{snapshotPath}` (proširiti postojeći)

- [ ] **Frontend Integration**
  - [ ] Set default snapshot action
  - [ ] Lock snapshot action
  - [ ] Snapshot timeline component
  - [ ] Promote to default functionality
  - [ ] Assign to machines functionality

**Dokumentacija:** `docs/analysis/implementation_priorities_ggnet2.md`, `docs/frontend/t-images.plan.md`

---

### 12. Image Import/Export

**Status:** ⚠️ Delimično  
**Prioritet:** 🟠 P1  
**Vreme:** 2 nedelje

#### TODO Stavke:

- [ ] **Backend Implementation**
  - [ ] Kreirati `app/backend/images/import_export.py`
  - [ ] Image import (VHD, raw)
  - [ ] Image export
  - [ ] Import progress tracking
  - [ ] Remote image download
  - [ ] API endpoints:
    - [ ] `GET /api/images/imported`
    - [ ] `POST /api/images/imported/{importId}/cancel`
    - [ ] `POST /api/images/imported/{importId}/finish`
    - [ ] `POST /api/images/import/vhd`
    - [ ] `POST /api/images/import`
    - [ ] `POST /api/images/{sourceSnapshotPath}/copy`
    - [ ] `GET /api/images/remote`
    - [ ] `POST /api/images/remote/{imageUuid}/download`

- [ ] **Frontend Integration**
  - [ ] Import workflow UI
  - [ ] Export workflow UI
  - [ ] Progress tracking
  - [ ] Remote download UI

**Dokumentacija:** `docs/analysis/implementation_priorities_ggnet2.md`, `docs/frontend/t-images.plan.md`

---

## 🟡 P2 - Srednji Prioritet (Nice to Have)

### 13. Machines Hardware Info

**Status:** ❌ Nedostaje  
**Prioritet:** 🟡 P2  
**Vreme:** 1 nedelja

#### TODO Stavke:

- [ ] **Backend Implementation**
  - [ ] API endpoints:
    - [ ] `GET /api/machines/{machineId}/hardware`
    - [ ] `POST /api/machines/{machineId}/hardware/displaysettings`
    - [ ] `GET /api/machines/{machineId}/hardware/displaysettings`
    - [ ] `POST /api/machines/displaysettings` (bulk)

- [ ] **Frontend Integration**
  - [ ] Hardware info display
  - [ ] Display settings management

**Dokumentacija:** `docs/analysis/implementation_priorities_ggnet2.md`

---

### 14. Scheduled Behaviors Integration

**Status:** ❌ Nedostaje  
**Prioritet:** 🟡 P2  
**Vreme:** 1 nedelja

#### TODO Stavke:

- [ ] **Backend Implementation**
  - [ ] API endpoints:
    - [ ] `PUT /api/machines/{id:guid}/scheduledBehavior/{behaviorId:guid}`
    - [ ] `DELETE /api/machines/{id:guid}/scheduledBehavior`

- [ ] **Frontend Integration**
  - [ ] Set scheduled behavior na machine
  - [ ] Remove scheduled behavior

**Dokumentacija:** `docs/analysis/implementation_priorities_ggnet2.md`

---

### 15. Server Updates Management

**Status:** ❌ Nedostaje  
**Prioritet:** 🟡 P2  
**Vreme:** 1-2 nedelje

#### TODO Stavke:

- [ ] **Backend Implementation**
  - [ ] API endpoints:
    - [ ] `GET /api/server/updates`
    - [ ] `POST /api/server/updates/{updateId}/install`
    - [ ] `GET /api/server/updates/progress`

- [ ] **Frontend Integration**
  - [ ] Updates list UI
  - [ ] Install updates UI
  - [ ] Progress tracking

**Dokumentacija:** `docs/analysis/implementation_priorities_ggnet2.md`

---

### 16. Server Commands

**Status:** ❌ Nedostaje  
**Prioritet:** 🟡 P2  
**Vreme:** 1 nedelja

#### TODO Stavke:

- [ ] **Backend Implementation**
  - [ ] API endpoints:
    - [ ] `GET /api/server/commands`
    - [ ] `GET /api/server/commands/lastExecution`
    - [ ] `POST /api/server/commands/run`
    - [ ] `POST /api/server/commands/cancel`

- [ ] **Frontend Integration**
  - [ ] Command runner UI
  - [ ] Command history

**Dokumentacija:** `docs/analysis/implementation_priorities_ggnet2.md`

---

### 17. Structured Settings API

**Status:** ⚠️ Delimično (osnovni settings)  
**Prioritet:** 🟡 P2  
**Vreme:** 1 nedelja

#### TODO Stavke:

- [ ] **Backend Implementation**
  - [ ] API endpoints:
    - [ ] `GET /api/settings/images`
    - [ ] `PUT /api/settings/images`
    - [ ] `GET /api/settings/trim`
    - [ ] `PUT /api/settings/trim`
    - [ ] `GET /api/settings/network`
    - [ ] `PUT /api/settings/network`
    - [ ] `GET /api/settings/boot`
    - [ ] `PUT /api/settings/boot`
    - [ ] `GET /api/settings/auth`
    - [ ] `PATCH /api/settings/auth`

- [ ] **Frontend Integration**
  - [ ] Structured settings UI per category

**Dokumentacija:** `docs/analysis/implementation_priorities_ggnet2.md`, `docs/frontend/t-settings.plan.md`

---

## 🟢 P3 - Nizak Prioritet (Future)

### 18-23. P3 Funkcionalnosti

**Status:** ❌ Nedostaje  
**Prioritet:** 🟢 P3

#### TODO Stavke:

- [ ] Release Streams API
- [ ] Features API
- [ ] Grafana Integration
- [ ] SSL Certificates Management
- [ ] Subscription Management
- [ ] Productboard Integration

**Dokumentacija:** `docs/analysis/implementation_priorities_ggnet2.md`

---

## 🎨 Frontend Tasks

### T-Array (Storage Page)

**Status:** 📋 Plan kreiran  
**Dokumentacija:** `docs/frontend/t-array.plan.md`

#### TODO Stavke:

- [ ] **Task 1: Health Status & Visual Indicators**
  - [ ] Add status LED component (Green/Amber/Red)
  - [ ] Display RAID type badge
  - [ ] Add visual cues for degraded/rebuilding drives
  - [ ] Update drive row styling for status indicators

- [ ] **Task 2: Drive Action Menu**
  - [ ] Implement overflow menu (⋮) for each drive row
  - [ ] Add all drive actions (Details, Identify, Mark Failed, Replace, Remove, View SMART)
  - [ ] Add role indicators (data/cache/spare)
  - [ ] Display temperature and Last Seen in drive table
  - [ ] Wire actions to backend API endpoints

- [ ] **Task 3: Rebuild/Resilver Progress**
  - [ ] Create rebuild progress component
  - [ ] Display ETA and resilver speed
  - [ ] Lock conflicting operations during rebuild
  - [ ] Add notification when rebuild completes
  - [ ] Integrate with WebSocket/SSE for real-time updates

- [ ] **Task 4: Add Drive Wizard Enhancements**
  - [ ] Add Step 1: Pre-flight checklist
  - [ ] Add validation: capacity ≥ largest drive
  - [ ] Add SSD/HDD mixing warning
  - [ ] Add estimated rebuild window
  - [ ] Integrate resilver progress after submission

- [ ] **Task 5: Replace Drive Flow**
  - [ ] Create replace drive modal/wizard
  - [ ] Add physical swap instructions
  - [ ] Implement mark replaced functionality
  - [ ] Add rebuild progress during replacement

- [ ] **Task 6: Remove Drive Flow**
  - [ ] Add validation: Only allow for RAID levels that support removal (disallow RAID0)
  - [ ] Add confirmation dialog with safeguards
  - [ ] Add status updates

- [ ] **Task 7: Snapshot & Writeback Automation**
  - [ ] Add retention controls inline
  - [ ] Add toggle for automation with tooltip
  - [ ] Add upcoming cleanup schedule display
  - [ ] Add "Run Now" button with confirmation

- [ ] **Task 8: TRIM Scheduler UI**
  - [ ] TRIM scheduler status display
  - [ ] Last run timestamp
  - [ ] Cadence selection (daily/weekly/custom cron)
  - [ ] Target pools selection
  - [ ] SAN compatibility warning
  - [ ] Log of recent TRIM runs with durations

- [ ] **Task 9: Alerts & Edge Cases**
  - [ ] Persistent banner when array is DEGRADED or FAULTED
  - [ ] Link to relevant KB articles
  - [ ] Reserved space threshold breach highlighting
  - [ ] Toast notifications for threshold breaches
  - [ ] Hide destructive actions during rebuild
  - [ ] Acknowledgement required for irreversible operations

- [ ] **Task 10: Auto-refresh & Real-time Updates**
  - [ ] Auto-refresh for array metrics (remove manual "Sync with backend")
  - [ ] WebSocket/SSE for real-time resilver progress
  - [ ] Streaming updates for capacity stats

---

### T-Images (Images Page)

**Status:** 📋 Plan kreiran  
**Dokumentacija:** `docs/frontend/t-images.plan.md`

#### TODO Stavke:

- [ ] **Task 1: Image Catalog Enhancements**
  - [ ] Implement card/table hybrid view
  - [ ] Add all metadata columns (Base Size, Latest Snapshot, Writebacks, Last Modified, Assigned Machines)
  - [ ] Add default sort by last updated
  - [ ] Add default boot image badge
  - [ ] Add compatibility hints for paired images
  - [ ] Implement search/filter functionality
  - [ ] Add combined filter (All/System/Game)

- [ ] **Task 2: Create Image Wizard Enhancements**
  - [ ] Convert to multi-step wizard (Details → Source → Summary)
  - [ ] Add source selection (clone vs. upload)
  - [ ] Add OS template selection for system images
  - [ ] Add storage impact warnings
  - [ ] Implement disk space validation
  - [ ] Add support notes and microcopy
  - [ ] Add tooltips and help text

- [ ] **Task 3: Snapshot Management**
  - [ ] Create snapshot timeline component
  - [ ] Add Promote to Default action
  - [ ] Add Assign to Machines action
  - [ ] Implement dependency check before deletion
  - [ ] Add snapshot metadata display (author, notes)
  - [ ] Add protection/pinning indicators
  - [ ] Integrate with automation policy

- [ ] **Task 4: Writeback Handling**
  - [ ] Add Apply Writebacks button per image
  - [ ] Implement per-image retention override
  - [ ] Add warning banner for large writebacks
  - [ ] Enhance writeback size display

- [ ] **Task 5: Image Settings & Metadata**
  - [ ] Implement edit description/changelog/labels
  - [ ] Display checksum and build version
  - [ ] Add advanced options panel
  - [ ] Implement copy image functionality
  - [ ] Implement edit image functionality

- [ ] **Task 6: Bulk Operations**
  - [ ] Implement multi-select UI
  - [ ] Add bulk delete snapshots
  - [ ] Add bulk change defaults
  - [ ] Add bulk export metadata
  - [ ] Add progress feedback
  - [ ] Add mounted snapshot check

- [ ] **Task 7: Backup/Restore Workflows**
  - [ ] Create local backup modal/workflow
  - [ ] Create remote backup modal/workflow
  - [ ] Implement restore flows
  - [ ] Add checksum validation
  - [ ] Add CLI instructions link

- [ ] **Task 8: Automation Integration**
  - [ ] Display upcoming automated deletions
  - [ ] Add protect snapshot from automation
  - [ ] Add retention settings UI
  - [ ] Display cleanup schedule

- [ ] **Task 9: Edge Cases**
  - [ ] Handle missing base snapshot
  - [ ] Add upload feature with progress
  - [ ] Improve error handling
  - [ ] Add empty states

---

### T-Settings (Settings Page)

**Status:** 📋 Plan kreiran  
**Dokumentacija:** `docs/frontend/t-settings.plan.md`

#### TODO Stavke:

- [ ] **Task 1: Settings Data Integration**
  - [ ] Map API settings response to component state
  - [ ] Implement settings loading from API
  - [ ] Handle settings not found (defaults)
  - [ ] Add error handling for settings fetch

- [ ] **Task 2: General Settings**
  - [ ] Implement RAM allocation sliders
  - [ ] Add RAM sum validation
  - [ ] Add Release Stream dropdown
  - [ ] Add UI Preferences section
  - [ ] Add Server Metadata section with copy buttons
  - [ ] Implement "Maximize size" toggle
  - [ ] Add manual override fields
  - [ ] Add inline validation
  - [ ] Implement save with debouncing

- [ ] **Task 3: Network Settings**
  - [ ] Create bridge status card component
  - [ ] Implement auto-configure button with spinner
  - [ ] Create interfaces table
  - [ ] Add DHCP/PXE controls
  - [ ] Add network config log viewer
  - [ ] Implement error handling and retry
  - [ ] Add bridge readiness status indicators

- [ ] **Task 4: Array & Images Settings**
  - [ ] Implement interactive retention controls
  - [ ] Add automated cleanup scheduling UI
  - [ ] Add next cleanup run preview
  - [ ] Add TRIM scheduler configuration
  - [ ] Display current space usage context
  - [ ] Add validation for threshold values

- [ ] **Task 5: Secure Boot Settings**
  - [ ] Create secure boot status card
  - [ ] Implement enable/disable toggle with confirmation
  - [ ] Add certificate upload field
  - [ ] Add validation result display
  - [ ] Add guidance text and links

- [ ] **Task 6: Common Features**
  - [ ] Implement unsaved changes detection
  - [ ] Add navigation warning with unsaved changes
  - [ ] Implement save functionality (wire to API)
  - [ ] Implement cancel/reset functionality
  - [ ] Add success toast and timestamp
  - [ ] Create history drawer component
  - [ ] Add localStorage for last visited tab
  - [ ] Make header sticky with breadcrumb

- [ ] **Task 7: Additional Tabs**
  - [ ] Implement Scheduler tab
  - [ ] Implement Software Update tab
  - [ ] Implement Subscriptions tab
  - [ ] Implement Account tab
  - [ ] Implement Employees tab

---

### T-Shared (Shared Components & Utilities)

**Status:** 📋 Plan kreiran  
**Dokumentacija:** `docs/frontend/t-shared.plan.md`

#### TODO Stavke:

- [ ] **Task 1: Create Shared Utilities**
  - [ ] Create `utils/formatters.js` with all formatting functions
  - [ ] Create `utils/validators.js` with validation functions
  - [ ] Create `utils/transformers.js` with data transformation functions
  - [ ] Update all pages to use shared utilities
  - [ ] Remove duplicate formatting functions

- [ ] **Task 2: Create Shared UI Components**
  - [ ] Create StatusLED component
  - [ ] Create ProgressBar component
  - [ ] Create EmptyState component
  - [ ] Create LoadingState component
  - [ ] Create ErrorState component
  - [ ] Create ActionMenu component
  - [ ] Create Wizard component
  - [ ] Create form components (Input, Select, Slider, etc.)

- [ ] **Task 3: Standardize Error Handling**
  - [ ] Create error handling utilities
  - [ ] Create ErrorBoundary component
  - [ ] Add error states to all pages
  - [ ] Standardize error messages

- [ ] **Task 4: Standardize Loading States**
  - [ ] Create LoadingSpinner component
  - [ ] Create LoadingSkeleton component
  - [ ] Standardize loading states across pages

- [ ] **Task 5: Mock Data Management**
  - [ ] Create mock data utilities
  - [ ] Add environment flag for mock mode
  - [ ] Ensure all pages support mock data
  - [ ] Add data source indicator

---

## 📚 Dokumentacija

### TODO Stavke iz `docs/index.md`:

- [ ] Add API authentication documentation
- [ ] Add troubleshooting guides for common issues
- [ ] Add performance tuning guides
- [ ] Add deployment best practices
- [ ] Add security considerations

### TODO Stavke iz `docs/backend/api.md`:

- [ ] Implement JWT authentication (već implementirano, ali treba dokumentovati)
- [ ] Add API versioning
- [ ] Implement rate limiting
- [ ] Add request/response compression
- [ ] Add API documentation (OpenAPI/Swagger)
- [ ] Implement request caching
- [ ] Add metrics collection

---

## 🔧 TODO Stavke iz Koda (Code-Level TODOs)

### Frontend Code TODOs

#### Machines.jsx
- [ ] **Bulk Apply Writebacks** (Line 388)
  - Implement bulk apply writebacks functionality
  - Wire to backend API endpoint
  - Add progress tracking

#### Storage.jsx
- [ ] **Save Configuration** (Line 408)
  - Implement save configuration functionality
  - Wire automation settings to backend API
  - Add success/error handling

- [ ] **Cancel Configuration** (Line 435)
  - Implement cancel configuration functionality
  - Reset form to original values
  - Add confirmation dialog

- [ ] **Replace Drive Modal** (Line 849)
  - Open replace drive modal from drive action menu
  - Implement replace drive wizard flow

#### Images.jsx
- [ ] **Copy Image Functionality** (Line 230)
  - Implement copy image functionality
  - Create copy image modal/wizard
  - Wire to backend API endpoint

- [ ] **Edit Image Functionality** (Line 237)
  - Implement edit image functionality
  - Create edit image modal
  - Wire to backend API endpoint

---

## 🎨 Advanced Frontend Implementation Tasks

### Array Advanced Operations

**Status:** 📋 Plan kreiran  
**Dokumentacija:** `docs/frontend/array-advanced-implementation.md`

#### TODO Stavke:

- [ ] **Add Drive Wizard Enhancements**
  - Multi-step dialog (Checklist → Drive Selection → Summary)
  - Validate capacity requirements (new drive ≥ largest existing)
  - Show rebuild warning banner and require acknowledgement checkbox
  - Hook up to rebuild progress UI (progress bar, ETA, disable conflicting actions)

- [ ] **Remove Drive Flow**
  - Dialog presenting drive details, RAID support check, typed confirmation
  - Block action for unsupported RAID levels (e.g., RAID0)
  - Display inline progress states (queued, in-progress, completed)

- [ ] **Replace Drive Flow**
  - Wizard guiding physical swap: prompt to install drive, select replacement, confirm
  - Update progress indicators and post-completion health check prompt

- [ ] **Take Offline / Bring Online**
  - Confirmation dialogs with reason text and warnings
  - Update drive status icons immediately after action

- [ ] **RAID Conversion Tool**
  - Advanced menu entry launching wizard with Overview → Preparation → Execution → Finalization steps
  - Include multi-factor confirmation (checkbox + typed phrase)
  - Provide progress tracker that survives page reload (state persistence)

- [ ] **Forklift Upgrade Guide**
  - Implement guided modal/timeline with step-by-step checklist
  - Provide export/print option (runbook PDF)
  - Integrate health diagnostics summary at completion

- [ ] **History & Reporting**
  - Add history tab or panel summarizing advanced operations (user, timestamp, drives)
  - Allow download of operation report (CSV/JSON)

### Virtual Machines Advanced

**Status:** 📋 Plan kreiran  
**Dokumentacija:** `docs/frontend/virtual-machines-advanced-implementation.md`

#### TODO Stavke:

- [ ] **Enablement Checklist UI**
  - Banner/card summarising prerequisites with status indicators (BIOS virtualization, static IP, clients powered off)
  - Link to troubleshooting guide (re-run bridge script, view logs)

- [ ] **Ops Runbooks Integration**
  - Provide quick-access panel for rolling update workflow (snapshot → update → promote)
  - Buttons/links for "Force Sync with ggLeap" and "Apply Writebacks"
  - Option to launch backup/restore flows (reuse from Images plan) for VM recovery

- [ ] **Resource Monitoring**
  - Display VM RAM allocation vs available pool (tying into Settings data)
  - Show writeback usage specific to VMs with warnings when approaching thresholds

- [ ] **Troubleshooting Helpers**
  - Inline tips for console issues (noVNC reconnect, popup block instructions)
  - Quick action to re-run bridge configuration (if allowed in UI)
  - Provide microcopy for common error messages (insufficient RAM, disk space)

- [ ] **Operational Actions**
  - Buttons for generate VM report (inventory, snapshots, writebacks)
  - Hooks to guide decommission workflow (unassign, delete, cleanup)

### Scheduler Advanced

**Status:** 📋 Plan kreiran  
**Dokumentacija:** `docs/frontend/scheduler-advanced-implementation.md`

#### TODO Stavke:

- [ ] **Metadata Fetching**
  - Implement service to retrieve behaviour definitions (fields, types, validation rules)
  - Cache metadata with versioning and handle fallbacks if fetch fails

- [ ] **Dynamic Form Rendering**
  - Extend scheduler create/edit wizard to render inputs based on metadata:
    - Field types: text, numeric, dropdown, checkbox, cron expression, custom components
    - Validation messages surfaced inline
  - Group behaviours into categories (Power, Maintenance, Scripts, Custom)

- [ ] **Developer Mode & Test Run**
  - Add toggle to enable "Developer Mode" (role-protected)
  - Provide "Test Run" button that executes behaviour immediately with provided inputs (requires backend support)
  - Display detailed logs/results after test run

- [ ] **Help & Documentation**
  - Inline help text sourced from metadata (description, prerequisites)
  - Link to behaviour documentation or runbook if provided
  - Provide behaviour summary table (name, description, owner/contact)

- [ ] **Feature Flags & Permissions**
  - Integrate feature flag checks to hide beta behaviours
  - Ensure UI respects role permissions for behaviour creation

- [ ] **Error Handling**
  - Show warning banner if metadata fails to load (fall back to static config)
  - Clearly display backend error messages on execution failure
  - Warn about conflicting behaviours (optional)

### Storage Maintenance

**Status:** 📋 Plan kreiran  
**Dokumentacija:** `docs/frontend/storage-maintenance-implementation.md`

#### TODO Stavke:

- [ ] **Automated Cleanup (Snapshots & Writebacks)**
  - Retention settings UI (Settings → Array & Images):
    - Numeric inputs for `Unutilized Snapshots (days)`, `Unprotected Snapshots (count)`, `Inactive Writebacks (days)`
    - On/off toggle for automation with confirmation modal
    - Next run/last run summary, including "Run Now" button
    - Protect/unprotect snapshot list (searchable, tag display)
  - Warning banners:
    - When automation disabled and space risk detected
    - When writebacks exceed safe threshold

- [ ] **Snapshot Retention Ops Checklist**
  - Provide documentation view within UI (link to internal runbook)
  - Add "Checklist" component summarising ops steps (backup reminder, protect critical snapshots)
  - Manual run confirmation wizard referencing best practices
  - Add link to download resulting cleanup report (CSV/JSON)

- [ ] **TRIM Management**
  - TRIM configuration panel in Settings:
    - Toggle `Turn on TRIM`
    - Schedule inputs: `Day of week`, `Start`, `End`
    - Pool selector (checkboxes for SSD-backed pools)
    - Advanced options (pause during rebuild, throttle if applicable)
    - Status card: `Last Run`, `Data Trimmed`, `Next Run`
    - Manual run button with confirmation modal
  - Alerts:
    - Banner when TRIM disabled on SSD arrays
    - Warning if TRIM window conflicts with rebuild or cleanup tasks

- [ ] **Forklift Upgrade Support**
  - Guided wizard/timeline component with phases:
    1. Preparation (disable automation, backup verification, export configuration)
    2. Disk swap steps with checkboxes and instructions
    3. Validation (health checks, machine boot verification)
    4. Finalization (re-enable automation, review logs)
  - Export/print runbook as PDF
  - Progress persistence across sessions
  - Health diagnostics summary post-completion

---

## 🧪 Testing & Validation Tasks

### Backend Testing

**Iz:** `docs/backend/NEXT_STEPS_AFTER_P0.md`, `NEXT_STEPS.md`, `PROJECT_STATUS.md`

#### TODO Stavke:

- [ ] **Authentication & Authorization Testing**
  - [ ] Login/Logout flow
  - [ ] Token refresh
  - [ ] Role-based access control
  - [ ] Permission checking
  - [ ] Security testovi (SQL injection, XSS)

- [ ] **Bulk Operations - Machines Testing**
  - [ ] Bulk restart
  - [ ] Bulk shutdown
  - [ ] Bulk wake
  - [ ] Bulk turn on
  - [ ] Batch status tracking
  - [ ] WebSocket progress updates
  - [ ] Error handling za bulk operacije

- [ ] **Writebacks Management Testing**
  - [ ] List writebacks
  - [ ] Keep writeback
  - [ ] Delete writeback
  - [ ] Keep all writebacks

- [ ] **Bulk Operations - Images Testing**
  - [ ] Local backup
  - [ ] Local restore
  - [ ] Local test
  - [ ] Remote backup
  - [ ] Remote restore
  - [ ] Remote test
  - [ ] Batch status tracking
  - [ ] Progress tracking

- [ ] **Drive Management Testing**
  - [ ] List drives
  - [ ] List free drives
  - [ ] Get SMART data
  - [ ] Sync drives

- [ ] **Array Operations Testing**
  - [ ] Create array
  - [ ] Extend array
  - [ ] Add drive
  - [ ] Remove drive
  - [ ] Replace drive
  - [ ] Online/Offline drive
  - [ ] Export array
  - [ ] Delete array

- [ ] **TRIM Management Testing**
  - [ ] Resume TRIM
  - [ ] Suspend TRIM
  - [ ] Run TRIM
  - [ ] Cancel TRIM
  - [ ] Get TRIM status
  - [ ] Get rebuild status
  - [ ] WebSocket progress updates

### Frontend Testing

**Iz:** `NEXT_STEPS.md`, `PROJECT_STATUS.md`

#### TODO Stavke:

- [ ] **Login Page Testing**
  - [ ] Login form validation
  - [ ] Error handling
  - [ ] Token storage
  - [ ] Redirect after login

- [ ] **Machines Page Testing**
  - [ ] Machine list display
  - [ ] Bulk operations UI
  - [ ] Batch status modal
  - [ ] Progress tracking
  - [ ] Individual machine actions (Turn On, Shutdown, Reboot, Apply Writebacks)
  - [ ] Create VM modal
  - [ ] Machine details modal

- [ ] **Storage Page Testing**
  - [ ] Drive list display
  - [ ] Drive details modal
  - [ ] Free drives modal
  - [ ] Array creation wizard
  - [ ] TRIM status modal
  - [ ] TRIM controls
  - [ ] Rebuild progress tracking
  - [ ] Automation settings
  - [ ] TRIM scheduler UI

- [ ] **Images Page Testing**
  - [ ] Image list display
  - [ ] Batch operations modal
  - [ ] Batch status modal
  - [ ] Image selection
  - [ ] Create image modal
  - [ ] Snapshot management
  - [ ] Writeback handling

- [ ] **Writebacks Page Testing**
  - [ ] Writeback list display
  - [ ] Keep/Delete actions
  - [ ] Machine writebacks

- [ ] **Settings Page Testing**
  - [ ] General settings (RAM sliders, Release Stream, UI Preferences)
  - [ ] Network settings (Bridge, Interfaces, DHCP/PXE)
  - [ ] Array & Images settings (Retention, TRIM scheduler)
  - [ ] Secure Boot settings
  - [ ] Save/Cancel functionality
  - [ ] Unsaved changes detection

- [ ] **Dashboard Testing**
  - [ ] Stats display
  - [ ] Quick actions
  - [ ] Recent activity

### Integration Testing

**Iz:** `NEXT_STEPS.md`

#### TODO Stavke:

- [ ] **Authentication Flow**
  - [ ] Login → Dashboard
  - [ ] Token expiration handling
  - [ ] Auto-logout on 401

- [ ] **Bulk Operations Flow**
  - [ ] Select machines → Bulk operation → Status tracking → Completion
  - [ ] WebSocket real-time updates
  - [ ] Error handling

- [ ] **Image Operations Flow**
  - [ ] Select images → Batch operation → Status tracking → Completion
  - [ ] Progress updates
  - [ ] Error handling

- [ ] **Array Operations Flow**
  - [ ] Create array wizard → Drive selection → Review → Creation
  - [ ] TRIM operations → Status tracking
  - [ ] Error handling

- [ ] **Error Handling Testing**
  - [ ] Network errors
  - [ ] 401 Unauthorized
  - [ ] 403 Forbidden
  - [ ] 404 Not Found
  - [ ] 500 Server Error
  - [ ] Timeout handling
  - [ ] Invalid token handling

---

## 🚀 Deployment & Production Readiness

### Server Deployment

**Iz:** `DEPLOYMENT_GUIDE.md`, `NEXT_STEPS.md`, `PROJECT_STATUS.md`

#### TODO Stavke:

- [ ] **Server Preparation**
  - [ ] Debian/Ubuntu instaliran
  - [ ] Network konfigurisan
  - [ ] Storage pripremljen za ZFS
  - [ ] SSH pristup konfigurisan

- [ ] **Installation**
  - [ ] Clone repository na server
  - [ ] Run installation script (`scripts/install.sh`)
  - [ ] Configure environment variables (`.env`)
  - [ ] Setup PostgreSQL
  - [ ] Initialize database (migrations + default data)
  - [ ] Build frontend
  - [ ] Setup Nginx reverse proxy
  - [ ] Setup systemd services

- [ ] **Post-Installation**
  - [ ] Configure ZFS pool
  - [ ] Configure network (bridge, IP forwarding)
  - [ ] Configure firewall
  - [ ] Setup SSL/TLS (opciono)
  - [ ] Verify all services

- [ ] **Verification**
  - [ ] Backend API responding
  - [ ] Frontend accessible
  - [ ] Database connection working
  - [ ] Login functional
  - [ ] All services running

### Production Readiness

**Iz:** `NEXT_STEPS.md`, `PROJECT_STATUS.md`

#### TODO Stavke:

- [ ] **Code Quality**
  - [ ] Add unit tests (backend)
  - [ ] Add component tests (frontend)
  - [ ] Code cleanup (remove TODOs)
  - [ ] Add error boundaries (frontend)
  - [ ] Improve logging
  - [ ] Add API documentation (OpenAPI/Swagger)

- [ ] **Performance Optimization**
  - [ ] Database query optimization
  - [ ] Frontend bundle size optimization
  - [ ] API response caching
  - [ ] WebSocket connection pooling
  - [ ] Image lazy loading

- [ ] **Security Hardening**
  - [ ] Password strength requirements
  - [ ] Rate limiting
  - [ ] CORS configuration review
  - [ ] Input validation
  - [ ] SQL injection prevention
  - [ ] XSS prevention
  - [ ] Change default admin password
  - [ ] Configure HTTPS/SSL
  - [ ] Review RBAC permissions
  - [ ] Security audit

- [ ] **Monitoring & Logging**
  - [ ] Set up logging
  - [ ] Configure alerts
  - [ ] Performance monitoring
  - [ ] Error tracking

- [ ] **Backup Strategy**
  - [ ] Database backup strategy
  - [ ] Image backup strategy
  - [ ] Configuration backup
  - [ ] Disaster recovery plan

---

## 📋 Implementation Checklists iz Dokumentacije

### Array Implementation Checklist

**Iz:** `docs/frontend/array-implementation.md`

#### TODO Stavke:

- [ ] **Array Overview Banner**
  - [ ] Implement status LED (online/degraded/offline) with RAID badge
  - [ ] Usage bar showing Size/Used/Free/Reserved segments
  - [ ] Include warning threshold indicators and link to Settings > Array & Images

- [ ] **Drive Grid Updates**
  - [ ] Table with columns: Device, Model/Serial, Role, Status, Temperature, Last Seen
  - [ ] Row overflow actions: Details, Identify, Mark Failed, Replace, Remove, View SMART
  - [ ] Details modal displaying serial, firmware, interface, stripe membership
  - [ ] Progress indicators for drives undergoing rebuild/resilvering

- [ ] **Drive Actions**
  - [ ] `Add Drive` wizard integration
  - [ ] `Replace` flow with new drive selection and rebuild monitoring
  - [ ] `Remove Drive` dialog with RAID-level validation (block for RAID0)
  - [ ] `Take Offline` / `Bring Online` confirmation modals with warnings

- [ ] **Snapshot & Writeback Automation**
  - [ ] Inline view of retention settings and upcoming cleanup
  - [ ] Quick toggle to enable/disable automation (with confirm)
  - [ ] Link to detailed plan

- [ ] **TRIM Panel**
  - [ ] Display next/last run summary and manual trigger button
  - [ ] Show data trimmed metrics

- [ ] **Alerts**
  - [ ] Persistent banners for DEGRADED/FAULTED states
  - [ ] Toasts for threshold breaches (reserved space)
  - [ ] Info callouts reminding about rebuild risk during operations

### Images Implementation Checklist

**Iz:** `docs/frontend/images-implementation.md`

#### TODO Stavke:

- [ ] **Catalog View**
  - [ ] Implement type tabs (System/Game) with optional "All" filter
  - [ ] Create card/table hybrid with metadata chips (default tag, writeback counts)
  - [ ] Add search/filter inputs (name, type, assigned machines)

- [ ] **Create Image Wizard**
  - [ ] Build multi-step dialog (Details → Source → Summary)
  - [ ] Include microcopy (placeholders, tooltips for Type/Make Default)
  - [ ] Validate volume size against available space (needs backend data)
  - [ ] Show support note that workflow is recommended for Game images

- [ ] **Snapshot Timeline**
  - [ ] Timeline component showing snapshots with tags (latest, custom)
  - [ ] Actions: Promote, Assign, Delete, Notes (with confirmation prompts)
  - [ ] Tooltips for icon statuses; inline warnings if snapshot is pinned elsewhere

- [ ] **Writeback Management**
  - [ ] Display banner when writebacks exceed threshold
  - [ ] Button to Apply Writebacks referencing machine plan; show progress & result

- [ ] **Metadata Editing**
  - [ ] Inline editable fields (description, changelog, tags)
  - [ ] Advanced section toggles for Protected/Pinned snapshots

- [ ] **Bulk Operations**
  - [ ] Multi-select UI: delete snapshots, change defaults, export metadata
  - [ ] Confirmation dialogues with caution copy

- [ ] **Backup/Restore Workflows**
  - [ ] Provide modal for Local Backup (path selection, progress)
  - [ ] Remote Backup (SSH creds, host validation)
  - [ ] Restore flows with checksum validation summary
  - [ ] Link to CLI instructions for advanced users

### Settings Implementation Checklist

**Iz:** `docs/frontend/settings-implementation.md`

#### TODO Stavke:

- [ ] **Layout & Navigation**
  - [ ] Implement sticky header with breadcrumb, `Save`, `Reset`, and unsaved changes badge
  - [ ] Persist last visited subsection (local storage or query param)

- [ ] **General Tab**
  - [ ] Build RAM allocation component:
    - [ ] `Maximize size` toggle + slider inputs (RAM Cache, VM Max, Server Reserved)
    - [ ] Inline helper text and validation (sum <= total RAM)
  - [ ] Release stream dropdown with microcopy and restart warning modal
  - [ ] Dark mode toggle, default tab layout preferences, language selectors
  - [ ] Read-only metadata (hostname, version, uptime) with copy buttons

- [ ] **Network Tab**
  - [ ] Bridge status card with red/green states and descriptive text
  - [ ] `Auto-Configure Bridge` button; show spinner and status log
  - [ ] NIC table with roles, link speed; toggles for DHCP/PXE services
  - [ ] Error banner area for failed configuration attempts (with retry)

- [ ] **Array & Images Tab**
  - [ ] Retention controls: numeric inputs for unutilized/unprotected snapshots, inactive writebacks
  - [ ] Reserved disk space and warning threshold inputs with usage meter
  - [ ] Integration with TRIM scheduler component
  - [ ] Upcoming cleanup schedule preview + manual run button

- [ ] **Secure Boot Tab**
  - [ ] Status summary card for clients/VMs
  - [ ] Toggle with hardware prerequisite warning
  - [ ] Certificate upload component validating `.crt`/`.pem`
  - [ ] Confirmation modal outlining restart requirements

- [ ] **Global UX**
  - [ ] Unsaved changes detection per tab
  - [ ] Toast notifications on save success/failure
  - [ ] History drawer showing last 5 changes (optional toggle)

### Machines Implementation Checklist

**Iz:** `docs/frontend/machines-implementation.md`

#### TODO Stavke:

- [ ] **Table Enhancements**
  - [ ] Implement server-side pagination & filtering
  - [ ] Add column chooser modal with persistence
  - [ ] Update row styling to reveal overflow actions on hover

- [ ] **Status & Snapshot Icons**
  - [ ] Integrate icon set described in plan (ggLeap integration, warning, exclamation, link speed, keep writebacks)
  - [ ] Ensure tooltip copy matches microcopy
  - [ ] Join image snapshot metadata to machine records (API update may be required)

- [ ] **Machine Settings Modal**
  - [ ] Add Hardware tab (read-only fields)
  - [ ] Add Advanced tab with `Keep Writebacks` toggle and snapshot override drop-downs
  - [ ] Validate VM Settings tab toggles when machine is VM

- [ ] **Bulk Operations**
  - [ ] Update bulk toolbar for multi-select: Reboot, Turn Off, Turn On, Edit Selected
  - [ ] Implement bulk edit modal matching documented fields, including confirm checkbox
  - [ ] Display progress indicator for bulk actions (success/failure toasts)

- [ ] **Create VM Button**
  - [ ] Conditionally render button based on VM enablement flag
  - [ ] Link to VM creation workflow

- [ ] **Deletion & Confirmations**
  - [ ] Ensure Delete, Remove Drive, Take Offline actions require confirm checkbox/type-to-confirm
  - [ ] Provide undo banner where feasible

### Virtual Machines Implementation Checklist

**Iz:** `docs/frontend/virtual-machines-implementation.md`

#### TODO Stavke:

- [ ] **VM Enablement Banner**
  - [ ] Checklist UI (BIOS virtualization, static IP, powered-off clients)
  - [ ] Enable VMs button with progress spinner and success/error feedback
  - [ ] Link to admin manual for troubleshooting

- [ ] **Create VM Dialog**
  - [ ] Form fields: Name, System Image, Game Image, vCPUs, Boot Mode, Drives Connection, RAM Size
  - [ ] Input validation (RAM limits vs reserved pool, CPU >= 1)
  - [ ] Contextual tips for Local vs Network drives
  - [ ] Submit flow with loading state and toast on success

- [ ] **VM Settings Tab**
  - [ ] Mirror creation form with existing values
  - [ ] Display warnings that changes require reboot
  - [ ] Support snapshot override dropdowns (system/game)

- [ ] **Control Surface Enhancements**
  - [ ] Overflow actions: Turn On, Shutdown, Reboot, Control VM, Open in New Tab, Full Screen
  - [ ] noVNC embed with toolbar (share link TTL 60s)
  - [ ] Popup blocker fallback messaging

- [ ] **Status Indicators**
  - [ ] VM-specific tags (Powered Off, Running, Updating)
  - [ ] RAM pool usage bar referencing Settings slider
  - [ ] Licensing banner (ggLeap seat usage)

- [ ] **Error Handling UI**
  - [ ] Display bridge configuration errors with link to Settings > Network
  - [ ] Show inline messages for creation failures (insufficient RAM, missing bridge)
  - [ ] Reconnect prompt when control session expires

### Scheduler Implementation Checklist

**Iz:** `docs/frontend/scheduler-implementation.md`

#### TODO Stavke:

- [ ] **Scheduler Dashboard**
  - [ ] Implement jobs table with columns: Name, Task Type, Scope, Next Run, Recurrence, Status
  - [ ] Add filters (task type, status, next run window) and summary cards (active, paused, failures)
  - [ ] Provide bulk actions (Pause, Resume, Delete) with confirm dialogs

- [ ] **Schedule Detail Panel**
  - [ ] Side panel showing description, creator, recurrence string, targets, recent history
  - [ ] Buttons for Edit, Duplicate, Delete, View Full History

- [ ] **History View**
  - [ ] Full-page or modal list of executions with filters and log download
  - [ ] Inline status indicators and duration

- [ ] **Create/Edit Flow**
  - [ ] Multi-step wizard: Task Selection → Target Selection → Timing/Recurrence → Options → Review
  - [ ] Support standard frequencies + custom cron expression (with validation & preview)
  - [ ] Conflict detection UI for overlapping jobs (optional warning)

- [ ] **Run Now & Notifications**
  - [ ] Add "Run Now" button with confirmation
  - [ ] Configure notification toggles (email, in-app, webhook) per job
  - [ ] Summaries for next 24h tasks (card or panel)

- [ ] **Error Handling & Pause Mode**
  - [ ] Display failure banner with error details and retry option
  - [ ] Global banner when scheduler paused (maintenance window)

- [ ] **Dynamic Behaviour Support**
  - [ ] Fetch behaviour metadata to render custom fields
  - [ ] Developer mode toggle to expose test run functionality

---

## 🔧 System Utilities & Setup

### TODO Stavke iz `docs/backend/NEXT_STEPS_AFTER_P0.md`:

- [ ] **Install System Utilities**
  - [ ] Install `util-linux` (drive management)
  - [ ] Install `smartmontools` (SMART data)
  - [ ] Install `wakeonlan` (opciono)

- [ ] **Configure Services**
  - [ ] Systemd services (ako nisu već konfigurisani)
  - [ ] Nginx configuration (ako nije već konfigurisano)
  - [ ] Firewall rules

- [ ] **Production Readiness**
  - [ ] Change default admin password
  - [ ] Configure HTTPS/SSL
  - [ ] Review RBAC permissions
  - [ ] Security audit
  - [ ] Set up logging
  - [ ] Configure alerts
  - [ ] Performance monitoring
  - [ ] Error tracking
  - [ ] Database backup strategy
  - [ ] Image backup strategy
  - [ ] Configuration backup
  - [ ] Disaster recovery plan

---

## 📋 Checklist za Početak

### Priprema

- [ ] Review `docs/analysis/implementation_priorities_ggnet2.md`
- [ ] Review `docs/analysis/api_analysis_2289.md`
- [ ] Review `docs/analysis/api_comparison_2200_vs_2289.md`
- [ ] Review `docs/backend/NEXT_STEPS_AFTER_P0.md`
- [ ] Review `docs/frontend/tasks-summary.md`

### Setup

- [ ] Setup development environment
- [ ] Setup test environment
- [ ] Setup database migrations
- [ ] Review existing codebase

### Dokumentacija

- [ ] Review all implementation plans
- [ ] Review all status documents
- [ ] Review frontend task plans

---

## 🎯 Preporučeni Redosled Implementacije

### Faza 1: MVP Foundation (Nedelja 1-8)

**Nedelja 1-2:**
- [ ] Authentication & Authorization (migrations, default data, testing)
- [ ] Frontend Authentication UI

**Nedelja 3:**
- [ ] Bulk Operations - Machines (frontend integration)
- [ ] Writebacks Management (frontend integration)

**Nedelja 4:**
- [ ] Testing & Bug Fixes
- [ ] Documentation

**Nedelja 5-6:**
- [ ] Array Operations - Drive Management (frontend integration)
- [ ] Array Operations - TRIM Management (frontend integration)

**Nedelja 7:**
- [ ] Bulk Operations - Images (frontend integration)

**Nedelja 8:**
- [ ] Testing & Bug Fixes
- [ ] Documentation

### Faza 2: Frontend Core Features (Nedelja 9-12)

**Nedelja 9-10:**
- [ ] T-Shared utilities and components
- [ ] T-Array core features (Tasks 1-3)

**Nedelja 11-12:**
- [ ] T-Images core features (Tasks 1-3)
- [ ] T-Settings core features (Tasks 1-2)

### Faza 3: Advanced Features (Nedelja 13-20)

**Nedelja 13-16:**
- [ ] Scheduling System
- [ ] Progress Tracking - WebSocket Events
- [ ] Activity Logging & Audit Trail

**Nedelja 17-20:**
- [ ] Server Management API
- [ ] Image Snapshot Management
- [ ] Image Import/Export
- [ ] Remaining frontend tasks

---

## 📊 Statistika TODO Stavki

| Kategorija | Broj TODO Stavki | Prioritet |
|-----------|------------------|-----------|
| **P0 - Backend** | ~50 | 🔴 Kritično |
| **P0 - Frontend** | ~30 | 🔴 Kritično |
| **P1 - Backend** | ~40 | 🟠 Visok |
| **P1 - Frontend** | ~20 | 🟠 Visok |
| **P2 - Backend** | ~25 | 🟡 Srednji |
| **P2 - Frontend** | ~15 | 🟡 Srednji |
| **P3 - Backend** | ~15 | 🟢 Nizak |
| **Frontend Tasks (T-Array, T-Images, T-Settings, T-Shared)** | ~150 | 🟠 Visok |
| **Advanced Frontend (Array Advanced, VM Advanced, Scheduler Advanced)** | ~80 | 🟠 Visok |
| **Implementation Checklists (Array, Images, Settings, Machines, VM, Scheduler)** | ~120 | 🟠 Visok |
| **Code-Level TODOs** | ~5 | 🟡 Srednji |
| **Testing & Validation** | ~100 | 🟠 Visok |
| **Deployment & Production** | ~50 | 🟠 Visok |
| **Dokumentacija** | ~10 | 🟡 Srednji |
| **System Setup** | ~15 | 🟠 Visok |
| **UKUPNO** | **~720+** | |

---

## 🔗 Reference Dokumenti

### Analiza
- `docs/analysis/implementation_priorities_ggnet2.md` - Prioriteti implementacije
- `docs/analysis/api_analysis_2289.md` - API analiza verzije 2289
- `docs/analysis/api_comparison_2200_vs_2289.md` - Uporedna analiza
- `docs/analysis/NEXT_STEPS_ROADMAP.md` - Roadmap

### Backend Implementation
- `docs/backend/IMPLEMENTATION_PLANS_INDEX.md` - Index planova
- `docs/backend/NEXT_STEPS_AFTER_P0.md` - Sledeći koraci
- `docs/backend/PLANS_REVIEW.md` - Review planova
- `docs/backend/P0_IMPLEMENTATION_SUMMARY.md` - P0 sažetak

### Frontend Implementation
- `docs/frontend/tasks-summary.md` - Frontend tasks summary
- `docs/frontend/t-machines.plan.md` - Machines page plan
- `docs/frontend/t-array.plan.md` - Array page plan
- `docs/frontend/t-images.plan.md` - Images page plan
- `docs/frontend/t-settings.plan.md` - Settings page plan
- `docs/frontend/t-shared.plan.md` - Shared components plan

---

---

## 📝 Dodatne Napomene

### Status Implementacije

**Iz:** `PROJECT_STATUS.md`, `P0_IMPLEMENTATION_COMPLETE.md`, `FRONTEND_P0_FINAL_COMPLETE.md`

#### Backend P0 Status: ✅ 100% Kompletno
- ✅ Authentication & Authorization
- ✅ Bulk Operations - Machines
- ✅ Bulk Operations - Images
- ✅ Writebacks Management
- ✅ Array Operations - Drive Management
- ✅ Array Operations - TRIM Management

#### Frontend P0 Status: ✅ 86% Kompletno
- ✅ Authentication UI
- ✅ Bulk Operations - Machines UI
- ✅ Drive Management UI
- ✅ TRIM Management UI
- ✅ Bulk Operations - Images UI
- ✅ Writebacks Management UI
- ✅ Array Operations UI (osnovni wizard)
- ⚠️ Array Operations - Advanced UI (pending)

#### Database Migrations: ✅ Kompletno
- ✅ Migration file kreiran (`001_add_p0_modules.py`)
- ✅ Migracija primenjena
- ✅ Default data inicijalizovano

#### WSL Setup: ✅ Kompletno
- ✅ WSL Debian 13 "Trixie" setup guide
- ✅ Quick start guide
- ✅ Troubleshooting guides

### Known Issues & Fixes

**Iz:** `PROJECT_STATUS.md`, `FRONTEND_FIXES_2025-11-19.md`

#### Fixed Issues ✅
- ✅ JWT Token Fix: `sub` mora biti string
- ✅ Login Endpoint Fix: Dodat `/login` endpoint
- ✅ Me Endpoint Fix: Dodat `/me` endpoint
- ✅ ProtectedRoute Hooks Fix: Hooks order fix
- ✅ Login Response Handling Fix: Fetch user data nakon login
- ✅ Rebuild Status Endpoint: Dodat `/api/array/{pool_name}/rebuild/status`
- ✅ Settings Authentication: Dodata autentifikacija na settings endpoint

#### Pending Issues ⚠️
- ⚠️ Frontend Testing: Machines, Storage, Images, Writebacks pages pending test
- ⚠️ Integration Testing: End-to-end flows pending
- ⚠️ WebSocket Testing: Real-time updates pending test
- ⚠️ Production Deployment: Server deployment pending

---

## 🎯 Quick Reference - Prioriteti

### 🔴 P0 - Kritično (Sada)
1. Authentication - Migrations & Testing
2. Frontend Testing - Svi P0 moduli
3. Integration Testing - End-to-end flows
4. Code TODOs - Remove/implement

### 🟠 P1 - Visok (Sledeće)
1. Scheduling System
2. Progress Tracking - WebSocket Events
3. Activity Logging
4. Frontend Advanced Features (Array Advanced, VM Advanced, Scheduler Advanced)

### 🟡 P2 - Srednji (Kasnije)
1. Hardware Info
2. Server Updates
3. Settings API enhancements
4. Implementation Checklists completion

### 🟢 P3 - Nizak (Future)
1. Release Streams
2. Grafana Integration
3. SSL Certificates Management
4. Subscription Management

---

---

## 📈 Izvori Podataka

### Analizirani Fajlovi (170+)

#### Dokumentacija (`docs/`)
- **Backend:** 34 fajlova (implementation plans, status documents, guides)
- **Frontend:** 36 fajlova (task plans, implementation checklists, component docs)
- **Architecture:** 5 fajlova (system overview, workflows, sequences)
- **Scripts:** 9 fajlova (install, setup guides)
- **Windows Client:** 4 fajlova (overview, implementations, deployment)
- **Analysis:** 30 fajlova (API analysis, priorities, recommendations)

#### Root Folder
- **Status Documents:** PROJECT_STATUS.md, P0_IMPLEMENTATION_COMPLETE.md, FRONTEND_P0_FINAL_COMPLETE.md
- **Next Steps:** NEXT_STEPS.md, NEXT_STEPS_PLAN.md, docs/backend/NEXT_STEPS_AFTER_P0.md
- **Deployment:** DEPLOYMENT_GUIDE.md, DEPLOYMENT_READY_SUMMARY.md, QUICK_START.md
- **WSL Guides:** WSL_*.md (10+ fajlova)

#### Code Files
- **Frontend:** Machines.jsx, Storage.jsx, Images.jsx (TODO komentari)
- **Backend:** models.py, array.py (status fields, pending operations)

### Metodologija

1. **Pretraga svih `.md` fajlova** - 170+ fajlova
2. **Grep pretraga** - TODO, FIXME, XXX, HACK, Missing, Nedostaje, Not implemented, [ ], pending
3. **Čitanje ključnih fajlova** - Implementation plans, status documents, checklists
4. **Ekstrakcija TODO stavki** - Organizovano po prioritetima i kategorijama
5. **Dopuna sa code-level TODOs** - Direktno iz koda
6. **Kategorizacija** - P0-P3, Backend/Frontend, Testing/Deployment

---

---

## ✅ Sažetak

### Šta je Urađeno

✅ **Kompletan TODO plan kreiran** sa ~720+ TODO stavki organizovanih u:
- **12 glavnih kategorija** (P0-P3, Frontend Tasks, Advanced Features, Testing, Deployment, itd.)
- **28+ funkcionalnosti** sa detaljnim breakdown-om
- **170+ analiziranih `.md` fajlova** iz celog projekta
- **Code-level TODOs** direktno iz koda
- **Implementation checklists** iz svih planova

### Ključni Nalazi

1. **P0 Backend:** ✅ 100% implementirano (osim migracija i testiranja)
2. **P0 Frontend:** ✅ 86% implementirano (preostalo: Array Advanced UI)
3. **P1 Features:** ❌ Nedostaje (Scheduling, Progress Tracking, Activity Logging)
4. **Frontend Advanced:** ❌ Nedostaje (Array Advanced, VM Advanced, Scheduler Advanced)
5. **Testing:** ⚠️ Delimično (Backend: 70%, Frontend: 30%, Integration: 0%)
6. **Deployment:** ⚠️ Pending (Server setup, Production readiness)

### Preporučeni Sledeći Koraci

1. **Odmah (P0):**
   - [ ] Završiti frontend testing za sve P0 module
   - [ ] Završiti integration testing
   - [ ] Implementirati code-level TODOs (save/cancel configuration, copy/edit image)

2. **Kratkoročno (P1):**
   - [ ] Scheduling System
   - [ ] Progress Tracking - WebSocket Events
   - [ ] Activity Logging & Audit Trail
   - [ ] Frontend Advanced Features

3. **Dugoročno (P2-P3):**
   - [ ] Hardware Info
   - [ ] Server Updates
   - [ ] Grafana Integration
   - [ ] SSL Certificates Management

---

*Kompletan TODO plan kreiran na osnovu analize svih dokumentacija u `/docs` folderu i svih `.md` fajlova u projektu (170+ fajlova).*  
*Poslednje ažuriranje: 2025-11-26*  
*Ukupno TODO stavki: ~720+*  
*Dokument: 1770+ linija*

