# Systemd Service Setup Script

The Systemd service setup script (`setup-systemd.sh`) configures systemd services for ggnet2 backend API and VNC/WebSocket proxy.

## Overview

The Systemd setup script:

- Creates backend API service (`ggnet2-api.service`)
- Creates VNC/WebSocket proxy service (`ggnet2-novnc.service`)
- Configures service dependencies
- Sets up restart policies
- Enables and starts services

## Usage

```bash
# Run Systemd setup script
sudo bash scripts/setup-systemd.sh

# Or with custom paths
APP_DIR="/opt/ggnet2/app" bash scripts/setup-systemd.sh
```

## Script Structure

**setup-systemd.sh:**
```bash
#!/bin/bash

set -e

# Configuration
APP_DIR="${APP_DIR:-/opt/ggnet2/app}"
API_EXECUTABLE="${API_EXECUTABLE:-ggnet2-api}"
VNC_TOKEN_DIR="${VNC_TOKEN_DIR:-/etc/ggnet2/websockify/target.config.d}"

# Functions
print_info() {
    echo "[INFO] $1"
}

print_error() {
    echo "[ERROR] $1" >&2
}

# Create backend API service
create_api_service() {
    print_info "Creating backend API service..."
    
    cat > /etc/systemd/system/ggnet2-api.service <<EOF
[Unit]
Description=ggnet2 diskless boot system
After=libvirtd.service
Requires=libvirtd.service

[Service]
Type=simple
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/${API_EXECUTABLE}
Restart=always
RestartSec=10
KillSignal=SIGINT
SyslogIdentifier=ggnet2-api
StandardOutput=journal
StandardError=journal

# Environment variables
Environment="ASPNETCORE_ENVIRONMENT=Production"
Environment="ASPNETCORE_URLS=http://localhost:8000"

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service
    systemctl enable ggnet2-api.service
    
    print_info "Backend API service created"
}

# Create VNC/WebSocket proxy service
create_vnc_service() {
    print_info "Creating VNC/WebSocket proxy service..."
    
    # Create token directory
    mkdir -p "$VNC_TOKEN_DIR"
    chmod 755 "$VNC_TOKEN_DIR"
    
    cat > /etc/systemd/system/ggnet2-novnc.service <<EOF
[Unit]
Description=ggnet2 VNC client for VMs
After=network.target
Requires=network.target

[Service]
Type=simple
ExecStart=/usr/bin/websockify --web=/usr/share/novnc --token-plugin TokenFile --token-source ${VNC_TOKEN_DIR} 127.0.0.1:6080
Restart=always
RestartSec=2
SyslogIdentifier=ggnet2-novnc
StandardOutput=journal
StandardError=journal

# Environment variables
Environment="WEBSOCKIFY_OPTS=--web /usr/share/novnc"

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service
    systemctl enable ggnet2-novnc.service
    
    print_info "VNC/WebSocket proxy service created"
}

# Install dependencies
install_dependencies() {
    print_info "Installing dependencies..."
    
    # Install websockify (if not already installed)
    if ! command -v websockify &> /dev/null; then
        apt-get update
        apt-get install -y websockify novnc
    fi
    
    # Install libvirt (if not already installed)
    if ! systemctl is-active --quiet libvirtd.service; then
        apt-get update
        apt-get install -y libvirt-daemon-system libvirt-clients
        systemctl enable libvirtd.service
        systemctl start libvirtd.service
    fi
    
    print_info "Dependencies installed"
}

# Main
main() {
    print_info "Starting Systemd service setup..."
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        print_error "Please run as root (use sudo)"
        exit 1
    fi
    
    # Install dependencies
    install_dependencies
    
    # Create services
    create_api_service
    create_vnc_service
    
    print_info "Systemd services created"
    print_info "To start services, run:"
    print_info "  systemctl start ggnet2-api"
    print_info "  systemctl start ggnet2-novnc"
}

main "$@"
```

## Configuration

### Backend API Service

**Service File:** `/etc/systemd/system/ggnet2-api.service`

**Configuration:**
- **WorkingDirectory**: `/opt/ggnet2/app`
- **ExecStart**: `/opt/ggnet2/app/ggnet2-api`
- **After**: `libvirtd.service` (requires libvirt for VM management)
- **Restart**: `always` (automatic restart on failure)
- **RestartSec**: `10` (wait 10 seconds before restart)
- **KillSignal**: `SIGINT` (graceful shutdown)
- **SyslogIdentifier**: `ggnet2-api` (for log filtering)

**Environment Variables:**
- `ASPNETCORE_ENVIRONMENT=Production`
- `ASPNETCORE_URLS=http://localhost:8000`

**Resource Limits:**
- `LimitNOFILE=65536` (max open files)
- `LimitNPROC=4096` (max processes)

### VNC/WebSocket Proxy Service

