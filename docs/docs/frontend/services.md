# Frontend Services

The frontend services layer provides a clean API for communicating with the backend REST API.

## API Service Layer

The API service layer uses Axios for HTTP requests and provides typed functions for each API endpoint.

### API Client Setup

**services/api.js:**
```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: process.env.VITE_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // Handle errors
    if (error.response) {
      // Server responded with error
      console.error('API Error:', error.response.data)
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.request)
    } else {
      // Something else happened
      console.error('Error:', error.message)
    }
    return Promise.reject(error)
  }
)

export default api
```

## API Modules

### Machines API

**services/machines.js:**
```javascript
import api from './api'

export const machinesAPI = {
  // List all machines (physical + VM)
  list: (params = {}) => {
    return api.get('/machines', { params })
  },

  // Get machine details
  get: (id) => {
    return api.get(`/machines/${id}`)
  },

  // Update machine
  update: (id, data) => {
    return api.put(`/machines/${id}`, data)
  },

  // Delete machine
  delete: (id) => {
    return api.delete(`/machines/${id}`)
  },

  // Turn on machine (Wake-On-LAN for physical, start for VM)
  turnOn: (id) => {
    return api.post(`/machines/${id}/turn-on`)
  },

  // Shutdown machine
  shutdown: (id) => {
    return api.post(`/machines/${id}/shutdown`)
  },

  // Reboot machine
  reboot: (id) => {
    return api.post(`/machines/${id}/reboot`)
  },

  // Apply writebacks
  applyWritebacks: (id) => {
    return api.post(`/machines/${id}/writebacks`)
  },

  // Bulk operations
  bulkOperation: (data) => {
    return api.post('/machines/bulk', data)
  },

  // Bulk settings update
  bulkUpdateSettings: (data) => {
    return api.put('/machines/bulk', data)
  },

  // Force sync with ggLeap
  sync: () => {
    return api.post('/machines/sync')
  },

  // Get real-time status (SSE)
  getStatus: (id) => {
    return api.get(`/machines/${id}/status`)
  }
}
```

### VMs API

**services/vms.js:**
```javascript
import api from './api'

export const vmsAPI = {
  // Check if VMs are enabled
  checkEnabled: () => {
    return api.get('/vms/enabled')
  },

  // Enable VMs
  enable: () => {
    return api.post('/vms/enable')
  },

  // List all VMs
  list: () => {
    return api.get('/vms')
  },

  // Create VM
  create: (data) => {
    return api.post('/vms', data)
  },

  // Get VM details
  get: (id) => {
    return api.get(`/vms/${id}`)
  },

  // Update VM
  update: (id, data) => {
    return api.put(`/vms/${id}`, data)
  },

  // Delete VM
  delete: (id) => {
    return api.delete(`/vms/${id}`)
  },

  // Start VM
  start: (id) => {
    return api.post(`/vms/${id}/start`)
  },

  // Stop VM (force)
  stop: (id) => {
    return api.post(`/vms/${id}/stop`)
  },

  // Shutdown VM (graceful)
  shutdown: (id) => {
    return api.post(`/vms/${id}/shutdown`)
  },

  // Reboot VM
  reboot: (id) => {
    return api.post(`/vms/${id}/reboot`)
  },

  // Reset VM
  reset: (id) => {
    return api.post(`/vms/${id}/reset`)
  },

  // Get VM Control data
  getControl: (id) => {
    return api.get(`/vms/${id}/control`)
  },

  // Get VNC connection details
  getVNC: (id) => {
    return api.get(`/vms/${id}/vnc`)
  },

  // Apply writebacks
  applyWritebacks: (id) => {
    return api.post(`/vms/${id}/writebacks`)
  }
}
```

### Images API

**services/images.js:**
```javascript
import api from './api'

export const imagesAPI = {
  // List all images
  list: () => {
    return api.get('/images')
  },

  // Get image details
  get: (id) => {
    return api.get(`/images/${id}`)
  },

  // Create image
  create: (data) => {
    return api.post('/images', data)
  },

  // Delete image
  delete: (id) => {
    return api.delete(`/images/${id}`)
  },

  // Create snapshot
  createSnapshot: (id, data) => {
    return api.post(`/images/${id}/snapshots`, data)
  },

  // List snapshots
  listSnapshots: (id) => {
    return api.get(`/images/${id}/snapshots`)
  },

  // Delete snapshot
  deleteSnapshot: (id, snapshotName) => {
    return api.delete(`/images/${id}/snapshots/${snapshotName}`)
  },

  // Apply writebacks
  applyWritebacks: (id) => {
    return api.post(`/images/${id}/writebacks`)
  }
}
```

### Array API

