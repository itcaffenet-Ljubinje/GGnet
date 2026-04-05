# VM Workflow

The VM workflow describes the lifecycle of virtual machines, from creation to deletion, including VM control operations.

## VM Lifecycle

### VM Creation Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant VM
    participant Images
    participant Libvirt
    participant ZFS

    User->>API: Create VM
    API->>VM: create_vm()
    VM->>VM: Validate Config
    VM->>Images: create_vm_clones()
    Images->>ZFS: zfs clone system_image@base
    ZFS-->>Images: system_clone
    Images->>ZFS: zfs clone game_image@base
    ZFS-->>Images: game_clone
    Images-->>VM: Clone paths
    VM->>VM: Generate domain XML
    VM->>Libvirt: domain.createXML()
    Libvirt->>Libvirt: Create VM
    Libvirt->>Libvirt: Setup VNC
    Libvirt-->>VM: VM created
    VM-->>API: VM created
    API-->>User: Success
```

### VM State Transitions

```mermaid
stateDiagram-v2
    [*] --> Created: Create VM
    Created --> Running: Start VM
    Running --> Stopped: Stop VM
    Stopped --> Running: Start VM
    Running --> Rebooted: Reboot VM
    Rebooted --> Running: Boot Complete
    Stopped --> Reset: Reset VM
    Reset --> Running: Start VM
    Stopped --> [*]: Delete VM
    Running --> [*]: Delete VM (force)
```

## VM Operations

### Start VM

```mermaid
sequenceDiagram
    participant User
    participant API
    participant VM
    participant Libvirt

    User->>API: Start VM
    API->>VM: start_vm()
    VM->>Libvirt: domain.create()
    Libvirt->>Libvirt: Start VM
    Libvirt-->>VM: VM started
    VM-->>API: Success
    API-->>User: VM started
```

### Stop VM

```mermaid
sequenceDiagram
    participant User
    participant API
    participant VM
    participant Libvirt

    User->>API: Stop VM
    API->>VM: stop_vm()
    VM->>Libvirt: domain.destroy()
    Libvirt->>Libvirt: Force stop VM
    Libvirt-->>VM: VM stopped
    VM-->>API: Success
    API-->>User: VM stopped
```

### Shutdown VM

```mermaid
sequenceDiagram
    participant User
    participant API
    participant VM
    participant Libvirt

    User->>API: Shutdown VM
    API->>VM: shutdown_vm()
    VM->>Libvirt: domain.shutdown()
    Libvirt->>Libvirt: Graceful shutdown
    Libvirt-->>VM: VM shutdown
    VM-->>API: Success
    API-->>User: VM shutdown
```

### Reset VM

```mermaid
sequenceDiagram
    participant User
    participant API
    participant VM
    participant Libvirt

    User->>API: Reset VM
    API->>VM: reset_vm()
    VM->>Libvirt: domain.destroy()
    Libvirt->>Libvirt: Stop VM
    Libvirt-->>VM: VM stopped
    VM->>Libvirt: domain.create()
    Libvirt->>Libvirt: Start VM
    Libvirt-->>VM: VM started
    VM-->>API: Success
    API-->>User: VM reset
```

## VM Control Operations

### VNC Setup Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant VM
    participant Libvirt
    participant VNC

    User->>API: Get VNC URL
    API->>VM: get_vnc_url()
    VM->>Libvirt: Get VNC config
    Libvirt-->>VM: VNC port/password
    VM->>VNC: Setup VNC server
    VNC-->>VM: VNC ready
    VM-->>API: VNC URL
    API-->>User: VNC URL
```

### VM Console Access

**VNC Connection:**
```
VNC Server: localhost:5900
VNC Password: generated_password
noVNC URL: ws://localhost:6080/vnc.html?host=localhost&port=5900
```

## VM Network Configuration

### Local Drives Mode

```mermaid
sequenceDiagram
    participant VM
    participant Libvirt
    participant ZFS

    VM->>Libvirt: Attach disk
    Libvirt->>ZFS: Mount /dev/zvol/pool0/ggnet2/clones/vm-001-system
    ZFS-->>Libvirt: Disk attached
    Libvirt-->>VM: Disk available
```

**Configuration:**
- Direct attachment of ZFS volumes
- Maximum performance
- No network overhead

### Network Mode

```mermaid
sequenceDiagram
    participant VM
    participant Libvirt
    participant iSCSI
    participant ZFS

    VM->>Libvirt: Attach disk
    Libvirt->>iSCSI: Connect to target
    iSCSI->>ZFS: Expose /dev/zvol/pool0/ggnet2/clones/vm-001-system
    ZFS-->>iSCSI: Target ready
    iSCSI-->>Libvirt: Disk attached
    Libvirt-->>VM: Disk available
```

**Configuration:**
- iSCSI target setup
- Network boot support
- Useful for troubleshooting

## VM Resource Management

### CPU Allocation

**vCPU Allocation:**
- Each vCPU consumes one CPU thread
- Minimum: 2 vCPUs (recommended)
- Maximum: Based on available CPU threads

### RAM Allocation

**RAM Allocation:**
- Minimum: 4GB (recommended)
- Maximum: 32GB per VM
- Global limit: Maximum Boot RAM Size

### Storage Allocation

**Storage Allocation:**
- Clones use copy-on-write
- Base image data is shared
- Only changes are stored separately

## VM Writeback Management

### Apply Writebacks Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant VM
    participant Images
    participant ZFS

    User->>API: Apply Writebacks
    API->>VM: apply_writebacks()
    VM->>Images: apply_writebacks()
    Images->>ZFS: zfs send writeback_snapshot
    ZFS-->>Images: Snapshot sent
    Images->>ZFS: zfs receive base_image
    ZFS-->>Images: Writebacks applied
    Images-->>VM: Writebacks applied
    VM-->>API: Success
    API-->>User: Writebacks applied
```

## VM Settings Management

### Update VM Settings

**Settings Update:**
- Name: Can be changed anytime
- System Image: Can be changed when VM is offline
- Game Image: Can be changed when VM is offline
- vCPUs: Can be changed when VM is offline
- RAM: Can be changed when VM is offline
- Boot Mode: Can be changed when VM is offline
- Drives Connection: Can be changed when VM is offline

## Development Notes

- VM creation requires ZFS clones
- libvirt manages VM lifecycle
- VNC provides console access
- Network mode uses iSCSI targets
- Writebacks enable change tracking

## To-Do

- [ ] Implement VM migration
- [ ] Add VM snapshots (libvirt)
- [ ] Implement VM templates
- [ ] Add VM resource monitoring
- [ ] Implement VM autostart
- [ ] Add VM backup/restore

