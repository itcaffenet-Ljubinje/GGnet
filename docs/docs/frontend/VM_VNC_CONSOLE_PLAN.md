# VM VNC Console Frontend Implementation Plan

**Datum kreiranja:** 2025-01-26  
**Status:** 📋 Plan za implementaciju

---

## 📊 Pregled

Implementacija VNC konzole stranice za virtualne mašine, omogućavajući pristup VM konzoli direktno iz web browser-a kroz noVNC.

**URL Format:** `/machines/control-vm/:vm_id` ili `/vms/control/:vm_id`  
**Primer:** `https://192.168.0.180/machines/control-vm/1c0bc17a-68a6-4d45-872b-aeebadea7c3b`

---

## 🎯 Ciljevi

1. **VNC Console Page** - Dedicated stranica za VNC konzolu
2. **Routing Integration** - Dodati route u `App.jsx`
3. **API Integration** - Dodati `getVNC()` metodu u `vmsAPI.js`
4. **UI Components** - noVNC iframe embed sa toolbar-om
5. **Error Handling** - Loading states, error states, VM status checks
6. **Navigation** - Link iz Machines/VMs tabele i context menu-a

---

## 📋 Tasks

### Task 1: API Service Update (`vm-vnc-api-service`)

**Fajl:** `app/frontend/src/services/vmsAPI.js`

**Akcije:**
- Dodati `getVNC(vmId)` metodu koja poziva `GET /api/vms/{vm_id}/vnc`
- Return-uje VNC URL, token, port, host, websocket_url

**Code:**
```javascript
// Get VNC URL and connection details
getVNC: (id) => {
  return api.get(`/vms/${id}/vnc`)
},
```

**Validacija:**
- ✅ Metoda postoji u `vmsAPI.js`
- ✅ Koristi `api.get()` helper
- ✅ Handle-uje error responses

---

### Task 2: VNC Console Page Component (`vm-vnc-console-page`)

**Fajl:** `app/frontend/src/pages/VMConsole.jsx`

**Akcije:**
- Kreirati novu stranicu komponentu za VNC konzolu
- Koristiti React Router `useParams()` za dobijanje `vm_id` iz URL-a
- Koristiti `useQuery` za fetch-ovanje VNC info
- Prikazati noVNC iframe sa `vnc_url`
- Dodati toolbar sa:
  - VM name
  - Status indicator
  - Fullscreen toggle
  - Close button (navigate back)
  - Refresh button (reconnect)

**State Management:**
```javascript
const { vmId } = useParams()
const { data: vncInfo, isLoading, error } = useQuery({
  queryKey: ['vm-vnc', vmId],
  queryFn: () => vmsAPI.getVNC(vmId),
  enabled: !!vmId,
  retry: 2,
})
```

**UI Structure:**
```jsx
<div className="vm-console-page">
  <div className="vm-console-toolbar">
    <div className="toolbar-left">
      <h2>VM Console: {vmName}</h2>
      <Badge variant={vmStatus === 'running' ? 'success' : 'default'}>
        {vmStatus}
      </Badge>
    </div>
    <div className="toolbar-right">
      <Button onClick={handleFullscreen}>Fullscreen</Button>
      <Button onClick={handleRefresh}>Refresh</Button>
      <Button onClick={handleClose}>Close</Button>
    </div>
  </div>
  <div className="vm-console-container">
    {vncInfo && (
      <iframe
        src={vncInfo.vnc_url}
        className="vm-console-iframe"
        title="VM Console"
        allowFullScreen
      />
    )}
  </div>
</div>
```

**Validacija:**
- ✅ Komponenta se renderuje sa `vm_id` iz URL-a
- ✅ Prikazuje loading state dok se fetch-uje VNC info
- ✅ Prikazuje error state ako VM nije running ili VNC nije dostupan
- ✅ Iframe se renderuje sa `vnc_url`
- ✅ Toolbar funkcioniše (fullscreen, refresh, close)

---

### Task 3: VNC Console CSS (`vm-vnc-console-css`)

**Fajl:** `app/frontend/src/pages/VMConsole.css`

