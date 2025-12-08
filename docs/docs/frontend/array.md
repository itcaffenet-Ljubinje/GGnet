# Array Management Frontend Plan

## Scope
- Array dashboard within ggRock Web UI (`Array` tab and related dialogs).
- Drive lifecycle flows (status inspection, rebuilds, additions, replacements).
- Automation controls for snapshots, writebacks, and TRIM.

## Array Overview
- Provide high-level health banner with ZFS state, capacity gauges, ARC cache telemetry ([Array KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860731/Array); Array doc export, Nov 9 2025).
- Display status LED states: **Green** = Online, **Amber** = Degraded, **Red** = Offline; show RAID type badge adjacent to LED (Array doc export, Nov 9 2025).
- Usage bar must visualise **Size**, **Used** (with %), **Free**, and **Reserved** segments, matching ggRock semantics.
- Highlight warning thresholds (reserved space %, warning level) sourced from Settings (`settings.md`).
- Include per-pool metrics: usable capacity, used, writeback volume, snapshot count.

## Drive Grid
- Table listing member disks: `Device`, `Model/Serial`, `Role` (data/cache/spare), `Status`, `Temperature`, `Last Seen`.
- Visual cues for degraded/rebuilding drives (e.g., amber/red badges). Provide progress bar for resilver operations.
- Action menu per drive: `Details`, `Identify (blink)`, `Mark Failed`, `Replace`, `Remove`, `View SMART`.
- Details dialog triggered from row overflow must include serial, firmware, interface, capacity, stripe membership; closes via `Done` or `×` (Array doc export, Nov 9 2025).

## Adding Drives
- Entry point: `Add Drive` wizard triggered from array banner when free slots detected ([Add Drives KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860351/How+to+add+new+Drives+to+your+Array)).
- **Step 1:** Pre-flight checklist (confirm backup, note downtime impact; highlight temporary degraded performance during rebuild).
- **Step 2:** Drive selection (filter by interface/capacity, ensure identical size). Enforce validation that capacity ≥ largest drive currently in array (Array doc export, Nov 9 2025).
- **Step 3:** Confirmation with estimated rebuild window; display caution if mixing SSD/HDD.
- Post-submit: surface resilver progress, disable conflicting actions until complete.

## Replacing / Rebuilding
- Support replace flow triggered from drive row (auto-selects target slot). Provide instructions to physically swap and mark replaced.
- During rebuild, lock conflicting operations and show ETA/resilver speed.
- Notify when rebuild completes; log to activity stream.
- Make `Remove Drive` available only for RAID levels that support single-disk removal (e.g., disallow for RAID0, allow for RAID1 with safeguards) (Array doc export, Nov 9 2025).

## Snapshot & Writeback Automation
- Surface retention controls inline: `Unutilized Snapshots`, `Unprotected Snapshots`, `Inactive Writebacks`, `Reserved Disk Space`, `Warning Threshold` ([Automated Snapshot Removal KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860543/Automated+Snapshot+and+Writeback+Removal)).
- Provide toggle for automation with tooltip summarizing policy.
- Show upcoming cleanup schedule with ability to run now; confirm before purge.

## TRIM Management
- Present TRIM scheduler status and last run timestamp; allow manual run ([TRIM Management KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860429/TRIM+Management)).
- Let admins define cadence (daily/weekly/custom) and target pools; warn about SAN compatibility.
- Display log of recent TRIM runs with durations and data trimmed.

## Alerts & Edge Cases
- When array enters `DEGRADED` or `FAULTED`, show persistent banner; provide link to relevant KB.
- If reserved space threshold breached, highlight in capacity gauge and push toast.
- Hide destructive actions while rebuild in progress; require acknowledgement for irreversible operations (e.g., mark failed).
- `Take Offline` / `Bring Online` actions should warn about service disruption and confirm intent before toggling state (Array doc export, Nov 9 2025).

## Data Dependencies
- Backend endpoints: `GET/POST /array`, `POST /array/drives`, `POST /array/rebuild`, `POST /array/trim`, `POST /array/automation`.
- Requires streaming updates for resilver status and capacity stats (consider SSE/WebSocket).
- Integrate with notifications center for long-running tasks.

## Open Questions
- Clarify UI for staging multiple drive additions (batch vs. sequential).
- Determine if array metrics should auto-refresh or rely on manual refresh.
- Confirm user roles permitted to trigger TRIM or cleanup.

## References
- [Array KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860731/Array)
- [How to add new Drives to your Array](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860351/How+to+add+new+Drives+to+your+Array)
- [TRIM Management](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860429/TRIM+Management)
- [Automated Snapshot and Writeback Removal](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860543/Automated+Snapshot+and+Writeback+Removal)
- Confluence exports: `GGROCK/docs/Array.doc`, `GGROCK/docs/How+to+add+new+Drives+to+your+Array.doc`, `GGROCK/docs/TRIM+Management.doc`, `GGROCK/docs/Automated+Snapshot+and+Writeback+Removal.doc`

