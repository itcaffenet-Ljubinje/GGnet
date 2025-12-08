# Frontend Components

The frontend components are organized by feature area (Machines, Array, Images, Settings) with shared layout components.

## Component Structure

```
frontend/src/components/
├── Layout/
│   ├── Layout.jsx
│   ├── Header.jsx
│   ├── Sidebar.jsx
│   └── Footer.jsx
├── Machines/
│   ├── MachinesTable.jsx
│   ├── MachineRow.jsx
│   ├── MachineMenu.jsx
│   ├── MachineSettingsDialog.jsx
│   ├── CreateVMModal.jsx
│   ├── VMSettingsDialog.jsx
│   ├── ControlVMPage.jsx
│   ├── VMInteractiveView.jsx
│   ├── BulkOperationsBar.jsx
│   ├── BulkSettingsDialog.jsx
│   ├── StatusIndicator.jsx
│   ├── ColumnCustomizer.jsx
│   ├── MachineFilters.jsx
│   └── EnableVMsButton.jsx
├── Array/
│   ├── ArrayOverview.jsx
│   ├── PoolStatus.jsx
│   ├── PoolStats.jsx
│   ├── DriveList.jsx
│   ├── ScrubControl.jsx
│   └── TrimControl.jsx
├── Images/
│   ├── ImagesList.jsx
│   ├── ImageCard.jsx
│   ├── CreateImageModal.jsx
│   ├── ImageSettingsDialog.jsx
│   ├── SnapshotsList.jsx
│   └── CreateSnapshotModal.jsx
└── Settings/
    ├── SettingsForm.jsx
    ├── SettingsSection.jsx
    └── SettingsField.jsx
```

## Layout Components

### Layout (`Layout.jsx`)

Main layout wrapper with header, sidebar, and content area.

**Props:**
- `children`: Page content

**Example:**
```jsx
<Layout>
  <MachinesPage />
</Layout>
```

### Header (`Header.jsx`)

Application header with navigation and user menu.

**Features:**
- Navigation links (Machines, Array, Images, Settings)
- User menu (if authentication is implemented)
- Application title/logo

### Sidebar (`Sidebar.jsx`)

Sidebar navigation menu.

**Features:**
- Navigation links
- Active route highlighting
- Collapsible sections

### Footer (`Footer.jsx`)

Application footer with copyright and links.

## Machines Components

### MachinesTable (`MachinesTable.jsx`)

Main machines table displaying physical and virtual machines.

**Props:**
- `machines`: Array of machines
- `onMachineSelect`: Callback for machine selection
- `onBulkAction`: Callback for bulk actions

**Features:**
- Sortable columns
- Filterable rows
- Selectable rows (bulk selection)
- Column customization
- Real-time status updates

**Example:**
```jsx
<MachinesTable
  machines={machines}
  onMachineSelect={handleMachineSelect}
  onBulkAction={handleBulkAction}
/>
```

### MachineRow (`MachineRow.jsx`)

Single machine row in the machines table.

**Props:**
- `machine`: Machine object
- `onSelect`: Callback for row selection
- `onMenuClick`: Callback for menu click
- `selected`: Whether row is selected

**Features:**
- Machine status display
- Status indicators
- Menu button (3 dots)
- Checkbox for bulk selection

**Example:**
```jsx
<MachineRow
  machine={machine}
  onSelect={handleSelect}
  onMenuClick={handleMenuClick}
  selected={selectedMachines.includes(machine.id)}
/>
```

### MachineMenu (`MachineMenu.jsx`)

Overflow menu (3 dots) for machine actions.

**Props:**
- `machine`: Machine object
- `onAction`: Callback for menu action
- `anchorEl`: Menu anchor element

**Menu Items (Physical Machines):**
- Turn On
- Shutdown
- Reboot
- Apply Writebacks
- Settings
- Delete

**Menu Items (Virtual Machines):**
- Control the VM
- Stop the VM
- Reset the VM
- Turn On
- Shutdown
- Reboot
- Apply Writebacks
- Settings
- Delete

**Example:**
```jsx
<MachineMenu
  machine={machine}
  onAction={handleAction}
  anchorEl={menuAnchor}
/>
```

### MachineSettingsDialog (`MachineSettingsDialog.jsx`)

Settings dialog for physical machines.

**Props:**
- `open`: Whether dialog is open
- `machine`: Machine object
- `onClose`: Callback for dialog close
- `onSave`: Callback for save action

**Settings Fields:**
- Name
- IP Address (Read Only)
- MAC Address (Read Only)
- System Image
- Game Image
- Display Resolution (optional)
- Display Refresh Rate (optional)
- Hide The Machine checkbox
- Advanced Settings (snapshots, keep writebacks)

**Example:**
```jsx
<MachineSettingsDialog
  open={dialogOpen}
  machine={selectedMachine}
  onClose={handleClose}
  onSave={handleSave}
/>
```

### CreateVMModal (`CreateVMModal.jsx`)

Modal form for creating a new virtual machine.

