# T-Array Implementation Plan

## Objective

Complete the Storage/Array page implementation to match ggRock Array management UI/UX. Primary files: `app/frontend/src/pages/Storage.jsx`, `Storage.css`, and related components.

## Current Status

### ✅ Implemented
- Basic array overview with pool status
- Usage bar visualization (Size, Used, Free, Reserved)
- Stripe configuration display
- Drive listing table
- TRIM manual run functionality
- Array creation wizard (3-step: Pool name, Select drives, Review)
- Drive details modal
- SMART data viewing
- Free drives modal
- TRIM status modal with progress tracking

### ⚠️ Partially Implemented
- Pool status fetching (has "Sync with backend" button, but should auto-fetch)
- Drive actions (basic structure exists, but missing some actions)

### ❌ Missing Features

1. **Health Status Indicators**
   - Status LED states: Green (Online), Amber (Degraded), Red (Offline)
   - RAID type badge adjacent to LED
   - Visual cues for degraded/rebuilding drives

2. **Drive Action Menu**
   - Overflow menu (⋮) per drive row
   - Actions: Details, Identify (blink), Mark Failed, Replace, Remove, View SMART
   - Role indicators (data/cache/spare)
   - Temperature display
   - Last Seen timestamp

3. **Rebuild/Resilver Progress**
   - Progress bar for resilver operations
   - ETA and resilver speed display
   - Lock conflicting operations during rebuild
   - Notification when rebuild completes

4. **Add Drive Wizard Enhancements**
   - Pre-flight checklist (Step 1): Confirm backup, note downtime impact
   - Drive selection validation: capacity ≥ largest drive in array
   - Warning if mixing SSD/HDD
   - Estimated rebuild window display
   - Post-submit resilver progress tracking

5. **Replace Drive Flow**
   - Replace flow triggered from drive row
   - Instructions for physical swap
   - Mark replaced functionality
   - Rebuild progress during replacement

6. **Remove Drive Flow**
   - Validation: Only allow for RAID levels that support removal (disallow RAID0)
   - Confirmation dialog with safeguards
   - Status updates

7. **Snapshot & Writeback Automation**
   - Retention controls inline:
     - Unutilized Snapshots (days)
     - Unprotected Snapshots (count)
     - Inactive Writebacks (hours)
     - Reserved Disk Space (%)
     - Warning Threshold (%)
   - Toggle for automation with tooltip
   - Upcoming cleanup schedule display
   - "Run Now" button with confirmation

8. **TRIM Scheduler UI**
   - TRIM scheduler status display
   - Last run timestamp
   - Cadence selection (daily/weekly/custom cron)
   - Target pools selection
   - SAN compatibility warning
   - Log of recent TRIM runs with durations

9. **Alerts & Edge Cases**
   - Persistent banner when array is DEGRADED or FAULTED
   - Link to relevant KB articles
   - Reserved space threshold breach highlighting
   - Toast notifications for threshold breaches
   - Hide destructive actions during rebuild
   - Acknowledgement required for irreversible operations
   - Take Offline / Bring Online actions with warnings

10. **Auto-refresh & Real-time Updates**
    - Auto-refresh for array metrics (currently manual "Sync with backend")
    - WebSocket/SSE for real-time resilver progress
    - Streaming updates for capacity stats

## Implementation Tasks

### Task 1: Health Status & Visual Indicators
- [ ] Add status LED component (Green/Amber/Red)
- [ ] Display RAID type badge
- [ ] Add visual cues for degraded/rebuilding drives
- [ ] Update drive row styling for status indicators

### Task 2: Drive Action Menu
- [ ] Implement overflow menu (⋮) for each drive row
- [ ] Add all drive actions (Details, Identify, Mark Failed, Replace, Remove, View SMART)
- [ ] Add role indicators (data/cache/spare)
- [ ] Display temperature and Last Seen in drive table
- [ ] Wire actions to backend API endpoints

### Task 3: Rebuild Progress Tracking
- [ ] Create rebuild progress component
- [ ] Display ETA and resilver speed
- [ ] Lock conflicting operations during rebuild
- [ ] Add notification when rebuild completes
- [ ] Integrate with WebSocket/SSE for real-time updates

### Task 4: Add Drive Wizard Enhancements
- [ ] Add Step 1: Pre-flight checklist
- [ ] Add validation: capacity ≥ largest drive
- [ ] Add SSD/HDD mixing warning
- [ ] Add estimated rebuild window
- [ ] Integrate resilver progress after submission

### Task 5: Replace Drive Flow
- [ ] Create replace drive modal/wizard
- [ ] Add physical swap instructions
- [ ] Implement mark replaced functionality
- [ ] Integrate rebuild progress

