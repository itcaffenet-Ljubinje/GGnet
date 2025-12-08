# T-Settings Implementation Plan

## Objective

Complete the Settings page implementation to match ggRock Settings UI/UX. Primary files: `app/frontend/src/pages/Settings.jsx`, `Settings.css`, and related components.

## Current Status

### ✅ Implemented
- Sidebar navigation with multiple tabs
- General tab with basic structure
- Network tab with basic structure
- Array & Images tab with basic structure
- Secure Boot tab with basic structure
- RAM allocation display (mock data)
- Server actions (Reboot, Restart Services)
- Settings state management

### ⚠️ Partially Implemented
- Settings fetching (API call exists, but not mapped to state)
- Save/Cancel functionality (structure exists, but TODO comments)
- RAM allocation (display only, no interactive sliders)
- Network bridge configuration (display only, no auto-configure)
- Array & Images settings (display only, no save functionality)

### ❌ Missing Features

1. **General Settings**
   - Interactive RAM allocation sliders/inputs
   - RAM sum validation (total <= physical RAM)
   - Release Stream dropdown (Prod/Beta/etc.)
   - UI Preferences (Dark mode, default layout, language)
   - Server metadata (Hostname, version, uptime) - read-only with copy buttons
   - "Maximize size" toggle with automatic RAM cache management
   - Manual override fields with validation
   - Inline validation messages
   - Save button debouncing

2. **Network Settings**
   - Bridge status card with auto-configure button
   - Diagnostic spinner during auto-config
   - Interfaces table (NICs with role, IP/MAC, link speed)
   - DHCP/PXE controls with toggles
   - Network config action log viewer
   - Error handling with actionable errors and retry
   - Clear red/green state for bridge readiness

3. **Array & Images Settings**
   - Interactive controls for:
     - Reserved Disk Space %
     - Warning Threshold %
     - Unutilized Snapshots Retention (days)
     - Unprotected Snapshots Count
     - Inactive Writebacks Retention (hours)
   - Automated cleanup scheduling
   - Preview of next cleanup run
   - TRIM scheduler configuration (frequency, target pools)
   - Current space usage context display

4. **Secure Boot Settings**
   - Secure boot status card
   - Toggle for enable/disable with confirmation modal
   - Upload field for signed binaries/certificates
   - Validation result display
   - Guidance text with vendor documentation links
   - Restart impact warnings

5. **Common Features**
   - Unsaved changes detection
   - Warning on navigation with unsaved changes
   - Save/Reset controls per section
   - Successful save toast + timestamp update
   - History drawer (last 5 config changes)
   - Persistent last visited tab (localStorage)
   - Sticky header with breadcrumb

6. **Additional Tabs**
   - Scheduler tab (currently shows "coming soon")
   - Software Update tab (currently shows "coming soon")
   - Subscriptions tab (currently shows "coming soon")
   - Account tab (currently shows "coming soon")
   - Employees tab (currently shows "coming soon")

## Implementation Tasks

### Task 1: Settings Data Integration
- [ ] Map API settings response to component state
- [ ] Implement settings loading from API
- [ ] Handle settings not found (defaults)
- [ ] Add error handling for settings fetch

### Task 2: General Settings
- [ ] Implement RAM allocation sliders
- [ ] Add RAM sum validation
- [ ] Add Release Stream dropdown
- [ ] Add UI Preferences section
- [ ] Add Server Metadata section with copy buttons
- [ ] Implement "Maximize size" toggle
- [ ] Add manual override fields
- [ ] Add inline validation
- [ ] Implement save with debouncing

### Task 3: Network Settings
- [ ] Create bridge status card component
- [ ] Implement auto-configure button with spinner
- [ ] Create interfaces table
- [ ] Add DHCP/PXE controls
- [ ] Add network config log viewer
- [ ] Implement error handling and retry
- [ ] Add bridge readiness status indicators

### Task 4: Array & Images Settings
- [ ] Implement interactive retention controls
- [ ] Add automated cleanup scheduling UI
- [ ] Add next cleanup run preview
- [ ] Add TRIM scheduler configuration
- [ ] Display current space usage context
- [ ] Add validation for threshold values

### Task 5: Secure Boot Settings
- [ ] Create secure boot status card
- [ ] Implement enable/disable toggle with confirmation
- [ ] Add certificate upload field
- [ ] Add validation result display
- [ ] Add guidance text and links

### Task 6: Common Features
- [ ] Implement unsaved changes detection
- [ ] Add navigation warning with unsaved changes
- [ ] Implement save functionality (wire to API)
- [ ] Implement cancel/reset functionality
- [ ] Add success toast and timestamp
- [ ] Create history drawer component
- [ ] Add localStorage for last visited tab
- [ ] Make header sticky with breadcrumb

### Task 7: Additional Tabs
- [ ] Implement Scheduler tab
- [ ] Implement Software Update tab
- [ ] Implement Subscriptions tab
- [ ] Implement Account tab
- [ ] Implement Employees tab

## Backend API Requirements

### Existing Endpoints (Verify)
- `GET /api/settings` - List all settings
- `GET /api/settings/{key}` - Get setting by key
- `PUT /api/settings/{key}` - Update setting
- `POST /api/settings/bulk` - Bulk update settings

### Missing Endpoints (To Implement)
- `GET /api/settings/general` - Get general settings
- `PUT /api/settings/general` - Update general settings
- `GET /api/settings/network` - Get network settings
- `PUT /api/settings/network` - Update network settings
- `POST /api/settings/network/auto-configure` - Auto-configure bridge
- `GET /api/settings/network/interfaces` - List network interfaces
- `GET /api/settings/network/logs` - Get network config logs
- `GET /api/settings/storage` - Get storage/array settings
- `PUT /api/settings/storage` - Update storage settings
- `GET /api/settings/security` - Get secure boot settings
- `PUT /api/settings/security` - Update secure boot settings
- `POST /api/settings/security/certificate` - Upload certificate
- `GET /api/settings/history` - Get settings change history
- `GET /api/server/metadata` - Get server metadata (hostname, version, uptime)

## Files to Modify

1. **app/frontend/src/pages/Settings.jsx**
   - Map API settings to state
   - Implement RAM sliders
   - Add all missing settings sections
   - Implement save/cancel functionality
   - Add unsaved changes detection
   - Add history drawer
   - Implement all tabs

2. **app/frontend/src/pages/Settings.css**
   - Style RAM sliders
   - Style bridge status card
   - Style interfaces table
   - Style history drawer
   - Add sticky header styles

3. **app/frontend/src/services/settingsAPI.js**
   - Add missing API methods

## Testing Checklist

- [ ] Settings load from API correctly
- [ ] RAM sliders validate correctly
- [ ] Save functionality works for all sections
- [ ] Cancel resets changes correctly
- [ ] Unsaved changes warning appears
- [ ] Bridge auto-configure works
- [ ] Network interfaces display correctly
- [ ] Retention controls save correctly
- [ ] Secure boot toggle works with confirmation
- [ ] Certificate upload validates correctly
- [ ] History drawer displays changes
- [ ] Last visited tab persists

## Next Steps

1. Start with Task 1 (Settings Data Integration) - Foundation
2. Then Task 2 (General Settings) - Most used
3. Then Task 6 (Common Features) - Shared functionality
4. Continue with remaining tasks

## Notes

- Settings should be organized by category for better API structure
- Consider creating shared components for sliders, toggles, and validation
- Reference ggRock Settings KB documentation for exact UI/UX patterns
- Some backend endpoints may need to be implemented first
- RAM allocation should use MB internally but display GB for user


