# Scheduler Implementation Checklist

## Goal
Translate the Scheduler UX plan into actionable development tasks covering UI components, API integration, and error handling.

## Frontend Tasks
1. **Scheduler Dashboard**
   - Implement jobs table with columns: Name, Task Type, Scope, Next Run, Recurrence, Status.
   - Add filters (task type, status, next run window) and summary cards (active, paused, failures).
   - Provide bulk actions (Pause, Resume, Delete) with confirm dialogs.

2. **Schedule Detail Panel**
   - Side panel showing description, creator, recurrence string, targets, recent history.
   - Buttons for Edit, Duplicate, Delete, View Full History.

3. **History View**
   - Full-page or modal list of executions with filters and log download.
   - Inline status indicators and duration.

4. **Create/Edit Flow**
   - Multi-step wizard: Task Selection → Target Selection → Timing/Recurrence → Options → Review.
   - Support standard frequencies + custom cron expression (with validation & preview).
   - Conflict detection UI for overlapping jobs (optional warning).

5. **Run Now & Notifications**
   - Add “Run Now” button with confirmation.
   - Configure notification toggles (email, in-app, webhook) per job.
   - Summaries for next 24h tasks (card or panel).

6. **Error Handling & Pause Mode**
   - Display failure banner with error details and retry option.
   - Global banner when scheduler paused (maintenance window).

7. **Dynamic Behaviour Support**
   - Fetch behaviour metadata to render custom fields.
   - Developer mode toggle to expose test run functionality (see `scheduler-advanced.md`).

## Backend/API Needs
- Endpoints:
  - `GET/POST /scheduler/jobs`, `PATCH /scheduler/jobs/{id}`, `DELETE /scheduler/jobs/{id}`
  - `POST /scheduler/jobs/{id}/run`, `POST /scheduler/jobs/{id}/pause/resume`
  - `GET /scheduler/history`, `GET /scheduler/behaviours`
- Provide metadata for behaviours (field definitions, validations, descriptions).
- Support notification configuration (email, webhook endpoints).
- Audit logging for job changes and manual runs.

## Testing
- Unit tests for wizard validation, recurrence parser, behaviour field rendering.
- Integration tests mocking scheduler API (job creation, run now, failure).
- Manual QA:
  - Create jobs with different frequencies, run now, pause/resume.
  - Test behaviour-specific fields and validation errors.
  - Inspect history logs and ensure export works.

## Coordination
- Work with backend on metadata schema for behaviours.
- Align with `scheduler-advanced.md` for extension workflows.
- Coordinate with notifications system for alert delivery.

## Deliverables
- Scheduler dashboard and detail views.
- Creation/edit wizard and dynamic behaviour support.
- Notification integration.
- Updated test suites and documentation.

