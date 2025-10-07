# 🔐 SecureBoot Setup Guide for GGnet

Complete guide for enabling Windows 11 SecureBoot support in GGnet diskless system.

---

## 📋 **Table of Contents**

1. [Overview](#overview)
2. [Why SecureBoot Matters](#why-secureboot-matters)
3. [Prerequisites](#prerequisites)
4. [Installation Steps](#installation-steps)
5. [DHCP Configuration](#dhcp-configuration)
6. [TFTP Configuration](#tftp-configuration)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 **Overview**

SecureBoot is a UEFI firmware security feature that ensures only trusted software can boot. Windows 11 **REQUIRES** SecureBoot by default.

**Without SecureBoot support:**
- ❌ Windows 11 won't install
- ❌ Windows 11 won't boot
- ❌ "Secure Boot violation" error

**With GGnet SecureBoot support:**
- ✅ Windows 11 boots with SecureBoot enabled
- ✅ No BIOS configuration needed
- ✅ Enterprise-grade security

---

## ❗ **Why SecureBoot Matters**

### **Windows 11 Requirements:**

Microsoft mandates SecureBoot for Windows 11:
- TPM 2.0
- UEFI firmware
- **SecureBoot enabled**

### **Without `snponly.efi`:**

Using regular `ipxe.efi` with SecureBoot results in:

```
Security Violation

The system found an unauthorized change on the firmware,
operating system or UEFI driver.

Press [OK] to run the next boot device,
or enter directly to BIOS Setup.
```

### **With `snponly.efi`:**

- **Microsoft-signed** iPXE binary
- Passes UEFI SecureBoot validation
- Boots Windows 11 seamlessly

---

## 🔧 **Prerequisites**

### **1. Server Requirements:**

- GGnet server (Linux or Docker)
- DHCP server (isc-dhcp-server or dnsmasq)
- TFTP server (tftpd-hpa or dnsmasq)
- Internet connection (to download iPXE binaries)

### **2. Client Requirements:**

- UEFI firmware (not Legacy BIOS)
- SecureBoot **ENABLED** in BIOS/UEFI
- Network boot (PXE) enabled
- TPM 2.0 chip (for Windows 11)

### **3. Network Requirements:**

- DHCP server on same network as clients
- TFTP server accessible from clients
- GGnet backend API accessible (port 8000)

---

## 📥 **Installation Steps**

### **Step 1: Download iPXE Binaries**

#### **On Windows:**

```powershell
cd C:\Users\...\GGnet\infra\tftp
.\download-ipxe.ps1
```

#### **On Linux:**

```bash
cd /opt/ggnet/infra/tftp
chmod +x download-ipxe.sh
./download-ipxe.sh
```

**Expected output:**

```
========================================
 Downloading iPXE Binaries for GGnet
========================================

[CRITICAL] Downloading: snponly.efi
  Success: snponly.efi (1.2 MB)

[OPTIONAL] Downloading: ipxe.efi
  Success: ipxe.efi (1.2 MB)

[OPTIONAL] Downloading: undionly.kpxe
  Success: undionly.kpxe (90 KB)

========================================
 Download Summary
========================================
  Success: 5 files
  Failed: 0 files

✓ Minimum requirements met!
```

---

### **Step 2: Copy Files to TFTP Directory**

#### **Linux/Docker:**

```bash
# Copy to TFTP root
sudo cp infra/tftp/*.efi /var/lib/tftp/
sudo cp infra/tftp/*.kpxe /var/lib/tftp/
sudo cp infra/tftp/*.pxe /var/lib/tftp/

# Set permissions
sudo chmod 644 /var/lib/tftp/*
sudo chown tftp:tftp /var/lib/tftp/*
```

#### **Docker (via volume mount):**

```yaml
# docker-compose.yml
services:
  tftp:
    image: pghalliday/tftp
    volumes:
      - ./infra/tftp:/var/tftpboot
    ports:
      - "69:69/udp"
```

---

### **Step 3: Verify Files**

```bash
ls -lh /var/lib/tftp/

# Expected output:
-rw-r--r-- 1 tftp tftp 1.2M Oct 8 01:00 ipxe.efi
-rw-r--r-- 1 tftp tftp 1.2M Oct 8 01:00 snponly.efi
-rw-r--r-- 1 tftp tftp 1.1M Oct 8 01:00 ipxe32.efi
-rw-r--r-- 1 tftp tftp  90K Oct 8 01:00 undionly.kpxe
-rw-r--r-- 1 tftp tftp  85K Oct 8 01:00 undionly.pxe
```

---

## 🌐 **DHCP Configuration**

### **Update `docker/dhcp/dhcpd.conf`:**

GGnet's enhanced DHCP config automatically selects the correct boot file:

```conf
# Dynamic boot file selection
if option arch = 00:07 {
    # UEFI x64 (Windows 10/11)
    filename "snponly.efi";  # ⭐ SecureBoot-signed
} elsif option arch = 00:00 {
    # Legacy BIOS
    filename "undionly.kpxe";
}
```

**Configuration is already included!** Just verify:

```bash
# Check DHCP config
cat docker/dhcp/dhcpd.conf | grep -A5 "option arch"
```

### **Update Server IP:**

Edit line 33 in `docker/dhcp/dhcpd.conf`:

```conf
next-server 192.168.1.10;  # ⚠️ CHANGE THIS to your GGnet server IP!
```

Replace `192.168.1.10` with your actual server IP.

---

## 📡 **TFTP Configuration**

### **tftpd-hpa (Default):**

```bash
# Edit /etc/default/tftpd-hpa
sudo nano /etc/default/tftpd-hpa
```

```ini
TFTP_USERNAME="tftp"
TFTP_DIRECTORY="/var/lib/tftp"
TFTP_ADDRESS=":69"
TFTP_OPTIONS="--secure"
```

```bash
# Restart service
sudo systemctl restart tftpd-hpa
sudo systemctl status tftpd-hpa
```

### **dnsmasq (Alternative):**

```conf
# /etc/dnsmasq.conf
enable-tftp
tftp-root=/var/lib/tftp
tftp-no-blocksize
```

```bash
sudo systemctl restart dnsmasq
```

---

## 🧪 **Testing**

### **Test 1: TFTP File Access**

From another machine:

```bash
# Test TFTP download
tftp 192.168.1.10
> binary
> get snponly.efi
> quit

# Verify
ls -lh snponly.efi
# Should be ~1.2 MB
```

### **Test 2: DHCP PXE Boot**

Boot a client machine:

1. Enter BIOS/UEFI setup (usually F2, Del, F12)
2. **Enable SecureBoot**
3. **Enable Network Boot (PXE)**
4. Set boot order: Network first
5. Save and reboot

**Expected behavior:**

```
>> Start PXE over IPv4
   Station IP: 192.168.1.101
   Server IP: 192.168.1.10
   NBP filename: snponly.efi
   NBP filesize: 1234567 bytes

>> Downloading NBP file...

>> NBP file downloaded successfully

iPXE (http://ipxe.org) 
Features: DNS HTTP HTTPS iSCSI...

Press Ctrl-B for configuration...
```

### **Test 3: SecureBoot Verification**

In iPXE command line (press Ctrl-B):

```ipxe
iPXE> echo ${platform}
efi

iPXE> echo ${buildarch}
x86_64

iPXE> dhcp
OK

iPXE> sanboot iscsi:192.168.1.10::::0:iqn.2025-10.local.ggnet:test
```

If it boots Windows without errors, **SecureBoot is working!** ✅

---

## 🔍 **Troubleshooting**

### **Problem 1: "Security Boot Violation"**

**Symptoms:**
```
Security Violation

The system found an unauthorized change...
```

**Cause:** Using unsigned `ipxe.efi` instead of `snponly.efi`

**Solution:**
```bash
# Check DHCP log
sudo tail -f /var/log/syslog | grep dhcpd

# Should see:
# DHCPOFFER ... filename="snponly.efi"

# If seeing filename="ipxe.efi", update dhcpd.conf
```

---

### **Problem 2: "PXE-E11: ARP Timeout"**

**Cause:** TFTP server not responding

**Solution:**
```bash
# Check TFTP service
sudo systemctl status tftpd-hpa

# Test manually
tftp 192.168.1.10

# Check firewall
sudo ufw allow 69/udp
```

---

### **Problem 3: "PXE-E32: TFTP Open Timeout"**

**Cause:** File not found in TFTP directory

**Solution:**
```bash
# Verify files exist
ls -lh /var/lib/tftp/snponly.efi

# Check permissions
sudo chmod 644 /var/lib/tftp/snponly.efi
```

---

### **Problem 4: "iPXE Downloaded but Won't Boot"**

**Cause:** Corrupt download or wrong architecture

**Solution:**
```bash
# Re-download binaries
cd infra/tftp
rm *.efi *.kpxe
./download-ipxe.sh

# Verify checksums
sha256sum snponly.efi
# Compare with https://boot.ipxe.org/checksums.txt
```

---

### **Problem 5: "Boot Loops After iPXE Loads"**

**Cause:** iSCSI target not available or misconfigured

**Solution:**
```bash
# Check iPXE script URL in DHCP config
# Should point to: http://SERVER_IP:8000/boot/script.ipxe

# Test backend API
curl http://192.168.1.10:8000/api/health

# Check GGnet logs
docker-compose logs -f backend
```

---

## 📊 **Architecture Flow**

```
┌─────────────────────────────────────────────────┐
│  Client Machine (Windows 11, SecureBoot ON)    │
│                                                 │
│  1. UEFI Firmware                               │
│     ↓ Checks SecureBoot policy                 │
│  2. PXE ROM                                     │
│     ↓ Sends DHCP discover                      │
│  3. Receives DHCP offer                         │
│     - IP: 192.168.1.101                         │
│     - Next-server: 192.168.1.10                 │
│     - Filename: snponly.efi  ⭐                 │
│     ↓                                           │
│  4. TFTP downloads snponly.efi                  │
│     ↓ UEFI verifies Microsoft signature         │
│     ✅ Signature valid!                         │
│  5. Executes snponly.efi (iPXE)                 │
│     ↓ iPXE sends DHCP request (with user-class) │
│  6. Receives boot script URL                    │
│     - http://192.168.1.10:8000/boot/script.ipxe │
│     ↓                                           │
│  7. iPXE loads and executes boot script         │
│     ↓ Script connects to iSCSI target           │
│  8. sanboot iscsi://...                         │
│     ↓ Boots Windows 11 from iSCSI disk          │
│  9. ✅ Windows 11 running!                      │
└─────────────────────────────────────────────────┘
```

---

## 🔐 **Security Considerations**

### **What `snponly.efi` Protects:**

1. **Boot integrity:** Only Microsoft-signed code runs
2. **Firmware protection:** Prevents bootkit/rootkit attacks
3. **Trust chain:** UEFI → iPXE → OS (all verified)

### **What It Doesn't Protect:**

1. **Network security:** PXE boot is still unencrypted
2. **iSCSI security:** CHAP authentication recommended
3. **OS security:** Windows security policies still apply

### **Recommendations:**

```yaml
Security Best Practices:
  - Use isolated VLAN for PXE boot network
  - Enable iSCSI CHAP authentication
  - Use TLS for iPXE script downloads (https://)
  - Restrict TFTP to known MAC addresses
  - Monitor DHCP logs for unauthorized boots
```

---

## 📚 **References**

- iPXE SecureBoot: https://ipxe.org/appnote/uefi_secure_boot
- Microsoft SecureBoot: https://docs.microsoft.com/en-us/windows-hardware/design/device-experiences/oem-secure-boot
- UEFI Specification: https://uefi.org/specifications
- ggRock Package Analysis: `GGROCK_COMPARISON.md`

---

## ✅ **Verification Checklist**

- [ ] iPXE binaries downloaded
- [ ] Files copied to `/var/lib/tftp/`
- [ ] DHCP config updated with server IP
- [ ] DHCP service restarted
- [ ] TFTP service running
- [ ] Test client can download files via TFTP
- [ ] Client boots with SecureBoot enabled
- [ ] Windows 11 boots successfully

---

**Status:** 🎉 **SecureBoot support implemented and ready to test!**  
**Next:** Test with real Windows 11 client machine.

