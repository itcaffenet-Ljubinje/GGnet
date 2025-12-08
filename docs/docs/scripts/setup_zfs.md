# ZFS Setup Script

The ZFS setup script (`setup-zfs.sh`) configures ZFS pool and datasets for ggnet2.

## Overview

The ZFS setup script:

- **Optionally** creates ZFS pool (if not exists) - Pool can also be created later via web interface
- Creates base dataset structure
- Creates images and clones datasets
- Configures ZFS properties (compression, blocksize, etc.)

## Pool Creation Strategy

**You have two options for creating the ZFS pool:**

1. **During Installation** (via setup script): Run `setup-zfs.sh` which will create the pool if it doesn't exist
2. **Via Web Interface** (after installation): Use the web UI to create and configure the pool with more control

**Recommendation:** If you want more control over pool configuration (topology, devices selection), use the web interface. The setup script is suitable for quick automated installations.

## Usage

```bash
# Run ZFS setup script
sudo bash scripts/setup-zfs.sh

# Or with custom pool name
POOL_NAME="mypool" bash scripts/setup-zfs.sh
```

## Script Structure

**setup-zfs.sh:**
```bash
#!/bin/bash

set -e

# Configuration
POOL_NAME="${POOL_NAME:-pool0}"
BASE_PATH="${POOL_NAME}/ggnet2"
IMAGES_PATH="${BASE_PATH}/images"
CLONES_PATH="${BASE_PATH}/clones"

# Functions
print_info() {
    echo "[INFO] $1"
}

print_error() {
    echo "[ERROR] $1" >&2
}

# Check if pool exists
check_pool() {
    if zpool list "$POOL_NAME" &>/dev/null; then
        print_info "Pool $POOL_NAME already exists"
        return 0
    else
        return 1
    fi
}

# Create pool
create_pool() {
    print_info "Creating ZFS pool: $POOL_NAME"
    
    # Find available devices
    devices=$(lsblk -dno NAME,TYPE | grep disk | awk '{print "/dev/"$1}')
    
    if [ -z "$devices" ]; then
        print_error "No available devices found"
        exit 1
    fi
    
    # Create pool (stripe by default)
    zpool create -f "$POOL_NAME" $devices
    
    print_info "Pool $POOL_NAME created"
}

# Create datasets
create_datasets() {
    print_info "Creating datasets..."
    
    # Create base dataset
    zfs create -p "$BASE_PATH"
    
    # Create images dataset
    zfs create -p "$IMAGES_PATH"
    zfs set compression=lz4 "$IMAGES_PATH"
    zfs set mountpoint=none "$IMAGES_PATH"
    
    # Create clones dataset
    zfs create -p "$CLONES_PATH"
    zfs set compression=lz4 "$CLONES_PATH"
    zfs set mountpoint=none "$CLONES_PATH"
    
    print_info "Datasets created"
}

# Configure pool properties
configure_pool() {
    print_info "Configuring pool properties..."
    
    # Enable autotrim (for SSDs)
    zpool set autotrim=on "$POOL_NAME"
    
    # Set compression
    zpool set compression=lz4 "$POOL_NAME"
    
    print_info "Pool properties configured"
}

# Main
main() {
    print_info "Starting ZFS setup..."
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        print_error "Please run as root (use sudo)"
        exit 1
    fi
    
    # Check if pool exists
    if ! check_pool; then
        print_info "Pool $POOL_NAME does not exist"
        print_info "You can either:"
        print_info "  1. Let this script create it (automatic)"
        print_info "  2. Create it later via web interface (recommended for production)"
        read -p "Create pool now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            create_pool
        else
            print_info "Skipping pool creation. You can create it later via web interface."
            print_info "Note: Datasets will be created when pool is available."
            exit 0
        fi
    fi
    
    # Create datasets
    create_datasets
    
    # Configure pool
    configure_pool
    
    print_info "ZFS setup complete!"
}

main "$@"
```

## Configuration

### Pool Configuration

**Pool Name:**
- Default: `pool0`
- Can be customized via `POOL_NAME` environment variable

**Pool Type:**
- Default: Stripe (concatenation)
- Can be configured for mirror, raidz, etc.

### Dataset Structure

```
pool0/ggnet2/
├── images/          # Image datasets
└── clones/          # Clone datasets
```

### ZFS Properties

**Images Dataset:**
- `compression=lz4`: Fast compression
- `mountpoint=none`: No mountpoint (zvol)

**Clones Dataset:**
- `compression=lz4`: Fast compression
- `mountpoint=none`: No mountpoint (zvol)

