# Advanced Array Operations Implementation Checklist

## Goal
Break down `array-advanced.md` into actionable development work for the advanced maintenance flows (add/remove/replace drives, RAID conversion, forklift upgrade).

## Frontend Tasks
1. **Add Drive Wizard**
   - Build multi-step dialog (Checklist → Drive Selection → Summary).
   - Validate capacity requirements (new drive ≥ largest existing).
   - Show rebuild warning banner and require acknowledgement checkbox.
   - Hook up to rebuild progress UI (progress bar, ETA, disable conflicting actions).

2. **Remove Drive Flow**
   - Dialog presenting drive details, RAID support check, typed confirmation.
   - Block action for unsupported RAID levels (e.g., RAID0).
   - Display inline progress states (queued, in-progress, completed).

3. **Replace Drive Flow**
   - Wizard guiding physical swap: prompt to install drive, select replacement, confirm.
   - Update progress indicators and post-completion health check prompt.

4. **Take Offline / Bring Online**
   - Confirmation dialogs with reason text and warnings.
   - Update drive status icons immediately after action.

5. **RAID Conversion Tool**
   - Advanced menu entry launching wizard with Overview → Preparation → Execution → Finalization steps.
   - Include multi-factor confirmation (checkbox + typed phrase).
   - Provide progress tracker that survives page reload (state persistence).

6. **Forklift Upgrade Guide**
   - Implement guided modal/timeline with step-by-step checklist.
   - Provide export/print option (runbook PDF).
   - Integrate health diagnostics summary at completion.

7. **History & Reporting**
   - Add history tab or panel summarizing advanced operations (user, timestamp, drives).
   - Allow download of operation report (CSV/JSON).

## Backend/API Requirements
- Extend array endpoints to support:
  - `POST /array/drives/replace`, `/remove`, `/offline`, `/online`, `/add`.
  - `POST /array/raid/convert` with job status polling.
  - `POST /array/forklift/start`, with step tracking if implemented server-side.
- Provide rebuild progress endpoint (`GET /array/rebuild-status`) with SSE/WebSocket option.
- Add audit log endpoints or integrate with existing logging service.
- Supply check endpoints for RAID compatibility and prerequisites (pool health, disk count).

## Validation & Error Handling
- Inline errors for capacity mismatch, unsupported RAID level, missing replacement drives.
- Failure banners with link to detailed logs (e.g., `GET /array/jobs/{id}/logs`).
- Handle cancellation/rollback scenarios gracefully (if backend supports).

## Testing
- Unit tests for wizard workflows and validation logic.
- Integration tests simulating API responses (success/failure for each flow).
- Manual QA scenarios:
  - Add drive to stripe and monitor rebuild.
  - Attempt remove on RAID0 (ensure blocked).
  - Replace drive with mismatched capacity (error).
  - Complete RAID conversion end-to-end.
  - Follow forklift guide, ensuring each step requires confirmation.

## Coordination
- Work with backend team to confirm job orchestration and progress streaming.
- Align microcopy with product/UX (warnings, confirmations).
- Coordinate with storage automation team to ensure cleanup processes disabled/enabled at appropriate steps.

## Deliverables
- Advanced operations UI components (wizards, dialogs, history panel).
- API integration for new endpoints and progress tracking.
- Enhanced telemetry logging.
- Documentation/release notes covering advanced maintenance features.

