# Download iPXE binaries for GGnet Diskless System
# Run this script in PowerShell on Windows

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Downloading iPXE Binaries for GGnet" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "https://boot.ipxe.org"
$files = @{
    "ipxe.efi" = @{
        "url" = "$baseUrl/ipxe.efi"
        "description" = "UEFI x64 (standard)"
        "critical" = $false
    }
    "snponly.efi" = @{
        "url" = "$baseUrl/snponly.efi"
        "description" = "UEFI x64 SecureBoot (Win11)"
        "critical" = $true
    }
    "ipxe-i386.efi" = @{
        "url" = "$baseUrl/ipxe-i386.efi"
        "description" = "UEFI IA32 (32-bit)"
        "critical" = $false
    }
    "undionly.kpxe" = @{
        "url" = "$baseUrl/undionly.kpxe"
        "description" = "Legacy BIOS (UNDI driver)"
        "critical" = $false
    }
    "undionly.pxe" = @{
        "url" = "$baseUrl/undionly.pxe"
        "description" = "Legacy BIOS (PXE)"
        "critical" = $false
    }
}

$success = 0
$failed = 0

foreach ($filename in $files.Keys) {
    $fileInfo = $files[$filename]
    $url = $fileInfo.url
    $desc = $fileInfo.description
    $critical = $fileInfo.critical
    
    # Use the original filename, not the key (for ipxe-i386.efi)
    $outFile = Split-Path -Leaf $url
    
    # For ipxe-i386.efi, rename to ipxe32.efi
    if ($outFile -eq "ipxe-i386.efi") {
        $outFile = "ipxe32.efi"
    }
    
    $marker = if ($critical) { "[CRITICAL]" } else { "[OPTIONAL]" }
    
    Write-Host "$marker Downloading: $outFile" -ForegroundColor $(if ($critical) { "Red" } else { "Yellow" })
    Write-Host "  Description: $desc" -ForegroundColor Gray
    Write-Host "  URL: $url" -ForegroundColor Gray
    
    try {
        Invoke-WebRequest -Uri $url -OutFile $outFile -UseBasicParsing
        
        if (Test-Path $outFile) {
            $size = (Get-Item $outFile).Length
            $sizeKB = [math]::Round($size / 1024, 2)
            $sizeMB = [math]::Round($size / 1024 / 1024, 2)
            
            if ($size -gt 1MB) {
                Write-Host "  Success: $outFile ($sizeMB MB)" -ForegroundColor Green
            } else {
                Write-Host "  Success: $outFile ($sizeKB KB)" -ForegroundColor Green
            }
            
            $success++
        } else {
            Write-Host "  Failed: File not created" -ForegroundColor Red
            $failed++
        }
    }
    catch {
        Write-Host "  Error: $_" -ForegroundColor Red
        $failed++
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Download Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Success: $success files" -ForegroundColor Green
Write-Host "  Failed: $failed files" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($success -ge 2) {
    Write-Host "Minimum requirements met!" -ForegroundColor Green
    Write-Host "  - At least one UEFI file downloaded" -ForegroundColor Green
    Write-Host "  - At least one BIOS file downloaded" -ForegroundColor Green
} else {
    Write-Host "WARNING: Insufficient files downloaded!" -ForegroundColor Yellow
    Write-Host "  Need at least: snponly.efi (for SecureBoot) and undionly.kpxe (for BIOS)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Copy files to TFTP server directory: /var/lib/tftp/" -ForegroundColor White
Write-Host "  2. Update DHCP config for dynamic boot file selection" -ForegroundColor White
Write-Host "  3. Restart DHCP and TFTP services" -ForegroundColor White
Write-Host "  4. Test PXE boot with a client machine" -ForegroundColor White
Write-Host ""

