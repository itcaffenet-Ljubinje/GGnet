# Windows Registry Toolchain for GGnet Diskless System

Automated Windows configuration scripts for diskless clients.

---

## 📋 **Registry Scripts**

| File | Purpose | Requires Restart | Critical |
|------|---------|------------------|----------|
| `01-disable-uac.reg` | Disable UAC prompts | ✅ Yes | 🔴 Yes |
| `02-disable-firewall.reg` | Disable Windows Firewall | ❌ No | 🟡 Network-dependent |
| `03-enable-autologon.reg.template` | Auto-login configuration | ✅ Yes | 🔴 Yes |
| `04-rename-computer.reg.template` | Set computer name | ✅ Yes | 🟡 Optional |
| `05-ggnet-client-install.reg` | Diskless optimizations | ✅ Yes | 🔴 Yes |
| `06-inject-environment-vars.reg.template` | GGnet environment vars | ❌ No | 🟢 Optional |
| `07-enable-rdp.reg` | Enable Remote Desktop | ❌ No | 🟢 Optional |
| `08-optimize-performance.reg` | Performance tweaks | ✅ Yes | 🟡 Recommended |
| `09-disable-telemetry.reg` | Disable Windows tracking | ❌ No | 🟢 Privacy |

---

## 🚀 **Quick Start**

### **Option 1: Apply All (Automated)**

```batch
REM Run as Administrator
apply-all.bat
```

This will:
1. Apply all `.reg` files (except templates)
2. Show progress
3. Restart computer automatically

### **Option 2: Manual Application**

```batch
REM Apply specific tweaks
reg import 01-disable-uac.reg
reg import 05-ggnet-client-install.reg
reg import 08-optimize-performance.reg

REM Restart
shutdown /r /t 60
```

---

## 📝 **Template Files**

Some files are **templates** and need variables replaced:

### **03-enable-autologon.reg.template**

Replace before using:
- `{USERNAME}` → `GGUser` or `Administrator`
- `{PASSWORD}` → User password
- `{DOMAIN}` → `.` (for local) or domain name

```reg
"DefaultUserName"="GGUser"
"DefaultPassword"="ggnet123"
"DefaultDomainName"="."
```

### **04-rename-computer.reg.template**

Replace:
- `{COMPUTER_NAME}` → `GGNET-PC-001`

```reg
"ComputerName"="GGNET-PC-001"
```

### **06-inject-environment-vars.reg.template**

Replace:
- `{GGNET_SERVER}` → `192.168.1.10`
- `{MACHINE_ID}` → `42`
- `{MACHINE_NAME}` → `GGNET-PC-042`
- `{SESSION_ID}` → Current session UUID

---

## 🔧 **Automated Template Processing**

Use PowerShell to generate from templates:

```powershell
# Example: Generate auto-logon script
$content = Get-Content "03-enable-autologon.reg.template"
$content = $content -replace '{USERNAME}', 'GGUser'
$content = $content -replace '{PASSWORD}', 'ggnet123'
$content = $content -replace '{DOMAIN}', '.'
$content | Set-Content "03-enable-autologon.reg"

# Apply
reg import 03-enable-autologon.reg
```

**Or use backend to generate:**

```python
# backend/scripts/generate_registry.py

def generate_autologon_reg(username: str, password: str, domain: str = "."):
    """Generate auto-logon registry file"""
    template = Path("infra/windows-scripts/03-enable-autologon.reg.template").read_text()
    content = template.replace("{USERNAME}", username)
    content = content.replace("{PASSWORD}", password)
    content = content.replace("{DOMAIN}", domain)
    return content

def generate_computer_rename_reg(computer_name: str):
    """Generate computer rename registry file"""
    template = Path("infra/windows-scripts/04-rename-computer.reg.template").read_text()
    content = template.replace("{COMPUTER_NAME}", computer_name)
    return content

def generate_environment_vars_reg(machine_id: int, machine_name: str, server_ip: str, session_id: str):
    """Generate environment variables registry file"""
    template = Path("infra/windows-scripts/06-inject-environment-vars.reg.template").read_text()
    content = template.replace("{GGNET_SERVER}", server_ip)
    content = content.replace("{MACHINE_ID}", str(machine_id))
    content = content.replace("{MACHINE_NAME}", machine_name)
    content = content.replace("{SESSION_ID}", session_id)
    content = content.replace("{BOOT_TIME}", datetime.now().isoformat())
    return content
```

---

## 🌐 **Integration with iPXE Boot**

Registry scripts should be applied during first boot:

### **Method 1: Mount and Inject (Before Boot)**

