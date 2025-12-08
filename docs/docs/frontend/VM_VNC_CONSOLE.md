# VM VNC Console Frontend Implementation

**Datum kreiranja:** 2025-01-26  
**Status:** ✅ Implementirano

---

## 📊 Pregled

VNC konzola stranica za virtualne mašine, omogućavajući pristup VM konzoli direktno iz web browser-a kroz noVNC.

**URL Format:** 
- `/machines/control-vm/:vm_id` - Main route (za Machines page)
- `/vms/control/:vm_id` - Alternative route (za VMs page)

**Primer:** `https://192.168.0.180/machines/control-vm/1c0bc17a-68a6-4d45-872b-aeebadea7c3b`

---

## ✅ Implementirano

### 1. API Service (`vmsAPI.js`)

**Metoda:** `getVNC(id)`

```javascript
// Get VNC URL and connection details
getVNC: (id) => {
  return api.get(`/vms/${id}/vnc`)
}
```

**Response:**
```json
{
  "vnc_url": "https://localhost/vnc/console?token=abc123",
  "vnc_token": "abc123",
  "vnc_port": 5900,
  "vnc_host": "127.0.0.1",
  "websocket_url": "ws://127.0.0.1:6080/websockify?token=abc123"
}
```

---

### 2. VNC Console Page (`VMConsole.jsx`)

**Komponenta:** `VMConsole`

**Features:**
- ✅ Fetch VM info za status check
- ✅ Fetch VNC info kada je VM running
- ✅ noVNC iframe embed
- ✅ Toolbar sa VM name, status, VNC port
- ✅ Fullscreen toggle button
- ✅ Refresh button (reconnect)
- ✅ Close button (navigate back)
- ✅ Auto-refresh VM status (polling svakih 5 sekundi)
- ✅ Auto-refetch VNC info (polling svakih 30 sekundi)
- ✅ Keyboard shortcuts (F11 za fullscreen, Escape za exit)

**State Management:**
- `useParams()` - Get `vm_id` iz URL-a
- `useQuery()` - Fetch VM info i VNC info
- `useState()` - Fullscreen state, iframe loaded state
- `useEffect()` - Fullscreen event listeners, polling, keyboard shortcuts

**Error Handling:**
- VM not found (404)
- VM not running (prikazuje "Start VM" button)
- VNC not available (prikazuje error message sa retry)
- Network errors (retry button)

---

### 3. CSS Styling (`VMConsole.css`)

**Features:**
- ✅ Dark theme (match existing ggNET2 theme)
- ✅ Fixed toolbar na vrhu
- ✅ Full-screen console container
- ✅ Seamless iframe (no borders)
- ✅ Loading overlay za iframe
- ✅ Responsive design (mobile/tablet)
- ✅ Fullscreen styles

**Key Classes:**
- `.vm-console-page` - Main container (flex column, 100vh)
- `.vm-console-toolbar` - Fixed toolbar (flex, space-between)
- `.vm-console-container` - Console container (flex: 1, overflow hidden)
- `.vm-console-iframe` - noVNC iframe (100% width/height, no borders)
- `.iframe-loading-overlay` - Loading overlay (absolute, centered)

---

### 4. Routing (`App.jsx`)

**Routes:**
```javascript
<Route path="machines/control-vm/:vm_id" element={<VMConsole />} />
<Route path="vms/control/:vm_id" element={<VMConsole />} />
```

**Usage:**
- Navigate sa `navigate('/machines/control-vm/{vm_id}')` ili `navigate('/vms/control/{vm_id}')`
- `vm_id` može biti UUID ili integer ID

---

### 5. Machines Page Integration (`Machines.jsx`)

**Features:**
- ✅ "Control the VM" akcija u context menu
- ✅ Prikazuje se samo za VMs koji su running
- ✅ Proverava `machine.vm_id` (da li je VM)
- ✅ Proverava `machine.status === 'running'` ili `machine.state === 'running'`
- ✅ Navigacija na `/machines/control-vm/{vm_id}`

**Code:**
```javascript
const handleControlVM = (machine) => {
  if (!machine.vm_id) {
    addNotification({
      type: 'error',
      message: 'This machine is not a virtual machine',
    })
    return
  }

  if (machine.status !== 'running' && machine.state !== 'running') {
    addNotification({
      type: 'error',
      message: 'VM must be running to access console',
    })
    return
  }

  navigate(`/machines/control-vm/${machine.vm_id}`)
}
```

**Context Menu:**
```jsx
{machine.vm_id && (machine.status === 'running' || machine.state === 'running') && (
  <button
    type="button"
    role="menuitem"
    onClick={() => handleMenuAction('controlVM', machine)}
  >
    Control the VM
  </button>
)}
```

---

### 6. VMs Page Integration (`VMs.jsx`)

**Features:**
- ✅ "Control" button u VM card
- ✅ Prikazuje se samo za running VMs
- ✅ Navigacija na `/vms/control/{vm_id}`