**Akcije:**
- Kreirati CSS fajl za VNC konzolu stranicu
- Stilizovati toolbar (flexbox layout, dark theme)
- Stilizovati console container (full height, no borders)
- Stilizovati iframe (100% width/height, no borders, seamless)
- Responsive design za mobile/tablet

**CSS Structure:**
```css
.vm-console-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-primary);
}

.vm-console-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.vm-console-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.vm-console-iframe {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}
```

**Validacija:**
- ✅ Toolbar je na vrhu, fixed height
- ✅ Console container zauzima preostali prostor
- ✅ Iframe je seamless (no borders, full size)
- ✅ Responsive na mobile/tablet

---

### Task 4: Routing Integration (`vm-vnc-routing`)

**Fajl:** `app/frontend/src/App.jsx`

**Akcije:**
- Import-ovati `VMConsole` komponentu
- Dodati route za `/machines/control-vm/:vm_id`
- Opciono: dodati route za `/vms/control/:vm_id` (alternativa)

**Code:**
```javascript
import VMConsole from './pages/VMConsole'

// U Routes:
<Route path="machines/control-vm/:vm_id" element={<VMConsole />} />
<Route path="vms/control/:vm_id" element={<VMConsole />} />
```

**Validacija:**
- ✅ Route je dodat u `App.jsx`
- ✅ Navigacija na `/machines/control-vm/{vm_id}` radi
- ✅ `vm_id` se prosleđuje kao param

---

### Task 5: Machines Page Integration (`vm-vnc-machines-integration`)

**Fajl:** `app/frontend/src/pages/Machines.jsx`

**Akcije:**
- Dodati "Control the VM" akciju u context menu za VMs
- Koristiti `useNavigate()` za navigaciju na VNC konzolu
- Proveriti da li je VM running pre navigacije
- Ako VM nije running, prikazati error notification

**Code:**
```javascript
import { useNavigate } from 'react-router-dom'

const navigate = useNavigate()

const handleControlVM = (machine) => {
  // Proveri da li je VM
  if (!machine.vm_id) {
    addNotification({
      type: 'error',
      message: 'This machine is not a virtual machine',
    })
    return
  }
  
  // Proveri da li je running
  if (machine.status !== 'running') {
    addNotification({
      type: 'error',
      message: 'VM must be running to access console',
    })
    return
  }
  
  // Navigate to VNC console
  navigate(`/machines/control-vm/${machine.vm_id}`)
}
```

**Context Menu Update:**
```jsx
{menuOpenId === machine.id && (
  <div className="row-actions-menu">
    {/* Existing actions */}
    {machine.vm_id && machine.status === 'running' && (
      <button
        onClick={() => {
          handleControlVM(machine)
          setMenuOpenId(null)
        }}
      >
        Control the VM
      </button>
    )}
  </div>
)}
```

**Validacija:**
- ✅ "Control the VM" akcija je u context menu-u
- ✅ Prikazuje se samo za VMs koji su running
- ✅ Navigacija radi na klik
- ✅ Error handling za non-VM ili stopped VM

---

### Task 6: VMs Page Integration (`vm-vnc-vms-integration`)

**Fajl:** `app/frontend/src/pages/VMs.jsx`

**Akcije:**
- Dodati "Control" ili "Console" button u VM card
- Koristiti `useNavigate()` za navigaciju
- Prikazati button samo ako je VM running

**Code:**
```javascript
import { useNavigate } from 'react-router-dom'

const navigate = useNavigate()

const handleControlVM = (vm) => {
  if (vm.status !== 'running') {
    addNotification({
      type: 'error',
      message: 'VM must be running to access console',
    })
    return
  }
  
  navigate(`/vms/control/${vm.id}`)
}
```

**UI Update:**
```jsx
<div className="vm-actions">
  {vm.status === 'running' && (
    <button
      className="btn-primary"
      onClick={() => handleControlVM(vm)}
    >
      Control
    </button>
  )}
  {/* Existing actions */}
</div>
```

**Validacija:**
- ✅ "Control" button je u VM card-u
- ✅ Prikazuje se samo za running VMs
- ✅ Navigacija radi na klik

