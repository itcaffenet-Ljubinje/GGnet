# T-Shared Components & Utilities Plan

## Objective

Document shared components, utilities, and data needs across the frontend, identify gaps, and call out backend API dependencies.

## Current Shared Components

### ✅ UI Components
- **Button** (`components/ui/Button.jsx`) - Variants: primary, secondary, danger; Sizes: small, medium, large
- **Card** (`components/ui/Card.jsx`) - Variants: default, elevated, outlined
- **Badge** (`components/ui/Badge.jsx`) - Variants: success, warning, error, info, online, offline, system, game
- **Modal** (`components/ui/Modal.jsx`) - Sizes: small, medium, large; Keyboard navigation (Escape)
- **Notification** (`components/Notification.jsx`) - Toast notifications with auto-dismiss

### ✅ Layout Components
- **Layout** (`components/Layout.jsx`) - Main layout with header, sidebar, content area
- **Header** (`components/Header.jsx`) - Global header with logo, title, utility icons
- **ProtectedRoute** (`components/ProtectedRoute.jsx`) - Route protection wrapper

### ✅ Utilities & Helpers

**Formatting Functions (Duplicated Across Pages):**
- `formatBytes()` - Present in: Machines.jsx, Images.jsx, Storage.jsx, Dashboard.jsx, Writebacks.jsx
- `formatDate()` - Present in: Images.jsx
- `formatUptime()` - Present in: Machines.jsx
- `formatDuration()` - Present in: Machines.jsx
- `formatSpeed()` - Present in: Machines.jsx

**State Management:**
- **useStore** (`store/useStore.js`) - Zustand store for:
  - UI state (sidebar)
  - User/auth state
  - Selected items (image, machine, VM)
  - Notifications
  - Loading states

**API Services:**
- **api.js** - Base Axios instance with interceptors
- **machinesAPI.js** - Machines API methods
- **imagesAPI.js** - Images API methods
- **vmsAPI.js** - VMs API methods
- **storageAPI.js** - Storage API methods
- **settingsAPI.js** - Settings API methods
- **drivesAPI.js** - Drives API methods
- **arrayAPI.js** - Array API methods
- **batchImageOperationsAPI.js** - Batch image operations

**Hooks:**
- **useWebSocket** (`hooks/useWebSocket.js`) - WebSocket connection hook

## Gaps & Improvements Needed

### 1. Shared Utility Functions
**Issue:** Formatting functions are duplicated across multiple files.

**Solution:** Create shared utilities file:
- `utils/formatters.js` - Centralized formatting functions:
  - `formatBytes(bytes)` - Format bytes to human-readable (B, KB, MB, GB, TB)
  - `formatDate(dateString, format?)` - Format dates (support multiple formats)
  - `formatUptime(seconds, fallback?)` - Format uptime (hours, minutes, seconds)
  - `formatDuration(totalSeconds)` - Format duration
  - `formatSpeed(value, unit?)` - Format network speed (Mbps, Gbps)
  - `formatPercentage(value, decimals?)` - Format percentages
  - `formatMACAddress(mac)` - Format MAC addresses
  - `formatIPAddress(ip)` - Format IP addresses

### 2. Shared Status Components
**Missing:** Reusable status indicator components

**Solution:** Create status components:
- `components/ui/StatusLED.jsx` - Status LED (Green/Amber/Red)
- `components/ui/StatusBadge.jsx` - Enhanced badge with icons
- `components/ui/ProgressBar.jsx` - Progress bar component
- `components/ui/HealthIndicator.jsx` - Health status indicator

### 3. Shared Form Components
**Missing:** Reusable form components

**Solution:** Create form components:
- `components/ui/Input.jsx` - Text input with validation
- `components/ui/Select.jsx` - Select dropdown
- `components/ui/Slider.jsx` - Range slider
- `components/ui/Checkbox.jsx` - Checkbox
- `components/ui/Radio.jsx` - Radio button
- `components/ui/Textarea.jsx` - Textarea

