# Machines Tab Frontend Plan

## Scope
- Machines list UX in `Machines` tab of ggRock Web UI.
- Machine-level actions (overflow menu, per-machine settings).
- Bulk operations toolbar and hidden machines toggle.

## Primary Views
- **Machines Table:** Columns default to `Name`, `Status`, `IP`, `System Image`, `Game Image`, `Uptime`, `Sent`, `Received`, `Speed`, `Link Speed`; optional `MAC Address` is available via column chooser ([Machines KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860891/Machines)).
- **Column Customizer:** Floating menu at far right; supports select/reset, persists per user.
- **Overflow Menu (per row):** `Turn On`, `Shutdown`, `Reboot`, `Apply Writebacks`, `Settings`, `Delete`.
- **Indicators:** Status badges and snapshot state icons (e.g., red/green arrows) must mirror ggRock semantics to communicate snapshot drift and pending writeback behaviour.
- Status column iconography:
  - **gg** badge (green = powered on, grey = off) indicates ggLeap integration; empty circle variants for non-integrated systems.
  - Warning badge highlights missing ggRock client.
  - Exclamation denotes missing system/game image assignment.
  - Link-speed warning surfaces when negotiated speed < 1 Gbps.
  - Keep Writebacks icon reflects persistence flag (Machines doc export, Nov 9 2025).
- Image status icons:
  - Question mark (hover tooltip describing upcoming snapshot change).
  - Green circle = running latest snapshot.
  - Red circle = pinned custom snapshot.
  - Arrow variants (red→green, green→red) indicate divergence and pending transitions (Machines doc export, Nov 9 2025).

## Key Interactions
- **Row Hover:** Reveal overflow menu button and highlight selection affordances.
- **Column Customization:** Apply updates instantly; surface toast confirmation on save/reset.
- **Settings Modal:** Expose machine metadata; include tabs for `Main` (name, IP, MAC, system/game image assignments, display settings, hide toggle) and VM settings when machine is virtualised ([Machines KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860891/Machines)).
- **Create VM Button:** Visible when VMs enabled; routes to VM creation flow (see `virtual-machines.md`).
- **Hardware Tab:** Display read-only hardware inventory (NIC, GPU, CPU, motherboard) for quick diagnostics (Machines doc export, Nov 9 2025).
- **Advanced Tab:** Include `Keep Writebacks`, per-machine snapshot overrides for system/game images with inline guidance (Machines doc export, Nov 9 2025).

## Bulk Operations
- Multi-select via left checkboxes; support `Select All`.
- Bulk action bar: `Reboot`, `Turn Off`, `Turn On`, `Edit Selected`. Editing uses dialog matching KB table (system/game image, resolution, refresh rate, hide, keep writebacks, snapshot overrides).
- Provide feedback (progress inline + dismissal toasts). Ensure disabled states when no machines selected.
- Bulk edit dialog must list selected machines and allow simultaneous changes across all supported fields; enforce confirm checkbox for destructive operations (Machines doc export, Nov 9 2025).

## Edge Cases & Alerts
- Display license status badge when inactive, include countdown messaging ([Machines KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860891/Machines)).
- Handle hidden machines with `Show Hidden` / `Hide Hidden` toggles; default hidden state persists across sessions.
- When `Apply Writebacks` available, gate action to powered-off machines; show modal summary before confirmation.
- Deletion must require type-to-confirm; update list optimistically with undo option.
- Provide confirmation modals with explicit “Confirm” checkbox for removal/offline actions to match current UX (Machines doc export, Nov 9 2025).

## Data & Performance Notes
- Table requires server-side pagination and filtering to handle large deployments.
- Poll machine telemetry (status, speeds) on interval; adopt diff-based updates to avoid flashing.
- Snapshot icons require joining machine assignment with image snapshot metadata to reflect `current`, `pending`, `pinned` states.

## Dependencies
- API endpoints: `GET /machines`, `PATCH /machines/{id}`, `POST /machines/{id}/power`, `POST /machines/bulk`, etc.
- Shared components: modal framework, form controls, toasts.
- Auth: enforce role-based access (operators vs. admins) for destructive actions.

## Open Questions
- Should column layouts be stored per-user (backend preference) or local storage?
- Confirm UX for machines that are part of automation groups (e.g., keep writebacks locked).
- Clarify handling of license countdown expiry (banner vs. modal lockout).

## References
- [Machines KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860891/Machines)
- [Machines Confluence Export](https://ggcircuit.atlassian.net/wiki/export/sites/GKB/pages/15860891/Machines) (internal manual snapshot)

