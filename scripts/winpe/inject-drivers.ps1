# GGnet WinPE - Driver Injection Script

param(
    [string]$DriversURL,
    [string]$TargetPath = "W:\"
)

Write-Host "Injecting drivers into Windows installation..." -ForegroundColor Cyan

if (-not $DriversURL) {
    Write-Host "No driver URL provided. Skipping driver injection." -ForegroundColor Gray
    return
}

# Download driver pack
Write-Host "Downloading driver pack..." -ForegroundColor Yellow
$driverZip = "C:\drivers.zip"

try {
    Invoke-WebRequest -Uri $DriversURL -OutFile $driverZip -UseBasicParsing
    Write-Host "  Downloaded: $((Get-Item $driverZip).Length / 1MB) MB" -ForegroundColor Green
}
catch {
    Write-Host "  ERROR: Failed to download drivers!" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    return
}

# Extract drivers
Write-Host "Extracting drivers..." -ForegroundColor Yellow
$driverDir = "C:\drivers"
Expand-Archive -Path $driverZip -DestinationPath $driverDir -Force
Write-Host "  Extracted to: $driverDir" -ForegroundColor Green

# Inject drivers into offline Windows image
Write-Host "Injecting drivers into Windows image..." -ForegroundColor Yellow
Write-Host "  Target: $TargetPath" -ForegroundColor Gray

try {
    Dism /Image:"$TargetPath" /Add-Driver /Driver:"$driverDir" /Recurse /ForceUnsigned
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Drivers injected successfully!" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Some drivers may not have been injected" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  ERROR: Driver injection failed!" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
}

# Cleanup
Write-Host "Cleaning up..." -ForegroundColor Yellow
Remove-Item $driverZip -Force -ErrorAction SilentlyContinue
Remove-Item $driverDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Driver injection complete!" -ForegroundColor Green

