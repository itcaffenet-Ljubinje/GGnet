# Frontend P0 Analysis - Šta Postoji i Šta Nedostaje

**Datum:** 2025-11-18  
**Status:** 📊 Analiza Kompletna

---

## ✅ Šta Postoji na Frontend-u

### 1. Osnovna Struktura ✅
- ✅ React + Vite setup
- ✅ React Router (routing)
- ✅ Zustand (state management)
- ✅ React Query (data fetching)
- ✅ Axios (HTTP client)
- ✅ WebSocket hook (`useWebSocket.js`)

### 2. Komponente ✅
- ✅ Layout sa sidebar-om
- ✅ Header
- ✅ Notification system
- ✅ UI komponente (Button, Card, Badge, Modal)

### 3. Stranice ✅
- ✅ Dashboard
- ✅ Machines
- ✅ Images
- ✅ VMs
- ✅ Storage
- ✅ Settings
- ✅ Writebacks

### 4. API Services ✅
- ✅ `api.js` - Base API sa auth token interceptorom
- ✅ `machinesAPI.js` - Machines API
- ✅ `imagesAPI.js` - Images API
- ✅ `storageAPI.js` - Storage API (osnovni)
- ✅ `vmsAPI.js` - VMs API
- ✅ `settingsAPI.js` - Settings API
- ✅ `clientsAPI.js` - Clients API
- ✅ `networkAPI.js` - Network API
- ✅ `statsAPI.js` - Stats API

---

## ❌ Šta Nedostaje za P0 Module

### 1. Authentication & Authorization ❌

**Nedostaje:**
- ❌ Login page (`/login`)
- ❌ User management page
- ❌ Protected routes wrapper
- ❌ User menu/profile dropdown
- ❌ `usersAPI.js` service

**Potrebno:**
```javascript
// services/usersAPI.js
const usersAPI = {
  login: (credentials) => api.post('/users/login', credentials),
  getCurrentUser: () => api.get('/users/me'),
  listUsers: () => api.get('/users'),
  createUser: (data) => api.post('/users', data),
  getPermissions: () => api.get('/users/permissions'),
}
```

**Stranice:**
- `pages/Login.jsx` - Login form
- `pages/Users.jsx` - User management (opciono)

---

### 2. Bulk Operations - Machines ❌

**Postoji (placeholder):**
- ⚠️ Machines page ima `selectedMachineIds` state
- ⚠️ Bulk action buttons (turnOn, turnOff, reboot, applyWritebacks)
- ⚠️ Ali ne pozivaju stvarni API

**Nedostaje:**
- ❌ `machinesAPI.js` - Bulk operations metode
- ❌ Batch operation status modal
- ❌ Progress tracking UI
- ❌ WebSocket integration za real-time updates

**Potrebno dodati u `machinesAPI.js`:**
```javascript
// Bulk operations
bulkRestart: (machineIds) => api.post('/machines/bulk/restart', { machine_ids: machineIds }),
bulkShutdown: (machineIds) => api.post('/machines/bulk/shutdown', { machine_ids: machineIds }),
bulkWake: (machineIds) => api.post('/machines/bulk/wake', { machine_ids: machineIds }),
bulkTurnOn: (machineIds) => api.post('/machines/bulk/turn-on', { machine_ids: machineIds }),
getBatchStatus: (operationId) => api.get(`/machines/batch/${operationId}`),
```

**Komponente:**
- `components/BatchOperationModal.jsx` - Batch status modal
- `components/BatchProgress.jsx` - Progress indicator

---

### 3. Bulk Operations - Images ❌

**Nedostaje:**
- ❌ `batchImageOperationsAPI.js` service
- ❌ Bulk backup/restore/test UI
- ❌ Batch operation history
- ❌ Progress tracking

**Potrebno:**
```javascript
// services/batchImageOperationsAPI.js
const batchImageOperationsAPI = {
  getHistory: () => api.get('/batchImageOperations/history'),
  backupLocal: (data) => api.post('/batchImageOperations/backup/local', data),
  backupRemote: (data) => api.post('/batchImageOperations/backup/remote', data),
  restoreLocal: (data) => api.post('/batchImageOperations/restore/local', data),
  restoreRemote: (data) => api.post('/batchImageOperations/restore/remote', data),
  testLocal: (data) => api.post('/batchImageOperations/test/local', data),
  testRemote: (data) => api.post('/batchImageOperations/test/remote', data),
}
```

**Stranice:**
- `pages/BatchImageOperations.jsx` - Batch operations page
- Ili integracija u `Images.jsx`

---

### 4. Writebacks Management ⚠️

**Postoji:**
- ✅ `Writebacks.jsx` page
- ⚠️ Osnovna struktura

**Nedostaje:**
- ❌ API metode za writeback management
- ❌ Keep/delete writeback funkcionalnost
- ❌ Writeback listing za machines i images

**Potrebno dodati:**
```javascript
// machinesAPI.js
listWritebacks: (machineId) => api.get(`/machines/${machineId}/writebacks`),
keepWriteback: (writebackPath) => api.post(`/machines/writebacks/${writebackPath}/keep`),
keepAllWritebacks: () => api.post('/machines/writebacks/keep'),
deleteWriteback: (writebackPath) => api.delete(`/machines/writebacks/${writebackPath}`),

// imagesAPI.js
deleteImageWritebacks: (imagePath) => api.delete(`/images/${imagePath}/writebacks`),
```

