#!/bin/bash
# Download iPXE binaries for GGnet Diskless System

set -e

echo "========================================"
echo " Downloading iPXE Binaries for GGnet"
echo "========================================"
echo ""

BASE_URL="https://boot.ipxe.org"

# Function to download and verify
download_file() {
    local url=$1
    local filename=$2
    local description=$3
    local critical=$4
    
    if [ "$critical" = "true" ]; then
        echo -e "\e[31m[CRITICAL]\e[0m Downloading: $filename"
    else
        echo -e "\e[33m[OPTIONAL]\e[0m Downloading: $filename"
    fi
    echo "  Description: $description"
    echo "  URL: $url"
    
    if wget -q "$url" -O "$filename"; then
        size=$(ls -lh "$filename" | awk '{print $5}')
        echo -e "  \e[32mSuccess: $filename ($size)\e[0m"
        echo ""
        return 0
    else
        echo -e "  \e[31mFailed: Could not download\e[0m"
        echo ""
        return 1
    fi
}

# Download files
success=0
failed=0

# UEFI binaries
download_file "$BASE_URL/ipxe.efi" "ipxe.efi" "UEFI x64 (standard)" "false" && ((success++)) || ((failed++))
download_file "$BASE_URL/snponly.efi" "snponly.efi" "UEFI x64 SecureBoot (Win11)" "true" && ((success++)) || ((failed++))
download_file "$BASE_URL/ipxe-i386.efi" "ipxe32.efi" "UEFI IA32 (32-bit)" "false" && ((success++)) || ((failed++))

# Legacy BIOS binaries  
download_file "$BASE_URL/undionly.kpxe" "undionly.kpxe" "Legacy BIOS (UNDI driver)" "false" && ((success++)) || ((failed++))
download_file "$BASE_URL/undionly.pxe" "undionly.pxe" "Legacy BIOS (PXE)" "false" && ((success++)) || ((failed++))

# Summary
echo "========================================"
echo " Download Summary"
echo "========================================"
echo -e "  Success: \e[32m$success files\e[0m"
echo -e "  Failed: $(if [ $failed -gt 0 ]; then echo -e "\e[31m$failed files\e[0m"; else echo -e "\e[32m$failed files\e[0m"; fi)"
echo ""

# Check minimum requirements
if [ -f "snponly.efi" ] && [ -f "undionly.kpxe" ]; then
    echo -e "\e[32m✓ Minimum requirements met!\e[0m"
    echo "  - snponly.efi (SecureBoot)"
    echo "  - undionly.kpxe (Legacy BIOS)"
elif [ $success -ge 2 ]; then
    echo -e "\e[32m✓ Basic requirements met!\e[0m"
    echo "  - At least 2 boot files downloaded"
    echo -e "\e[33m  WARNING: snponly.efi recommended for Windows 11!\e[0m"
else
    echo -e "\e[31m✗ Insufficient files downloaded!\e[0m"
    echo "  Need at least: snponly.efi and undionly.kpxe"
    exit 1
fi

echo ""
echo "Next steps:"
echo "  1. Copy files to TFTP directory:"
echo "     sudo cp *.efi *.kpxe *.pxe /var/lib/tftp/"
echo "  2. Set permissions:"
echo "     sudo chmod 644 /var/lib/tftp/*"
echo "  3. Update DHCP config (see README.md)"
echo "  4. Restart services:"
echo "     sudo systemctl restart isc-dhcp-server tftpd-hpa"
echo "  5. Test PXE boot!"
echo ""

exit 0