---

### Task 7: Error Handling & Edge Cases (`vm-vnc-error-handling`)

**Fajl:** `app/frontend/src/pages/VMConsole.jsx`

**Akcije:**
- Handle-ovati slučajeve kada:
  - VM nije running (prikazati error sa "Start VM" button-om)
  - VNC nije dostupan (prikazati error message)
  - VM ne postoji (404 error)
  - Network error (retry button)
- Dodati auto-refresh ako se VM stop-uje tokom sesije
- Dodati connection status indicator

**Error States:**
```jsx
// VM not running
if (vmInfo && vmInfo.status !== 'running') {
  return (
    <ErrorState
      title="VM is not running"
      message="The virtual machine must be running to access the console."
      action={
        <Button onClick={() => handleStartVM()}>
          Start VM
        </Button>
      }
    />
  )
}

// VNC not available
if (error && error.response?.status === 400) {
  return (
    <ErrorState
      title="VNC not available"
      message={error.response.data.detail}
    />
  )
}
```

**Auto-refresh:**
```javascript
// Poll VM status while console is open
useEffect(() => {
  if (!vmId || !vncInfo) return
  
  const interval = setInterval(() => {
    queryClient.invalidateQueries(['vm', vmId])
  }, 5000) // Check every 5 seconds
  
  return () => clearInterval(interval)
}, [vmId, vncInfo, queryClient])
```

**Validacija:**
- ✅ Error states su prikazani za sve edge cases
- ✅ Auto-refresh radi kada je VM stop-ovan
- ✅ Connection status indicator prikazuje trenutni status

---

### Task 8: Fullscreen Support (`vm-vnc-fullscreen`)

**Fajl:** `app/frontend/src/pages/VMConsole.jsx`

**Akcije:**
- Implementirati fullscreen toggle button
- Koristiti Fullscreen API
- Handle-ovati fullscreen exit events
- Dodati keyboard shortcut (F11)

**Code:**
```javascript
const [isFullscreen, setIsFullscreen] = useState(false)

const handleFullscreen = () => {
  const container = document.querySelector('.vm-console-container')
  
  if (!isFullscreen) {
    if (container.requestFullscreen) {
      container.requestFullscreen()
    } else if (container.webkitRequestFullscreen) {
      container.webkitRequestFullscreen()
    } else if (container.mozRequestFullScreen) {
      container.mozRequestFullScreen()
    } else if (container.msRequestFullscreen) {
      container.msRequestFullscreen()
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen()
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen()
    } else if (document.mozCancelFullScreen) {
      document.mozCancelFullScreen()
    } else if (document.msExitFullscreen) {
      document.msExitFullscreen()
    }
  }
}

useEffect(() => {
  const handleFullscreenChange = () => {
    setIsFullscreen(!!document.fullscreenElement)
  }
  
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  document.addEventListener('webkitfullscreenchange', handleFullscreenChange)
  document.addEventListener('mozfullscreenchange', handleFullscreenChange)
  document.addEventListener('MSFullscreenChange', handleFullscreenChange)
  
  return () => {
    document.removeEventListener('fullscreenchange', handleFullscreenChange)
    document.removeEventListener('webkitfullscreenchange', handleFullscreenChange)
    document.removeEventListener('mozfullscreenchange', handleFullscreenChange)
    document.removeEventListener('MSFullscreenChange', handleFullscreenChange)
  }
}, [])
```

**Validacija:**
- ✅ Fullscreen toggle button radi
- ✅ Fullscreen API je cross-browser compatible
- ✅ Keyboard shortcut (F11) radi
- ✅ Exit fullscreen radi

---

### Task 9: Loading & Connection States (`vm-vnc-loading-states`)

**Fajl:** `app/frontend/src/pages/VMConsole.jsx`

**Akcije:**
- Prikazati loading spinner dok se fetch-uje VNC info
- Prikazati "Connecting..." state dok se iframe učitava
- Dodati connection status indicator (connected/disconnected)
- Handle-ovati iframe load events

