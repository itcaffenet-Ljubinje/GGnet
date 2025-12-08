# T-Images Implementation Plan

## Objective

Complete the Images page implementation to match ggRock Images management UI/UX. Primary files: `app/frontend/src/pages/Images.jsx`, `Images.css`, and related components.

## Current Status

### ✅ Implemented
- Image listing with type filtering (System/Game)
- Image detail view with snapshots and writebacks tables
- Create image modal
- Snapshot creation
- Snapshot deletion
- Writeback display
- Batch operations modal structure
- Image details modal

### ⚠️ Partially Implemented
- Image catalog view (basic structure exists, but missing some metadata)
- Snapshot management (create/delete work, but missing promote/assign)
- Writeback handling (display works, but missing apply functionality per image)
- Bulk operations (modal exists, but functionality incomplete)

### ❌ Missing Features

1. **Image Catalog Enhancements**
   - Card/table hybrid view with all metadata:
     - Name, Type, Base Size, Latest Snapshot, Writebacks count, Last Modified, Assigned Machines
   - Default sort by last updated
   - Default boot image tag/badge
   - Compatibility hints for paired system/game images
   - Search/filter by name
   - Combined filter (All/System/Game)

2. **Create Image Wizard Enhancements**
   - Multi-step wizard: Details → Source → Summary
   - Source selection (clone existing vs. upload)
   - OS template selection for system images
   - Storage impact warning for game images
   - Disk space validation against array reserved space
   - Warning if under threshold
   - Support note about native creation flow for game images
   - Better microcopy and tooltips

3. **Snapshot Management**
   - Snapshot timeline component
   - Promote to Default action
   - Assign to Machines action
   - Dependency check before deletion (warn if machines pinned)
   - Integration with automation policy for aged snapshots
   - Snapshot metadata: created, author, notes
   - Protection/pinning indicators

4. **Writeback Handling**
   - Apply Writebacks button per image (commit functionality)
   - Per-image retention override (opt-out of automated cleanup)
   - Warning banner for large writebacks
   - Writeback size display and management

5. **Image Settings & Metadata**
   - Edit description, changelog, custom labels
   - Display checksum and build version
   - Advanced options panel (pinned snapshot, protected flag)
   - Copy image functionality (currently TODO)
   - Edit image functionality (currently TODO)

6. **Bulk Operations**
   - Multi-select UI for images/snapshots
   - Bulk delete snapshots
   - Bulk change defaults
   - Bulk export metadata
   - Progress feedback
   - Block bulk delete if any snapshot is mounted

7. **Backup/Restore Workflows**
   - Local backup workflow (path selection, progress)
   - Remote backup workflow (SSH credentials, target, job status)
   - Restore flows (local/remote) with checksum validation
   - Link to CLI instructions for advanced users

8. **Automation Integration**
   - Display upcoming automated deletions
   - Ability to protect snapshot from automation
   - Retention settings UI inline
   - Cleanup schedule display

9. **Edge Cases**
   - Handle missing base snapshot (mark as "Requires Repair")
   - Upload feature with resumable progress and hash verification
   - Graceful error handling
   - Empty states for no images/snapshots/writebacks

## Implementation Tasks

### Task 1: Image Catalog Enhancements
- [ ] Implement card/table hybrid view
- [ ] Add all metadata columns (Base Size, Latest Snapshot, Writebacks, Last Modified, Assigned Machines)
- [ ] Add default sort by last updated
- [ ] Add default boot image badge
- [ ] Add compatibility hints for paired images
- [ ] Implement search/filter functionality
- [ ] Add combined filter (All/System/Game)

### Task 2: Create Image Wizard
- [ ] Convert to multi-step wizard (Details → Source → Summary)
- [ ] Add source selection (clone vs. upload)
- [ ] Add OS template selection for system images
- [ ] Add storage impact warnings
- [ ] Implement disk space validation
- [ ] Add support notes and microcopy
- [ ] Add tooltips and help text

### Task 3: Snapshot Management
- [ ] Create snapshot timeline component
- [ ] Add Promote to Default action
- [ ] Add Assign to Machines action
- [ ] Implement dependency check before deletion
- [ ] Add snapshot metadata display (author, notes)
- [ ] Add protection/pinning indicators
- [ ] Integrate with automation policy