**Props:**
- `open`: Whether modal is open
- `onClose`: Callback for modal close
- `onCreate`: Callback for create action

**Form Fields:**
- Name (required)
- System Image (required)
- Game Image (required)
- Virtual CPUs (minimum 2)
- RAM Size (slider 0-32GB, minimum 4GB)
- Boot Mode (Legacy/UEFI)
- Drives Connection (Local Drives/Network)
- Maximum Boot RAM Size (info and link to Settings)

**Example:**
```jsx
<CreateVMModal
  open={modalOpen}
  onClose={handleClose}
  onCreate={handleCreate}
/>
```

### VMSettingsDialog (`VMSettingsDialog.jsx`)

Settings dialog for virtual machines with VM Settings tab.

**Props:**
- `open`: Whether dialog is open
- `vm`: VM object
- `onClose`: Callback for dialog close
- `onSave`: Callback for save action

**Settings Fields:**
- Name
- System Image
- Game Image
- Display Resolution (optional)
- Display Refresh Rate (optional)
- Hide The Machine checkbox

**VM Settings Tab:**
- Virtual CPUs
- RAM Size
- Boot Mode
- Drives Connection
- Maximum Boot RAM Size

**Advanced Settings:**
- System Image Snapshot
- Game Image Snapshot
- Keep Writebacks checkbox

**Example:**
```jsx
<VMSettingsDialog
  open={dialogOpen}
  vm={selectedVM}
  onClose={handleClose}
  onSave={handleSave}
/>
```

### ControlVMPage (`ControlVMPage.jsx`)

Dedicated VM Control page with interactive VM view.

**Props:**
- `vm`: VM object
- `onBack`: Callback for back button
- `onDelete`: Callback for delete action
- `onApplyWritebacks`: Callback for apply writebacks action
- `onSettings`: Callback for settings button
- `onPowerToggle`: Callback for power toggle
- `onReboot`: Callback for reboot action

**Features:**
- Back button
- Delete button
- Apply Writebacks button
- VM Settings button
- Turn On/Shut Down button
- Reboot button
- VM Interactive Area (noVNC/VNC embedded)

**Example:**
```jsx
<ControlVMPage
  vm={vm}
  onBack={handleBack}
  onDelete={handleDelete}
  onApplyWritebacks={handleApplyWritebacks}
  onSettings={handleSettings}
  onPowerToggle={handlePowerToggle}
  onReboot={handleReboot}
/>
```

### VMInteractiveView (`VMInteractiveView.jsx`)

noVNC/VNC embedded view for VM interaction.

**Props:**
- `vm`: VM object
- `vncUrl`: VNC connection URL
- `onOpenInNewTab`: Callback for open in new tab action

**Features:**
- Embedded noVNC client
- Fullscreen support (F11)
- Open in new tab button
- Keyboard and mouse input

**Example:**
```jsx
<VMInteractiveView
  vm={vm}
  vncUrl={vncUrl}
  onOpenInNewTab={handleOpenInNewTab}
/>
```

### BulkOperationsBar (`BulkOperationsBar.jsx`)

Toolbar for bulk operations on selected machines.

**Props:**
- `selectedMachines`: Array of selected machine IDs
- `onBulkAction`: Callback for bulk action
- `onEdit`: Callback for bulk edit action

**Bulk Actions:**
- Reboot
- Turn Off
- Turn On
- Edit Selected

**Example:**
```jsx
<BulkOperationsBar
  selectedMachines={selectedMachines}
  onBulkAction={handleBulkAction}
  onEdit={handleBulkEdit}
/>
```

### BulkSettingsDialog (`BulkSettingsDialog.jsx`)

Dialog for bulk editing settings of multiple machines.

**Props:**
- `open`: Whether dialog is open
- `selectedMachines`: Array of selected machine IDs
- `onClose`: Callback for dialog close
- `onSave`: Callback for save action

**Settings Fields:**
- Machines Selected (list)
- System Image
- Game Image
- Display Resolution
- Display Refresh Rate
- Hide These Machines checkbox
- Keep Writebacks checkbox
- System Image Snapshot
- Game Image Snapshot

**Example:**
```jsx
<BulkSettingsDialog
  open={dialogOpen}
  selectedMachines={selectedMachines}
  onClose={handleClose}
  onSave={handleSave}
/>
```

### StatusIndicator (`StatusIndicator.jsx`)

Status icons/indicators for machines.

**Props:**
- `machine`: Machine object
- `size`: Icon size (default: "small")

**Status Icons:**
- **Green Circle**: Machine on current snapshot, will switch to new snapshot on restart
- **Red Arrow -> Green Circle**: Machine on old snapshot, will switch to new snapshot on restart (if writeback applied)
- **Red Arrow -> Red Circle**: Machine on old snapshot, won't switch on restart (custom snapshot)
- **Green Arrow -> Red Circle**: Machine on current snapshot, will switch to older snapshot on restart (custom snapshot)

**Example:**
```jsx
<StatusIndicator
  machine={machine}
  size="small"
/>
```

