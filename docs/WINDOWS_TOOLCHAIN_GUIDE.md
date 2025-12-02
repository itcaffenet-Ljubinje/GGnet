# 🪟 Windows Toolchain Guide for GGnet

Complete guide for automating Windows configuration in GGnet diskless system.

---

## 📋 **Table of Contents**

1. [Overview](#overview)
2. [Registry Scripts](#registry-scripts)
3. [Deployment Methods](#deployment-methods)
4. [Template Variables](#template-variables)
5. [Integration with Boot Process](#integration-with-boot-process)
6. [Testing](#testing)
7. [Best Practices](#best-practices)

---

## 🎯 **Overview**

The Windows Toolchain automates Windows configuration for diskless clients using registry scripts.

### **What It Does:**

- ✅ Disables UAC (unattended operation)
- ✅ Disables Windows Firewall (trusted network)
- ✅ Enables auto-login (no password prompt)
- ✅ Renames computer (matches GGnet inventory)
- ✅ Optimizes for diskless (disables updates, hibernation, etc.)
- ✅ Injects environment variables (GGNET_SERVER, GGNET_MACHINE_ID)
- ✅ Enables Remote Desktop
- ✅ Performance tweaks (gaming-optimized)
- ✅ Disables telemetry (privacy + bandwidth)

### **Why This Matters:**

**Without automation:**
- ⏱️ 30+ minutes manual configuration per machine
- 🐛 Human errors and inconsistencies
- 🔄 Configuration lost on every restart (diskless!)
- 📋 Complex checklists for technicians

**With GGnet Toolchain:**
- ⚡ **Fully automatic** - zero manual steps
- 🎯 **Consistent** - same config every time
- 🔄 **Persistent** - applied on every boot
- 📊 **Trackable** - logged via GGnet API

---

## 📝 **Registry Scripts**

All scripts located in `infra/windows-scripts/`:

### **01-disable-uac.reg** 🔴 CRITICAL

**Purpose:** Disable User Account Control prompts

```reg
[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System]
"EnableLUA"=dword:00000000
```

**Why:** Allows software installation and system changes without prompts

**Restart Required:** ✅ Yes

---

### **02-disable-firewall.reg** 🟡 NETWORK-DEPENDENT

**Purpose:** Disable Windows Firewall

**⚠️ WARNING:** Only use in isolated/trusted networks!

**Alternative:** Configure specific firewall rules instead

**Restart Required:** ❌ No

---

### **03-enable-autologon.reg.template** 🔴 CRITICAL

**Purpose:** Automatic user login on boot

**Template Variables:**
- `{USERNAME}` - Windows username
- `{PASSWORD}` - User password (plaintext!)
- `{DOMAIN}` - Domain or `.` for local

**Example:**
```reg
"DefaultUserName"="GGUser"
"DefaultPassword"="ggnet123"
"DefaultDomainName"="."
```

**Security:** Password stored in plaintext - use only in controlled environment!

**Restart Required:** ✅ Yes

---

### **04-rename-computer.reg.template** 🟡 OPTIONAL

**Purpose:** Set computer name to match GGnet inventory

**Template Variables:**
- `{COMPUTER_NAME}` - New computer name

**Example:**
```reg
"ComputerName"="GGNET-PC-042"
```

**Restart Required:** ✅ Yes

---

### **05-ggnet-client-install.reg** 🔴 CRITICAL

**Purpose:** Optimize Windows for diskless operation

**Key Changes:**
```reg
# Disable Windows Update (CRITICAL - would break diskless!)
"NoAutoUpdate"=dword:00000001

# Disable System Restore (no persistent storage)
"DisableSR"=dword:00000001

# Disable Hibernation
"HibernateEnabled"=dword:00000000

# Disable Page File (or use iSCSI/RAM)
"PagingFiles"=""

# Disable Crash Dumps (save bandwidth)
"CrashDumpEnabled"=dword:00000000
```

**Why Critical:**
- Windows Update would modify system (lost on restart!)
- Page file wastes iSCSI bandwidth
- System Restore doesn't work with diskless
- Crash dumps fill up iSCSI target

**Restart Required:** ✅ Yes

---

### **06-inject-environment-vars.reg.template** 🟢 OPTIONAL

**Purpose:** Set environment variables for GGnet client software

**Template Variables:**
- `{GGNET_SERVER}` - Server IP (e.g., `192.168.1.10`)
- `{MACHINE_ID}` - Machine ID from database
- `{MACHINE_NAME}` - Machine name
- `{SESSION_ID}` - Current session UUID
- `{BOOT_TIME}` - ISO timestamp

**Example:**
```reg
"GGNET_SERVER"="192.168.1.10"
"GGNET_MACHINE_ID"="42"
"GGNET_SESSION_ID"="uuid-12345678"
```

**Usage:**
```batch
REM In batch scripts:
echo Server: %GGNET_SERVER%

REM In PowerShell:
$server = $env:GGNET_SERVER
```

**Restart Required:** ❌ No

---

### **07-enable-rdp.reg** 🟢 OPTIONAL

**Purpose:** Enable Remote Desktop for remote administration

**Restart Required:** ❌ No

---

### **08-optimize-performance.reg** 🟡 RECOMMENDED

**Purpose:** Performance optimizations for gaming/diskless

**Changes:**
- Disable visual effects
- Disable Windows Search indexing
- Disable Superfetch/Prefetch
- Enable Game Mode
- High Performance power plan

**Restart Required:** ✅ Yes

---

### **09-disable-telemetry.reg** 🟢 PRIVACY

**Purpose:** Disable Windows telemetry and tracking

**Changes:**
- Disable telemetry
- Disable Cortana
- Disable Activity Feed
- Disable Advertising ID

**Restart Required:** ❌ No

---

## 🚀 **Deployment Methods**

### **Method 1: Manual Application (Testing)**

```batch
REM Run as Administrator
cd C:\path\to\ggnet\infra\windows-scripts
apply-all.bat
```

**Pros:** Simple, good for testing  
**Cons:** Requires manual intervention

---

### **Method 2: Startup Script (Post-Boot)**

#### **Option A: RunOnce Registry**

```powershell
# Add to system image before deployment
$runOnce = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"
Set-ItemProperty -Path $runOnce -Name "GGnetConfig" -Value "C:\ggnet\apply-all.bat"
```

**Pros:** Runs once, then removes itself  
**Cons:** Requires pre-configuration of image

---

#### **Option B: Startup Folder Script**

```powershell
# Create startup script
$startupPath = "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp"
$scriptPath = "$startupPath\ggnet-config.bat"

@"
@echo off
if not exist C:\ggnet-configured (
    REM Download registry pack from server
    powershell -Command "Invoke-WebRequest -Uri 'http://${env:GGNET_SERVER}:8000/api/machines/%COMPUTERNAME%/registry-pack' -OutFile C:\temp\registry.zip"
    
    REM Extract and apply
    powershell -Command "Expand-Archive C:\temp\registry.zip C:\temp\registry -Force"
    for %%f in (C:\temp\registry\*.reg) do reg import "%%f"
    
    REM Mark as configured
    echo Configured > C:\ggnet-configured
    
    REM Restart
    shutdown /r /t 60 /c "GGnet: Configuration applied. Restarting..."
)
"@ | Out-File $scriptPath -Encoding ASCII
```

**Pros:** Automatic on first boot  
**Cons:** Requires network connectivity

---

### **Method 3: Pre-Boot Injection (Best)**

#### **Mount and Inject (Before Boot):**

```bash
#!/bin/bash
# On GGnet server, before client boots

MACHINE_ID=42
IMAGE_PATH="/opt/ggnet/images/machine-${MACHINE_ID}.vhdx"
MOUNT_POINT="/mnt/windows-${MACHINE_ID}"

# Mount image
sudo mkdir -p "$MOUNT_POINT"
sudo guestmount -a "$IMAGE_PATH" -m /dev/sda2 "$MOUNT_POINT"

# Generate registry files from templates
python3 backend/scripts/generate_registry.py \
    --machine-id "$MACHINE_ID" \
    --output "$MOUNT_POINT/Windows/Setup/Scripts/"

# Create auto-apply script
cat > "$MOUNT_POINT/Windows/Setup/Scripts/setup.bat" << 'EOF'
@echo off
cd %~dp0
for %%f in (*.reg) do reg import "%%f"
del %~f0
EOF

# Add to RunOnce
# (requires registry editing - use hivex or regedit)

# Unmount
sudo guestunmount "$MOUNT_POINT"
```

**Pros:** 
- ✅ Applied before first boot
- ✅ No network dependency
- ✅ Fastest boot time

**Cons:**
- ⚠️ Requires image mounting
- ⚠️ More complex automation

---

### **Method 4: Backend API Generation (Recommended)**

#### **Backend Endpoint:**

```python
# backend/app/routes/registry.py

from pathlib import Path
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import zipfile
import io

router = APIRouter(prefix="/api/machines", tags=["registry"])

@router.get("/{machine_id}/registry-pack")
async def get_registry_pack(
    machine_id: int,
    current_user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db)
):
    """Generate and download registry pack for machine"""
    
    machine = await get_machine_or_404(db, machine_id)
    session = machine.active_session
    
    # Generate registry files
    files = {}
    
    # Static files (no templates)
    static_files = [
        "01-disable-uac.reg",
        "02-disable-firewall.reg",
        "05-ggnet-client-install.reg",
        "07-enable-rdp.reg",
        "08-optimize-performance.reg",
        "09-disable-telemetry.reg",
    ]
    
    for filename in static_files:
        path = Path(f"infra/windows-scripts/{filename}")
        files[filename] = path.read_text()
    
    # Generate from templates
    files["03-enable-autologon.reg"] = generate_autologon_reg(
        username="GGUser",
        password="ggnet123",  # TODO: Get from config
        domain="."
    )
    
    files["04-rename-computer.reg"] = generate_computer_rename_reg(
        computer_name=machine.hostname or f"GGNET-{machine_id:03d}"
    )
    
    files["06-inject-environment-vars.reg"] = generate_environment_vars_reg(
        machine_id=machine.id,
        machine_name=machine.name,
        server_ip=get_server_ip(),
        session_id=str(session.id) if session else ""
    )
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in files.items():
            zip_file.writestr(filename, content)
        
        # Add apply script
        zip_file.writestr("apply-all.bat", Path("infra/windows-scripts/apply-all.bat").read_text())
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=registry-{machine_id}.zip"
        }
    )
```

**Frontend Integration:**

```typescript
// frontend/src/components/MachineActions.tsx

const downloadRegistryPack = async (machineId: number) => {
  const response = await api.get(
    `/api/machines/${machineId}/registry-pack`,
    { responseType: 'blob' }
  );
  
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `registry-${machineId}.zip`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};
```

**Pros:**
- ✅ Fully automated
- ✅ Per-machine customization
- ✅ Auditable (API logs)
- ✅ No manual template editing

---

## 🔧 **Template Variables**

### **Available Variables:**

| Variable | Type | Example | Used In |
|----------|------|---------|---------|
| `{USERNAME}` | string | `GGUser` | 03-enable-autologon |
| `{PASSWORD}` | string | `ggnet123` | 03-enable-autologon |
| `{DOMAIN}` | string | `.` or `WORKGROUP` | 03-enable-autologon |
| `{COMPUTER_NAME}` | string | `GGNET-PC-042` | 04-rename-computer |
| `{GGNET_SERVER}` | IP address | `192.168.1.10` | 06-inject-environment-vars |
| `{MACHINE_ID}` | integer | `42` | 06-inject-environment-vars |
| `{MACHINE_NAME}` | string | `Gaming-PC-01` | 06-inject-environment-vars |
| `{SESSION_ID}` | UUID | `uuid-...` | 06-inject-environment-vars |
| `{BOOT_TIME}` | ISO8601 | `2025-10-08T01:00:00Z` | 06-inject-environment-vars |

### **Replacement Example:**

```python
def generate_autologon_reg(username: str, password: str, domain: str = "."):
    """Generate auto-logon registry file"""
    template = Path("infra/windows-scripts/03-enable-autologon.reg.template").read_text()
    
    content = template.replace("{USERNAME}", username)
    content = content.replace("{PASSWORD}", password)
    content = content.replace("{DOMAIN}", domain)
    
    return content
```

---

## 🔗 **Integration with Boot Process**

### **Complete Automation Flow:**

```
┌─────────────────────────────────────────────────┐
│ 1. Client boots via iPXE + iSCSI                │
│    ↓                                            │
│ 2. Windows starts                               │
│    ↓                                            │
│ 3. Startup script runs                          │
│    - Checks if configured (C:\ggnet-configured) │
│    ↓                                            │
│ 4. If not configured:                           │
│    - Reads GGNET_SERVER env var                 │
│    - Downloads registry pack via API            │
│    - http://SERVER:8000/api/machines/ID/registry│
│    ↓                                            │
│ 5. Extracts ZIP file                            │
│    ↓                                            │
│ 6. Applies all .reg files                       │
│    - UAC disabled                               │
│    - Firewall disabled                          │
│    - Auto-login enabled                         │
│    - etc.                                       │
│    ↓                                            │
│ 7. Creates C:\ggnet-configured marker           │
│    ↓                                            │
│ 8. Restarts computer                            │
│    ↓                                            │
│ 9. Second boot: Auto-login works                │
│    ↓                                            │
│10. ✅ Fully configured Windows session!         │
└─────────────────────────────────────────────────┘
```

---

## 🧪 **Testing**

### **Test 1: Manual Application**

```powershell
# On test VM
cd C:\path\to\infra\windows-scripts
.\apply-all.bat

# Wait for restart

# Verify:
# - UAC disabled (no prompts when running as admin)
# - Auto-login works
# - Environment variables set
```

### **Test 2: API Generation**

```bash
# Test backend endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/machines/1/registry-pack \
  -o registry-pack.zip

# Extract and inspect
unzip registry-pack.zip
cat 06-inject-environment-vars.reg
```

### **Test 3: Full Boot Process**

```
1. Create test Windows 11 image
2. Boot via GGnet iPXE/iSCSI
3. Observe automatic configuration
4. Verify all settings applied
5. Test second boot (should skip config)
```

---

## ✅ **Best Practices**

### **Security:**

1. **Password Storage:**
   ```python
   # Don't hardcode passwords!
   password = get_config("default_user_password")
   
   # Or use Windows Hello/PIN
   # Or null password + network-level security
   ```

2. **Firewall:**
   ```reg
   # Instead of disabling completely, configure rules:
   netsh advfirewall firewall add rule name="GGnet API" dir=in action=allow protocol=TCP localport=8000
   ```

3. **Audit Trail:**
   ```python
   # Log registry pack downloads
   await log_user_activity(
       action=AuditAction.DOWNLOAD,
       message=f"Downloaded registry pack for machine {machine_id}",
       resource_type="machines",
       resource_id=machine_id
   )
   ```

### **Maintenance:**

1. **Version Control:**
   - Keep registry scripts in git
   - Tag versions for rollback
   - Document all changes

2. **Testing:**
   - Test on VM before production
   - Verify Windows 10 and 11 compatibility
   - Test all template combinations

3. **Updates:**
   - Review Windows updates for registry changes
   - Update scripts for new Windows versions
   - Monitor for deprecated registry keys

---

## 📚 **References**

- Windows Registry: https://docs.microsoft.com/en-us/windows/win32/sysinfo/registry
- Auto-Logon: https://docs.microsoft.com/en-us/troubleshoot/windows-server/user-profiles-and-logon/turn-on-automatic-logon
- ggRock Toolchain Analysis: `GGROCK_COMPARISON.md`

---

**Status:** ✅ **Windows Toolchain implemented and documented!**  
**Next:** Integrate with backend API and test full automation.

