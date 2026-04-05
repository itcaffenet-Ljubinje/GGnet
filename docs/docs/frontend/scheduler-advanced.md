# Scheduler Behaviour Extension Plan

## Scope
- Documentation for extending ggRock Scheduler with new task behaviours and managing existing jobs.
- Inspired by Confluence export `GGROCK/docs/ggRock+Scheduler+-+Adding+New+Behavior.doc`.

## Audience
- Developers and advanced administrators customizing scheduler functionality.
- Support staff diagnosing scheduler behaviour issues.

## Architecture Overview
- Scheduler supports pluggable task behaviours defined via backend metadata.
- Each behaviour exposes:
  - Unique identifier.
  - Input schema (fields, types, validations).
  - Execution handler (service/action invoked on run).
  - Optional post-run hooks and notifications.

## Behaviour Registration Workflow
1. Implement backend behaviour (per manual), exposing metadata endpoint.
2. UI fetches metadata to render dynamic form fields.
3. Test behaviour using staging environment before exposing to production.
4. Document behaviour in admin UI (short description + prerequisites).

## UI Requirements
- Dynamic form rendering:
  - Support field types: text, number, dropdown, checkbox, cron expressions.
  - Display validation messages from metadata (e.g., “must be between 1-10”).
- Custom help text:
  - Provide inline descriptions for behaviours (sourced from metadata).
- Categorization:
  - Group behaviours (Power, Maintenance, Scripts, Custom).

## Testing & Validation
- Provide “Test Run” button in developer mode to execute behaviour immediately with sample inputs.
- Show detailed logs on completion for debugging.
- Allow behaviour-specific overrides (e.g., concurrency limits).

## Deployment Considerations
- Versioning: ensure UI handles metadata version changes gracefully.
- Feature flags: hide beta behaviours behind feature toggle.
- Permissions: restrict creation of jobs with certain behaviours to admin roles.

## Troubleshooting
- Behaviour metadata not loading: fallback to static configuration and display warning.
- Execution failures: surface backend error messages, highlight invalid inputs.
- Conflicting behaviours: warn if new behaviour targets same resources as existing critical tasks.

## Documentation & Support
- Maintain reference table of behaviours (name, description, inputs, owner).
- Provide links to internal runbooks or repos for behaviour implementation.
- Encourage creators to supply sample configs for documentation.

## References
- `GGROCK/docs/ggRock+Scheduler+-+Adding+New+Behavior.doc`
- `docs/frontend/scheduler.md` (base scheduler UI plan)

