# 🧪 Phase 1 Testing Plan - SecureBoot & Windows Toolchain

Complete testing plan for validating Phase 1 implementation.

---

## 📋 **Test Overview**

**Objective:** Verify that GGnet can:
1. Boot Windows 11 with SecureBoot enabled via `snponly.efi`
2. Automatically configure Windows using registry toolchain
3. Support multiple client architectures (UEFI + BIOS)

**Duration:** ~2 hours  
**Requirements:** 
- GGnet server (running backend + DHCP + TFTP)
- Test client machine or VM
- Windows 11 installation media

---

## 🎯 **Test Categories**

1. [Infrastructure Tests](#infrastructure-tests) (No client needed)
2. [BIOS/Legacy Boot Tests](#bioslegacy-boot-tests)
3. [UEFI Boot Tests](#uefi-boot-tests)
4. [SecureBoot Tests](#secureboot-tests) 🔴 CRITICAL
5. [Windows Toolchain Tests](#windows-toolchain-tests)
6. [End-to-End Tests](#end-to-end-tests)

---

## 🔧 **Infrastructure Tests**

### **Test 1.1: iPXE Binaries Downloaded**

**Steps:**
```powershell
cd C:\Users\...\GGnet\infra\tftp
.\download-ipxe.ps1
```

**Expected:**
```
✓ snponly.efi (1.2 MB)
✓ ipxe.efi (1.2 MB)
✓ ipxe32.efi (1.1 MB)
✓ undionly.kpxe (90 KB)
✓ undionly.pxe (85 KB)

✅ All checks passed!
```

**Pass Criteria:** All 5 files downloaded successfully

---

### **Test 1.2: TFTP Server Responding**

**Steps:**
```bash
# From another machine on same network
tftp 192.168.1.10
> binary
> get snponly.efi
> quit

ls -lh snponly.efi
```

**Expected:** File downloaded, size ~1.2 MB

**Pass Criteria:** TFTP download successful

---

### **Test 1.3: DHCP Configuration Valid**

**Steps:**
```bash
# Check DHCP config syntax
sudo dhcpd -t -cf docker/dhcp/dhcpd.conf
```

**Expected:**
```
Internet Systems Consortium DHCP Server 4.4.1
Copyright 2004-2018 Internet Systems Consortium.
All rights reserved.
Configuration file: docker/dhcp/dhcpd.conf
Configuration syntax valid
```

**Pass Criteria:** No syntax errors

---

## 💾 **BIOS/Legacy Boot Tests**

### **Test 2.1: Legacy BIOS Client Boots**

**Setup:**
- VM or physical machine with Legacy BIOS mode
- Network boot (PXE) enabled
- Boot order: Network first

**Steps:**
1. Power on machine
2. Observe boot process
3. Press Ctrl+B when iPXE loads
4. Type `dhcp` and press Enter

**Expected:**
```
>> Start PXE over IPv4
>> Downloading NBP file...
>> NBP filename: undionly.kpxe

iPXE (http://ipxe.org) ...
Features: DNS HTTP HTTPS iSCSI...

iPXE> dhcp
Configuring (net0 00:11:22:33:44:55)....... ok
iPXE> echo ${platform}
pcbios
```

**Pass Criteria:**
- ✅ `undionly.kpxe` downloaded
- ✅ iPXE loads successfully
- ✅ `${platform}` shows `pcbios`

---

## 🖥️ **UEFI Boot Tests**

### **Test 3.1: UEFI x64 Client Boots (SecureBoot OFF)**

**Setup:**
- VM or physical machine with UEFI mode
- **SecureBoot DISABLED**
- Network boot enabled

**Steps:**
1. Enter BIOS/UEFI setup
2. Disable SecureBoot
3. Enable Network Boot
4. Save and reboot

**Expected:**
```
>> Start PXE over IPv4
>> NBP filename: snponly.efi (or ipxe.efi if DHCP configured that way)

iPXE (http://ipxe.org) ...
iPXE> dhcp
OK
iPXE> echo ${platform}
efi
iPXE> echo ${buildarch}
x86_64
```

**Pass Criteria:**
- ✅ `snponly.efi` or `ipxe.efi` downloaded
- ✅ iPXE loads successfully
- ✅ `${platform}` shows `efi`

---

## 🔐 **SecureBoot Tests** 🔴 CRITICAL

### **Test 4.1: SecureBoot Enabled - Boot with snponly.efi**

**Setup:**
- UEFI machine with TPM 2.0
- **SecureBoot ENABLED** in BIOS
- Windows 11 compatible hardware

**Steps:**
1. Enter BIOS/UEFI setup
2. **Enable SecureBoot**
3. Verify SecureBoot status: `Enabled`
4. Enable Network Boot
5. Save and reboot

**Expected:**
```
>> Start PXE over IPv4
>> DHCP offer received
>> NBP filename: snponly.efi
>> Downloading NBP file...
>> Verifying signature...
>> ✅ Signature valid (Microsoft UEFI CA)
>> Executing NBP...

iPXE (http://ipxe.org) 
iPXE> dhcp
OK
```

**Pass Criteria:**
- ✅ `snponly.efi` downloaded
- ✅ **NO** "Security Boot Violation" error
- ✅ iPXE loads successfully
- ✅ No firmware errors

**If Test FAILS:**

```
❌ Security Violation

The system found an unauthorized change on the firmware,
operating system or UEFI driver.

Press [OK] to run the next boot device...
```

**Troubleshooting:**
1. Check DHCP log: `sudo tail -f /var/log/syslog | grep dhcpd`
2. Verify filename served: Should be `snponly.efi`, **NOT** `ipxe.efi`
3. Re-download `snponly.efi` (might be corrupt)
4. Verify TFTP file exists: `ls -lh /var/lib/tftp/snponly.efi`

---

### **Test 4.2: SecureBoot - Boot Windows 11**

**Setup:**
- Same as Test 4.1
- Windows 11 image uploaded to GGnet
- iSCSI target created
- Machine configured in GGnet

**Steps:**
1. Boot via iPXE (SecureBoot enabled)
2. iPXE connects to iSCSI target
3. Windows 11 boots

**Expected:**
```
iPXE> dhcp
OK
iPXE> sanboot iscsi:192.168.1.10::::0:iqn.2025-10.local.ggnet:machine-01
Connecting to 192.168.1.10...
[Boot Windows 11]

Windows 11 logo appears...
```

**Pass Criteria:**
- ✅ iSCSI connection successful
- ✅ Windows 11 boots without errors
- ✅ No "SecureBoot violation" during Windows boot
- ✅ Windows shows SecureBoot enabled in Settings

**Verify Windows SecureBoot Status:**

```powershell
# In Windows, run PowerShell as Admin:
Confirm-SecureBootUEFI
# Should return: True
```

---

## 🪟 **Windows Toolchain Tests**

### **Test 5.1: Manual Registry Application**

**Setup:**
- Windows 11 VM (not necessarily diskless)

**Steps:**
```powershell
# Copy registry scripts to VM
cd C:\temp\ggnet\infra\windows-scripts

# Apply all
.\apply-all.bat

# Wait for restart

# After restart, verify:
```

**Verification:**

1. **UAC Disabled:**
   ```powershell
   # Should be 0
   Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name EnableLUA
   ```

2. **Auto-Login Configured:**
   ```powershell
   Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" -Name AutoAdminLogon
   # Should be "1"
   ```

3. **RDP Enabled:**
   ```powershell
   Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" -Name fDenyTSConnections
   # Should be 0
   ```

4. **Environment Variables Set:**
   ```powershell
   $env:GGNET_SERVER
   # Should show server IP (if template was filled)
   ```

**Pass Criteria:** All registry values set correctly

---

### **Test 5.2: Template Generation (Backend)**

**Steps:**
```bash
# Test backend registry generation endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/machines/1/registry-pack \
  -o registry-pack.zip

# Extract
unzip registry-pack.zip

# Inspect generated files
cat 03-enable-autologon.reg
cat 04-rename-computer.reg
cat 06-inject-environment-vars.reg
```

**Expected:**
- All template variables replaced
- No `{VARIABLE}` placeholders left
- Valid registry syntax

**Pass Criteria:** Templates correctly generated

---

### **Test 5.3: Automated Application (Startup Script)**

**Setup:**
- Windows 11 diskless client
- Startup script configured
- GGnet backend running

**Steps:**
1. Boot Windows 11 diskless client
2. Startup script runs automatically
3. Downloads registry pack from server
4. Applies all registry files
5. Restarts

**Expected:**
```batch
GGnet Configuration
===================
Downloading registry pack...
[OK] Downloaded 9 files
Applying registry tweaks...
[OK] 01-disable-uac.reg applied
[OK] 02-disable-firewall.reg applied
...
[OK] 09-disable-telemetry.reg applied

Restarting in 10 seconds...
```

**Pass Criteria:**
- ✅ Script runs automatically
- ✅ All registry files applied
- ✅ Restart happens
- ✅ Second boot: auto-login works

---

## 🔄 **End-to-End Tests**

### **Test 6.1: Complete Diskless Boot Flow**

**Full stack test:**

**Setup:**
- Physical machine or VM
- UEFI + SecureBoot enabled
- TPM 2.0
- Network boot enabled
- No local disk (diskless!)

**Steps:**
1. Power on machine
2. PXE boot starts
3. Downloads `snponly.efi` via TFTP
4. iPXE loads (SecureBoot verified)
5. iPXE downloads boot script via HTTP
6. Connects to iSCSI target
7. Boots Windows 11 from iSCSI
8. Startup script applies registry config
9. Windows restarts
10. Auto-login works
11. Fully configured Windows 11 session

**Expected Timeline:**
```
[00:00] Power on
[00:05] PXE boot starts
[00:10] iPXE loaded
[00:15] iSCSI connected
[00:20] Windows boot
[01:00] Windows first login screen (if not configured)
[01:30] Registry config applied
[01:35] Restart
[02:00] Auto-login
[02:10] Windows desktop ready
```

**Pass Criteria:**
- ✅ No manual intervention needed
- ✅ SecureBoot stays enabled throughout
- ✅ Windows boots successfully
- ✅ Configuration applied automatically
- ✅ Auto-login works on second boot

---

### **Test 6.2: Multi-Architecture Support**

**Test with 3 different client types:**

| Client Type | Architecture | Boot File | Expected Result |
|-------------|--------------|-----------|-----------------|
| Old PC (2015) | Legacy BIOS | `undionly.kpxe` | ✅ Boots |
| Gaming PC (2020) | UEFI x64 | `snponly.efi` | ✅ Boots |
| Windows 11 PC (2024) | UEFI + SecureBoot | `snponly.efi` | ✅ Boots |

**Pass Criteria:** All 3 client types boot successfully

---

## 📊 **Test Results Template**

```markdown
# Phase 1 Testing Results

**Date:** 2025-10-08  
**Tester:** [Your Name]  
**Environment:** [Production / Test / VM]

## Infrastructure Tests

- [x] Test 1.1: iPXE Binaries Downloaded - ✅ PASS
- [x] Test 1.2: TFTP Server Responding - ✅ PASS
- [x] Test 1.3: DHCP Configuration Valid - ✅ PASS

## BIOS/Legacy Boot Tests

- [x] Test 2.1: Legacy BIOS Client Boots - ✅ PASS

## UEFI Boot Tests

- [x] Test 3.1: UEFI x64 Client Boots - ✅ PASS

## SecureBoot Tests 🔴 CRITICAL

- [ ] Test 4.1: SecureBoot Enabled - Boot with snponly.efi - ⏳ PENDING
- [ ] Test 4.2: SecureBoot - Boot Windows 11 - ⏳ PENDING

## Windows Toolchain Tests

- [x] Test 5.1: Manual Registry Application - ✅ PASS
- [ ] Test 5.2: Template Generation (Backend) - ⏳ PENDING
- [ ] Test 5.3: Automated Application (Startup Script) - ⏳ PENDING

## End-to-End Tests

- [ ] Test 6.1: Complete Diskless Boot Flow - ⏳ PENDING
- [ ] Test 6.2: Multi-Architecture Support - ⏳ PENDING

## Issues Found

[List any issues discovered during testing]

## Recommendations

[Any recommendations for improvements]

## Conclusion

**Overall Status:** ⏳ IN PROGRESS  
**Blockers:** [List blockers]  
**Next Steps:** [What needs to be done next]
```

---

## 🚨 **Known Limitations**

### **Test 4.1 & 4.2 (SecureBoot):**

**Limitation:** Requires physical hardware or VM with proper SecureBoot support.

**VMs with SecureBoot:**
- ✅ **Hyper-V (Gen 2)** - Full SecureBoot support
- ✅ **VMware Workstation/ESXi** - UEFI + SecureBoot
- ⚠️ **VirtualBox** - Limited SecureBoot (v7.0+)
- ❌ **QEMU/KVM** - SecureBoot complex to setup

**Workaround for Local Testing:**

```bash
# Test without SecureBoot first
# Verify iPXE loads and iSCSI connects
# Then test on real hardware with SecureBoot
```

---

## ✅ **Phase 1 Completion Criteria**

To mark Phase 1 as **COMPLETE**, all of the following must pass:

- [x] Infrastructure tests (1.1, 1.2, 1.3)
- [x] BIOS boot test (2.1)
- [x] UEFI boot test (3.1)
- [ ] **SecureBoot test with snponly.efi (4.1)** 🔴 CRITICAL
- [ ] **SecureBoot + Windows 11 boot (4.2)** 🔴 CRITICAL
- [x] Manual registry application (5.1)
- [ ] Backend template generation (5.2)
- [ ] Automated registry application (5.3)
- [ ] Complete end-to-end flow (6.1)
- [ ] Multi-architecture support (6.2)

**Minimum for Production:**
- Tests 4.1, 4.2, 5.3, 6.1 **MUST** pass
- Others are recommended but not blocking

---

## 📝 **Testing Notes**

### **For SecureBoot Testing:**

1. **Use Real Hardware:** VMs may not fully support SecureBoot
2. **Check BIOS Version:** Update to latest for best compatibility
3. **TPM 2.0:** Required for Windows 11
4. **Verify Signature:** `snponly.efi` must be from official iPXE repo

### **For Windows Toolchain Testing:**

1. **Backup Image:** Before testing, backup Windows image
2. **Test VM First:** Test registry scripts on VM before production
3. **Monitor Logs:** Check GGnet backend logs for errors
4. **Gradual Rollout:** Test one registry script at a time

---

## 🎯 **Success Metrics**

**Phase 1 is successful if:**

- ✅ Windows 11 boots with SecureBoot enabled
- ✅ No manual BIOS configuration needed
- ✅ Windows configuration fully automated
- ✅ Boot time < 3 minutes (from power on to desktop)
- ✅ Works with multiple client types
- ✅ Zero manual intervention needed

**Target:** 100% automated diskless boot with SecureBoot

---

**Status:** 📋 **Test plan ready - awaiting hardware for SecureBoot testing**  
**Next:** Execute tests and document results

