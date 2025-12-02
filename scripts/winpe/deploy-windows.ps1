# GGnet WinPE - Windows Deployment Script
# Runs inside WinPE to deploy fresh Windows installation

param(
    [string]$ServerURL = "http://192.168.1.10:8000",
    [switch]$Auto,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " GGnet Fresh Windows Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get machine MAC address
Write-Host "[1/7] Detecting hardware..." -ForegroundColor Yellow
$adapter = Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object -First 1
$mac = $adapter.MacAddress.Replace("-", ":")
Write-Host "  MAC Address: $mac" -ForegroundColor Green

# Contact GGnet server
Write-Host ""
Write-Host "[2/7] Contacting GGnet server..." -ForegroundColor Yellow
try {
    $config = Invoke-RestMethod -Uri "$ServerURL/winpe/deployment-info?mac=$mac"
    Write-Host "  Server: $ServerURL" -ForegroundColor Green
    Write-Host "  Image: $($config.image_url)" -ForegroundColor Green
    Write-Host "  Hostname: $($config.hostname)" -ForegroundColor Green
}
catch {
    Write-Host "  ERROR: Cannot contact server!" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Partition disk
Write-Host ""
Write-Host "[3/7] Partitioning disk..." -ForegroundColor Yellow
& "$PSScriptRoot\partition-disk.ps1" -DiskNumber $config.disk_config.disk
Write-Host "  Disk partitioned successfully" -ForegroundColor Green

# Download Windows image
Write-Host ""
Write-Host "[4/7] Downloading Windows image..." -ForegroundColor Yellow
$imagePath = "C:\install.wim"

# Show progress
$ProgressPreference = 'Continue'
Invoke-WebRequest -Uri $config.image_url -OutFile $imagePath -UseBasicParsing

$imageSize = (Get-Item $imagePath).Length / 1GB
Write-Host "  Downloaded: $($imageSize.ToString('0.00')) GB" -ForegroundColor Green

# Apply Windows image
Write-Host ""
Write-Host "[5/7] Applying Windows image..." -ForegroundColor Yellow
Write-Host "  This may take 10-20 minutes..." -ForegroundColor Gray

$applyResult = Dism /Apply-Image /ImageFile:"$imagePath" /Index:1 /ApplyDir:"W:\" /CheckIntegrity

if ($LASTEXITCODE -eq 0) {
    Write-Host "  Windows image applied successfully" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Failed to apply image!" -ForegroundColor Red
    exit 1
}

# Inject drivers (if available)
if ($config.drivers_url) {
    Write-Host ""
    Write-Host "[6/7] Injecting drivers..." -ForegroundColor Yellow
    & "$PSScriptRoot\inject-drivers.ps1" -DriversURL $config.drivers_url -TargetPath "W:\"
} else {
    Write-Host ""
    Write-Host "[6/7] No driver injection configured (skipping)" -ForegroundColor Gray
}

# Configure boot
Write-Host ""
Write-Host "[7/7] Configuring boot..." -ForegroundColor Yellow
bcdboot W:\Windows /s S: /f UEFI
Write-Host "  Boot configuration complete" -ForegroundColor Green

# Apply hostname
if ($config.hostname) {
    Write-Host ""
    Write-Host "Setting computer name: $($config.hostname)" -ForegroundColor Yellow
    
    # TODO: Implement offline registry editing to set computer name
    # Requires hivex or similar tool in WinPE
}

# Cleanup
Write-Host ""
Write-Host "Cleaning up..." -ForegroundColor Yellow
Remove-Item $imagePath -Force

# Success
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Windows Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The computer will reboot in 10 seconds..." -ForegroundColor Yellow
Write-Host "Remove PXE boot from boot order to boot Windows." -ForegroundColor Yellow
Write-Host ""

Start-Sleep -Seconds 10

Write-Host "Rebooting now..." -ForegroundColor Cyan
wpeutil reboot

