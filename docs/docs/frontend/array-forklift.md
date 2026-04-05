# Forklift Storage Upgrade Plan

## Scope
- UI/UX guidelines for replacing all array drives (“forklift upgrade”) while preserving data.
- Derived from Confluence export `GGROCK/docs/Replacing+all+ggRock+Array+Drives+(Forklift+Storage+Upgrade).doc`.

## Objectives
- Guide administrators step-by-step through full disk replacement.
- Minimize risk by enforcing backups, sequencing operations, and providing checklists.
- Offer progress tracking and validation at each stage.

## Entry Point
- Accessed via `Array` tab banner or advanced maintenance menu.
- Present overview modal summarizing prerequisites before launching flow.

## Prerequisite Checklist
- Confirm recent backups of system & game images (with links to backup tools).
- Ensure spare capacity or staging storage is available if needed.
- Warn about expected downtime and degraded performance.
- Require acknowledgment checkbox to proceed.

## Multi-Step Wizard

1. **Preparation**
   - Disable automated tasks (snapshot cleanup, TRIM) with toggles and reminders to re-enable later.
   - Prompt to document current array configuration (download JSON/report).

2. **Disk Swap Sequence**
   - Step-by-step instructions:
     - Physically install new drives (one stripe at a time).
     - Use UI prompts to `Mark Old Drive Failed`, `Replace`, and monitor rebuild.
   - Provide checklist for each stripe:
     - `Remove old drive`, `Insert new`, `Run Replace Wizard`, `Wait for rebuild`.
   - Display rebuild progress and estimated completion per stripe.

3. **Validation**
   - After all replacements, run automated health checks (pool status, SMART).
   - Require manual confirmation that machines boot successfully.
   - Offer optional snapshot cleanup to remove stale data from old disks.

4. **Finalization**
   - Re-enable previously disabled automation (snapshot removal, TRIM).
   - Update documentation/report with new drive inventory (downloadable summary).
   - Provide reminder to adjust retention policies if capacity changed.

## Safety Nets
- Ability to pause between steps with state persistence (resume later).
- Banner warnings if rebuild in progress when user attempts to advance.
- Log all actions with timestamps for audit.

## Notifications
- Send notifications (toast/email) when each rebuild completes or fails.
- Alert if rebuild exceeds expected duration or encounters errors.

## UI Components
- Timeline/Checklist component with completion ticks.
- Rebuild progress bars aggregated per stripe.
- Downloadable “runbook” PDF summarizing procedure for on-site technicians.

## API/Integration Needs
- Endpoints to trigger/monitor replacements already covered by array APIs.
- Additional endpoint for generating/exporting configuration report.
- Hooks to temporarily disable/re-enable automation features.

## Open Questions
- Should wizard support parallel replacement (multiple drives) if RAID allows?
- Need rollback guidance if new drive fails during process?
- Provide integration with hardware chassis LED control (`Identify`) for physical swap assistance?

## References
- Confluence export: `GGROCK/docs/Replacing+all+ggRock+Array+Drives+(Forklift+Storage+Upgrade).doc`
- Related plans: `docs/frontend/array.md`, `docs/frontend/array-advanced.md`, `docs/frontend/array-automation.md`

