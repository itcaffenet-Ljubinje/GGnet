# Frontend Overview

The ggnet2 frontend is a modern React-based web application that provides a user interface for managing images, virtual machines, physical machines, storage, and system settings.

## Architecture

The frontend is built using:

- **React 18+**: UI framework
- **Vite**: Build tool and development server
- **React Router**: Client-side routing
- **WebSocket/SignalR**: Real-time communication with backend
- **Axios/Fetch**: HTTP client for API requests

## Project Structure

```
frontend/
├── package.json
├── vite.config.js
├── index.html
└── src/
    ├── main.jsx                 # Application entry point
    ├── App.jsx                  # Root component
    ├── components/
    │   ├── Layout/              # Layout components
    │   ├── Machines/            # Machine management components
    │   ├── Array/               # Storage/Array components
    │   ├── Images/               # Image management components
    │   └── Settings/             # Settings components
    ├── pages/
    │   ├── MachinesPage.jsx     # Machines page
    │   ├── ArrayPage.jsx        # Array/Storage page
    │   ├── ImagesPage.jsx       # Images page
    │   └── SettingsPage.jsx     # Settings page
    ├── services/
    │   └── api.js               # API service layer
    └── hooks/
        └── useWebSocket.js       # WebSocket hook
```

## Technology Stack

### Core Framework

- **React 18+**: Modern React with hooks and functional components
- **Vite**: Fast build tool and dev server
- **React Router v6**: Client-side routing

### State Management

- **React Context**: Global state management
- **React Hooks**: Local state management (useState, useReducer)
- **Zustand/Redux**: Optional state management library

### HTTP Client

- **Axios**: HTTP client for API requests
- **Fetch API**: Alternative HTTP client

### Real-time Communication

- **WebSocket**: Real-time updates via WebSocket
- **SignalR Client**: SignalR client for real-time communication

### UI Components

- **Material-UI / Chakra UI**: Component library (optional)
- **Custom Components**: Custom React components

## Application Structure

### Entry Point

**main.jsx:**
```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

### Root Component

**App.jsx:**
```jsx
import { BrowserRouter } from 'react-router-dom'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import MachinesPage from './pages/MachinesPage'
import ArrayPage from './pages/ArrayPage'
import ImagesPage from './pages/ImagesPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<MachinesPage />} />
          <Route path="/machines" element={<MachinesPage />} />
          <Route path="/array" element={<ArrayPage />} />
          <Route path="/images" element={<ImagesPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
```

## Component Organization

### Layout Components

- **Layout**: Main layout wrapper with navigation
- **Header**: Application header with navigation
- **Sidebar**: Sidebar navigation menu
- **Footer**: Application footer

### Machines Components

- **MachinesTable**: Main machines table
- **MachineRow**: Single machine row
- **MachineMenu**: Overflow menu (3 dots)
- **MachineSettingsDialog**: Settings dialog for machines
- **CreateVMModal**: Create VM modal form
- **VMSettingsDialog**: VM Settings dialog
- **ControlVMPage**: Dedicated VM Control page
- **VMInteractiveView**: noVNC/VNC embedded view
- **BulkOperationsBar**: Bulk operations toolbar
- **BulkSettingsDialog**: Bulk settings dialog
- **StatusIndicator**: Status icons/indicators
- **ColumnCustomizer**: Column customization
- **MachineFilters**: Filters/search
- **EnableVMsButton**: Enable VMs functionality

### Array Components

- **ArrayOverview**: Array/storage overview
- **PoolStatus**: Pool status display
- **PoolStats**: Pool statistics
- **DriveList**: Drive list display
- **ScrubControl**: Scrub control buttons
- **TrimControl**: TRIM control buttons

### Images Components

- **ImagesList**: Images list display
- **ImageCard**: Single image card
- **CreateImageModal**: Create image modal
- **ImageSettingsDialog**: Image settings dialog
- **SnapshotsList**: Snapshots list display
- **CreateSnapshotModal**: Create snapshot modal

### Settings Components

- **SettingsForm**: Settings form
- **SettingsSection**: Settings section
- **SettingsField**: Settings field component

## Routing

### Route Structure

- `/` - Machines page (default)
- `/machines` - Machines page
- `/array` - Array/Storage page
- `/images` - Images page
- `/settings` - Settings page
- `/machines/:id` - Machine details page
- `/vms/:id/control` - VM Control page

See [Routing](routing.md) for detailed routing documentation.

## API Integration

### API Service Layer

The frontend uses a service layer for API communication:

```javascript
// services/api.js
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

export const machinesAPI = {
  list: () => api.get('/machines'),
  get: (id) => api.get(`/machines/${id}`),
  create: (data) => api.post('/machines', data),
  update: (id, data) => api.put(`/machines/${id}`, data),
  delete: (id) => api.delete(`/machines/${id}`)
}

export const vmsAPI = {
  list: () => api.get('/vms'),
  create: (data) => api.post('/vms', data),
  start: (id) => api.post(`/vms/${id}/start`),
  stop: (id) => api.post(`/vms/${id}/stop`),
  getVNC: (id) => api.get(`/vms/${id}/vnc`)
}

export const imagesAPI = {
  list: () => api.get('/images'),
  create: (data) => api.post('/images', data),
  delete: (id) => api.delete(`/images/${id}`)
}
```

See [Services](services.md) for detailed API service documentation.

## Real-time Communication

### WebSocket Integration

The frontend uses WebSocket for real-time updates:

```javascript
// hooks/useWebSocket.js
import { useEffect, useState } from 'react'

export function useWebSocket(url) {
  const [socket, setSocket] = useState(null)
  const [messages, setMessages] = useState([])

  useEffect(() => {
    const ws = new WebSocket(url)
    ws.onopen = () => setSocket(ws)
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      setMessages(prev => [...prev, message])
    }
    return () => ws.close()
  }, [url])

  return { socket, messages }
}
```

See [WebSocket Integration](websocket.md) for detailed WebSocket documentation.

## State Management

### Global State

Global state is managed using React Context:

```javascript
// contexts/MachinesContext.jsx
import { createContext, useContext, useState } from 'react'

const MachinesContext = createContext()

export function MachinesProvider({ children }) {
  const [machines, setMachines] = useState([])
  const [selectedMachines, setSelectedMachines] = useState([])

  return (
    <MachinesContext.Provider value={{
      machines,
      setMachines,
      selectedMachines,
      setSelectedMachines
    }}>
      {children}
    </MachinesContext.Provider>
  )
}

export function useMachines() {
  return useContext(MachinesContext)
}
```

### Local State

Local state is managed using React hooks:

```javascript
import { useState } from 'react'

function MachineRow({ machine }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [status, setStatus] = useState(machine.status)

  return (
    // Component JSX
  )
}
```

## Development

### Development Server

Start development server:

```bash
npm run dev
```

### Build

Build for production:

```bash
npm run build
```

### Preview

Preview production build:

```bash
npm run preview
```

## Development Notes

- All components use functional components with hooks
- API calls are handled through the service layer
- Real-time updates use WebSocket/SignalR
- State management uses React Context and hooks
- Routing uses React Router v6

## To-Do

- [ ] Add error boundaries for error handling
- [ ] Implement loading states and skeletons
- [ ] Add form validation
- [ ] Implement optimistic updates
- [ ] Add offline support
- [ ] Implement caching strategy

