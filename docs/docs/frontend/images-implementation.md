# Images Tab Implementation Checklist

## Goal
Convert the UX plan in `images.md` into concrete development tasks for the frontend and backend.

## Frontend Tasks
1. **Catalog View**
   - Implement type tabs (System/Game) with optional “All” filter.
   - Create card/table hybrid with metadata chips (default tag, writeback counts).
   - Add search/filter inputs (name, type, assigned machines).

2. **Create Image Wizard**
   - Build multi-step dialog (Details → Source → Summary).
   - Include microcopy (placeholders, tooltips for Type/Make Default).
   - Validate volume size against available space (needs backend data).
   - Show support note that workflow is recommended for Game images.

3. **Snapshot Timeline**
   - Timeline component showing snapshots with tags (latest, custom).
   - Actions: Promote, Assign, Delete, Notes (with confirmation prompts).
   - Tooltips for icon statuses; inline warnings if snapshot is pinned elsewhere.

4. **Writeback Management**
   - Display banner when writebacks exceed threshold.
   - Button to Apply Writebacks referencing machine plan; show progress & result.

5. **Metadata Editing**
   - Inline editable fields (description, changelog, tags).
   - Advanced section toggles for Protected/Pinned snapshots.

6. **Bulk Operations**
   - Multi-select UI: delete snapshots, change defaults, export metadata.
   - Confirmation dialogues with caution copy.

7. **Backup/Restore Workflows**
   - Provide modal for Local Backup (path selection, progress).
   - Remote Backup (SSH creds, host validation).
   - Restore flows with checksum validation summary.
   - Link to CLI instructions for advanced users.

## Backend/API Needs
1. **Statistics & Validation**
   - Endpoint providing free space, reserved thresholds for volume size checks.
   - Snapshot metadata including protection state, pinned references.

2. **Bulk APIs**
   - `POST /images/bulk` for default changes and metadata updates.
   - Async job endpoints for backup/restore (polling or websocket events).

3. **Writeback Data**
   - Endpoint exposing per-image writeback sizes/counts.
   - Operation to trigger apply writebacks per image.

4. **Retention Overrides**
   - If per-image retention needed, provide API hooks.

## Testing
- Unit tests for form validation, timeline actions.
- Integration tests simulating API interactions (backup/restore, writeback application).
- Manual QA scenarios:
  - Creating new Game image and verifying machine assignment.
  - Promoting snapshot and confirming machine state changes.
  - Running backup/restore flows with success/failure paths.

## Coordination
- Work with backend on asynchronous job handling (progress notifications).
- Ensure alignment with storage automation docs (`array-automation.md`, `snapshot-retention.md`).
- Collaborate with UX/content for microcopy approvals.

## Deliverables
- New components (image cards, timeline, wizards).
- API integration layers for images module.
- Test suite updates (unit + integration).
- User documentation update summarizing new features.