### ColumnCustomizer (`ColumnCustomizer.jsx`)

Column customization dialog for machines table.

**Props:**
- `open`: Whether dialog is open
- `columns`: Array of column definitions
- `onClose`: Callback for dialog close
- `onApply`: Callback for apply action

**Features:**
- Checkbox for enable/disable columns
- Apply/Reset buttons

**Example:**
```jsx
<ColumnCustomizer
  open={dialogOpen}
  columns={columns}
  onClose={handleClose}
  onApply={handleApply}
/>
```

### MachineFilters (`MachineFilters.jsx`)

Filters and search for machines table.

**Props:**
- `onFilter`: Callback for filter change
- `onSearch`: Callback for search change

**Filters:**
- Type (Physical/Virtual/All)
- Status (Online/Offline/Unknown)
- System Image
- Game Image

**Search:**
- Search by name, IP, MAC address

**Example:**
```jsx
<MachineFilters
  onFilter={handleFilter}
  onSearch={handleSearch}
/>
```

### EnableVMsButton (`EnableVMsButton.jsx`)

Button for enabling Virtual Machines functionality.

**Props:**
- `vmsEnabled`: Whether VMs are enabled
- `onEnable`: Callback for enable action

**Features:**
- Warning dialog before enabling
- Prerequisites check display
- Enable button

**Example:**
```jsx
<EnableVMsButton
  vmsEnabled={vmsEnabled}
  onEnable={handleEnable}
/>
```

## Array Components

### ArrayOverview (`ArrayOverview.jsx`)

Array/storage overview page.

**Features:**
- Pool status display
- Pool statistics
- Drive list
- Scrub control
- TRIM control

### PoolStatus (`PoolStatus.jsx`)

ZFS pool status display.

**Props:**
- `pool`: Pool object

**Features:**
- Pool name
- Pool status (online/offline/degraded)
- Pool size and usage
- Pool health
- Topology display

### PoolStats (`PoolStats.jsx`)

Pool statistics display.

**Props:**
- `pool`: Pool object

**Features:**
- IO statistics
- ARC statistics
- Performance metrics

### DriveList (`DriveList.jsx`)

Drive list display.

**Props:**
- `drives`: Array of drive objects

**Features:**
- Drive information
- Drive status
- Drive health

### ScrubControl (`ScrubControl.jsx`)

Scrub control buttons.

**Props:**
- `pool`: Pool object
- `onStartScrub`: Callback for start scrub action
- `onGetStatus`: Callback for get scrub status action

### TrimControl (`TrimControl.jsx`)

TRIM control buttons.

**Props:**
- `pool`: Pool object
- `onEnableAutotrim`: Callback for enable autotrim action
- `onManualTrim`: Callback for manual TRIM action

## Images Components

### ImagesList (`ImagesList.jsx`)

Images list display.

**Props:**
- `images`: Array of image objects
- `onImageSelect`: Callback for image selection
- `onCreateImage`: Callback for create image action

### ImageCard (`ImageCard.jsx`)

Single image card.

**Props:**
- `image`: Image object
- `onSelect`: Callback for image selection
- `onDelete`: Callback for delete action

### CreateImageModal (`CreateImageModal.jsx`)

Modal form for creating a new image.

**Props:**
- `open`: Whether modal is open
- `onClose`: Callback for modal close
- `onCreate`: Callback for create action

### ImageSettingsDialog (`ImageSettingsDialog.jsx`)

Settings dialog for images.

**Props:**
- `open`: Whether dialog is open
- `image`: Image object
- `onClose`: Callback for dialog close
- `onSave`: Callback for save action

### SnapshotsList (`SnapshotsList.jsx`)

Snapshots list display.

**Props:**
- `image`: Image object
- `snapshots`: Array of snapshot objects
- `onCreateSnapshot`: Callback for create snapshot action

### CreateSnapshotModal (`CreateSnapshotModal.jsx`)

Modal form for creating a new snapshot.

**Props:**
- `open`: Whether modal is open
- `image`: Image object
- `onClose`: Callback for modal close
- `onCreate`: Callback for create action

## Settings Components

### SettingsForm (`SettingsForm.jsx`)

Settings form component.

**Props:**
- `settings`: Settings object
- `onSave`: Callback for save action

### SettingsSection (`SettingsSection.jsx`)

Settings section component.

**Props:**
- `title`: Section title
- `children`: Section content

### SettingsField (`SettingsField.jsx`)

Settings field component.

**Props:**
- `label`: Field label
- `name`: Field name
- `value`: Field value
- `onChange`: Callback for value change
- `type`: Field type (text, number, select, checkbox)

## Development Notes

- All components use functional components with hooks
- Props are validated using PropTypes or TypeScript
- Components are organized by feature area
- Shared components are in a common folder
- Components use consistent naming conventions

## To-Do

- [ ] Add component documentation (Storybook)
- [ ] Implement component testing
- [ ] Add component accessibility (ARIA)
- [ ] Implement component lazy loading
- [ ] Add component error boundaries
- [ ] Implement component performance optimization