---

### 5. Drive Management ❌

**Nedostaje:**
- ❌ `drivesAPI.js` service
- ❌ Drives list page ili integracija u Storage
- ❌ Drive details modal (SMART data)
- ❌ Free drives list

**Potrebno:**
```javascript
// services/drivesAPI.js
const drivesAPI = {
  list: () => api.get('/drives'),
  listFree: () => api.get('/drives/free'),
  getSmartData: (driveName) => api.get(`/drives/${driveName}/smart`),
}
```

**Komponente:**
- `components/DriveDetailsModal.jsx` - Drive details sa SMART data
- Integracija u `Storage.jsx` page

---

### 6. Array Operations ❌

**Nedostaje:**
- ❌ `arrayAPI.js` service
- ❌ Array creation wizard
- ❌ Drive add/remove/replace UI
- ❌ Array extend UI

**Potrebno:**
```javascript
// services/arrayAPI.js
const arrayAPI = {
  create: (data) => api.post('/array', data),
  extend: (data) => api.post('/array/extend', data),
  addDrives: (data) => api.post('/array/drives', data),
  removeDrive: (driveUuid, force) => api.delete(`/array/drives/${driveUuid}`, { params: { force } }),
  replaceDrive: (oldUuid, newUuid) => api.post(`/array/drives/${oldUuid}/replace`, { new_drive_uuid: newUuid }),
  driveOnline: (driveUuid) => api.post(`/array/drives/${driveUuid}/online`),
  driveOffline: (driveUuid, force) => api.post(`/array/drives/${driveUuid}/offline`, { params: { force } }),
  export: (poolName, force) => api.post('/array/export', { pool_name: poolName, force }),
  delete: (poolName, force) => api.delete('/array', { params: { pool_name: poolName, force } }),
  lookupStripes: (poolName) => api.get('/array/stripes/lookup', { params: { pool_name: poolName } }),
}
```

**Komponente:**
- `components/ArrayCreationWizard.jsx` - Array creation
- `components/DriveSelector.jsx` - Drive selection
- Integracija u `Storage.jsx`

---

### 7. TRIM Management ⚠️

**Postoji (osnovno):**
- ⚠️ `storageAPI.manualTrim()` - samo manual trim
- ⚠️ Storage page ima Trim button

**Nedostaje:**
- ❌ TRIM resume/suspend/cancel
- ❌ TRIM status display
- ❌ TRIM progress indicator
- ❌ TRIM settings UI

**Potrebno dodati u `storageAPI.js`:**
```javascript
// TRIM operations
trimResume: (poolName) => api.post('/array/trim/resume', { pool_name: poolName }),
trimSuspend: (poolName) => api.post('/array/trim/suspend', { pool_name: poolName }),
trimRun: (poolName) => api.post('/array/trim/run', { pool_name: poolName }),
trimCancel: (poolName) => api.post('/array/trim/cancel', { pool_name: poolName }),
getTrimStatus: (poolName) => api.get('/array/trim/status', { params: { pool_name: poolName } }),
```

**Komponente:**
- `components/TrimStatus.jsx` - TRIM status display
- `components/TrimControls.jsx` - TRIM control buttons
- Integracija u `Storage.jsx`

---

## 📊 Status Pregled

| P0 Modul | Backend | Frontend API | Frontend UI | Status |
|----------|---------|--------------|-------------|--------|
| **Authentication** | ✅ | ❌ | ❌ | Backend ready |
| **Bulk Ops - Machines** | ✅ | ⚠️ | ⚠️ | Partial |
| **Bulk Ops - Images** | ✅ | ❌ | ❌ | Backend ready |
| **Writebacks** | ✅ | ⚠️ | ⚠️ | Partial |
| **Drive Management** | ✅ | ❌ | ❌ | Backend ready |
| **Array Operations** | ✅ | ❌ | ❌ | Backend ready |
| **TRIM Management** | ✅ | ⚠️ | ⚠️ | Partial |

---

## 🚀 Prioriteti za Frontend Integraciju

### P0 (Critical)
1. **Authentication UI** - Login page, protected routes
2. **Bulk Operations - Machines** - Integracija postojećih bulk buttons
3. **Drive Management** - Drives list i SMART data

### P1 (High)
4. **Array Operations** - Array creation wizard
5. **TRIM Management** - TRIM controls i status
6. **Bulk Operations - Images** - Batch operations UI

### P2 (Medium)
7. **Writebacks Management** - Keep/delete funkcionalnost

---

## 📝 Preporuke

### 1. Authentication (Prvo)
- Kreirati `pages/Login.jsx`
- Dodati protected routes wrapper
- Dodati `services/usersAPI.js`
- Integrisati u Layout (user menu)

### 2. Bulk Operations - Machines
- Dodati metode u `machinesAPI.js`
- Integrisati postojeće bulk buttons
- Dodati batch status modal
- WebSocket integration za progress

### 3. Drive Management
- Kreirati `services/drivesAPI.js`
- Dodati drives list u Storage page
- Drive details modal sa SMART data

### 4. Array Operations
- Kreirati `services/arrayAPI.js`
- Array creation wizard
- Drive management UI

### 5. TRIM Management
- Proširiti `storageAPI.js` sa TRIM metodama
- TRIM controls u Storage page
- TRIM status i progress

---

*Frontend P0 Analysis - Detaljna analiza šta postoji i šta nedostaje!*

