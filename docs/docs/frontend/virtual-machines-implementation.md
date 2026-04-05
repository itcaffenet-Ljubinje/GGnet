# Virtual Machines Implementation Checklist

## Goal
Convert the requirements in `virtual-machines.md` into actionable development items for the Machines tab VM flows.

## Frontend Tasks
1. **VM Enablement Banner**
   - Checklist UI (BIOS virtualization, static IP, powered-off clients).
   - Enable VMs button with progress spinner and success/error feedback.
   - Link to admin manual for troubleshooting.

2. **Create VM Dialog**
   - Form fields: Name, System Image, Game Image, vCPUs, Boot Mode, Drives Connection, RAM Size.
   - Input validation (RAM limits vs reserved pool, CPU >= 1).
   - Contextual tips for Local vs Network drives.
   - Submit flow with loading state and toast on success.

3. **VM Settings Tab**
   - Mirror creation form with existing values.
   - Display warnings that changes require reboot.
   - Support snapshot override dropdowns (system/game).

4. **Control Surface Enhancements**
   - Overflow actions: Turn On, Shutdown, Reboot, Control VM, Open in New Tab, Full Screen.
   - noVNC embed with toolbar (share link TTL 60s).
   - Popup blocker fallback messaging.

5. **Status Indicators**
   - VM-specific tags (Powered Off, Running, Updating).
   - RAM pool usage bar referencing Settings slider.
   - Licensing banner (ggLeap seat usage).

6. **Error Handling UI**
   - Display bridge configuration errors with link to Settings > Network.
   - Show inline messages for creation failures (insufficient RAM, missing bridge).
   - Reconnect prompt when control session expires.

## Backend/API Needs
- Endpoints:
  - `POST /vms` (creation), `PATCH /vms/{id}` (update settings), `POST /vms/{id}/power` (turn on/off/reboot), `POST /vms/{id}/control-session`.
- Provide metadata for available system/game images and snapshot lists.
- Surface VM licensing status (ggLeap integration).
- Return detailed error codes for UI messages.

## Testing
- Unit tests for form validation and state handling.
- Integration tests mocking VM API responses.
- Manual QA:
  - Enable/disable VMs, create VM, update settings, control session.
  - Test share link expiry and popup block scenarios.
  - Validate licensing banner when license count exhausted.

## Coordination
- Work with backend on control session lifecycle and share link TTL.
- Align with `virtual-machines-advanced.md` for advanced operations.
- Coordinate with Settings team for RAM allocation interplay.

## Deliverables
- VM enablement banner component.
- VM creation/edit dialogs.
- Updated machine overflow actions.
- Test coverage (unit/integration).