**Code:**
```javascript
const handleControlVM = (vm) => {
  if (vm.status !== 'running') {
    addNotification({
      type: 'error',
      message: 'VM must be running to access console',
    })
    return
  }

  const vmId = vm.vm_id || vm.id
  navigate(`/vms/control/${vmId}`)
}
```

**UI:**
```jsx
{vm.status === 'running' && (
  <button
    className="btn-primary"
    onClick={() => handleControlVM(vm)}
  >
    Control
  </button>
)}
```

---

## 🎨 UI/UX Features

### Toolbar
- **Left:** VM name, status badge, VNC port info
- **Right:** Fullscreen toggle, Refresh, Close

### Console
- **Full-screen iframe** - Seamless noVNC embed
- **Loading overlay** - "Connecting to VM console..." dok se iframe učitava
- **Auto-refresh** - Polling VM status i VNC info

### Error States
- **VM not found** - Error message sa "Go to VMs" button
- **VM not running** - Error message sa "Start VM" button
- **VNC not available** - Error message sa retry button

### Keyboard Shortcuts
- **F11** - Toggle fullscreen
- **Escape** - Exit fullscreen

---

## 🔄 Auto-Refresh & Polling

### VM Status Polling
- Polling svakih **5 sekundi** dok je console otvoren
- Automatski se stop-uje ako se VM stop-uje

### VNC Info Polling
- Polling svakih **30 sekundi** dok je VM running
- Automatski se stop-uje ako VM nije running

---

## 🐛 Error Handling

### Edge Cases

1. **VM Not Found (404)**
   - Prikazuje error message
   - "Go to VMs" button za navigaciju

2. **VM Not Running**
   - Prikazuje error message
   - "Start VM" button za start VM-a
   - Auto-refetch VNC info kada se VM start-uje

3. **VNC Not Available**
   - Prikazuje error message sa razlogom
   - Retry button za ponovni pokušaj

4. **Network Errors**
   - Prikazuje error message
   - Retry button sa refetch

5. **VM Deleted**
   - Auto-redirect na Machines/VMs page (404 error)

6. **Session Timeout**
   - Handle authentication errors
   - Redirect na login page (handled by API interceptor)

---

## 📚 Usage

### From Machines Page

1. Klikni na "⋮" (three dots) u machine row-u
2. Ako je VM i running, klikni "Control the VM"
3. Console se otvara u novoj stranici

### From VMs Page

1. Klikni "Control" button u VM card-u (samo za running VMs)
2. Console se otvara u novoj stranici

### In Console

1. **Fullscreen** - Klikni "Fullscreen" button ili pritisni F11
2. **Refresh** - Klikni "Refresh" button za reconnect
3. **Close** - Klikni "Close" button ili idi nazad u browser-u

---

## 🔧 Troubleshooting

### Console se ne učitava

**Problem:** Iframe se ne učitava ili prikazuje error

**Rešenje:**
1. Proveri da li je VM running:
   ```bash
   curl https://localhost/api/vms/{vm_id}
   ```

2. Proveri da li je VNC dostupan:
   ```bash
   curl https://localhost/api/vms/{vm_id}/vnc
   ```

3. Proveri browser console za errors

4. Proveri da li je websockify service running:
   ```bash
   sudo systemctl status ggnet2-novnc
   ```

### VM se stop-uje tokom sesije

**Problem:** Console se gubi kada se VM stop-uje

**Rešenje:**
- Auto-refresh će detektovati da je VM stop-ovan
- Prikazuje se error message sa "Start VM" button-om
- Klikni "Start VM" da restart-uješ VM

### Fullscreen ne radi

**Problem:** Fullscreen button ne radi

**Rešenje:**
- Proveri browser support za Fullscreen API
- Pokušaj sa F11 keyboard shortcut
- Proveri browser console za errors

---

## 📚 Reference

- **Backend API:** `app/backend/api/vms.py` - `GET /api/vms/{vm_id}/vnc`
- **VM Manager:** `app/backend/vms/vm_manager.py` - `get_vnc_url()`
- **noVNC Integration:** `docs/NOVNC_INTEGRATION.md`
- **Frontend Plan:** `docs/frontend/VM_VNC_CONSOLE_PLAN.md`
- **React Router:** https://reactrouter.com/
- **noVNC:** https://github.com/novnc/noVNC

---

## ✅ Checklist

- [x] API Service Update (`vmsAPI.getVNC()`)
- [x] VNC Console Page Component (`VMConsole.jsx`)
- [x] CSS Styling (`VMConsole.css`)
- [x] Routing Integration (`App.jsx`)
- [x] Machines Page Integration (context menu)
- [x] VMs Page Integration (button)
- [x] Error Handling (all edge cases)
- [x] Fullscreen Support (Fullscreen API + keyboard shortcuts)
- [x] Loading States (loading spinners, connection status)
- [x] Documentation (`docs/frontend/VM_VNC_CONSOLE.md`)

---

**VNC Console Implementation Complete!** ✅

