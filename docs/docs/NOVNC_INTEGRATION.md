# noVNC Integration for Virtual Machines

**Datum kreiranja:** 2025-01-26  
**Status:** 📋 noVNC Integration Documentation

---

## 📊 Pregled

ggNET2 koristi **noVNC** za web-based VNC pristup virtualnim mašinama. noVNC omogućava pristup VM konzoli direktno iz web browser-a bez potrebe za VNC klijentom.

---

## ✅ Postojeća Infrastruktura

### 1. Systemd Service

**Service:** `ggnet2-novnc.service`

**Konfiguracija:**
```ini
[Unit]
Description=ggnet2 VNC client for VMs
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/websockify --web=/usr/share/novnc \
  --token-plugin TokenFile \
  --token-source /etc/ggnet2/websockify/target.config.d/ \
  127.0.0.1:6080
Restart=always
RestartSec=2
SyslogIdentifier=ggnet2-novnc
```

**Setup:**
```bash
# Service se automatski kreira tokom instalacije
sudo bash scripts/setup_systemd.sh

# Start service
sudo systemctl start ggnet2-novnc
sudo systemctl enable ggnet2-novnc
```

---

### 2. Nginx Proxy Configuration

**Location Blocks:**
```nginx
# VNC console access (noVNC)
location = /vnc/console {
    proxy_pass http://vnc_proxy/vnc.html;
}

location /vnc/ {
    proxy_pass http://vnc_proxy/;
}

# WebSocket proxy for VNC
location /websockify {
    proxy_http_version 1.1;
    proxy_pass http://vnc_proxy/;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    
    # VNC connection timeout (from version 2289)
    proxy_read_timeout 61s;
    
    # Disable cache
    proxy_buffering off;
}
```

**Upstream:**
```nginx
upstream vnc_proxy {
    server 127.0.0.1:6080;
}
```

---

### 3. Backend API

**Endpoint:** `GET /api/vms/{vm_id}/vnc`

**Response:**
```json
{
  "vnc_url": "https://localhost/vnc/console?token=abc123def456",
  "vnc_token": "abc123def456",
  "vnc_port": 5900,
  "vnc_host": "127.0.0.1",
  "websocket_url": "ws://127.0.0.1:6080/websockify?token=abc123def456"
}
```

**Usage:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://localhost/api/vms/1/vnc
```

---

### 4. VM Manager Methods

**Metode u `VMManager` klasi:**

- `get_vnc_url(db, vm_id)` - Get VNC URL i connection details
- `_setup_vnc_token(db, vm, domain)` - Setup VNC token kada se VM start-uje
- `_cleanup_vnc_token(vm)` - Cleanup VNC token kada se VM stop-uje
- `_get_vnc_port(domain)` - Get VNC port iz libvirt domain XML

---

## 🔧 Kako Radi

### 1. VM Start Flow

```
1. User start-uje VM
2. VM Manager start-uje libvirt domain
3. Libvirt automatski dodeljuje VNC port (5900+)
4. VM Manager čita VNC port iz domain XML
5. VM Manager generiše token
6. VM Manager kreira token file u /etc/ggnet2/websockify/target.config.d/{vm_id}
7. Token file sadrži: "127.0.0.1:{vnc_port}"
8. VM Manager čuva vnc_port i vnc_token u database
```

### 2. VNC Access Flow

```
1. User poziva GET /api/vms/{vm_id}/vnc
2. Backend proverava da li je VM running
3. Backend vraća VNC URL sa token-om
4. Frontend otvara VNC URL u iframe ili novom prozoru
5. noVNC se povezuje na websockify sa token-om
6. websockify čita token file i prosleđuje konekciju na VNC server
```

### 3. Token File Format

**File:** `/etc/ggnet2/websockify/target.config.d/{vm_id}`

**Content:**
```
127.0.0.1:5900
```

**Format:** `{vnc_host}:{vnc_port}`

---

## 📋 Requirements

### System Packages

```bash
# websockify (WebSocket to VNC proxy)
sudo apt-get install -y websockify

