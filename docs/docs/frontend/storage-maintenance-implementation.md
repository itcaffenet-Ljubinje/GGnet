# Storage Maintenance Implementation Checklist

## Goal
Translate the operational plans for storage maintenance (`array-automation.md`, `snapshot-retention.md`, `trim-management.md`, `array-forklift.md`) into actionable development tasks covering UI, backend, and coordination.

---

## 1. Automated Cleanup (Snapshots & Writebacks)
### Frontend
- Retention settings UI (Settings → Array & Images):
  - Numeric inputs for `Unutilized Snapshots (days)`, `Unprotected Snapshots (count)`, `Inactive Writebacks (days)`.
  - On/off toggle for automation with confirmation modal.
  - Next run/last run summary, including “Run Now” button.
  - Protect/unprotect snapshot list (searchable, tag display).
- Warning banners:
  - When automation disabled and space risk detected.
  - When writebacks exceed safe threshold.

### Backend
- Endpoints:
  - `GET/PUT /settings/storage-retention`
  - `POST /cleanup/run`
  - `GET /cleanup/history`
- Return cleanup summaries (snapshots deleted, GB freed).
- Provide snapshot protection metadata (protected list).

### Testing
- Unit: field validation, toggle states, run-now button behaviour.
- Integration: simulate cleanup API success/failure.
- Manual QA: configure retention, run manual cleanup, verify updates in history.

---

## 2. Snapshot Retention Ops Checklist (`snapshot-retention.md`)
- Provide documentation view within UI (link to internal runbook).
- Add “Checklist” component summarising ops steps (backup reminder, protect critical snapshots).
- Manual run confirmation wizard referencing best practices.
- Add link to download resulting cleanup report (CSV/JSON).

---

## 3. TRIM Management
### Frontend
- TRIM configuration panel in Settings:
  - Toggle `Turn on TRIM`.
  - Schedule inputs: `Day of week`, `Start`, `End`.
  - Pool selector (checkboxes for SSD-backed pools).
  - Advanced options (pause during rebuild, throttle if applicable).
  - Status card: `Last Run`, `Data Trimmed`, `Next Run`.
  - Manual run button with confirmation modal.
- Alerts:
  - Banner when TRIM disabled on SSD arrays.
  - Warning if TRIM window conflicts with rebuild or cleanup tasks.

### Backend
- Endpoints:
  - `GET/PUT /settings/trim`
  - `POST /trim/run`
  - `GET /trim/history`
- Return per-run metrics (`data_trimmed_gb`, duration, status).
- Provide validation for schedule conflicts.

### Testing
- Unit: schedule validation, toggle interactions.
- Integration: manual run (success/failure), history rendering.
- Manual QA: configure schedule, run TRIM, inspect history and alerts.

---

## 4. Forklift Upgrade Support (`array-forklift.md`)
### Frontend
- Guided wizard/timeline component with phases:
  1. Preparation (disable automation, backup verification, export configuration).
  2. Disk swap steps with checkboxes and instructions.
  3. Validation (health checks, machine boot verification).
  4. Finalization (re-enable automation, review logs).
- Export/print runbook as PDF.
- Progress persistence across sessions.
- Health diagnostics summary post-completion.

### Backend
- Provide API hooks:
  - `POST /array/forklift/start`, `GET /array/forklift/status`, `POST /array/forklift/complete` (or reuse existing endpoints if purely client guided).
- Optionally integrate with audit log for each phase.

### Testing
- Unit: step state handling, progress persistence.
- Integration: simulate API status updates.
- Manual QA: walkthrough entire wizard, ensure instructions and toggles behave as expected.

---

## Cross-Cutting Considerations
- **Notifications**: ensure cleanup/TRIM/forklift tasks push success/failure alerts (toast/email).
- **Telemetry**: log all maintenance actions with user + timestamp for audit.
- **Access Control**: restrict destructive operations to admin roles; enforce confirm dialogs.
- **Documentation**: link UI components to relevant Confluence exports for detailed guidance.

---

## Deliverables
- Updated Settings & Array UI components (retention, TRIM, forklift wizard).
- Backend API implementations for cleanup/trim/forklift operations.
- Test coverage across units/integration/manual checks.
- Admin documentation summarizing new maintenance tooling.

