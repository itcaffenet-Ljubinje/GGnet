# System Overview

The ggnet2 system is a ZFS-based storage management platform for disk images and virtual/physical machine management.

## Architecture Diagram

```mermaid
graph TB
    subgraph "Frontend"
        UI[React Frontend]
        WS[WebSocket Client]
    end
    
    subgraph "Backend API"
        API[FastAPI Server]
        SR[SignalR Hub]
    end
    
    subgraph "Backend Modules"
        IMG[Images Module]
        VM[VM Module]
        MACH[Machines Module]
        STOR[Storage Module]
        NET[Network Module]
        CLIENT[Client Module]
    end
    
    subgraph "Storage Layer"
        ZFS[ZFS Pool]
        ZVOL[ZFS Volumes]
        SNAP[ZFS Snapshots]
        CLONE[ZFS Clones]
    end
    
    subgraph "Virtualization"
        LIBVIRT[libvirt]
        QEMU[QEMU/KVM]
        VNC[VNC/noVNC]
    end
    
    subgraph "Network Services"
        PXE[PXE Boot]
        DHCP[DNSMASQ DHCP]
        TFTP[TFTP Server]
        ISCSI[iSCSI Target]
    end
    
    subgraph "Windows Clients"
        WCLIENT[Windows Client]
        WSVC[Windows Service]
    end
    
    UI --> API
    WS --> SR
    API --> IMG
    API --> VM
    API --> MACH
    API --> STOR
    API --> NET
    API --> CLIENT
    SR --> CLIENT
    
    IMG --> ZFS
    VM --> IMG
    VM --> LIBVIRT
    MACH --> IMG
    MACH --> PXE
    STOR --> ZFS
    
    IMG --> ZVOL
    IMG --> SNAP
    IMG --> CLONE
    
    LIBVIRT --> QEMU
    VM --> VNC
    
    PXE --> DHCP
    PXE --> TFTP
    MACH --> ISCSI
    
    CLIENT --> WCLIENT
    WCLIENT --> WSVC
    WCLIENT --> SR
```

## System Components

### Frontend

- **React Application**: User interface for managing the system
- **WebSocket Client**: Real-time updates via WebSocket/SignalR
- **API Client**: HTTP requests to backend API

### Backend API

- **FastAPI Server**: REST API for system operations
- **SignalR Hub**: WebSocket hub for real-time communication
- **API Routes**: Endpoints for images, VMs, machines, storage, clients

### Backend Modules

- **Images Module**: Image management and ZFS operations
- **VM Module**: Virtual machine lifecycle management
- **Machines Module**: Physical machine management
- **Storage Module**: ZFS pool management and monitoring
- **Network Module**: PXE boot and network configuration
- **Client Module**: Windows client management

### Storage Layer

- **ZFS Pool**: Storage pool for images and clones
- **ZFS Volumes**: Block devices for images
- **ZFS Snapshots**: Point-in-time copies of images
- **ZFS Clones**: Copy-on-write clones for VMs/machines

### Virtualization

- **libvirt**: Virtualization management library
- **QEMU/KVM**: Hypervisor for virtual machines
- **VNC/noVNC**: Console access for VMs

### Network Services

- **PXE Boot**: Network boot server for physical machines
- **DHCP**: IP address allocation via dnsmasq
- **TFTP**: Boot file serving
- **iSCSI**: Block storage over network for machines

### Windows Clients

- **Windows Client**: Client application for physical machines
- **Windows Service**: Background service for client operations

## Data Flow

### Image Creation Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Images
    participant ZFS

    User->>Frontend: Create Image
    Frontend->>API: POST /api/images
    API->>Images: create_image()
    Images->>ZFS: zfs create -V size pool0/ggnet2/images/name
    ZFS-->>Images: Volume created
    Images->>Images: Create base snapshot
    Images->>ZFS: zfs snapshot @base
    ZFS-->>Images: Snapshot created
    Images-->>API: Image created
    API-->>Frontend: Success
    Frontend-->>User: Image created
```

### VM Creation Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant VM
    participant Images
    participant Libvirt
    participant ZFS

    User->>Frontend: Create VM
    Frontend->>API: POST /api/vms
    API->>VM: create_vm()
    VM->>Images: create_clone()
    Images->>ZFS: zfs clone snapshot clone_path
    ZFS-->>Images: Clone created
    Images-->>VM: Clone paths
    VM->>Libvirt: create_domain()
    Libvirt->>Libvirt: Generate domain XML
    Libvirt->>Libvirt: Create VM
    Libvirt-->>VM: VM created
    VM-->>API: VM created
    API-->>Frontend: Success
    Frontend-->>User: VM created
```

### Physical Machine Boot Flow

```mermaid
sequenceDiagram
    participant Machine
    participant DHCP
    participant TFTP
    participant iSCSI
    participant Server

    Machine->>DHCP: DHCP Discover
    DHCP->>Machine: DHCP Offer (IP + TFTP)
    Machine->>TFTP: Request pxelinux.0
    TFTP->>Machine: Send pxelinux.0
    Machine->>TFTP: Request config
    TFTP->>Machine: Send config
    Machine->>iSCSI: Connect to target
    iSCSI->>Machine: Serve disk image
    Machine->>Server: Boot complete, register
    Server->>Machine: Client registered
```

## Communication Patterns

### REST API

- **HTTP/HTTPS**: Standard REST API communication
- **JSON**: Request/response format
- **Authentication**: JWT tokens (future)

### WebSocket/SignalR

- **Real-time Updates**: Status updates, commands
- **Persistent Connection**: Maintains connection for real-time communication
- **Event-based**: Event-driven communication

### ZFS Operations

- **Command-line**: ZFS operations via subprocess
- **Parsing**: Parse ZFS command outputs
- **Error Handling**: Handle ZFS errors

## System Integration

### Images ↔ VMs

- VMs use clones from Images module
- Images module creates clones for VMs
- VM deletion cleans up clones

### Images ↔ Machines

- Physical machines use clones from Images module
- Images module creates clones for machines
- Machine deletion cleans up clones

### VMs ↔ libvirt

- VM module uses libvirt for VM operations
- libvirt manages QEMU/KVM instances
- VNC/noVNC provides console access

### Machines ↔ PXE

- Machines module configures PXE boot
- PXE boot uses iSCSI targets for disk images
- Network module manages PXE configuration

### Clients ↔ Server

- Windows clients connect via SignalR
- Server sends commands to clients
- Clients report status to server

## Development Notes

- System uses modular architecture for maintainability
- ZFS provides storage layer for images and clones
- libvirt manages virtualization layer
- PXE boot enables network boot for physical machines
- SignalR provides real-time communication

## To-Do

- [ ] Add system monitoring and metrics
- [ ] Implement system backup and recovery
- [ ] Add system health checks
- [ ] Implement system logging and auditing
- [ ] Add system performance optimization
- [ ] Implement system security hardening

