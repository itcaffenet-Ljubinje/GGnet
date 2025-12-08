# Installation Script

The main installation script (`install.sh`) automates the installation of ggnet2 on a Debian Linux server.

## Overview

The installation script:

- Installs system dependencies
- Sets up ZFS pool and datasets
- Configures PXE boot server
- Sets up Nginx reverse proxy
- Configures systemd services
- Installs Python dependencies

## Usage

```bash
# Run installation script
sudo bash install.sh

# Or make executable and run
chmod +x install.sh
sudo ./install.sh
```

## Script Structure

**install.sh:**
```bash
#!/bin/bash

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
POOL_NAME="pool0"
BASE_PATH="pool0/ggnet2"
IMAGES_PATH="pool0/ggnet2/images"
CLONES_PATH="pool0/ggnet2/clones"

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Main installation
main() {
    print_info "Starting ggnet2 installation..."
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        print_error "Please run as root (use sudo)"
        exit 1
    fi
    
    # Install dependencies
    print_info "Installing system dependencies..."
    bash scripts/requirements-debian.sh
    
    # Setup ZFS
    print_info "Setting up ZFS..."
    bash scripts/setup-zfs.sh
    
    # Setup PXE
    print_info "Setting up PXE boot server..."
    bash scripts/setup-pxe.sh
    
    # Setup Nginx
    print_info "Setting up Nginx..."
    bash scripts/setup-nginx.sh
    
    # Setup systemd services
    print_info "Setting up systemd services..."
    bash scripts/setup-systemd.sh
    
    # Install Python dependencies
    print_info "Installing Python dependencies..."
    pip3 install -r requirements.txt
    
    print_info "Installation complete!"
}

main "$@"
```

## Prerequisites

### System Requirements

- **OS**: Debian 11 (Bullseye) or Debian 12 (Bookworm)
- **Architecture**: x86_64
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: Minimum 100GB, recommended 500GB+
- **Network**: One or more network interfaces with IP addresses (auto-detected during installation)

**Note:** The installation script will automatically detect IP addresses on the server. If only one IP is detected, it will be used automatically. If multiple IPs are detected, you will be prompted to select one.

### Root Access

The installation script requires root privileges:

```bash
sudo bash install.sh
```

## Installation Steps

### 1. System Dependencies

Installs required Debian packages:

- ZFS packages (`zfs-dkms`, `zfsutils-linux`, `zfs-zed`)
- Python packages (`python3`, `python3-pip`, `python3-dev`)
- QEMU/KVM packages (`qemu-system-x86`, `libvirt-daemon`)
- Networking packages (`dnsmasq`, `network-manager`)
- Web server packages (`nginx`)
- Build tools (`build-essential`, `gcc`, `g++`)

### 2. Network Configuration

Configures network settings:

- **IP Address Detection**: Automatically detects all IP addresses on the server
- **IP Selection**: Auto-selects if only one IP, prompts if multiple
- **Bridge Network**: Optionally creates `vmbr0` bridge for virtual machines
- **IP Forwarding**: Enables IP forwarding for iSCSI routing
- **DNS Configuration**: Verifies DNS configuration, adds default if missing
- **dnsmasq Configuration**: Updates dnsmasq with selected IP address

**Bridge Network Creation:**
- If VMs are enabled, a bridge network (`vmbr0`) is created
- The physical network adapter is moved under the bridge
- Network service is restarted after bridge creation

### 3. ZFS Setup

Sets up ZFS pool and datasets:

- Creates ZFS pool (if not exists)
- Creates base dataset structure
- Creates images and clones datasets
- Configures ZFS properties

### 4. PXE Boot Setup

Configures PXE boot server:

- Sets up TFTP server
- Configures dnsmasq for DHCP/DNS (uses selected IP address)
- Sets up PXE boot files
- Configures iSCSI targets

### 5. Nginx Setup

Configures Nginx reverse proxy:

- Sets up Nginx configuration
- Configures SSL certificates (if available)
- Sets up reverse proxy for API
- Configures static file serving

### 6. Systemd Services

Sets up systemd services:

- Creates service files
- Enables services
- Starts services

### 7. Python Dependencies

Installs Python packages:

- FastAPI and related packages
- libvirt-python
- Other dependencies from `requirements.txt`

## Post-Installation

### Verify Installation

```bash
# Check ZFS pool
zpool status

# Check systemd services
systemctl status ggnet2-api
systemctl status ggnet2-toolchain

# Check Nginx
systemctl status nginx

# Check PXE boot
systemctl status tftpd-hpa
systemctl status dnsmasq
```

### Configure Settings

```bash
# Edit settings file
nano /etc/ggnet2/settings.json

# Or use API
curl -X PUT http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "pool_name": "pool0",
    "max_vm_ram": "32G",
    "pxe_enabled": true
  }'
```

## Troubleshooting

### Installation Fails

**Check Logs:**
```bash
# Check installation logs
tail -f /var/log/ggnet2/install.log

# Check systemd journal
journalctl -u ggnet2-api -f
```

### ZFS Pool Not Created

**Check ZFS:**
```bash
# Check ZFS module
lsmod | grep zfs

# Check ZFS pool
zpool list

# Check devices
lsblk
```

### Services Not Starting

**Check Service Status:**
```bash
# Check service status
systemctl status ggnet2-api

# Check service logs
journalctl -u ggnet2-api -n 50

# Restart service
systemctl restart ggnet2-api
```

## Development Notes

- Installation script uses `set -e` for error handling
- All operations are logged to `/var/log/ggnet2/install.log`
- Script is idempotent (can be run multiple times)
- Configuration files are created in `/etc/ggnet2/`
- Log files are created in `/var/log/ggnet2/`

## To-Do

- [ ] Add installation verification
- [ ] Implement rollback mechanism
- [ ] Add installation progress tracking
- [ ] Implement configuration validation
- [ ] Add installation logging
- [ ] Implement uninstallation script

