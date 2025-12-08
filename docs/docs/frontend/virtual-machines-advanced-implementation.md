# Advanced VM Administration Implementation Checklist

## Goal
Turn the guidance in `virtual-machines-advanced.md` into actionable development tasks for UI enhancements, backend support, and operational tooling.

## Frontend Tasks
1. **Enablement Checklist UI**
   - Banner/card summarising prerequisites with status indicators (BIOS virtualization, static IP, clients powered off).
   - Link to troubleshooting guide (re-run bridge script, view logs).

2. **Ops Runbooks Integration**
   - Provide quick-access panel for rolling update workflow (snapshot → update → promote).
   - Buttons/links for “Force Sync with ggLeap” and “Apply Writebacks”.
   - Option to launch backup/restore flows (reuse from Images plan) for VM recovery.

3. **Resource Monitoring**
   - Display VM RAM allocation vs available pool (tying into Settings data).
   - Show writeback usage specific to VMs with warnings when approaching thresholds.

4. **Troubleshooting Helpers**
   - Inline tips for console issues (noVNC reconnect, popup block instructions).
   - Quick action to re-run bridge configuration (if allowed in UI).
   - Provide microcopy for common error messages (insufficient RAM, disk space).

5. **Operational Actions**
   - Buttons for generate VM report (inventory, snapshots, writebacks).
   - Hooks to guide decommission workflow (unassign, delete, cleanup).

## Backend/API Requirements
- Expose endpoints:
  - `GET /vms/status` (bridge status, prerequisites).
  - `POST /vms/bridge/reconfigure`.
  - `GET /vms/resources` (RAM usage, writebacks).
  - `POST /vms/report` (download inventory).
- Provide metadata for license counts (ggLeap integration status).
- Ensure audit logging for admin actions (enable/disable VMs, bridge reconfiguration).

## Testing
- Unit: ensure banners update based on prerequisite data.
- Integration: simulate bridge reconfigure success/failure, license status updates.
- Manual QA:
  - Walk through enablement checklist under various failure scenarios.
  - Execute rolling update runbook (mock entry).
  - Validate resource warnings when thresholds crossed.

## Coordination
- Align with backend ops team for bridge scripts and log retrieval.
- Coordinate with license management to fetch ggLeap counts.
- Ensure consistency with basic VM plan (`virtual-machines.md`) and settings UI.

## Deliverables
- Advanced admin components (checklist, runbooks, reports).
- API integration for resource monitoring and bridge scripts.
- Updated documentation/releases for support teams.