**services/array.js:**
```javascript
import api from './api'

export const arrayAPI = {
  // Create pool
  createPool: (data) => {
    return api.post('/array/pool', data)
  },

  // Import pool
  importPool: (data) => {
    return api.post('/array/pool/import', data)
  },

  // Get pool status
  getPoolStatus: () => {
    return api.get('/array/pool')
  },

  // Get pool stats
  getPoolStats: () => {
    return api.get('/array/pool/stats')
  },

  // Start scrub
  startScrub: () => {
    return api.post('/array/pool/scrub')
  },

  // Get ARC stats
  getARCStats: () => {
    return api.get('/array/arc/stats')
  },

  // Enable autotrim
  enableAutotrim: () => {
    return api.post('/array/trim/enable')
  },

  // Manual TRIM
  manualTrim: () => {
    return api.post('/array/trim/manual')
  }
}
```

### Clients API

**services/clients.js:**
```javascript
import api from './api'

export const clientsAPI = {
  // List all clients
  list: () => {
    return api.get('/clients')
  },

  // Get client details
  get: (id) => {
    return api.get(`/clients/${id}`)
  },

  // Register client
  register: (data) => {
    return api.post('/clients', data)
  },

  // Update client
  update: (id, data) => {
    return api.put(`/clients/${id}`, data)
  },

  // Delete client
  delete: (id) => {
    return api.delete(`/clients/${id}`)
  },

  // Generate registry script
  generateRegistryScript: (id, data) => {
    return api.post(`/clients/${id}/registry-script`, data)
  }
}
```

### Settings API

**services/settings.js:**
```javascript
import api from './api'

export const settingsAPI = {
  // Get settings
  get: () => {
    return api.get('/settings')
  },

  // Update settings
  update: (data) => {
    return api.put('/settings', data)
  }
}
```

## Usage Examples

### Using Machines API

```javascript
import { machinesAPI } from './services/machines'

// List machines
const machines = await machinesAPI.list()

// Get machine details
const machine = await machinesAPI.get('machine-001')

// Update machine
await machinesAPI.update('machine-001', {
  name: 'PC-1-Updated',
  system_image: 'win11-updated'
})

// Turn on machine
await machinesAPI.turnOn('machine-001')

// Bulk operation
await machinesAPI.bulkOperation({
  machine_ids: ['machine-001', 'machine-002'],
  operation: 'reboot'
})
```

### Using VMs API

```javascript
import { vmsAPI } from './services/vms'

// Check if VMs are enabled
const { enabled } = await vmsAPI.checkEnabled()

// Enable VMs
if (!enabled) {
  await vmsAPI.enable()
}

// Create VM
const vm = await vmsAPI.create({
  name: 'VM-1',
  system_image: 'win11',
  game_image: 'games',
  vcpus: 4,
  ram: '8G',
  boot_mode: 'uefi',
  drives_connection: 'local'
})

// Start VM
await vmsAPI.start('vm-001')

// Get VNC connection
const { vnc_url } = await vmsAPI.getVNC('vm-001')
```

### Using Images API

```javascript
import { imagesAPI } from './services/images'

// List images
const images = await imagesAPI.list()

// Create image
const image = await imagesAPI.create({
  name: 'win11',
  type: 'system',
  size: '100G'
})

// Create snapshot
await imagesAPI.createSnapshot('win11', {
  name: '2024-01-01',
  description: 'Monthly snapshot'
})
```

### Using Array API

```javascript
import { arrayAPI } from './services/array'

// Create pool (can be done via web interface instead of during installation)
const pool = await arrayAPI.createPool({
  pool_name: 'pool0',
  devices: ['/dev/sda', '/dev/sdb'],
  topology: 'stripe'  // or 'mirror', 'raidz', 'raidz2', 'raidz3'
})

// Import existing pool
await arrayAPI.importPool({
  pool_name: 'pool0'
})

// Get pool status
const status = await arrayAPI.getPoolStatus()

// Get pool stats
const stats = await arrayAPI.getPoolStats()

// Start scrub
await arrayAPI.startScrub()

// Get ARC stats
const arcStats = await arrayAPI.getARCStats()

// Enable autotrim
await arrayAPI.enableAutotrim()

// Manual TRIM
await arrayAPI.manualTrim()
```

## Error Handling

### Error Handling Example

```javascript
import { machinesAPI } from './services/machines'

try {
  const machines = await machinesAPI.list()
} catch (error) {
  if (error.response) {
    // Server responded with error
    console.error('API Error:', error.response.data)
  } else if (error.request) {
    // Request made but no response
    console.error('Network Error:', error.request)
  } else {
    // Something else happened
    console.error('Error:', error.message)
  }
}
```

## Development Notes

- All API calls use Axios for HTTP requests
- API responses are automatically parsed from JSON
- Errors are handled in interceptors
- Authentication tokens are added automatically
- Timeout is set to 30 seconds

## To-Do

- [ ] Add request caching
- [ ] Implement request retry logic
- [ ] Add request/response logging
- [ ] Implement request cancellation
- [ ] Add request debouncing
- [ ] Implement request queue