### Task 4: Writeback Handling
- [ ] Add Apply Writebacks button per image
- [ ] Implement per-image retention override
- [ ] Add warning banner for large writebacks
- [ ] Enhance writeback size display

### Task 5: Image Settings & Metadata
- [ ] Implement edit description/changelog/labels
- [ ] Display checksum and build version
- [ ] Add advanced options panel
- [ ] Implement copy image functionality
- [ ] Implement edit image functionality

### Task 6: Bulk Operations
- [ ] Implement multi-select UI
- [ ] Add bulk delete snapshots
- [ ] Add bulk change defaults
- [ ] Add bulk export metadata
- [ ] Add progress feedback
- [ ] Add mounted snapshot check

### Task 7: Backup/Restore Workflows
- [ ] Create local backup modal/workflow
- [ ] Create remote backup modal/workflow
- [ ] Implement restore flows
- [ ] Add checksum validation
- [ ] Add CLI instructions link

### Task 8: Automation Integration
- [ ] Display upcoming automated deletions
- [ ] Add protect snapshot from automation
- [ ] Add retention settings UI
- [ ] Display cleanup schedule

### Task 9: Edge Cases & Error Handling
- [ ] Handle missing base snapshot
- [ ] Add upload feature with progress
- [ ] Improve error handling
- [ ] Add empty states

## Backend API Requirements

### Existing Endpoints (Verify)
- `GET /api/images` - List images
- `GET /api/images/{id}` - Get image details
- `POST /api/images` - Create image
- `DELETE /api/images/{id}` - Delete image
- `GET /api/images/{id}/snapshots` - List snapshots
- `POST /api/images/{id}/snapshots` - Create snapshot
- `DELETE /api/images/{id}/snapshots/{name}` - Delete snapshot

### Missing Endpoints (To Implement)
- `POST /api/images/{id}/snapshots/{name}/promote` - Promote to default
- `POST /api/images/{id}/snapshots/{name}/assign` - Assign to machines
- `POST /api/images/{id}/writebacks/apply` - Apply writebacks
- `PUT /api/images/{id}` - Update image metadata
- `POST /api/images/{id}/clone` - Copy/clone image
- `POST /api/images/{id}/backup/local` - Local backup
- `POST /api/images/{id}/backup/remote` - Remote backup
- `POST /api/images/{id}/restore` - Restore image
- `GET /api/images/{id}/automation/settings` - Get automation settings
- `PUT /api/images/{id}/automation/settings` - Update automation settings
- `POST /api/images/bulk` - Bulk operations
- `GET /api/images/{id}/checksum` - Get checksum

## Files to Modify

1. **app/frontend/src/pages/Images.jsx**
   - Enhance image catalog view
   - Convert create modal to wizard
   - Add snapshot timeline
   - Add writeback apply functionality
   - Add image settings/metadata editing
   - Implement bulk operations
   - Add backup/restore workflows
   - Add automation integration

2. **app/frontend/src/pages/Images.css**
   - Style card/table hybrid view
   - Add snapshot timeline styles
   - Style wizard steps
   - Add backup/restore modal styles

3. **app/frontend/src/services/imagesAPI.js**
   - Add missing API methods

## Testing Checklist

- [ ] Image catalog displays all metadata correctly
- [ ] Create image wizard validates and creates images
- [ ] Snapshot timeline displays correctly
- [ ] Promote to default works
- [ ] Assign to machines works
- [ ] Writeback apply works per image
- [ ] Image metadata editing saves correctly
- [ ] Bulk operations work correctly
- [ ] Backup/restore workflows complete successfully
- [ ] Automation settings save and apply

## Next Steps

1. Start with Task 1 (Image Catalog Enhancements) - Improve current view
2. Then Task 2 (Create Image Wizard) - Better UX for creation
3. Then Task 3 (Snapshot Management) - Core functionality
4. Continue with remaining tasks

## Notes

- Some backend endpoints may need to be implemented first
- Consider creating shared components for timeline and wizard
- Reference ggRock Images KB documentation for exact UI/UX patterns
- Integration with machines module for assigned machines count


