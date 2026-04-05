# Scheduler Behaviour Extension Implementation Checklist

## Goal
Convert `scheduler-advanced.md` into concrete development tasks for supporting dynamic behaviours in the Scheduler.

## Frontend Tasks
1. **Metadata Fetching**
   - Implement service to retrieve behaviour definitions (fields, types, validation rules).
   - Cache metadata with versioning and handle fallbacks if fetch fails.

2. **Dynamic Form Rendering**
   - Extend scheduler create/edit wizard to render inputs based on metadata:
     - Field types: text, numeric, dropdown, checkbox, cron expression, custom components.
     - Validation messages surfaced inline.
   - Group behaviours into categories (Power, Maintenance, Scripts, Custom).

3. **Developer Mode & Test Run**
   - Add toggle to enable “Developer Mode” (role-protected).
   - Provide “Test Run” button that executes behaviour immediately with provided inputs (requires backend support).
   - Display detailed logs/results after test run.

4. **Help & Documentation**
   - Inline help text sourced from metadata (description, prerequisites).
   - Link to behaviour documentation or runbook if provided.
   - Provide behaviour summary table (name, description, owner/contact).

5. **Feature Flags & Permissions**
   - Integrate feature flag checks to hide beta behaviours.
   - Ensure UI respects role permissions for behaviour creation.

6. **Error Handling**
   - Show warning banner if metadata fails to load (fall back to static config).
   - Clearly display backend error messages on execution failure.
   - Warn about conflicting behaviours (optional).

## Backend/API Requirements
- Provide behaviour metadata endpoint (`GET /scheduler/behaviours`) with versioning info.
- Support test runs (`POST /scheduler/behaviours/{id}/test`) returning execution logs.
- Extend job creation endpoint to accept dynamic behaviour payloads.
- Expose behaviour catalog for documentation (`GET /scheduler/behaviours/catalog`).
- Audit logging for behaviour execution (test or scheduled).

## Testing
- Unit tests for dynamic form component, validation handling, developer mode logic.
- Integration tests mocking metadata fetch and test run responses.
- Manual QA:
  - Verify behaviours render correctly.
  - Run test behaviour with sample inputs.
  - Check feature-flag and permission restrictions.

## Coordination
- Collaborate with backend developers implementing metadata/test endpoints.
- Align with documentation team to maintain behaviour catalog.
- Coordinate with security for permission model and feature flag strategy.

## Deliverables
- Updated scheduler wizard supporting dynamic behaviours.
- Developer mode/test run functionality.
- Behaviour catalog UI.
- Tests and documentation updates.