### 4. Shared Table Components
**Missing:** Reusable table components

**Solution:** Create table components:
- `components/ui/Table.jsx` - Base table component
- `components/ui/TableRow.jsx` - Table row with selection
- `components/ui/TableHeader.jsx` - Sortable table header
- `components/ui/EmptyState.jsx` - Empty state component
- `components/ui/LoadingState.jsx` - Loading state component
- `components/ui/ErrorState.jsx` - Error state component

### 5. Shared Wizard/Modal Components
**Missing:** Reusable wizard component

**Solution:** Create wizard component:
- `components/ui/Wizard.jsx` - Multi-step wizard component
- `components/ui/WizardStep.jsx` - Wizard step component

### 6. Shared Action Menu
**Missing:** Reusable overflow menu component

**Solution:** Create action menu component:
- `components/ui/ActionMenu.jsx` - Overflow menu (⋮) component
- `components/ui/ActionMenuItem.jsx` - Menu item component

### 7. Data Formatting & Validation
**Missing:** Centralized data validation and transformation

**Solution:** Create utilities:
- `utils/validators.js` - Validation functions:
  - `validateMACAddress(mac)`
  - `validateIPAddress(ip)`
  - `validateEmail(email)`
  - `validateRequired(value)`
- `utils/transformers.js` - Data transformation:
  - `transformMachineData(machine)` - Transform machine data for display
  - `transformImageData(image)` - Transform image data for display
  - `transformStorageData(storage)` - Transform storage data for display

### 8. Mock vs Live Data
**Current State:**
- Storage page uses mock data with "Sync with backend" button
- Some pages use placeholder data
- Need consistent approach to mock vs live data

**Solution:**
- Create `utils/mockData.js` for development mock data
- Add environment flag for mock mode
- Ensure all pages can work with both mock and live data
- Add data source indicator (dev mode only)

### 9. Error Handling
**Current State:**
- Basic error handling in API interceptor
- Page-level error states (Machines has it, others may not)

**Solution:**
- Create shared error handling utilities:
  - `utils/errorHandler.js` - Centralized error handling
  - `components/ui/ErrorBoundary.jsx` - React error boundary
  - Standardize error display across pages

### 10. Loading States
**Current State:**
- Each page implements its own loading state
- Inconsistent loading indicators

**Solution:**
- Create shared loading components:
  - `components/ui/LoadingSpinner.jsx` - Reusable spinner
  - `components/ui/LoadingSkeleton.jsx` - Skeleton loader
  - Standardize loading states

## Backend API Gaps

### Missing Endpoints Identified

1. **Machines API**
   - ✅ Most endpoints exist
   - ⚠️ Bulk apply writebacks (frontend shows "coming soon")
   - ⚠️ Bulk edit (frontend shows "coming soon")

2. **Storage/Array API**
   - ⚠️ Drive actions: identify, mark-failed, replace, remove
   - ⚠️ Rebuild/resilver status endpoint
   - ⚠️ Automation settings endpoints
   - ⚠️ TRIM schedule endpoints
   - ⚠️ Array offline/online endpoints

3. **Images API**
   - ⚠️ Promote snapshot to default
   - ⚠️ Assign snapshot to machines
   - ⚠️ Apply writebacks per image
   - ⚠️ Update image metadata
   - ⚠️ Copy/clone image
   - ⚠️ Backup/restore endpoints
   - ⚠️ Automation settings per image

4. **Settings API**
   - ⚠️ Category-based endpoints (general, network, storage, security)
   - ⚠️ Network auto-configure endpoint
   - ⚠️ Network interfaces endpoint
   - ⚠️ Network logs endpoint
   - ⚠️ Secure boot certificate upload
   - ⚠️ Settings history endpoint
   - ⚠️ Server metadata endpoint

