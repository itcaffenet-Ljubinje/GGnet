# Machines Tab Implementation Checklist

## Goal
Translate the UX plan in `machines.md` into actionable development work: component updates, API integrations, and testing steps. Use this checklist to create development issues or stories.

## Frontend Tasks
1. **Table Enhancements**
   - Implement server-side pagination & filtering (reuse existing table component or extend).
   - Add column chooser modal with persistence (evaluate storing preferences via API vs local storage).
   - Update row styling to reveal overflow actions on hover.

2. **Status & Snapshot Icons**
   - Integrate icon set described in plan (ggLeap integration, warning, exclamation, link speed, keep writebacks).
   - Ensure tooltip copy matches microcopy.
   - Join image snapshot metadata to machine records (API update may be required).

3. **Machine Settings Modal**
   - Add Hardware tab (read-only fields).
   - Add Advanced tab with `Keep Writebacks` toggle and snapshot override drop-downs.
   - Validate VM Settings tab toggles when machine is VM.

4. **Bulk Operations**
   - Update bulk toolbar for multi-select: Reboot, Turn Off, Turn On, Edit Selected.
   - Implement bulk edit modal matching documented fields, including confirm checkbox.
   - Display progress indicator for bulk actions (success/failure toasts).

5. **Create VM Button**
   - Conditionally render button based on VM enablement flag.
   - Link to VM creation workflow (`virtual-machines.md` plan).

6. **Deletion & Confirmations**
   - Ensure Delete, Remove Drive, Take Offline actions require confirm checkbox/type-to-confirm.
   - Provide undo banner where feasible.

## Backend/API Considerations
1. **Extended Machine DTO**
   - Include hardware info (NIC, GPU, CPU, motherboard).
   - Provide snapshot state details per machine (current vs pinned snapshots).

2. **Preferences Storage**
   - If column layouts stored server-side, expose endpoints (`GET/PUT /machines/preferences`).

3. **Bulk Operations**
   - Confirm endpoints for bulk edit (`POST /machines/bulk` with new fields) return operation status.
   - Ensure bulk power operations provide aggregated success/fail responses for UI.

4. **Snapshots Integration**
   - Provide machine-level snapshot metadata (latest, custom, pending) to support icon logic.

## Testing
- Unit tests for table selectors, modal forms, multi-select flows.
- Integration tests for bulk operations (mock API responses).
- Manual QA scenarios:
  - Applying writebacks, snapshot changes, toggling keep writebacks.
  - Confirm hidden machine toggle persists.
  - Validate Deletion flow (confirm prompt + undo).

## Dependencies & Coordination
- Coordinate with backend for new fields/APIs.
- Align with `virtual-machines-advanced.md` for VM-specific settings.
- Sync microcopy with product/UX (see `machines.md`).

## Deliverables
- Updated components (table, modals, icons).
- API integration layer adjustments.
- Test coverage additions.
- Release notes summarizing machine tab improvements.