**Pool Properties:**
- `autotrim=on`: Enable autotrim for SSDs
- `compression=lz4`: Enable compression

## Verification

### Check Pool Status

```bash
# Check pool status
zpool status "$POOL_NAME"

# Check pool list
zpool list

# Check pool properties
zpool get all "$POOL_NAME"
```

### Check Datasets

```bash
# List datasets
zfs list -r "$BASE_PATH"

# Check dataset properties
zfs get all "$IMAGES_PATH"
zfs get all "$CLONES_PATH"
```

## Troubleshooting

### Pool Creation Fails

**Check Devices:**
```bash
# List available devices
lsblk

# Check device status
fdisk -l
```

**Check ZFS Module:**
```bash
# Check if ZFS module is loaded
lsmod | grep zfs

# Load ZFS module
modprobe zfs
```

### Dataset Creation Fails

**Check Pool Status:**
```bash
# Check pool status
zpool status "$POOL_NAME"

# Check pool health
zpool list -v "$POOL_NAME"
```

## ZFS zpool.d Configuration

### Custom lsblk Script

ZFS uses scripts in `/etc/zfs/zpool.d/` to customize output for `zpool status` and related commands. ggnet2 includes a custom `ggnet2-lsblk` script that provides formatted output for disk information.

**Script Location:**
- Source: `/usr/lib/ggnet2/zpool.d/ggnet2-lsblk`
- Link: `/etc/zfs/zpool.d/ggnet2-lsblk` (symlink to source)

**Setup:**
```bash
# Create zpool.d directory if it doesn't exist
mkdir -p /etc/zfs/zpool.d

# Create source directory
mkdir -p /usr/lib/ggnet2/zpool.d

# Create custom lsblk script
cat > /usr/lib/ggnet2/zpool.d/ggnet2-lsblk <<'EOF'
#!/bin/bash
# Custom lsblk script for ZFS zpool.d
# Provides formatted output: SIZE, MODEL, SERIAL

exec lsblk -dno SIZE,MODEL,SERIAL "$@"
EOF

# Make script executable
chmod +x /usr/lib/ggnet2/zpool.d/ggnet2-lsblk

# Create symlink
ln -sf /usr/lib/ggnet2/zpool.d/ggnet2-lsblk /etc/zfs/zpool.d/ggnet2-lsblk
```

**Script Output Format:**
The custom script formats `lsblk` output to show:
- **SIZE**: Disk size (e.g., `1.8T`)
- **MODEL**: Disk model (e.g., `ST2000DM001-1ER164`)
- **SERIAL**: Disk serial number (e.g., `Z1Z8P8ZX`)

**Example Output:**
```
SIZE  MODEL                SERIAL
1.8T  ST2000DM001-1ER164   Z1Z8P8ZX
1.8T  ST2000DM001-1ER164   Z1Z8P8ZY
```

**Usage:**
The custom script is automatically used by ZFS when displaying pool status:
```bash
# ZFS will use custom lsblk output
zpool status pool0
```

**Integration with ZFS:**
- ZFS automatically looks for scripts in `/etc/zfs/zpool.d/`
- Scripts are executed with disk device paths as arguments
- Output is integrated into ZFS status display

**Customization:**
You can customize the output format by modifying the `ggnet2-lsblk` script:
```bash
# Edit custom script
nano /usr/lib/ggnet2/zpool.d/ggnet2-lsblk

# Example: Add more fields
exec lsblk -dno SIZE,MODEL,SERIAL,ROTA,TYPE "$@"
```

**Verification:**
```bash
# Check if script exists
test -f /etc/zfs/zpool.d/ggnet2-lsblk && echo "Script exists" || echo "Script missing"

# Test script directly
/etc/zfs/zpool.d/ggnet2-lsblk /dev/sda

# Check symlink
ls -la /etc/zfs/zpool.d/ggnet2-lsblk
```

## Development Notes

- Script is idempotent (can be run multiple times)
- Pool creation checks for existing pool
- Dataset creation uses `-p` flag for parent creation
- ZFS properties are set for optimal performance
- Compression is enabled for space efficiency
- Custom lsblk script provides formatted disk information

## To-Do

- [ ] Add pool type selection (stripe, mirror, raidz)
- [ ] Implement pool expansion
- [ ] Add dataset validation
- [ ] Implement pool backup
- [ ] Add pool monitoring
- [ ] Implement pool health checks
- [ ] Add custom lsblk script setup to installation script