5. **Real-time Updates**
   - ⚠️ WebSocket/SSE for rebuild progress
   - ⚠️ WebSocket/SSE for capacity stats
   - ⚠️ WebSocket/SSE for machine status updates

## Implementation Tasks

### Task 1: Create Shared Utilities
- [ ] Create `utils/formatters.js` with all formatting functions
- [ ] Create `utils/validators.js` with validation functions
- [ ] Create `utils/transformers.js` with data transformation functions
- [ ] Update all pages to use shared utilities
- [ ] Remove duplicate formatting functions

### Task 2: Create Shared UI Components
- [ ] Create StatusLED component
- [ ] Create ProgressBar component
- [ ] Create EmptyState component
- [ ] Create LoadingState component
- [ ] Create ErrorState component
- [ ] Create ActionMenu component
- [ ] Create Wizard component
- [ ] Create form components (Input, Select, Slider, etc.)

### Task 3: Standardize Error Handling
- [ ] Create error handling utilities
- [ ] Create ErrorBoundary component
- [ ] Add error states to all pages
- [ ] Standardize error messages

### Task 4: Standardize Loading States
- [ ] Create LoadingSpinner component
- [ ] Create LoadingSkeleton component
- [ ] Standardize loading states across pages

### Task 5: Mock Data Management
- [ ] Create mock data utilities
- [ ] Add environment flag for mock mode
- [ ] Ensure all pages support mock data
- [ ] Add data source indicator

### Task 6: Backend API Integration
- [ ] Document all missing endpoints
- [ ] Prioritize endpoint implementation
- [ ] Update frontend to use new endpoints as they become available

## Files to Create

1. **app/frontend/src/utils/formatters.js**
2. **app/frontend/src/utils/validators.js**
3. **app/frontend/src/utils/transformers.js**
4. **app/frontend/src/utils/errorHandler.js**
5. **app/frontend/src/utils/mockData.js**
6. **app/frontend/src/components/ui/StatusLED.jsx**
7. **app/frontend/src/components/ui/ProgressBar.jsx**
8. **app/frontend/src/components/ui/EmptyState.jsx**
9. **app/frontend/src/components/ui/LoadingState.jsx**
10. **app/frontend/src/components/ui/ErrorState.jsx**
11. **app/frontend/src/components/ui/ActionMenu.jsx**
12. **app/frontend/src/components/ui/Wizard.jsx**
13. **app/frontend/src/components/ui/ErrorBoundary.jsx**
14. **app/frontend/src/components/ui/LoadingSpinner.jsx**

## Files to Update

1. **app/frontend/src/pages/Machines.jsx** - Use shared utilities
2. **app/frontend/src/pages/Images.jsx** - Use shared utilities
3. **app/frontend/src/pages/Storage.jsx** - Use shared utilities
4. **app/frontend/src/pages/Dashboard.jsx** - Use shared utilities
5. **app/frontend/src/pages/Writebacks.jsx** - Use shared utilities
6. **app/frontend/src/pages/Settings.jsx** - Use shared utilities
7. **app/frontend/src/pages/VMs.jsx** - Use shared utilities

## Testing Checklist

- [ ] All formatting functions work correctly
- [ ] Shared components render correctly
- [ ] Error handling works across pages
- [ ] Loading states are consistent
- [ ] Mock data mode works
- [ ] No duplicate code in pages

## Next Steps

1. Start with Task 1 (Shared Utilities) - Quick win, reduces duplication
2. Then Task 2 (Shared UI Components) - Reusable components
3. Then Task 3 & 4 (Error & Loading States) - Consistency
4. Then Task 5 (Mock Data) - Development support
5. Finally Task 6 (Backend API) - As endpoints become available

## Notes

- Prioritize creating shared utilities first (biggest impact, least effort)
- Shared components should follow ggRock design system
- Consider creating a component library/storybook in the future
- Backend API gaps should be tracked separately and prioritized by feature importance


