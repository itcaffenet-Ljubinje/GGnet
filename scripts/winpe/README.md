# WinPE Boot Environment for GGnet

Windows Preinstallation Environment for fresh Windows deployment.

---

## 🎯 **Purpose**

WinPE allows GGnet to:
- Deploy fresh Windows installations to bare metal
- Partition disks automatically
- Inject drivers during installation
- Run pre-installation scripts
- Troubleshoot boot issues

---

## 📋 **Prerequisites**

### **Windows ADK (Assessment and Deployment Kit):**

**Download from Microsoft:**
- Windows ADK: https://go.microsoft.com/fwlink/?linkid=2243390
- Windows PE add-on: https://go.microsoft.com/fwlink/?linkid=2243391

**Install on Windows machine:**
```powershell
# Download and install ADK
Start-Process "adksetup.exe" -ArgumentList "/quiet /features OptionId.DeploymentTools" -Wait

# Download and install WinPE add-on
Start-Process "adkwinpesetup.exe" -ArgumentList "/quiet /features OptionId.WindowsPreinstallationEnvironment" -Wait
```

---

## 🛠️ **Build WinPE Image**

### **Step 1: Create WinPE Working Directory**

```powershell
# Run as Administrator
# Open "Deployment and Imaging Tools Environment"

# Create working directory
copype amd64 C:\WinPE_amd64

# Mount WinPE image
Dism /Mount-Image /ImageFile:"C:\WinPE_amd64\media\sources\boot.wim" /Index:1 /MountDir:"C:\WinPE_amd64\mount"
```

---

### **Step 2: Customize WinPE**

#### **Add Network Drivers:**
```powershell
# Add network drivers for iSCSI boot
Dism /Image:"C:\WinPE_amd64\mount" /Add-Driver /Driver:"C:\Drivers\Network" /Recurse
```

#### **Add iSCSI Support:**
```powershell
# Add iSCSI initiator
Dism /Image:"C:\WinPE_amd64\mount" /Add-Package /PackagePath:"C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Windows Preinstallation Environment\amd64\WinPE_OCs\WinPE-Scripting.cab"

Dism /Image:"C:\WinPE_amd64\mount" /Add-Package /PackagePath:"C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Windows Preinstallation Environment\amd64\WinPE_OCs\WinPE-WMI.cab"

Dism /Image:"C:\WinPE_amd64\mount" /Add-Package /PackagePath:"C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Windows Preinstallation Environment\amd64\WinPE_OCs\WinPE-NetFx.cab"

Dism /Image:"C:\WinPE_amd64\mount" /Add-Package /PackagePath:"C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Windows Preinstallation Environment\amd64\WinPE_OCs\WinPE-PowerShell.cab"
```

#### **Add GGnet Tools:**
```powershell
# Copy GGnet deployment scripts
Copy-Item -Path "deploy-windows.ps1" -Destination "C:\WinPE_amd64\mount\Windows\System32\"
Copy-Item -Path "partition-disk.ps1" -Destination "C:\WinPE_amd64\mount\Windows\System32\"
Copy-Item -Path "inject-drivers.ps1" -Destination "C:\WinPE_amd64\mount\Windows\System32\"
```

#### **Add Startup Script:**
```powershell
# Create startnet.cmd (runs on WinPE boot)
$startnet = @"
@echo off
echo ========================================
echo  GGnet WinPE Boot Environment
echo ========================================
echo.

wpeinit

REM Start network
wpeutil InitializeNetwork

REM Get IP via DHCP
ipconfig /renew

REM Show IP
ipconfig | findstr IPv4

echo.
echo Ready for Windows deployment!
echo.
echo Available commands:
echo   deploy-windows.ps1 - Deploy Windows from GGnet server
echo   partition-disk.ps1 - Partition disk
echo   inject-drivers.ps1 - Inject drivers
echo.

REM Auto-start deployment (comment out for manual)
REM PowerShell -ExecutionPolicy Bypass -File deploy-windows.ps1

cmd
"@

Set-Content -Path "C:\WinPE_amd64\mount\Windows\System32\startnet.cmd" -Value $startnet
```

---

### **Step 3: Unmount and Create ISO**

```powershell
# Unmount WinPE image
Dism /Unmount-Image /MountDir:"C:\WinPE_amd64\mount" /Commit

# Create bootable ISO
MakeWinPEMedia /ISO C:\WinPE_amd64 C:\WinPE_GGnet.iso

# Copy to GGnet server
scp C:\WinPE_GGnet.iso admin@ggnet-server:/opt/ggnet/winpe/
```

