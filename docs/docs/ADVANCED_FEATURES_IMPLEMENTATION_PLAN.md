# Advanced Features Implementation Plan

**Datum kreiranja:** 2025-01-26  
**Status:** 📋 Implementation Plan za P3 Advanced Features

---

## 📊 Pregled

Ovaj dokument sadrži detaljne planove za implementaciju P3 (nizak prioritet) advanced frontend funkcionalnosti. Ovi zadaci su opcioni i mogu se implementirati u budućim verzijama.

---

## 🎯 1. Array Advanced Operations

### Status
- **Prioritet:** 🟢 P3 (Nizak)
- **Plan:** `docs/frontend/array-advanced-implementation.md`
- **Status:** 📋 Plan kreiran, čeka implementaciju

### Implementacija

#### 1.1 Add Drive Wizard Enhancements
**Fajl:** `app/frontend/src/pages/Storage.jsx`

**Koraci:**
1. Proširiti postojeći Add Drive wizard sa multi-step flow:
   - **Step 1: Pre-flight Checklist**
     - Array health check
     - Available space check
     - Drive compatibility check
   - **Step 2: Drive Selection**
     - List available drives
     - Capacity validation (new drive ≥ largest existing)
     - SSD/HDD mixing warning
   - **Step 3: Summary & Confirmation**
     - Rebuild warning banner
     - Estimated rebuild time
     - Acknowledgement checkbox

2. Integrisati sa rebuild progress UI:
   - Progress bar
   - ETA display
   - Disable conflicting actions during rebuild

**API Endpoints:**
- `POST /api/v1/array/{pool_name}/drives/add` (već postoji)
- `GET /api/v1/array/{pool_name}/rebuild/status` (već postoji)

#### 1.2 Remove Drive Flow
**Fajl:** `app/frontend/src/pages/Storage.jsx`

**Koraci:**
1. Kreirati Remove Drive modal:
   - Drive details display
   - RAID support check
   - Typed confirmation (e.g., "REMOVE")
   - Block action for RAID0

2. Progress tracking:
   - Queued state
   - In-progress state
   - Completed state

**API Endpoints:**
- `POST /api/v1/array/{pool_name}/drives/remove` (već postoji)

#### 1.3 Replace Drive Flow
**Fajl:** `app/frontend/src/pages/Storage.jsx`

**Koraci:**
1. Kreirati Replace Drive wizard:
   - **Step 1: Physical Swap Instructions**
     - Instructions for physical drive swap
     - Safety warnings
   - **Step 2: Select Replacement Drive**
     - List available drives
     - Capacity validation
   - **Step 3: Confirm & Start**
     - Confirmation
     - Start rebuild

2. Progress tracking:
   - Rebuild progress
   - Health check after completion

**API Endpoints:**
- `POST /api/v1/array/{pool_name}/drives/replace` (već postoji)

#### 1.4 RAID Conversion Tool
**Fajl:** `app/frontend/src/pages/Storage.jsx`

**Koraci:**
1. Kreirati RAID Conversion wizard:
   - **Step 1: Overview**
     - Current RAID level
     - Target RAID level
     - Prerequisites check
   - **Step 2: Preparation**
     - Backup reminder
     - Health check
   - **Step 3: Execution**
     - Progress tracking
     - State persistence (survives page reload)
   - **Step 4: Finalization**
     - Health check
     - Summary

2. Multi-factor confirmation:
   - Checkbox confirmation
   - Typed phrase (e.g., "CONVERT RAID")

**API Endpoints:**
- `POST /api/v1/array/{pool_name}/raid/convert` (treba implementirati)
- `GET /api/v1/array/{pool_name}/raid/status` (treba implementirati)

#### 1.5 Forklift Upgrade Guide
**Fajl:** `app/frontend/src/pages/Storage.jsx`

**Koraci:**
1. Kreirati Forklift Upgrade wizard:
   - **Phase 1: Preparation**
     - Disable automation
     - Backup verification
     - Export configuration
   - **Phase 2: Disk Swap**
     - Step-by-step checklist
     - Instructions per step
   - **Phase 3: Validation**
     - Health checks
     - Machine boot verification
   - **Phase 4: Finalization**
     - Re-enable automation
     - Review logs

2. Features:
   - Export/print runbook as PDF
   - Progress persistence
   - Health diagnostics summary

**API Endpoints:**
- `POST /api/v1/array/{pool_name}/forklift/start` (treba implementirati)
- `GET /api/v1/array/{pool_name}/forklift/status` (treba implementirati)

#### 1.6 History & Reporting
**Fajl:** `app/frontend/src/pages/Storage.jsx`

**Koraci:**
1. Dodati History tab/panel:
   - List advanced operations
   - User, timestamp, drives
   - Operation status

2. Export functionality:
   - Download report (CSV/JSON)
   - Filter by date range
   - Filter by operation type

**API Endpoints:**
- `GET /api/v1/array/{pool_name}/history` (treba implementirati)
- `GET /api/v1/array/{pool_name}/history/export` (treba implementirati)

