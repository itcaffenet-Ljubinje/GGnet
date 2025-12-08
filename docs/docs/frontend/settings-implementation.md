# Settings Implementation Checklist

## Goal
Translate the UX requirements in `settings.md` into concrete development and backend tasks.

## General Approach
The Settings area spans multiple tabs (`General`, `Network`, `Array & Images`, `Secure Boot`). Each subsection requires UI updates, API integrations, and validation logic consistent with the plan and Confluence documentation.

## Frontend Tasks
### 1. Layout & Navigation
- Implement sticky header with breadcrumb, `Save`, `Reset`, and unsaved changes badge.
- Persist last visited subsection (local storage or query param).

### 2. General Tab
- Build RAM allocation component:
  - `Maximize size` toggle + slider inputs (RAM Cache, VM Max, Server Reserved).
  - Inline helper text and validation (sum <= total RAM).
- Release stream dropdown with microcopy and restart warning modal.
- Dark mode toggle, default tab layout preferences, language selectors.
- Read-only metadata (hostname, version, uptime) with copy buttons.

### 3. Network Tab
- Bridge status card with red/green states and descriptive text.
- `Auto-Configure Bridge` button; show spinner and status log.
- NIC table with roles, link speed; toggles for DHCP/PXE services.
- Error banner area for failed configuration attempts (with retry).

### 4. Array & Images Tab
- Retention controls: numeric inputs for unutilized/unprotected snapshots, inactive writebacks.
- Reserved disk space and warning threshold inputs with usage meter.
- Integration with TRIM scheduler component (pull from `trim-management.md` plan).
- Upcoming cleanup schedule preview + manual run button.

### 5. Secure Boot Tab
- Status summary card for clients/VMs.
- Toggle with hardware prerequisite warning.
- Certificate upload component validating `.crt`/`.pem`.
- Confirmation modal outlining restart requirements.

### 6. Global UX
- Unsaved changes detection per tab.
- Toast notifications on save success/failure.
- History drawer showing last 5 changes (optional toggle).

## Backend/API Tasks
- Validate endpoints:
  - `GET/PUT /settings/general`
  - `GET/PUT /settings/network`
  - `GET/PUT /settings/storage`
  - `GET/PUT /settings/security`
- Provide data for:
  - Total physical RAM and current allocation.
  - Reserved/warning thresholds and usage metrics.
  - Bridge status & logs.
  - Retention settings and next cleanup schedule.
- API to trigger actions:
  - Auto-configure bridge.
  - Run cleanup now (snapshots/writebacks).
  - Run TRIM job now.
  - Upload secure boot certificates.
- Audit logging for settings changes (user, timestamp, before/after).

## Validation & Error Handling
- Enforce numeric ranges on retention fields and TRIM schedule inputs.
- Display server errors inline (e.g., “bridge configuration failed: NIC busy”).
- Confirm restart requirements after critical updates (release stream, secure boot).
- Handle partial failures (e.g., one NIC failing to configure) with actionable messages.

## Testing
- Unit tests for form validation and change detection.
- Integration tests covering save flows and error scenarios.
- Manual QA:
  - Adjust RAM sliders and verify recalculated totals.
  - Run auto-config bridge on test setup (mocked).
  - Change retention settings, run cleanup, confirm updates.
  - Toggle secure boot with mock certificate.

## Dependencies & Coordination
- Coordinate with backend team on new data fields and event dispatch (e.g., cleanup/trim progress).
- Align with storage plans (`array-automation.md`, `trim-management.md`, `snapshot-retention.md`).
- Ensure security review for certificate upload handling.

## Deliverables
- Updated Settings UI components per tab.
- Backend API enhancements and event handling.
- Automated test coverage (unit + integration).
- Documentation/release notes summarizing settings updates.

