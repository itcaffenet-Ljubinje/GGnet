# PXE Boot Sequence

The PXE boot sequence describes how physical machines boot from the network using PXE boot and iSCSI.

## PXE Boot Process

### Complete Boot Sequence

```mermaid
sequenceDiagram
    participant Machine
    participant DHCP
    participant TFTP
    participant iSCSI
    participant Server

    Machine->>DHCP: DHCP Discover (broadcast)
    DHCP->>Machine: DHCP Offer (IP: 192.168.1.100, TFTP: 192.168.1.10)
    Machine->>Machine: DHCP Request
    DHCP->>Machine: DHCP ACK
    
    Machine->>TFTP: Request pxelinux.0
    TFTP->>Machine: Send pxelinux.0
    Machine->>TFTP: Request menu.c32
    TFTP->>Machine: Send menu.c32
    Machine->>TFTP: Request config (01-00-11-22-33-44-55)
    TFTP->>Machine: Send config file
    
    Machine->>iSCSI: Connect to target
    iSCSI->>Machine: Target ready
    Machine->>iSCSI: Login to target
    iSCSI->>Machine: Disk available
    
    Machine->>Machine: Boot from disk
    Machine->>Server: Boot complete, register
    Server->>Machine: Client registered
```

## DHCP Configuration

### DHCP Discover

**Machine Request:**
```
DHCP Discover (broadcast)
- Client MAC: 00:11:22:33:44:55
- Client ID: 00:11:22:33:44:55
```

**DHCP Server Response:**
```
DHCP Offer
- IP Address: 192.168.1.100
- Subnet Mask: 255.255.255.0
- Gateway: 192.168.1.1
- DNS Server: 192.168.1.1
- TFTP Server: 192.168.1.10
- Boot File: pxelinux.0
```

### DHCP Configuration

**dnsmasq Configuration:**
```
dhcp-range=192.168.1.100,192.168.1.200,12h
dhcp-option=option:router,192.168.1.1
dhcp-option=option:dns-server,192.168.1.1
dhcp-boot=pxelinux.0
enable-tftp
tftp-root=/tftpboot
```

## TFTP Configuration

### PXE Boot Files

**TFTP Root Structure:**
```
/tftpboot/
├── pxelinux.0              # PXE bootloader
├── menu.c32                # Menu system
├── memdisk                 # Memory disk loader
└── pxelinux.cfg/
    ├── default             # Default boot config
    └── 01-00-11-22-33-44-55  # Machine-specific config
```

### PXE Configuration File

**Machine-Specific Config:**
```
default win11
prompt 0
timeout 10

label win11
    kernel memdisk
    append initrd=win11.img raw
    ipappend 2
```

**MAC Address Format:**
- MAC: `00:11:22:33:44:55`
- Config file: `01-00-11-22-33-44-55` (prefixed with `01-`)

## iSCSI Target Setup

### iSCSI Target Configuration

**Target Creation:**
```bash
# Create iSCSI target
targetcli /backstores/block create name=machine-001-system \
  dev=/dev/zvol/pool0/ggnet2/clones/machine-001-system

# Create iSCSI target IQN
targetcli /iscsi create iqn.2024-01.ggnet2:machine-001

# Create LUN
targetcli /iscsi/iqn.2024-01.ggnet2:machine-001/tpg1/luns \
  create /backstores/block/machine-001-system
```

### iSCSI Connection

**Machine Connection:**
```
iSCSI Target: iqn.2024-01.ggnet2:machine-001
iSCSI Portal: 192.168.1.10:3260
LUN: 0
```

## Boot Sequence Details

### Phase 1: Network Discovery

```mermaid
sequenceDiagram
    participant Machine
    participant DHCP

    Machine->>Machine: Power On
    Machine->>Machine: Initialize Network
    Machine->>DHCP: DHCP Discover (broadcast)
    DHCP->>Machine: DHCP Offer
    Machine->>DHCP: DHCP Request
    DHCP->>Machine: DHCP ACK
    Machine->>Machine: Configure Network
```

### Phase 2: PXE Bootloader

```mermaid
sequenceDiagram
    participant Machine
    participant TFTP

    Machine->>TFTP: Request pxelinux.0
    TFTP->>Machine: Send pxelinux.0
    Machine->>Machine: Load pxelinux.0
    Machine->>TFTP: Request menu.c32
    TFTP->>Machine: Send menu.c32
    Machine->>Machine: Load menu.c32
```

### Phase 3: Boot Configuration

```mermaid
sequenceDiagram
    participant Machine
    participant TFTP

    Machine->>TFTP: Request config (MAC-based)
    TFTP->>Machine: Send config file
    Machine->>Machine: Parse config
    Machine->>Machine: Display boot menu
    Machine->>Machine: Select boot option
```

### Phase 4: iSCSI Connection

```mermaid
sequenceDiagram
    participant Machine
    participant iSCSI

    Machine->>iSCSI: Discover targets
    iSCSI->>Machine: Target list
    Machine->>iSCSI: Connect to target
    iSCSI->>Machine: Target connected
    Machine->>iSCSI: Login to target
    iSCSI->>Machine: LUN available
    Machine->>Machine: Mount disk
```

### Phase 5: OS Boot

```mermaid
sequenceDiagram
    participant Machine
    participant Server

    Machine->>Machine: Load OS from disk
    Machine->>Machine: Initialize OS
    Machine->>Server: Boot complete
    Machine->>Server: Register client
    Server->>Machine: Client registered
    Machine->>Server: Send status updates
```

## Client Registration

### Registration Flow

```mermaid
sequenceDiagram
    participant Machine
    participant Client
    participant Server

    Machine->>Machine: Boot complete
    Machine->>Client: Start Windows Client
    Client->>Server: Connect to SignalR
    Server->>Client: Connection established
    Client->>Server: Register client
    Server->>Server: Store client info
    Server->>Client: Registration confirmed
    Client->>Server: Send status updates
```

## Boot Configuration

### Machine-Specific Configuration

**PXE Config Generation:**
```python
# Generate PXE config for machine
pxe_config = f"""
default {system_image}
prompt 0
timeout 10

label {system_image}
    kernel memdisk
    append initrd={system_image}.img raw
    ipappend 2
"""

# Save to TFTP root
config_path = f"/tftpboot/pxelinux.cfg/01-{mac_address.replace(':', '-')}"
with open(config_path, 'w') as f:
    f.write(pxe_config)
```

## Troubleshooting

### Boot Fails at DHCP

**Check DHCP:**
```bash
# Check dnsmasq status
systemctl status dnsmasq

# Check DHCP leases
cat /var/lib/dhcp/dhcpd.leases

# Check network connectivity
ping machine_ip
```

### Boot Fails at TFTP

**Check TFTP:**
```bash
# Check TFTP server
systemctl status tftpd-hpa

# Check TFTP files
ls -la /tftpboot/

# Test TFTP
tftp localhost
get pxelinux.0
```

### Boot Fails at iSCSI

**Check iSCSI:**
```bash
# Check iSCSI target
systemctl status target

# List iSCSI targets
targetcli ls

# Check iSCSI connections
iscsiadm -m session
```

## Development Notes

- PXE boot requires network connectivity
- DHCP provides IP and TFTP server address
- TFTP serves boot files
- iSCSI provides disk images
- Client registration completes boot process

## To-Do

- [ ] Add PXE boot menu customization
- [ ] Implement DHCP reservations
- [ ] Add network boot image support
- [ ] Implement iSCSI target automation
- [ ] Add boot logging
- [ ] Implement boot monitoring

