# Advanced Array Operations Plan

## Scope
- UX requirements for advanced maintenance flows beyond daily array monitoring:
  - Adding drives after initial deployment.
  - Removing drives (RAID-dependent).
  - Replacing failed disks (forklift upgrade scenarios).
  - Converting between RAID0 and RAID10 configurations.
  - Large-scale disk replacement workflows.

## Resource References
- [Array KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860731/Array)
- [How to add new Drives to your Array](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860351/How+to+add+new+Drives+to+your+Array)
- [How to Convert your Array from RAID0-RAID10 and RAID10-RAID0](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860351/How+to+Convert+your+Array+from+RAID0-RAID10+and+RAID10-RAID0)
- [Replacing all ggRock Array Drives (Forklift Storage Upgrade)](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860351/Replacing+all+ggRock+Array+Drives+(Forklift+Storage+Upgrade))
- [Automated Snapshot and Writeback Removal](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860543/Automated+Snapshot+and+Writeback+Removal) (context for cleanup steps)
- Confluence exports: `GGROCK/docs/Array.doc`, `GGROCK/docs/How+to+add+new+Drives+to+your+Array.doc`, `GGROCK/docs/How+to+Convert+your+Array+from+RAID0-RAID10+and+RAID10-RAID0.doc`, `GGROCK/docs/Replacing+all+ggRock+Array+Drives+(Forklift+Storage+Upgrade).doc`, `GGROCK/docs/Automated+Snapshot+and+Writeback+Removal.doc`

## User Personas
- **System Administrators** performing storage maintenance with minimal downtime.
- **Support Technicians** guiding customers remotely through rebuild/replacement tasks.

## Preconditions & Warnings
- Ensure array health indicator is green before starting.
- Display reminder to take recent backups (system images, game images) prior to destructive actions.
- Highlight expected performance impact during rebuild (degraded throughput, increased risk).
- For RAID conversion/forklift operations, require explicit confirmation checkbox acknowledging downtime and risk.

## UI Flow Requirements

### 1. Add Drive Wizard
1. Entry via stripe overflow menu `Add Drive`.
2. **Step 1:** Display checklist:
   - Confirm new disk matches or exceeds largest drive capacity.
   - Warn about rebuild duration and degraded performance.
3. **Step 2:** Drive selection list:
   - Filter by interface/capacity.
   - Show current status (`available`, `in use`, `offline`).
4. **Step 3:** Summary & confirmation:
   - Show target stripe, expected rebuild progress indicator.
   - Require acknowledgement checkbox.
5. Post submission:
   - Present rebuild progress bar with ETA.
   - Disable conflicting operations (additional adds/removes) until rebuild completes.

### 2. Remove Drive Flow
1. Available only for supported RAID levels (block action for RAID0).
2. Overflow menu `Remove Drive` opens dialog:
   - Show drive details (serial, role, stripe).
   - Explain impact (data redistribution, downtime).
   - Confirm checkbox + typed confirmation.
3. On confirm, kick off removal and show inline progress; allow cancellation only before operation starts.

### 3. Replace Drive Flow
1. Overflow `Replace` opens dialog pre-populated with failing drive.
2. Steps:
   - Prompt to physically install new drive.
   - Present dropdown of eligible replacement disks (filtered by capacity).
   - Display warning about degraded performance during rebuild.
3. On submission, show progress similar to Add Drive.
4. Post-completion: prompt to run health check and clear alerts.

### 4. Take Offline / Bring Online
1. Actions accessible via overflow menu when drive is healthy/failed.
2. Dialog must include:
   - Reason text (e.g., "Use this if drive is known to be faulty").
   - Confirmation checkbox.
3. After offline:
   - Update drive state visually.
   - Provide quick action to `Bring Online` once issue resolved.

### 5. RAID Conversion Tool (RAID0 ↔ RAID10)
1. Accessible from advanced settings banner.
2. Multi-step wizard:
   - **Overview:** Explain requirements (minimum disk count, downtime, backups).
   - **Preparation:** Validate available disks; offer link to forklift guide.
   - **Execution:** Show tasks performed (snapshot cleanup, pool conversion).
   - **Finalization:** Prompt to verify machines boot, restore snapshots if needed.
3. Require multi-factor confirmation (checkbox + typed phrase).
4. Provide progress tracker with stateful resume support (in case of UI reload).

### 6. Forklift Upgrade Scenario
1. Dedicated guide modal summarising full replacement sequence:
   - Step-by-step: disable automation, remove old disks sequentially, add new, rebuild, re-enable cleanup.
   - Provide checklist after each phase.
2. Offer printable/exportable runbook for onsite technicians.
3. After completion, run auto-health diagnostics and present status report.

## Error Handling
- If validation fails (e.g., capacity mismatch), show inline error with remediation tip.
- On rebuild failure, surface actionable alerts with link to logs.
- Provide ability to download operation report (start/end times, drives involved).

## Telemetry & Audit
- Log every advanced operation with user, timestamp, drives affected.
- Expose history tab in array UI for traceability (filter by operation type).
- Notify admins via toast/email when long-running tasks finish or fail.

## Open Questions
- Should rebuild progress integrate with backend streaming (SSE/WebSocket) vs manual polling?
- Do we require maintenance mode to block client boots during conversions?
- Need alignment with automation policies (e.g., disable snapshot cleanup during replacement?).
- Confirm support for repeating forklift operation on multi-pool arrays.

