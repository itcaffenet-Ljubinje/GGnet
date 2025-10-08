# GGnet WinPE - Disk Partitioning Script

param(
    [int]$DiskNumber = 0,
    [switch]$Force
)

Write-Host "Partitioning disk $DiskNumber for Windows..." -ForegroundColor Cyan

# Safety check
if (-not $Force) {
    Write-Host ""
    Write-Host "WARNING: This will ERASE all data on disk $DiskNumber!" -ForegroundColor Red
    Write-Host "Press Ctrl+C to cancel, or" -ForegroundColor Yellow
    pause
}

# Clean disk
Write-Host "Cleaning disk..." -ForegroundColor Yellow
$disk = Get-Disk -Number $DiskNumber
Clear-Disk -Number $DiskNumber -RemoveData -Confirm:$false

# Initialize as GPT (for UEFI)
Initialize-Disk -Number $DiskNumber -PartitionStyle GPT

# Create EFI System Partition (500 MB)
Write-Host "Creating EFI System Partition (500 MB)..." -ForegroundColor Yellow
$efi = New-Partition -DiskNumber $DiskNumber -Size 500MB -GptType '{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}'
Format-Volume -Partition $efi -FileSystem FAT32 -NewFileSystemLabel "System" -Confirm:$false
$efi | Add-PartitionAccessPath -AccessPath "S:"

# Create MSR (Microsoft Reserved) Partition (128 MB)
Write-Host "Creating MSR Partition (128 MB)..." -ForegroundColor Yellow
New-Partition -DiskNumber $DiskNumber -Size 128MB -GptType '{e3c9e316-0b5c-4db8-817d-f92df00215ae}' | Out-Null

# Create Windows partition (remaining space)
Write-Host "Creating Windows Partition..." -ForegroundColor Yellow
$windows = New-Partition -DiskNumber $DiskNumber -UseMaximumSize -GptType '{ebd0a0a2-b9e5-4433-87c0-68b6b72699c7}'
Format-Volume -Partition $windows -FileSystem NTFS -NewFileSystemLabel "Windows" -Confirm:$false
$windows | Add-PartitionAccessPath -AccessPath "W:"

Write-Host ""
Write-Host "Disk partitioning complete!" -ForegroundColor Green
Write-Host "  EFI System: S: (500 MB, FAT32)"
Write-Host "  Windows: W: ($([math]::Round($windows.Size / 1GB, 2)) GB, NTFS)"
Write-Host ""

# Show partition layout
Get-Partition -DiskNumber $DiskNumber | Format-Table -AutoSize

