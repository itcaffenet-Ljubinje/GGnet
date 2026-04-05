# Array Tab Implementation Checklist

## Goal
Translate the UX specifications in `array.md` into actionable development items for the Array tab.

## Frontend Tasks
1. **Array Overview Banner**
   - Implement status LED (online/degraded/offline) with RAID badge.
   - Usage bar showing Size/Used/Free/Reserved segments; integrate with current capacity metrics.
   - Include warning threshold indicators and link to Settings > Array & Images.

2. **Drive Grid Updates**
   - Table with columns: Device, Model/Serial, Role, Status, Temperature, Last Seen.
   - Row overflow actions: Details, Identify, Mark Failed, Replace, Remove, View SMART.
   - Details modal displaying serial, firmware, interface, stripe membership.
   - Progress indicators for drives undergoing rebuild/resilvering.

3. **Drive Actions**
   - `Add Drive` wizard integration (should link to advanced plan `array-advanced.md`).
   - `Replace` flow with new drive selection and rebuild monitoring.
   - `Remove Drive` dialog with RAID-level validation (block for RAID0).
   - `Take Offline` / `Bring Online` confirmation modals with warnings.

4. **Snapshot & Writeback Automation**
   - Inline view of retention settings and upcoming cleanup (pull data from Settings APIs).
   - Quick toggle to enable/disable automation (with confirm).
   - Link to detailed plan (`array-automation.md`).

5. **TRIM Panel**
   - Display next/last run summary and manual trigger button (synced with `trim-management.md`).
   - Show data trimmed metrics.

6. **Alerts**
   - Persistent banners for DEGRADED/FAULTED states.
   - Toasts for threshold breaches (reserved space).
   - Info callouts reminding about rebuild risk during operations.

## Backend/API Requirements
- Provide enriched drive metadata (serial, firmware, status, role, temperature, last seen).
- Endpoints for:
  - `POST /array/drives/add`, `replace`, `remove`, `offline`, `online`.
  - `GET /array/rebuild-status` for real-time progress.
  - `GET /array/metrics` for usage gauge.
- Integrate with retention and TRIM endpoints from Settings.
- Ensure event streaming for rebuild progress (SSE/WebSocket) or poll-friendly endpoints.

## Testing
- Unit tests for dialogs, validation, icon states.
- Integration tests for drive action flows (mock API responses).
- Manual QA:
  - Add drive simulation (mock success/failure).
  - Replace drive mid-operation, monitor progress.
  - Trigger offline/online and confirm status changes.
  - Validate automation toggles and TRIM manual runs.

## Coordination
- Work closely with backend to confirm action endpoints and permission checks.
- Align with `array-advanced.md`, `array-automation.md`, `array-forklift.md` for additional flows.
- Ensure consistent microcopy (check `array.md` plan).

## Deliverables
- Updated array dashboard components.
- Integrated drive management flows.
- Monitoring UI for rebuild, automation, TRIM.
- Test suite updates (unit + integration).

