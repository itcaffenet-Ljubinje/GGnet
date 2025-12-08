# Virtual Machines Frontend Plan

## Scope
- VM enablement surfaces inside machines tab.
- Dedicated VM creation, settings, control, and lifecycle flows within ggRock Web UI.
- Alignment with ggLeap licensing and ggRock server prerequisites.

## Prerequisites & Enablement
- Display checklist (BIOS virtualization, static IP, powered-off clients) before toggle becomes available ([Virtual Machines KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860971/Virtual+Machines)).
- Provide `Enable VMs` action with confirmation dialog; show spinner until server confirms bridge configuration.
- Surface errors when prerequisites missing; link to admin manual for remediation ([VM Admin Manual](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15861139/ggRock+Virtual+Machines+Administration+manual)).

## VM Creation Flow
- Triggered by `Create VM` button on Machines tab when enabled.
- **Form Fields:** `Name`, `System Image`, `Game Image`, `Virtual CPUs`, `Boot Mode`, `Drives Connection (Local vs Network)`, `RAM Size` ([Virtual Machines KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860971/Virtual+Machines)).
- Inline validation (e.g., RAM limit vs. reserved pool, CPU count > 0).
- Provide contextual tips (local drives faster; network boot for PXE testing).
- On submit, display progress and route user to VM row once created.

## VM Settings & Editing
- Machine settings modal gains `VM Settings` tab for VM entries; mirrors form structure with persisted values.
- Changes require reboot warning; show toast after save noting reboot needed.
- Support snapshot overrides identical to physical machines (system/game images).

## VM Control Surfaces
- Overflow menu actions: `Turn On`, `Shutdown`, `Reboot`, `Control VM`, `Open in New Tab`, `Full Screen`.
- `Control VM` launches embedded noVNC session; include toolbar with `Open in New Tab` (60-second share link) and `Full Screen` icons ([Virtual Machines KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860971/Virtual+Machines)).
- Respect browser popup blockers; fallback instructions if blocked.

## Monitoring & Status
- Show VM-specific status tags (e.g., `Powered Off`, `Running`, `Updating`).
- Indicate RAM pool usage; integrate total VM RAM cap slider from Settings (`settings.md`).
- Display licensing banner noting each VM consumes ggLeap license until policy changes ([Virtual Machines KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860971/Virtual+Machines)).

## Error Handling
- If bridge configuration fails, prompt to retry with logs (link to `/settings/network`).
- VM creation failures should roll back partially created entries and display actionable message (e.g., insufficient RAM).
- When control session expires, show reconnect prompt with countdown.

## Dependencies
- API contract: `POST /vms`, `PATCH /vms/{id}`, `POST /vms/{id}/power`, `POST /vms/{id}/control-session`.
- Shared with machines: column customization, bulk operations (VMs should participate with respect to power actions).
- Integration with array/image modules for snapshot selection.

## Open Questions
- Confirm retention of VM-specific console credentials in UI (auto-generated vs. user-specified).
- Determine messaging for background game updates triggered via VMs.
- Evaluate need for VM templates or cloning from existing machines.

## References
- [Virtual Machines KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860971/Virtual+Machines)
- [VM Administration Manual](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15861139/ggRock+Virtual+Machines+Administration+manual)
- Confluence exports: `GGROCK/docs/Virtual+Machines.doc`, `GGROCK/docs/ggRock+Virtual+Machines+Administration+manual.doc`

