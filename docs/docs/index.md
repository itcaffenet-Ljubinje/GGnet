# ggnet2 Documentation

Welcome to the ggnet2 documentation. This documentation provides a comprehensive guide to the ggnet2 ZFS-based storage management system.

## Overview

ggnet2 is a ZFS-based storage management system for disk image and storage management, featuring:

- **ZFS Integration**: Advanced ZFS pool and dataset management with snapshot/clone capabilities
- **Image Management**: System and Game image creation, cloning, and snapshot management
- **Virtual Machines**: QEMU/KVM-based VM management with web-based console access
- **Physical Machines**: PXE boot support for physical client machines
- **Windows Client**: Real-time communication between Windows clients and server via SignalR
- **Web Interface**: Modern React-based frontend with real-time updates

## Documentation Structure

### Backend Documentation

- [Backend Overview](backend/overview.md) - Backend architecture and module organization
- [API Documentation](backend/api.md) - REST API endpoints and WebSocket/SignalR hubs
- [Images Module](backend/images.md) - Image management and ZFS operations
- [Virtual Machines](backend/vms.md) - VM lifecycle management via QEMU/libvirt
- [Physical Machines](backend/machines.md) - Physical machine management and PXE boot
- [Storage Management](backend/storage.md) - ZFS pool management, monitoring, and TRIM
- [Network Configuration](backend/network.md) - PXE boot, dnsmasq, and network setup
- [Client Management](backend/clients.md) - Windows client operations and registry management
- [Utilities](backend/utils.md) - Shared utilities and helpers
- [Configuration](backend/config.md) - Configuration management and settings
- [CLI Tool](backend/cli.md) - Command-line interface

### Frontend Documentation

- [Frontend Overview](frontend/overview.md) - Frontend architecture and technology stack
- [Components](frontend/components.md) - React component structure and organization
- [Services](frontend/services.md) - API service layer and data fetching
- [WebSocket Integration](frontend/websocket.md) - Real-time updates via WebSocket/SignalR
- [Routing](frontend/routing.md) - Frontend routing and navigation

### Windows Client Documentation

- [Windows Client Overview](windows_client/overview.md) - Windows client architecture
- [.NET Client](windows_client/dotnet_client.md) - .NET 6.0/8.0 Windows Service implementation
- [Python Client](windows_client/python_client.md) - Alternative Python implementation
- [Deployment](windows_client/deployment.md) - Windows client deployment and configuration

### Scripts Documentation

- [Installation Script](scripts/install.md) - Main installation script for Debian server
- [ZFS Setup](scripts/setup_zfs.md) - ZFS pool and dataset initialization
- [iPXE Setup](scripts/setup_pxe.md) - iPXE boot server configuration (Windows 11 UEFI Secure Boot support)
- [Nginx Setup](scripts/setup_nginx.md) - Web server and reverse proxy configuration (SSL, VNC, Grafana, Prometheus)
- [Systemd Setup](scripts/setup_systemd.md) - Systemd service configuration (backend API and VNC/WebSocket)
- [SSL Setup](scripts/setup_ssl.md) - SSL certificate management (self-signed certificate generation)
- [Prometheus Setup](scripts/setup_prometheus.md) - Prometheus monitoring setup (metrics collection and visualization)
- [Grafana Setup](scripts/setup_grafana.md) - Grafana monitoring setup (sub-path serving, JWT auth, dashboards)
- [Client Deployment](scripts/deploy_clients.md) - Windows client deployment automation

### Architecture Documentation

- [System Overview](architecture/system_overview.md) - High-level system architecture
- [API Workflow](architecture/api_workflow.md) - Request/response flow and authentication
- [ZFS Workflow](architecture/zfs_flow.md) - ZFS operations and image management flow
- [VM Workflow](architecture/vm_workflow.md) - Virtual machine lifecycle and operations
- [PXE Boot Sequence](architecture/pxe_boot_sequence.md) - PXE boot process and client initialization

## Quick Start

1. **Installation**: See [Installation Script](scripts/install.md) for Debian server setup
2. **Backend Setup**: Configure ZFS pools and datasets - see [Storage Management](backend/storage.md)
3. **Frontend Setup**: Start the React development server - see [Frontend Overview](frontend/overview.md)
4. **Client Deployment**: Deploy Windows clients - see [Windows Client Deployment](windows_client/deployment.md)

## Technology Stack

### Backend
- **Python 3.10+**: Core language
- **FastAPI**: REST API framework
- **libvirt-python**: QEMU/KVM virtualization
- **ZFS**: Storage management

### Frontend
- **React 18+**: UI framework
- **Vite**: Build tool
- **WebSocket/SignalR**: Real-time communication

### Windows Client
- **.NET 6.0/8.0**: Primary implementation
- **Python 3.10+**: Alternative implementation
- **SignalR Client**: Real-time communication

## Development Notes

- All documentation is maintained in Markdown format
- Diagrams use Mermaid syntax for easy rendering
- Cross-references use relative paths within the `/docs` folder
- Each module documentation includes architecture notes and workflows

## To-Do

- [ ] Add API authentication documentation
- [ ] Add troubleshooting guides for common issues
- [ ] Add performance tuning guides
- [ ] Add deployment best practices
- [ ] Add security considerations