### Task 6: Remove Drive Flow
- [ ] Add RAID level validation (disallow RAID0)
- [ ] Create confirmation dialog with safeguards
- [ ] Wire to backend API

### Task 7: Snapshot & Writeback Automation
- [ ] Create automation settings section
- [ ] Add retention control inputs
- [ ] Add automation toggle with tooltip
- [ ] Display cleanup schedule
- [ ] Add "Run Now" button with confirmation

### Task 8: TRIM Scheduler UI
- [ ] Create TRIM scheduler settings section
- [ ] Add cadence selection (daily/weekly/custom)
- [ ] Add target pools selection
- [ ] Display last run timestamp
- [ ] Create TRIM run log/history
- [ ] Add SAN compatibility warning

### Task 9: Alerts & Edge Cases
- [ ] Create alert banner component
- [ ] Add DEGRADED/FAULTED banner
- [ ] Add threshold breach highlighting
- [ ] Implement action locking during rebuild
- [ ] Add confirmation dialogs for destructive actions
- [ ] Add Take Offline / Bring Online warnings

### Task 10: Auto-refresh & Real-time
- [ ] Replace manual "Sync with backend" with auto-refresh
- [ ] Implement WebSocket/SSE for real-time updates
- [ ] Add polling for resilver progress
- [ ] Update capacity stats automatically

## Backend API Requirements

### Existing Endpoints (Verify)
- `GET /api/storage/pool` - Pool status
- `GET /api/drives` - List drives
- `GET /api/drives/free` - Free drives
- `GET /api/drives/{name}/smart` - SMART data
- `POST /api/storage/trim/run` - Run TRIM
- `GET /api/storage/trim/status` - TRIM status
- `POST /api/array` - Create array
- `POST /api/array/extend` - Extend array

### Missing Endpoints (To Implement)
- `POST /api/drives/{name}/identify` - Blink drive LED
- `POST /api/drives/{name}/mark-failed` - Mark drive as failed
- `POST /api/drives/{name}/replace` - Replace drive
- `POST /api/drives/{name}/remove` - Remove drive
- `GET /api/storage/rebuild/status` - Rebuild/resilver status
- `GET /api/storage/automation/settings` - Get automation settings
- `PUT /api/storage/automation/settings` - Update automation settings
- `POST /api/storage/automation/run-now` - Run cleanup now
- `GET /api/storage/trim/schedule` - Get TRIM schedule
- `PUT /api/storage/trim/schedule` - Update TRIM schedule
- `GET /api/storage/trim/history` - TRIM run history
- `POST /api/array/{pool}/offline` - Take array offline
- `POST /api/array/{pool}/online` - Bring array online

## Files to Modify

1. **app/frontend/src/pages/Storage.jsx**
   - Add health status indicators
   - Implement drive action menu
   - Add rebuild progress tracking
   - Enhance add drive wizard
   - Add replace/remove drive flows
   - Add automation controls
   - Add TRIM scheduler UI
   - Add alerts and edge case handling
   - Implement auto-refresh

2. **app/frontend/src/pages/Storage.css**
   - Add styles for status LEDs
   - Style drive action menu
   - Add rebuild progress styles
   - Style automation controls
   - Add alert banner styles

3. **app/frontend/src/services/storageAPI.js**
   - Add missing API methods for new endpoints

4. **app/frontend/src/services/drivesAPI.js**
   - Add drive action methods (identify, mark-failed, replace, remove)

5. **app/frontend/src/services/arrayAPI.js**
   - Add array offline/online methods
   - Add rebuild status method

## Testing Checklist

- [ ] Health status indicators display correctly
- [ ] Drive action menu works for all actions
- [ ] Rebuild progress updates in real-time
- [ ] Add drive wizard validates correctly
- [ ] Replace drive flow works end-to-end
- [ ] Remove drive validates RAID level
- [ ] Automation settings save and apply
- [ ] TRIM scheduler saves schedule
- [ ] Alerts display for degraded/faulted arrays
- [ ] Actions lock during rebuild
- [ ] Auto-refresh works without manual sync

## Next Steps

1. Start with Task 1 (Health Status & Visual Indicators) - Quick win
2. Then Task 2 (Drive Action Menu) - Core functionality
3. Then Task 3 (Rebuild Progress) - Important UX
4. Continue with remaining tasks in order

## Notes

- Some backend endpoints may need to be implemented first
- WebSocket/SSE integration may require backend changes
- Consider creating shared components for status indicators and progress bars
- Reference ggRock Array KB documentation for exact UI/UX patterns


