# iPXE Boot Files for GGnet Diskless System

This directory contains iPXE network boot binaries for different client types.

---

## 📦 **Required Files**

### **UEFI Boot (Modern Systems):**

1. **ipxe.efi** - Standard UEFI x64 boot
   - For: UEFI systems without SecureBoot
   - Download: `wget https://boot.ipxe.org/ipxe.efi`

2. **snponly.efi** - UEFI with SecureBoot
   - For: Windows 11 with SecureBoot enabled
   - Download: `wget https://boot.ipxe.org/snponly.efi`
   - **CRITICAL:** Must be signed by Microsoft for SecureBoot!

3. **ipxe32.efi** - UEFI IA32 (32-bit)
   - For: Rare 32-bit UEFI systems
   - Download: `wget https://boot.ipxe.org/ipxe-i386.efi -O ipxe32.efi`

### **Legacy BIOS Boot (Old Systems):**

4. **undionly.kpxe** - Legacy BIOS with UNDI driver
   - For: BIOS-based systems
   - Download: `wget https://boot.ipxe.org/undionly.kpxe`

5. **undionly.pxe** - Legacy BIOS PXE
   - For: Very old BIOS systems
   - Download: `wget https://boot.ipxe.org/undionly.pxe`

---

## 🔧 **Download All Files**

```bash
#!/bin/bash
# Download all iPXE binaries

cd infra/tftp

# UEFI binaries
echo "Downloading UEFI binaries..."
wget -q https://boot.ipxe.org/ipxe.efi
wget -q https://boot.ipxe.org/snponly.efi
wget -q https://boot.ipxe.org/ipxe-i386.efi -O ipxe32.efi

# Legacy BIOS binaries
echo "Downloading Legacy BIOS binaries..."
wget -q https://boot.ipxe.org/undionly.kpxe
wget -q https://boot.ipxe.org/undionly.pxe

# Verify downloads
echo "Verifying files..."
for file in ipxe.efi snponly.efi ipxe32.efi undionly.kpxe undionly.pxe; do
    if [ -f "$file" ]; then
        size=$(ls -lh "$file" | awk '{print $5}')
        echo "✓ $file ($size)"
    else
        echo "✗ $file MISSING!"
    fi
done

echo ""
echo "iPXE binaries ready!"
```

**Or download on Windows:**

```powershell
# PowerShell script to download iPXE binaries

$baseUrl = "https://boot.ipxe.org"
$files = @{
    "ipxe.efi" = "$baseUrl/ipxe.efi"
    "snponly.efi" = "$baseUrl/snponly.efi"
    "ipxe32.efi" = "$baseUrl/ipxe-i386.efi"
    "undionly.kpxe" = "$baseUrl/undionly.kpxe"
    "undionly.pxe" = "$baseUrl/undionly.pxe"
}

foreach ($file in $files.Keys) {
    Write-Host "Downloading $file..."
    Invoke-WebRequest -Uri $files[$file] -OutFile $file
}

Write-Host "`n✓ All iPXE binaries downloaded!"
```

---

## 📋 **File Purposes**

| File | Type | SecureBoot | Use Case |
|------|------|------------|----------|
| `snponly.efi` | UEFI | ✅ YES | **Windows 11** with SecureBoot |
| `ipxe.efi` | UEFI | ❌ NO | UEFI without SecureBoot |
| `ipxe32.efi` | UEFI 32-bit | ❌ NO | Rare 32-bit UEFI systems |
| `undionly.kpxe` | BIOS | N/A | Legacy BIOS systems |
| `undionly.pxe` | BIOS | N/A | Very old BIOS systems |

---

## 🔐 **SecureBoot Requirements**

### **Why `snponly.efi` is Critical:**

Windows 11 **REQUIRES** SecureBoot by default. Regular `ipxe.efi` will:
- ❌ Not boot (SecureBoot violation)
- ❌ Show "Security Boot Violation" error
- ❌ Require manual SecureBoot disable

`snponly.efi` is:
- ✅ Signed by Microsoft
- ✅ Passes SecureBoot validation
- ✅ Boots Windows 11 without issues

### **How to Verify SecureBoot Binary:**

```bash
# Check if signed
pesign -S -i snponly.efi

# Should show Microsoft signature
```

---

## 🌐 **DHCP Configuration**

After downloading binaries, update DHCP to serve correct file:

```conf
# docker/dhcp/dhcpd.conf

option arch code 93 = unsigned integer 16;

if option arch = 00:07 or option arch = 00:09 {
    # UEFI x64
    if exists user-class and option user-class = "iPXE" {
        # Already in iPXE, load our script
        filename "http://192.168.1.10:8000/boot/script.ipxe";
    } else {
        # Check if SecureBoot is enabled
        # For Windows 11, use snponly.efi
        filename "snponly.efi";
    }
} elsif option arch = 00:00 {
    # Legacy BIOS
    filename "undionly.kpxe";
} else {
    # Default to UEFI
    filename "ipxe.efi";
}
```

---

## 📂 **TFTP Directory Structure**

```
/var/lib/tftp/  (or infra/tftp/ in development)
├── ipxe.efi              (1.2 MB) - UEFI standard
├── snponly.efi           (1.2 MB) - UEFI SecureBoot ⭐
├── ipxe32.efi            (1.1 MB) - UEFI 32-bit
├── undionly.kpxe         (90 KB)  - BIOS UNDI
├── undionly.pxe          (85 KB)  - BIOS PXE
├── boot.ipxe             (text)   - iPXE boot script
└── README.md             (this file)
```

---

## 🧪 **Testing**

### **Test UEFI Boot:**
```bash
# Using QEMU
qemu-system-x86_64 \
  -bios /usr/share/ovmf/OVMF.fd \
  -boot n \
  -m 4096 \
  -netdev user,id=net0,tftp=./infra/tftp,bootfile=ipxe.efi \
  -device e1000,netdev=net0
```

### **Test SecureBoot:**
```bash
# Using real hardware:
1. Enable SecureBoot in BIOS
2. Set PXE boot first
3. Should load snponly.efi
4. Verify in iPXE menu: platform = efi, SecureBoot = enabled
```

---

## 🔗 **References**

- iPXE Downloads: https://boot.ipxe.org/
- iPXE Documentation: https://ipxe.org/
- SecureBoot: https://ipxe.org/appnote/uefi_secure_boot
- ggRock Package: https://packagecloud.io/ggcircuit/stable

---

## ⚠️ **Important Notes**

1. **File Sizes:**
   - UEFI files: ~1-1.2 MB each
   - BIOS files: ~85-90 KB each
   - Total: ~5 MB for all binaries

2. **Updates:**
   - Check for new iPXE versions monthly
   - Update URL: https://github.com/ipxe/ipxe/releases

3. **Licensing:**
   - iPXE is GPL v2
   - Free to use and redistribute
   - Must maintain copyright notices

4. **Security:**
   - Verify checksums after download
   - Only download from official sources
   - For production, use official signed binaries

---

**Status:** ⏳ Files need to be downloaded (run download script above)  
**Next:** After download, configure DHCP and test!

