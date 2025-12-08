# Settings Frontend Plan

## Scope
- ggRock Web UI `Settings` area covering `General`, `Network`, `Array & Images`, and `Secure Boot` subsections.
- Alignment with KB guidance and current admin console snapshots (`https://192.168.0.180/settings/...`).

## Information Architecture
- Persistent left nav for section switching; remember last visited tab.
- Sticky header with breadcrumb, save/apply controls, and unsaved changes indicator.
- Surface global alerts (e.g., license expiry, config mismatch) across subsections.

## General Settings
- **RAM Allocation:** Sliders/inputs for cache, VM pool, system reserved; enforce total sum <= physical RAM ([Settings KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860423/Settings)).
- **Release Stream:** Dropdown (Prod/Beta/etc.) with tooltip describing risk.
- **UI Preferences:** Dark mode toggle, default machines tab layout, language packs (if available).
- **Server Metadata:** Hostname, version, uptime. Display read-only fields with copy buttons.
- Highlight recommendation to keep `Maximize size` checked for automatic RAM cache management; expose manual override fields with validation (Settings doc export, Nov 9 2025).
- Microcopy:
  - RAM slider hint: `ggRock automatically tunes cache size when "Maximize" is enabled.`
  - Manual RAM input helper: `Enter values in GB. Totals must not exceed available memory.`
  - Release stream tooltip: `Prod = stable. Switch only with support guidance.`
- Save button should debounce and show inline validation (e.g., RAM minimums).
- Warn users that changing release stream triggers service restart.

## Network Settings
- **Bridge Configuration:** Status card showing VM bridge state; `Auto-Configure` button triggers diagnostic spinner ([Settings KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860423/Settings)).
- **Interfaces Table:** List NICs with role (PXE, Bridge, Management), IP/MAC, link speed.
- **DHCP/PXE Controls:** Link to network manager; show toggles to enable/disable services.
- Provide log viewer snippet for recent network config actions.
- If configuration fails, display actionable errors with retry.
- Provide clear red/green state for bridge readiness and detailed error messaging when auto-config fails (Settings doc export, Nov 9 2025).
- Microcopy:
  - Bridge status badge: `Green = Bridge ready for VM traffic. Red = Configuration required.`
  - Auto-config button tooltip: `Interrupts network briefly while creating bridge interface.`
  - Failure banner text: `Bridge setup failed. Check NIC assignments and try again.`

## Array & Images Settings
- Consolidate storage policies referenced by array/images modules:
  - `Reserved Disk Space %`
  - `Warning Threshold %`
  - `Unutilized Snapshots Retention`
  - `Unprotected Snapshots Count`
  - `Inactive Writebacks Retention`
- Allow scheduling for automated cleanup and provide preview of next run ([Automated Snapshot Removal](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860543/Automated+Snapshot+and+Writeback+Removal)).
- Include TRIM scheduler configuration (frequency, target pools) with link to array tab ([TRIM Management](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860429/TRIM+Management)).
- Display context about current space usage to prevent unsafe changes.
- Microcopy:
  - `Reserved Disk Space` helper: `Blocks new PXE boots and snapshot creation when threshold reached.`
  - `Unutilized Snapshots` tooltip: `Snapshots older than this window are eligible for cleanup unless protected.`
  - TRIM schedule hint: `Select maintenance window when array load is lowest.`

## Secure Boot Settings
- Card summarising secure boot status for physical clients and VMs.
- Toggle to enable/disable secure boot enforcement; requires confirmation modal referencing hardware prerequisites ([Settings KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860423/Settings)).
- Upload field for signed binaries or certificates if required; show validation result.
- Provide guidance text linking to vendor documentation; highlight restart impact.
- Microcopy:
  - Toggle warning: `Enabling Secure Boot requires compatible firmware on client machines.`
  - Certificate upload helper: `Accepted formats: .crt, .pem. Files are validated server-side.`

## UX Patterns
- All sections share `Save` and `Reset` controls; warn on navigation with unsaved changes.
- Use inline validation messages under fields.
- Successful save triggers toast + update timestamp.
- History drawer showing last 5 config changes with operator and time.

## Data & Permissions
- APIs: `GET/PUT /settings/general`, `/settings/network`, `/settings/storage`, `/settings/security`.
- Lock sensitive actions (secure boot, network changes) behind admin role; request confirmation.
- When applying network or secure boot settings, show blocking modal until service restarts complete.

## Open Questions
- Confirm whether release stream changes require scheduled maintenance window prompt.
- Determine if secure boot certificates should be stored encrypted client-side before upload.
- Align RAM allocation sliders with backend increments (MB vs. GB).
- Document whether software update/subscription panels need additional UI in future iteration.

## References
- [Settings KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860423/Settings)
- Admin console references: `https://192.168.0.180/settings/general`, `/network`, `/array-and-images`, `/secure-boot`
- Confluence export: `GGROCK/docs/Settings.doc` (local manual snapshot)

