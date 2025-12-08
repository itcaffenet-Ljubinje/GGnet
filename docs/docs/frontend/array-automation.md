# Automated Snapshot & Writeback Management Plan

## Scope
- UI/UX requirements for configuring automated cleanup of snapshots and writebacks within ggRock.
- Visibility into cleanup status, upcoming jobs, and manual override controls.
- Alignment with guidance from Confluence export `GGROCK/docs/Automated+Snapshot+and+Writeback+Removal.doc`.

## Goals
- Prevent array saturation caused by stale snapshots or inactive writebacks.
- Provide intuitive levers for retention policies and clear feedback about consequences.
- Offer manual intervention tools (on-demand cleanup, protect/unprotect snapshots).

## Surface Areas
- **Settings → Array & Images** section (primary configuration panel).
- **Array tab** warning banners when thresholds approached.
- **Notifications** for cleanup results and failures.

## Configuration Panel Requirements
1. **Retention Controls**
   - Inputs for:
     - `Unutilized Snapshots (days)` – older than X days.
     - `Unprotected Snapshots (count)` – max number, beyond which unlocked snapshots are candidates.
     - `Inactive Writebacks (days)` – delete stale writebacks.
   - Helper text per field describing impact (from Confluence doc).
   - Validation: enforce positive integers; highlight recommended ranges based on array size.

2. **Reserved Disk Space & Warning Threshold**
   - Integrate with existing settings; show usage meter.
   - Banner: `Operations will pause when reserved space is exhausted (PXE boot, snapshot creation).`

3. **Schedule & Execution**
   - Allow configuring cleanup cadence (daily/weekly/custom).
   - Display next run timestamp and last execution summary (success/failure, freed space).
   - Toggle to temporarily pause automation; inform user of consequences.

4. **Protection Overrides**
   - List of “protected snapshots” excluded from cleanup.
   - Quick actions: add/remove protection, search by image/snapshot name.

5. **Manual Run**
   - Button `Run Cleanup Now` with confirmation modal explaining tasks performed.
   - Show progress indicator; disable conflicting actions during run.

## Feedback & Alerts
- **Dashboard Alerts:** if array usage nears critical threshold or automation disabled.
- **Toast/Email Notification:** summarize cleanup (snapshots deleted, writebacks purged, errors encountered).
- **Error Handling:** display actionable messages if job fails (e.g., “Snapshot locked by active machine”); link to affected resources.

## Data & API
- Endpoints: `GET/PUT /settings/storage-retention`, `POST /cleanup/run`, `GET /cleanup/history`.
- Consider streaming updates or polling for long-running job status.
- Log retention: maintain history table (timestamp, duration, results) with export option.

## Edge Cases
- When cleanup would delete snapshots currently pinned to machines, require explicit confirmation or skip with warning.
- If writebacks are set to “Keep” for specific machines, exclude from auto purges and show note.
- Handle arrays with mixed media (SSD/HDD) where retention interval might differ.

## Open Questions
- Should users be able to define per-image retention overrides?
- Do we expose dry-run mode to preview deletions?
- Need bulk-protect action when prepping for maintenance?

## References
- Confluence export: `GGROCK/docs/Automated+Snapshot+and+Writeback+Removal.doc`
- Related plans: `docs/frontend/array.md`, `docs/frontend/settings.md`