**Code:**
```javascript
const [iframeLoaded, setIframeLoaded] = useState(false)

// Loading state
if (isLoading) {
  return <LoadingState message="Loading VNC console..." />
}

// Iframe loading
<iframe
  src={vncInfo.vnc_url}
  onLoad={() => setIframeLoaded(true)}
  className="vm-console-iframe"
  title="VM Console"
  allowFullScreen
/>

{!iframeLoaded && (
  <div className="iframe-loading-overlay">
    <LoadingState message="Connecting to VM console..." />
  </div>
)}
```

**Validacija:**
- ✅ Loading state je prikazan dok se fetch-uje VNC info
- ✅ "Connecting..." state je prikazan dok se iframe učitava
- ✅ Connection status indicator prikazuje trenutni status

---

### Task 10: Documentation (`vm-vnc-documentation`)

**Fajl:** `docs/frontend/VM_VNC_CONSOLE.md`

**Akcije:**
- Dokumentovati VNC konzolu implementaciju
- Objasniti kako se koristi
- Objasniti error handling
- Objasniti fullscreen support
- Objasniti routing

**Content:**
- Overview
- Usage
- API Integration
- Error Handling
- Fullscreen Support
- Troubleshooting

**Validacija:**
- ✅ Dokumentacija je kompletna
- ✅ Objašnjava sve feature-e
- ✅ Uključuje troubleshooting sekciju

---

## 🔄 Integration Points

### Backend API
- `GET /api/vms/{vm_id}/vnc` - VNC URL i connection details
- `GET /api/vms/{vm_id}` - VM info (status check)

### Frontend Services
- `vmsAPI.getVNC(vmId)` - Fetch VNC info
- `vmsAPI.get(vmId)` - Fetch VM info

### Frontend Pages
- `Machines.jsx` - Context menu integration
- `VMs.jsx` - VM card integration
- `VMConsole.jsx` - VNC console page

### Routing
- `/machines/control-vm/:vm_id` - Main route
- `/vms/control/:vm_id` - Alternative route

---

## ✅ Checklist

- [ ] Task 1: API Service Update
- [ ] Task 2: VNC Console Page Component
- [ ] Task 3: VNC Console CSS
- [ ] Task 4: Routing Integration
- [ ] Task 5: Machines Page Integration
- [ ] Task 6: VMs Page Integration
- [ ] Task 7: Error Handling & Edge Cases
- [ ] Task 8: Fullscreen Support
- [ ] Task 9: Loading & Connection States
- [ ] Task 10: Documentation

---

## 🎨 UI/UX Considerations

### Design
- **Dark Theme** - Match existing ggNET2 theme
- **Toolbar** - Fixed top, minimal design
- **Console** - Full-screen iframe, seamless integration
- **Status Indicators** - Clear visual feedback

### User Experience
- **Quick Access** - One-click access from Machines/VMs table
- **Error Messages** - Clear, actionable error messages
- **Loading States** - Smooth loading transitions
- **Fullscreen** - Easy fullscreen toggle

### Accessibility
- **Keyboard Navigation** - Support for keyboard shortcuts
- **Screen Readers** - Proper ARIA labels
- **Focus Management** - Proper focus handling

---

## 🐛 Edge Cases & Error Handling

### VM Not Running
- Prikazati error message sa "Start VM" button-om
- Auto-redirect kada se VM start-uje

### VNC Not Available
- Prikazati error message sa razlogom
- Offer retry option

### Network Errors
- Prikazati retry button
- Auto-retry sa exponential backoff

### VM Deleted
- Prikazati 404 error
- Offer redirect to Machines/VMs page

### Session Timeout
- Handle authentication errors
- Redirect to login page

---

## 📚 Reference

- **Backend API:** `app/backend/api/vms.py` - `GET /api/vms/{vm_id}/vnc`
- **VM Manager:** `app/backend/vms/vm_manager.py` - `get_vnc_url()`
- **noVNC Integration:** `docs/NOVNC_INTEGRATION.md`
- **React Router:** https://reactrouter.com/
- **noVNC:** https://github.com/novnc/noVNC

---

**Plan Complete!** ✅