---

## 🖥️ 2. Virtual Machines Advanced

### Status
- **Prioritet:** 🟢 P3 (Nizak)
- **Plan:** `docs/frontend/virtual-machines-advanced-implementation.md`
- **Status:** 📋 Plan kreiran, čeka implementaciju

### Implementacija

#### 2.1 Enablement Checklist UI
**Fajl:** `app/frontend/src/pages/VMs.jsx` (ili novi fajl)

**Koraci:**
1. Kreirati Enablement Checklist komponentu:
   - Banner/card sa status indicators
   - Prerequisites:
     - BIOS virtualization enabled
     - Static IP configured
     - Clients powered off
   - Link to troubleshooting guide

**API Endpoints:**
- `GET /api/v1/vms/status` (treba implementirati)

#### 2.2 Ops Runbooks Integration
**Fajl:** `app/frontend/src/pages/VMs.jsx`

**Koraci:**
1. Kreirati Ops Runbooks panel:
   - Rolling update workflow
   - Buttons:
     - "Force Sync with ggLeap"
     - "Apply Writebacks"
   - Backup/restore flows (reuse from Images)

**API Endpoints:**
- `POST /api/v1/vms/sync` (treba implementirati)
- `POST /api/v1/vms/apply-writebacks` (treba implementirati)

#### 2.3 Resource Monitoring
**Fajl:** `app/frontend/src/pages/VMs.jsx`

**Koraci:**
1. Kreirati Resource Monitoring panel:
   - VM RAM allocation vs available pool
   - Writeback usage per VM
   - Warnings when approaching thresholds

**API Endpoints:**
- `GET /api/v1/vms/resources` (treba implementirati)

#### 2.4 Troubleshooting Helpers
**Fajl:** `app/frontend/src/pages/VMs.jsx`

**Koraci:**
1. Dodati troubleshooting helpers:
   - Inline tips for console issues
   - noVNC reconnect instructions
   - Popup block instructions
   - Quick action to re-run bridge configuration
   - Microcopy for common errors

**API Endpoints:**
- `POST /api/v1/vms/bridge/reconfigure` (treba implementirati)

#### 2.5 Operational Actions
**Fajl:** `app/frontend/src/pages/VMs.jsx`

**Koraci:**
1. Dodati operational actions:
   - Generate VM report button
   - Decommission workflow guide

**API Endpoints:**
- `POST /api/v1/vms/report` (treba implementirati)

---

## ⏰ 3. Scheduler Advanced

### Status
- **Prioritet:** 🟢 P3 (Nizak)
- **Plan:** `docs/frontend/scheduler-advanced-implementation.md`
- **Status:** 📋 Plan kreiran, čeka implementaciju

### Implementacija

#### 3.1 Metadata Fetching
**Fajl:** `app/frontend/src/services/schedulerAPI.js`

**Koraci:**
1. Dodati metadata fetching:
   - Service za retrieval behaviour definitions
   - Caching sa versioning
   - Fallback ako fetch fails

**API Endpoints:**
- `GET /api/v1/scheduler/behaviours` (treba implementirati)
- `GET /api/v1/scheduler/behaviours/catalog` (treba implementirati)

#### 3.2 Dynamic Form Rendering
**Fajl:** `app/frontend/src/pages/Settings.jsx` (Scheduler tab)

**Koraci:**
1. Proširiti scheduler wizard:
   - Dynamic form rendering based on metadata
   - Field types: text, numeric, dropdown, checkbox, cron
   - Inline validation messages
   - Group behaviours by category

#### 3.3 Developer Mode & Test Run
**Fajl:** `app/frontend/src/pages/Settings.jsx` (Scheduler tab)

**Koraci:**
1. Dodati Developer Mode:
   - Toggle (role-protected)
   - Test Run button
   - Display logs/results after test run

**API Endpoints:**
- `POST /api/v1/scheduler/behaviours/{id}/test` (treba implementirati)

#### 3.4 Help & Documentation
**Fajl:** `app/frontend/src/pages/Settings.jsx` (Scheduler tab)

**Koraci:**
1. Dodati help & documentation:
   - Inline help text from metadata
   - Link to behaviour documentation
   - Behaviour summary table

---

## 💾 4. Storage Maintenance

### Status
- **Prioritet:** 🟢 P3 (Nizak)
- **Plan:** `docs/frontend/storage-maintenance-implementation.md`
- **Status:** 📋 Plan kreiran, čeka implementaciju

### Implementacija

#### 4.1 Automated Cleanup (Snapshots & Writebacks)
**Fajl:** `app/frontend/src/pages/Settings.jsx` (Array & Images tab)

**Koraci:**
1. Dodati retention settings UI:
   - Numeric inputs za retention settings
   - Toggle za automation
   - Next run/last run summary
   - "Run Now" button
   - Protect/unprotect snapshot list