```bash
# On server, before client boots
# Mount iSCSI target image
sudo mount /opt/ggnet/images/machine-001.vhdx /mnt/windows

# Copy registry scripts
sudo cp infra/windows-scripts/*.reg /mnt/windows/Windows/Setup/Scripts/

# Create startup script
cat > /mnt/windows/Windows/Setup/Scripts/apply-ggnet-config.bat << 'EOF'
@echo off
cd %~dp0
for %%f in (*.reg) do reg import "%%f"
del %~f0
EOF

# Add to RunOnce
# ... (requires registry editing while mounted)

sudo umount /mnt/windows
```

### **Method 2: HTTP Download During Boot**

Add to `boot.ipxe`:

```ipxe
# After iSCSI connection, before boot
kernel http://ggnet-server:8000/scripts/apply-registry.bat
initrd http://ggnet-server:8000/scripts/registry-pack.zip
```

### **Method 3: Startup Script (Post-Boot)**

Create `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp\ggnet-config.bat`:

```batch
@echo off
if not exist C:\ggnet-configured (
    REM Download and apply registry
    powershell -Command "Invoke-WebRequest -Uri 'http://ggnet-server:8000/api/machines/%COMPUTERNAME%/registry-pack' -OutFile C:\temp\registry.zip"
    powershell -Command "Expand-Archive C:\temp\registry.zip C:\temp\registry"
    
    REM Apply all
    for %%f in (C:\temp\registry\*.reg) do reg import "%%f"
    
    REM Mark as configured
    echo Configured > C:\ggnet-configured
    
    REM Restart
    shutdown /r /t 60 /c "GGnet: Configuration applied. Restarting..."
)
```

---

## ⚠️ **Security Considerations**

1. **Passwords in plaintext:**
   - Auto-logon registry contains plaintext password
   - Only use in controlled/isolated networks
   - Consider using null password + network-level security

2. **Firewall disabled:**
   - Only disable in trusted gaming center networks
   - Alternative: Configure firewall rules instead of disabling

3. **UAC disabled:**
   - Required for unattended operation
   - Acceptable in controlled environment
   - All users have admin rights anyway

4. **Windows Update disabled:**
   - **CRITICAL for diskless!**
   - Updates would be lost on restart
   - Apply updates to master image instead

---

## 📊 **What Each Script Does**

### **01-disable-uac.reg:**
- Disables User Account Control
- No more "Do you want to allow...?" prompts
- Required for auto-install of software

### **02-disable-firewall.reg:**
- Turns off Windows Firewall completely
- Use with caution - only in isolated network
- Alternative: Configure specific firewall rules

### **03-enable-autologon.reg:**
- Automatically logs in user on boot
- No password prompt
- Perfect for gaming stations

### **04-rename-computer.reg:**
- Sets computer name to match GGnet inventory
- Helps with identification
- Useful for management

### **05-ggnet-client-install.reg:**
- **MOST IMPORTANT!**
- Disables Windows Update (would break diskless!)
- Disables System Restore (no persistent storage)
- Disables hibernation
- Disables page file (use RAM or iSCSI)
- Optimizes for diskless operation

### **06-inject-environment-vars.reg:**
- Sets GGNET_SERVER, GGNET_MACHINE_ID, etc.
- Available to all applications
- Useful for custom client software

### **07-enable-rdp.reg:**
- Enables Remote Desktop
- Allows remote administration
- Useful for troubleshooting

### **08-optimize-performance.reg:**
- Disables visual effects
- Disables unnecessary services
- Enables Game Mode
- High performance power plan
- Speeds up boot and runtime

### **09-disable-telemetry.reg:**
- Disables Windows telemetry
- Disables Cortana
- Disables tracking features
- Reduces network usage
- Improves privacy

---

## 🧪 **Testing**

### **Test on Local VM:**

```powershell
# 1. Create Windows 11 VM
# 2. Apply registry scripts
cd infra\windows-scripts
.\apply-all.bat

# 3. Restart and verify
#    - UAC should be disabled (no prompts)
#    - Auto-login should work
#    - Performance should be better
```

### **Verify Settings:**

```batch
REM Check if UAC is disabled
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v EnableLUA

REM Check if RDP is enabled
reg query "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server" /v fDenyTSConnections

REM Check environment variables
echo %GGNET_SERVER%
echo %GGNET_MACHINE_ID%
```

---

## 📦 **Deployment**

### **Include in Master Image:**

1. Install Windows 11
2. Apply all registry tweaks
3. Install required software
4. Convert to VHDX
5. Upload to GGnet

### **Apply on First Boot:**

1. Client boots via iPXE
2. Connects to iSCSI target
3. Windows starts
4. Startup script downloads registry pack
5. Applies tweaks
6. Restarts
7. Ready to use!

---

## 🔗 **References**

- Windows Registry Reference: https://docs.microsoft.com/en-us/windows/win32/sysinfo/registry
- ggRock Toolchain: Reverse-engineered from package analysis
- Best Practices: Gaming center diskless deployment guides

---

**Status:** ✅ Registry scripts created and ready to use!  
**Next:** Integrate with iPXE boot process and test!

