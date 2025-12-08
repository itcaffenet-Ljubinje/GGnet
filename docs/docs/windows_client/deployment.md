# Windows Client Deployment

This document describes how to deploy the ggnet2 Windows Client to physical machines.

## Deployment Options

### Option 1: Manual Installation

1. **Download Client Installer**
   - Download installer from server
   - Run installer on target machine
   - Configure client settings

2. **Registry Script Installation**
   - Generate registry script from server
   - Apply registry script on target machine
   - Install Windows Service

### Option 2: Automated Deployment

1. **Group Policy Deployment**
   - Create Group Policy for client installation
   - Deploy to target machines via Group Policy

2. **Scripted Deployment**
   - Use deployment script
   - Deploy via network share or remote execution

## Registry Script Generation

### Generate Registry Script

**From Server API:**
```bash
curl -X POST http://server:8000/api/clients/client-001/registry-script \
  -H "Content-Type: application/json" \
  -d '{
    "script_type": "install",
    "computer_name": "PC-1",
    "server_url": "http://server:8000",
    "client_id": "client-001"
  }'
```

**Generated Script:**
```
Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\SOFTWARE\ggnet2]
"ServerURL"="http://server:8000"
"ClientID"="client-001"
"ComputerName"="PC-1"
```

### Apply Registry Script

**On Target Machine:**
```bash
reg import ggnet2-install.reg
```

## .NET Client Deployment

### Build Client

```bash
cd windows_client/ggnet2-toolchain
dotnet build -c Release
```

### Install Service

**Prerequisites:**
1. Create installation directory (if it doesn't exist)
2. Copy `ggnet2-toolchain.exe` to the installation directory
3. Verify the executable path before creating the service

**Installation:**

```bash
# Set installation directory (use environment variable or default)
$InstallDir = $env:GGNET2_INSTALL_DIR
if (-not $InstallDir) {
    # Use Program Files (handles localized Windows versions)
    $ProgramFiles = [Environment]::GetFolderPath("ProgramFiles")
    $InstallDir = Join-Path $ProgramFiles "ggnet2"
}

# Create installation directory if it doesn't exist
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force
}

# Copy executable to installation directory
Copy-Item "ggnet2-toolchain.exe" -Destination "$InstallDir\ggnet2-toolchain.exe"

# Verify executable exists
$ExePath = Join-Path $InstallDir "ggnet2-toolchain.exe"
if (-not (Test-Path $ExePath)) {
    Write-Error "Executable not found at: $ExePath"
    exit 1
}

# Create Windows Service
sc create ggnet2-toolchain binPath="$ExePath"

# Start service
sc start ggnet2-toolchain
```

**Alternative: Using Custom Installation Path**

```bash
# Set custom installation path
$InstallDir = "C:\CustomPath\ggnet2"
$env:GGNET2_INSTALL_DIR = $InstallDir

# Then follow installation steps above
```

### Configure Client

**appsettings.json:**
```json
{
  "Server": {
    "Url": "http://server:8000"
  },
  "Client": {
    "ClientId": "client-001",
    "UpdateInterval": 30000,
    "HeartbeatInterval": 60000
  }
}
```

## Python Client Deployment

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install Service

```bash
python main.py install
python main.py start
```

### Configure Client

**config.json:**
```json
{
  "server_url": "http://server:8000",
  "client_id": "client-001",
  "update_interval": 30,
  "heartbeat_interval": 60
}
```

## Deployment Script

### PowerShell Deployment Script

**deploy-client.ps1:**
```powershell
# Deploy ggnet2 Windows Client
$ServerUrl = "http://server:8000"
$ClientId = "client-001"

# Download client installer
$InstallerUrl = "$ServerUrl/api/clients/$ClientId/installer"
Invoke-WebRequest -Uri $InstallerUrl -OutFile "ggnet2-client-installer.exe"

# Install client
Start-Process -FilePath "ggnet2-client-installer.exe" -Wait

# Download registry script
$RegistryScriptUrl = "$ServerUrl/api/clients/$ClientId/registry-script"
Invoke-WebRequest -Uri $RegistryScriptUrl -OutFile "ggnet2-install.reg"

# Apply registry script
reg import ggnet2-install.reg

# Start service
Start-Service ggnet2-toolchain
```

## Group Policy Deployment

### Create Group Policy

1. **Create GPO**
   - Create new Group Policy Object
   - Configure client installation

2. **Deploy Installer**
   - Add installer to Group Policy
   - Configure installation settings

3. **Deploy Registry Script**
   - Add registry script to Group Policy
   - Configure registry settings

## Verification

### Check Service Status

```bash
# .NET Client
sc query ggnet2-toolchain

# Python Client
python main.py status
```

### Check Client Connection

**From Server:**
```bash
curl http://server:8000/api/clients/client-001
```

**Response:**
```json
{
  "id": "client-001",
  "name": "PC-1",
  "status": "online",
  "last_seen": "2024-01-01T12:00:00Z"
}
```

## Troubleshooting

### Service Not Starting

**Check Service Logs:**
```bash
# .NET Client
Get-EventLog -LogName Application -Source ggnet2-toolchain

# Python Client
python main.py debug
```

### Connection Issues

**Check Network Connectivity:**
```bash
ping server
telnet server 8000
```

**Check Firewall:**
```bash
# Allow outbound connection
netsh advfirewall firewall add rule name="ggnet2-client" dir=out action=allow protocol=TCP localport=8000
```

### Registry Issues

**Check Registry Values:**
```bash
reg query HKEY_LOCAL_MACHINE\SOFTWARE\ggnet2
```

## Development Notes

- Client deployment requires administrator privileges
- Registry scripts must be applied with appropriate permissions
- Windows Service must be installed and started
- Network connectivity to server is required
- Firewall rules may need to be configured

## To-Do

- [ ] Create installer package
- [ ] Implement silent installation
- [ ] Add deployment automation
- [ ] Implement client update mechanism
- [ ] Add deployment verification
- [ ] Implement rollback mechanism