2. Warning banners:
   - Automation disabled + space risk
   - Writebacks exceed threshold

**API Endpoints:**
- `GET /api/v1/settings/storage-retention` (treba implementirati)
- `PUT /api/v1/settings/storage-retention` (treba implementirati)
- `POST /api/v1/cleanup/run` (treba implementirati)
- `GET /api/v1/cleanup/history` (treba implementirati)

#### 4.2 Snapshot Retention Ops Checklist
**Fajl:** `app/frontend/src/pages/Storage.jsx`

**Koraci:**
1. Dodati ops checklist:
   - Documentation view
   - Checklist component
   - Manual run confirmation wizard
   - Download cleanup report

#### 4.3 TRIM Management
**Fajl:** `app/frontend/src/pages/Settings.jsx` (Array & Images tab)

**Koraci:**
1. Proširiti TRIM configuration:
   - Toggle "Turn on TRIM"
   - Schedule inputs (Day, Start, End)
   - Pool selector
   - Advanced options
   - Status card
   - Manual run button

2. Alerts:
   - TRIM disabled on SSD arrays
   - Schedule conflicts

**API Endpoints:**
- `GET /api/v1/settings/trim` (već postoji)
- `PUT /api/v1/settings/trim` (već postoji)
- `POST /api/v1/trim/run` (već postoji)
- `GET /api/v1/trim/history` (treba implementirati)

#### 4.4 Forklift Upgrade Support
**Fajl:** `app/frontend/src/pages/Storage.jsx`

**Koraci:**
1. Kreirati Forklift Upgrade wizard (slično kao u Array Advanced)
2. Integrisati sa Storage Maintenance

---

## 📋 Implementation Priority

### Phase 1 (Opciono - Future)
1. **Storage Maintenance** - Automated cleanup i TRIM management (najkorisnije)
2. **Array Advanced** - RAID conversion i forklift upgrade (za napredne korisnike)

### Phase 2 (Opciono - Future)
3. **Scheduler Advanced** - Dynamic behaviours (za power users)
4. **VM Advanced** - Enablement checklist i ops runbooks (za enterprise)

---

## 🔧 Backend Requirements

### Potrebni Novi API Endpoints

#### Array Advanced
- `POST /api/v1/array/{pool_name}/raid/convert`
- `GET /api/v1/array/{pool_name}/raid/status`
- `POST /api/v1/array/{pool_name}/forklift/start`
- `GET /api/v1/array/{pool_name}/forklift/status`
- `GET /api/v1/array/{pool_name}/history`
- `GET /api/v1/array/{pool_name}/history/export`

#### VM Advanced
- `GET /api/v1/vms/status`
- `POST /api/v1/vms/sync`
- `POST /api/v1/vms/apply-writebacks`
- `GET /api/v1/vms/resources`
- `POST /api/v1/vms/bridge/reconfigure`
- `POST /api/v1/vms/report`

#### Scheduler Advanced
- `GET /api/v1/scheduler/behaviours`
- `GET /api/v1/scheduler/behaviours/catalog`
- `POST /api/v1/scheduler/behaviours/{id}/test`

#### Storage Maintenance
- `GET /api/v1/settings/storage-retention`
- `PUT /api/v1/settings/storage-retention`
- `POST /api/v1/cleanup/run`
- `GET /api/v1/cleanup/history`
- `GET /api/v1/trim/history`

---

## ✅ Implementation Checklist

### Array Advanced
- [ ] Add Drive Wizard enhancements
- [ ] Remove Drive Flow
- [ ] Replace Drive Flow (već delimično implementirano)
- [ ] RAID Conversion Tool
- [ ] Forklift Upgrade Guide
- [ ] History & Reporting

### VM Advanced
- [ ] Enablement Checklist UI
- [ ] Ops Runbooks Integration
- [ ] Resource Monitoring
- [ ] Troubleshooting Helpers
- [ ] Operational Actions

### Scheduler Advanced
- [ ] Metadata Fetching
- [ ] Dynamic Form Rendering
- [ ] Developer Mode & Test Run
- [ ] Help & Documentation
- [ ] Feature Flags & Permissions
- [ ] Error Handling

### Storage Maintenance
- [ ] Automated Cleanup UI
- [ ] Snapshot Retention Ops Checklist
- [ ] TRIM Management enhancements
- [ ] Forklift Upgrade Support

---

## 📚 Reference

- **Array Advanced Plan:** `docs/frontend/array-advanced-implementation.md`
- **VM Advanced Plan:** `docs/frontend/virtual-machines-advanced-implementation.md`
- **Scheduler Advanced Plan:** `docs/frontend/scheduler-advanced-implementation.md`
- **Storage Maintenance Plan:** `docs/frontend/storage-maintenance-implementation.md`

---

**Napomena:** Ovi zadaci su P3 prioritet (nizak) i opcioni. Mogu se implementirati u budućim verzijama kada budu potrebni.

---

**Advanced Features Implementation Plan Complete!** 📋

