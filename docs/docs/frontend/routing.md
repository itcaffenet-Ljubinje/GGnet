# Frontend Routing

The frontend uses React Router v6 for client-side routing and navigation.

## Route Configuration

### App Router Setup

**App.jsx:**
```javascript
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import MachinesPage from './pages/MachinesPage'
import ArrayPage from './pages/ArrayPage'
import ImagesPage from './pages/ImagesPage'
import SettingsPage from './pages/SettingsPage'
import ControlVMPage from './components/Machines/ControlVMPage'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<MachinesPage />} />
          <Route path="/machines" element={<MachinesPage />} />
          <Route path="/machines/:id" element={<MachineDetailsPage />} />
          <Route path="/array" element={<ArrayPage />} />
          <Route path="/images" element={<ImagesPage />} />
          <Route path="/images/:id" element={<ImageDetailsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/vms/:id/control" element={<ControlVMPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
```

## Route Structure

### Main Routes

- `/` - Machines page (default)
- `/machines` - Machines page
- `/machines/:id` - Machine details page
- `/array` - Array/Storage page
- `/images` - Images page
- `/images/:id` - Image details page
- `/settings` - Settings page
- `/vms/:id/control` - VM Control page

### Route Components

**MachinesPage.jsx:**
```javascript
import { useNavigate } from 'react-router-dom'
import MachinesTable from '../components/Machines/MachinesTable'

function MachinesPage() {
  const navigate = useNavigate()

  const handleMachineSelect = (machineId) => {
    navigate(`/machines/${machineId}`)
  }

  return (
    <div>
      <h1>Machines</h1>
      <MachinesTable onMachineSelect={handleMachineSelect} />
    </div>
  )
}

export default MachinesPage
```

**MachineDetailsPage.jsx:**
```javascript
import { useParams, useNavigate } from 'react-router-dom'
import { machinesAPI } from '../services/machines'

function MachineDetailsPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [machine, setMachine] = useState(null)

  useEffect(() => {
    machinesAPI.get(id).then(setMachine)
  }, [id])

  if (!machine) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <button onClick={() => navigate('/machines')}>Back</button>
      <h1>{machine.name}</h1>
      {/* Machine details */}
    </div>
  )
}

export default MachineDetailsPage
```

**ControlVMPage.jsx:**
```javascript
import { useParams, useNavigate } from 'react-router-dom'
import { vmsAPI } from '../services/vms'
import VMInteractiveView from './VMInteractiveView'

function ControlVMPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [vm, setVM] = useState(null)
  const [vncUrl, setVncUrl] = useState(null)

  useEffect(() => {
    vmsAPI.get(id).then(setVM)
    vmsAPI.getVNC(id).then(({ vnc_url }) => setVncUrl(vnc_url))
  }, [id])

  if (!vm) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <button onClick={() => navigate('/machines')}>Back</button>
      <h1>{vm.name}</h1>
      <VMInteractiveView vm={vm} vncUrl={vncUrl} />
    </div>
  )
}

export default ControlVMPage
```

## Navigation

### Programmatic Navigation

**Using useNavigate:**
```javascript
import { useNavigate } from 'react-router-dom'

function MyComponent() {
  const navigate = useNavigate()

  const handleClick = () => {
    navigate('/machines')
  }

  return <button onClick={handleClick}>Go to Machines</button>
}
```

**Using Link:**
```javascript
import { Link } from 'react-router-dom'

function Navigation() {
  return (
    <nav>
      <Link to="/machines">Machines</Link>
      <Link to="/array">Array</Link>
      <Link to="/images">Images</Link>
      <Link to="/settings">Settings</Link>
    </nav>
  )
}
```

### Navigation Links

**Sidebar Navigation:**
```javascript
import { NavLink, useLocation } from 'react-router-dom'

function Sidebar() {
  const location = useLocation()

  return (
    <nav>
      <NavLink
        to="/machines"
        className={({ isActive }) => isActive ? 'active' : ''}
      >
        Machines
      </NavLink>
      <NavLink
        to="/array"
        className={({ isActive }) => isActive ? 'active' : ''}
      >
        Array
      </NavLink>
      <NavLink
        to="/images"
        className={({ isActive }) => isActive ? 'active' : ''}
      >
        Images
      </NavLink>
      <NavLink
        to="/settings"
        className={({ isActive }) => isActive ? 'active' : ''}
      >
        Settings
      </NavLink>
    </nav>
  )
}
```

## Route Parameters

### Using Route Parameters

**Accessing Parameters:**
```javascript
import { useParams } from 'react-router-dom'

function MachineDetailsPage() {
  const { id } = useParams()

  return <div>Machine ID: {id}</div>
}
```

**Query Parameters:**
```javascript
import { useSearchParams } from 'react-router-dom'

function MachinesPage() {
  const [searchParams, setSearchParams] = useSearchParams()

  const type = searchParams.get('type') || 'all'
  const status = searchParams.get('status') || 'all'

  const handleFilterChange = (newType) => {
    setSearchParams({ type: newType, status })
  }

  return (
    <div>
      <select value={type} onChange={(e) => handleFilterChange(e.target.value)}>
        <option value="all">All</option>
        <option value="physical">Physical</option>
        <option value="virtual">Virtual</option>
      </select>
    </div>
  )
}
```

## Protected Routes

### Route Protection Example

```javascript
import { Navigate } from 'react-router-dom'

function ProtectedRoute({ children }) {
  const isAuthenticated = localStorage.getItem('token')

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return children
}

// Usage
<Route
  path="/machines"
  element={
    <ProtectedRoute>
      <MachinesPage />
    </ProtectedRoute>
  }
/>
```

## Development Notes

- All routes use React Router v6
- Navigation is handled programmatically and via Link components
- Route parameters are accessed via useParams hook
- Query parameters are handled via useSearchParams hook
- Protected routes can be implemented for authentication

## To-Do

- [ ] Add route guards for authentication
- [ ] Implement route-based code splitting
- [ ] Add route transition animations
- [ ] Implement route breadcrumbs
- [ ] Add route error boundaries
- [ ] Implement route analytics

