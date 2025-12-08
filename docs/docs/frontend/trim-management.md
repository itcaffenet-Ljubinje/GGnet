# TRIM Management Plan

## Scope
- UX design for configuring, monitoring, and manually triggering TRIM operations on arrays with SSD storage.
- Based on Confluence export `GGROCK/docs/TRIM+Management.doc`.

## Objectives
- Ensure admins can schedule TRIM during low-usage windows.
- Provide transparency on last/next run and data trimmed.
- Warn about compatibility issues with SAN/NAS environments.

## UI Placement
- Primary controls live under `Settings → Array & Images → TRIM Settings`.
- Supplementary indicators on `Array` tab (status card showing TRIM health).

## Configuration Controls
1. **Enable Toggle**
   - Switch `Turn on TRIM`.
   - Tooltip: `Recommended for SSD-backed arrays. Disable if storage vendor advises against TRIM.`

2. **Schedule Inputs**
   - `Day of the week` dropdown (Monday–Sunday, plus `Daily` option).
   - `Start time` and `End time` pickers (24-hour format) with validation ensuring end > start.
   - Helper text: `Choose a maintenance window when client activity is minimal.`

3. **Target Selection**
   - If multiple pools, allow selecting pools for TRIM (checkbox list).
   - Note on mixed media arrays: highlight that TRIM runs only on SSD-backed pools.

4. **Advanced Options**
   - Optional throttle settings (if supported) to limit IO impact.
   - Checkbox `Pause TRIM during rebuild` to avoid extra load.

## Monitoring & Feedback
- **Status Card**:
  - `Last Run` timestamp and duration.
  - `Data Trimmed` (GB) for last run.
  - `Next Scheduled Run` preview.
  - Icon/colour indicating success/failure of last operation.

- **History Table**:
  - Columns: `Run Time`, `Status`, `Duration`, `Data Trimmed`, `Notes`.
  - Filters by date range and status.
  - Export CSV option for audit.

- **Manual Run**:
  - Button `Run TRIM Now`; show confirmation modal with caution about potential performance impact.
  - Progress indicator during job; disable repeat trigger until completion.

## Alerts & Error Handling
- Banner if TRIM disabled while SSDs detected: `TRIM is off. SSD performance may degrade over time.`
- Failure notifications with error message (e.g., “Pool not mounted”, “Unsupported by storage”).
- Detect and warn if TRIM window overlaps with other heavy operations (rebuild, snapshot cleanup).

## API & Data Needs
- Endpoints: `GET/PUT /settings/trim`, `POST /trim/run`, `GET /trim/history`.
- Provide streaming or polling mechanism for manual run status updates.
- Persist audit trail with user, action, timestamp.

## Open Questions
- Should UI auto-detect storage type and pre-enable TRIM suggestions?
- Need to provide vendor-specific guidance links (e.g., SAN compatibility list)?
- Determine default retention for history entries.

## References
- Confluence export: `GGROCK/docs/TRIM+Management.doc`
- Related plans: `docs/frontend/array.md`, `docs/frontend/settings.md`, `docs/frontend/array-automation.md`