---

## 🌐 **Integration with GGnet**

### **Add WinPE to iPXE Menu:**

Edit `infra/tftp/boot.ipxe.example`:

```ipxe
#!ipxe

:start
menu GGnet Diskless Boot System
item --gap -- ========================================
item boot_windows Boot Windows (Diskless)
item boot_winpe   Deploy Fresh Windows (WinPE)
item --gap -- ========================================
item shell        iPXE Shell
item reboot       Reboot
choose --default boot_windows --timeout 10000 target && goto ${target}

:boot_windows
# Existing diskless boot
sanboot iscsi:${iscsi-server}::::${iscsi-lun}:${iscsi-target}

:boot_winpe
# Boot WinPE for fresh installation
kernel http://${next-server}:8000/winpe/wimboot
initrd http://${next-server}:8000/winpe/boot.wim boot.wim
boot

:shell
shell

:reboot
reboot
```

---

### **Serve WinPE Files from Backend:**

```python
# backend/app/routes/winpe.py

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter(prefix="/winpe", tags=["winpe"])

WINPE_DIR = Path("/opt/ggnet/winpe")

@router.get("/wimboot")
async def get_wimboot():
    """Download wimboot loader for WinPE"""
    return FileResponse(WINPE_DIR / "wimboot")

@router.get("/boot.wim")
async def get_boot_wim():
    """Download WinPE boot.wim"""
    return FileResponse(WINPE_DIR / "boot.wim")
```

---

## 📝 **WinPE Deployment Scripts**

### **deploy-windows.ps1** (runs in WinPE):

```powershell
# Get machine info
$mac = (Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object -First 1).MacAddress
$mac = $mac.Replace("-", ":")

# Contact GGnet server
$serverUrl = "http://192.168.1.10:8000"
$response = Invoke-RestMethod -Uri "$serverUrl/api/winpe/deployment-info?mac=$mac"

# Get deployment details
$imageUrl = $response.image_url
$diskConfig = $response.disk_config
$drivers = $response.drivers

# Partition disk
Write-Host "Partitioning disk..."
& partition-disk.ps1 -Config $diskConfig

# Download and apply Windows image
Write-Host "Downloading Windows image..."
Invoke-WebRequest -Uri $imageUrl -OutFile "C:\install.wim"

Write-Host "Applying Windows image..."
Dism /Apply-Image /ImageFile:"C:\install.wim" /Index:1 /ApplyDir:"W:\"

# Inject drivers
Write-Host "Injecting drivers..."
& inject-drivers.ps1 -DriverPath $drivers -TargetPath "W:\"

# Configure boot
Write-Host "Configuring boot..."
bcdboot W:\Windows /s S: /f UEFI

Write-Host "Deployment complete! Rebooting..."
wpeutil reboot
```

---

## 🔧 **Backend API for WinPE**

```python
# backend/app/routes/winpe.py

@router.get("/deployment-info")
async def get_deployment_info(
    mac: str,
    db: AsyncSession = Depends(get_db)
):
    """Get deployment configuration for WinPE client"""
    
    # Find machine by MAC
    machine = await get_machine_by_mac(db, mac)
    
    if not machine or not machine.deployment_config:
        raise HTTPException(404, "No deployment configured for this machine")
    
    config = machine.deployment_config
    
    return {
        "image_url": f"http://{get_server_ip()}:8000/images/download/{config['image_id']}",
        "disk_config": {
            "disk": 0,
            "partitions": [
                {"type": "efi", "size": "500MB"},
                {"type": "msr", "size": "128MB"},
                {"type": "primary", "size": "remaining", "label": "Windows"}
            ]
        },
        "drivers": f"http://{get_server_ip()}:8000/drivers/{config['driver_pack_id']}",
        "hostname": machine.hostname,
        "timezone": "UTC",
        "locale": "en-US"
    }
```

---

## 📊 **Status**

**Current Implementation:** 🟡 FRAMEWORK READY

**Requires:**
- Windows machine with ADK installed
- WinPE image creation (~30 min)
- Driver packs prepared
- Testing with real hardware

**Estimated Time:** 8-12 hours for full implementation

---

## 🎯 **Next Steps**

1. Install Windows ADK on build machine
2. Create WinPE image using guide above
3. Test WinPE boot via iPXE
4. Implement deployment scripts
5. Test fresh Windows installation

---

**Status:** 📋 Framework Complete, Implementation Pending

