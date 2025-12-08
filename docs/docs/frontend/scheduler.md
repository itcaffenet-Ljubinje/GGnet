# Scheduler Frontend Plan

## Scope
- Design requirements for the ggRock Scheduler UI covering:
  - Viewing scheduled tasks (power, snapshots, scripts, maintenance).
  - Creating, editing, and deleting schedules.
  - Monitoring task execution history and upcoming runs.
  - Advanced behaviour extension hooks for new task types.

## Resource References
- [ggRock Scheduler KB](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860351/ggRock+Scheduler)
- [ggRock Scheduler – Adding New Behavior](https://ggcircuit.atlassian.net/wiki/spaces/GKB/pages/15860351/ggRock+Scheduler+-+Adding+New+Behavior)
- Confluence exports: `GGROCK/docs/ggRock+Scheduler.doc`, `GGROCK/docs/ggRock+Scheduler+-+Adding+New+Behavior.doc`

## User Personas
- **Operators** configuring recurring maintenance actions (shutdown, reboot, updates).
- **Support/Developers** adding custom behaviours or debugging scheduled jobs.

## Main Views

### 1. Scheduler Dashboard
- List of scheduled jobs with key columns:
  - `Name`, `Task Type`, `Target Scope` (single machine, group, global), `Next Run`, `Recurrence`, `Status`.
- Filters: by task type, status (active, paused, failed), next run window.
- Action bar: `Create Schedule`, `Pause`, `Resume`, `Delete`.
- Provide quick summary cards (total active jobs, paused jobs, recent failures).

### 2. Schedule Detail Panel
- Clicking a job reveals side panel with:
  - Description, creator, creation date.
  - Recurrence rule (cron-like description + human-readable string).
  - Targets (machine list, tags, groups) with ability to expand and view.
  - History snippet (last 5 runs with status, duration).
  - Buttons: `Edit`, `Duplicate`, `Delete`, `View Full History`.

### 3. History View
- Dedicated page/modal listing all past executions:
  - Columns: `Run Time`, `Status`, `Duration`, `Output/Log`.
  - Filters by date range, status (success, warning, error).
  - Option to download logs for support escalation.

## Schedule Creation/Edit Flow

1. **Task Selection**
   - Radio/cards for available task types (Power On/Off, Reboot, Snapshot, Script, VM operations).
   - Display description and required permissions.

2. **Target Selection**
   - Choose scope: `All Machines`, `Machine Group`, `Manual Selection`.
   - For manual selection, reuse machines list with search and multi-select.
   - Show estimated impact (number of machines, dependency warnings).

3. **Timing & Recurrence**
   - Scheduler should support:
     - One-time (specific date/time).
     - Daily/Weekly/Monthly patterns with start/end times.
     - Custom cron expression (advanced tab) with validation and preview.
   - Timezone awareness: display server TZ plus note for user local time.
   - Conflict detection: warn if overlapping tasks target same machines with different actions.

4. **Options**
   - Notifications: toggle email/alert on success/failure.
   - Pre/Post hooks (script execution, optional).
   - Safety checks: prompt for confirmation if task is destructive (shutdown).

5. **Review & Confirm**
   - Summary card showing task, targets, schedule, notifications.
   - Require confirmation checkbox for high-impact tasks.

6. **Save Outcome**
   - On success, show toast and highlight new entry in dashboard.
   - On validation failure, provide inline errors (e.g., missing target when required).

## Task Types & Behaviour Extensibility
- Each task type should define:
  - Required inputs (e.g., snapshot name, script payload).
  - Execution context (server-side vs. client-side).
  - Expected duration and rollback strategy.
- Provide extension mechanism (per KB “Adding New Behavior”):
  - UI should detect new behaviours exposed by backend metadata and auto-render appropriate form fields.
  - Include developer-mode toggle to route power users to behaviour docs.

## Error Handling & Monitoring
- Failed runs appear with red indicator; clicking reveals error log and retry option.
- Provide manual “Run Now” button to trigger schedule immediately (with confirmation).
- Pause/resume schedules without deleting configuration.
- Display banner for globally paused scheduler (e.g., maintenance window).

## Permissions & Roles
- Restrict creation/edit of destructive tasks to admins.
- Read-only users can view schedules and history but not modify.
- Log audit entries for create/edit/delete and manual runs.

## Notifications
- Configurable notifications per job:
  - Email, in-app alerts, webhook.
  - Option to aggregate daily digest of failures.
- Summaries in dashboard for upcoming tasks in next 24 hours.

## Open Questions
- Should scheduler support dependency chains (task B after task A success)?
- Do we need calendar visualization for monthly overview?
- Determine retention policy for history logs and whether to expose export function.
- Confirm API contract for dynamic behaviour metadata (field definitions, validation rules).

