# Virtual Machines Advanced Administration Plan

## Scope
- Operational documentation covering advanced VM administration topics beyond basic creation/control.
- Synthesized from `GGROCK/docs/ggRock+Virtual+Machines+Administration+manual.doc` and related exports.

## Topics Covered
- Environment prerequisites and validation.
- VM lifecycle management (templates, updates, troubleshooting).
- Resource allocation (RAM reservations, bridging).
- License considerations and ggLeap integration.
- Support workflow for enabling/disabling VM functionality.

## Prerequisites & Validation
- BIOS virtualization (Intel VT-x/AMD-V) enabled on ggRock server.
- Static IP configuration (per network manual).
- All client machines powered off during bridge configuration.
- VM network bridge verified (`Settings → Network → Bridge Status`).
- Sufficient RAM reserved in `Settings → General` (`Maximize size` guidance vs manual allocation).

## Enablement Procedure
- Step-by-step checklist mirroring manual:
  1. Confirm prerequisites.
  2. Press `Enable Virtual Machines`.
  3. Refresh page (if not auto-refreshing).
  4. Ensure `Create VM` button appears in Machines tab.
- Troubleshooting branch if enablement fails (check logs, re-run bridge script).

## VM Management Best Practices
- **Templates & Cloning**
  - Maintain “golden” system/game images for VM updates.
  - Document process for snapshotting before upgrades.
- **Game Updates**
  - Use VMs to update titles without booting physical clients.
  - After updates, apply writebacks and refresh playlists.
- **Resource Tuning**
  - Align VM RAM allocation with Settings slider.
  - Monitor arrays to ensure VM writebacks do not exceed thresholds.

## Licensing & ggLeap Integration
- Each VM consumes a ggLeap license; highlight ongoing work for license pooling.
- Provide instructions for naming conventions (internal name vs NETBIOS).
- Document steps to sync VM names with ggLeap (use Machines tab `Force Sync`).

## Troubleshooting
- **Bridge/WON’T CONTROL**
  - Re-run bridge creation script (`ggrock-create-bridge`).
  - Verify NIC assignments.
- **Console Issues**
  - Steps if noVNC session fails (clear cache, open new tab, check blocked popups).
- **Resource Shortages**
  - Error messages for insufficient RAM or disk space.
  - Guidance for adjusting allocation sliders or freeing writebacks.
- **Snapshot/Writeback conflicts**
  - VM-specific snapshot overrides and how they interact with automation.

## Operational Runbooks
- Rolling updates (snapshot, clone, update, promote).
- Disaster recovery (restore VM from backup image).
- Decommissioning VMs safely (unassign, delete, clean writebacks).

## Related Documentation
- `docs/frontend/virtual-machines.md` (UI plan)
- `docs/frontend/settings.md` (RAM allocation, bridge status)
- `docs/frontend/array-automation.md` / `docs/frontend/snapshot-retention.md` (cleanup policies)
- Confluence exports: `GGROCK/docs/Virtual+Machines.doc`, `GGROCK/docs/ggRock+Virtual+Machines+Administration+manual.doc`