# novnc (noVNC static files)
sudo apt-get install -y novnc
```

**Alternative (Python):**
```bash
pip install websockify
```

### Directory Structure

```
/etc/ggnet2/
└── websockify/
    └── target.config.d/    # Token files directory
        ├── 1                # VM ID 1 token file
        ├── 2                # VM ID 2 token file
        └── ...
```

---

## 🚀 Usage

### Backend API

```python
from app.backend.vms.vm_manager import VMManager

vm_manager = VMManager()
vnc_info = vm_manager.get_vnc_url(db, vm_id=1)

print(vnc_info["vnc_url"])
# Output: https://localhost/vnc/console?token=abc123def456
```

### Frontend Integration

**React Component Example:**
```jsx
import { useQuery } from '@tanstack/react-query';
import { vmsAPI } from '../services/vmsAPI';

function VMC console({ vmId }) {
  const { data: vncInfo } = useQuery({
    queryKey: ['vm-vnc', vmId],
    queryFn: () => vmsAPI.getVNC(vmId),
  });

  if (!vncInfo) return <div>Loading...</div>;

  return (
    <iframe
      src={vncInfo.vnc_url}
      style={{ width: '100%', height: '600px', border: 'none' }}
      title="VM Console"
    />
  );
}
```

---

## 🔒 Security

### Token-Based Access

- **Token Generation:** Koristi `secrets.token_urlsafe(16)` za siguran token
- **Token Storage:** Token se čuva u database i token file-u
- **Token Lifetime:** Token je validan dok je VM running
- **Token Cleanup:** Token se automatski briše kada se VM stop-uje

### Network Security

- **VNC Server:** Sluša samo na `127.0.0.1` (localhost)
- **websockify:** Sluša samo na `127.0.0.1:6080` (localhost)
- **Nginx Proxy:** Prosleđuje konekcije sa HTTPS enkripcijom
- **Token Files:** Permissions `644` (read owner/group, read others)

---

## 🐛 Troubleshooting

### VNC Not Available

**Problem:** `GET /api/vms/{vm_id}/vnc` vraća error

**Rešenje:**
1. Proverite da li je VM running:
   ```bash
   curl https://localhost/api/vms/1
   ```

2. Proverite da li postoji VNC port:
   ```bash
   sudo virsh dominfo vm-001
   ```

3. Proverite token file:
   ```bash
   cat /etc/ggnet2/websockify/target.config.d/1
   ```

### websockify Not Running

**Problem:** VNC konekcija pada

**Rešenje:**
```bash
# Check service status
sudo systemctl status ggnet2-novnc

# Check logs
sudo journalctl -u ggnet2-novnc -f

# Restart service
sudo systemctl restart ggnet2-novnc
```

### Token File Missing

**Problem:** Token file ne postoji

**Rešenje:**
1. Proverite da li je VM running
2. Proverite permissions:
   ```bash
   ls -la /etc/ggnet2/websockify/target.config.d/
   ```

3. Restart VM da se regeneriše token:
   ```bash
   curl -X POST https://localhost/api/vms/1/stop
   curl -X POST https://localhost/api/vms/1/start
   ```

---

## 📚 Reference

- **Backend API:** `app/backend/api/vms.py`
- **VM Manager:** `app/backend/vms/vm_manager.py`
- **Systemd Setup:** `scripts/setup_systemd.sh`
- **Nginx Setup:** `scripts/setup_nginx.sh`
- **noVNC Documentation:** https://github.com/novnc/noVNC
- **websockify Documentation:** https://github.com/novnc/websockify

---

## ✅ Checklist

- [ ] websockify instaliran
- [ ] novnc instaliran
- [ ] `ggnet2-novnc.service` kreiran i enabled
- [ ] Nginx VNC proxy konfigurisan
- [ ] Token directory kreiran (`/etc/ggnet2/websockify/target.config.d/`)
- [ ] Backend API endpoint `/api/vms/{vm_id}/vnc` radi
- [ ] VM Manager metode implementirane
- [ ] Token se automatski kreira kada se VM start-uje
- [ ] Token se automatski briše kada se VM stop-uje

---

**noVNC Integration Complete!** ✅