**Service File:** `/etc/systemd/system/ggnet2-novnc.service`

**Configuration:**
- **ExecStart**: `websockify --web=/usr/share/novnc --token-plugin TokenFile --token-source /etc/ggnet2/websockify/target.config.d 127.0.0.1:6080`
- **After**: `network.target` (requires network)
- **Restart**: `always` (automatic restart on failure)
- **RestartSec**: `2` (wait 2 seconds before restart)
- **SyslogIdentifier**: `ggnet2-novnc` (for log filtering)

**Token-Based Access:**
- Uses `TokenFile` plugin for token-based VNC access
- Token source directory: `/etc/ggnet2/websockify/target.config.d`
- Tokens are managed by backend API

**Environment Variables:**
- `WEBSOCKIFY_OPTS=--web /usr/share/novnc`

**Resource Limits:**
- `LimitNOFILE=65536` (max open files)
- `LimitNPROC=4096` (max processes)

## Service Management

### Enable Services

```bash
# Enable services (start on boot)
systemctl enable ggnet2-api.service
systemctl enable ggnet2-novnc.service
```

### Start Services

```bash
# Start services
systemctl start ggnet2-api
systemctl start ggnet2-novnc
```

### Stop Services

```bash
# Stop services
systemctl stop ggnet2-api
systemctl stop ggnet2-novnc
```

### Restart Services

```bash
# Restart services
systemctl restart ggnet2-api
systemctl restart ggnet2-novnc
```

### Check Service Status

```bash
# Check service status
systemctl status ggnet2-api
systemctl status ggnet2-novnc

# Check if services are enabled
systemctl is-enabled ggnet2-api
systemctl is-enabled ggnet2-novnc

# Check if services are active
systemctl is-active ggnet2-api
systemctl is-active ggnet2-novnc
```

### View Service Logs

```bash
# View service logs
journalctl -u ggnet2-api -f
journalctl -u ggnet2-novnc -f

# View recent logs
journalctl -u ggnet2-api -n 50
journalctl -u ggnet2-novnc -n 50

# View logs with timestamps
journalctl -u ggnet2-api --since "1 hour ago"
```

## Verification

### Check Service Dependencies

```bash
# Check backend API service dependencies
systemctl list-dependencies ggnet2-api.service

# Check VNC service dependencies
systemctl list-dependencies ggnet2-novnc.service
```

### Check Service Configuration

```bash
# View backend API service file
cat /etc/systemd/system/ggnet2-api.service

# View VNC service file
cat /etc/systemd/system/ggnet2-novnc.service
```

### Test Service Startup

```bash
# Test backend API service configuration
systemd-analyze verify ggnet2-api.service

# Test VNC service configuration
systemd-analyze verify ggnet2-novnc.service
```

## Troubleshooting

### Service Not Starting

**Check Service Status:**
```bash
# Check service status
systemctl status ggnet2-api
systemctl status ggnet2-novnc

# Check service logs
journalctl -u ggnet2-api -n 50
journalctl -u ggnet2-novnc -n 50

# Check if executable exists
test -f /opt/ggnet2/app/ggnet2-api && echo "API executable exists" || echo "API executable missing"

# Check if websockify is installed
which websockify
```

### Service Dependency Issues

**Check Dependencies:**
```bash
# Check if libvirt is running
systemctl status libvirtd

# Check if network is available
systemctl status network.target

# Check service dependencies
systemctl list-dependencies ggnet2-api.service
```

### Service Restart Loop

**Check Restart Loop:**
```bash
# Check service restart count
systemctl show ggnet2-api | grep RestartCount
systemctl show ggnet2-novnc | grep RestartCount

# Check service logs for errors
journalctl -u ggnet2-api --since "5 minutes ago" | grep -i error
journalctl -u ggnet2-novnc --since "5 minutes ago" | grep -i error
```

### VNC Token Issues

**Check VNC Token Configuration:**
```bash
# Check token directory
ls -la /etc/ggnet2/websockify/target.config.d/

# Check token file permissions
find /etc/ggnet2/websockify/target.config.d/ -type f -ls

# Test websockify manually
websockify --web=/usr/share/novnc --token-plugin TokenFile --token-source /etc/ggnet2/websockify/target.config.d 127.0.0.1:6080
```

## Development Notes

- Services are created in `/etc/systemd/system/`
- Services are enabled via `systemctl enable`
- Services are started via `systemctl start`
- Logs are available via `journalctl -u <service-name>`
- Service dependencies are managed via `After` and `Requires` directives
- Restart policies are configured for automatic recovery
- Resource limits are set for stability

## To-Do

- [ ] Add service health checks
- [ ] Implement service monitoring
- [ ] Add service restart notifications
- [ ] Implement service resource monitoring
- [ ] Add service performance metrics
- [ ] Implement service auto-scaling

