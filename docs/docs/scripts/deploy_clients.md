# Windows Client Deployment Script

The Windows client deployment script (`deploy-windows-client.sh`) automates the deployment of ggnet2 Windows Client to physical machines.

## Overview

The deployment script:

- Generates registry scripts for clients
- Packages client installer
- Deploys client to target machines
- Configures client settings
- Verifies client installation

## Usage

```bash
# Deploy client to single machine
sudo bash scripts/deploy-windows-client.sh --client-id client-001 --target 192.168.1.100

# Deploy client to multiple machines
sudo bash scripts/deploy-windows-client.sh --client-ids client-001,client-002

# Deploy with custom configuration
sudo bash scripts/deploy-windows-client.sh \
  --client-id client-001 \
  --target 192.168.1.100 \
  --server-url http://server:8000
```

## Script Structure

**deploy-windows-client.sh:**
```bash
#!/bin/bash

set -e

# Configuration
SERVER_URL="${SERVER_URL:-http://localhost:8000}"
CLIENT_ID="${CLIENT_ID:-}"
TARGET_IP="${TARGET_IP:-}"
CLIENT_IDS="${CLIENT_IDS:-}"

# Functions
print_info() {
    echo "[INFO] $1"
}

print_error() {
    echo "[ERROR] $1" >&2
}

# Parse arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --client-id)
                CLIENT_ID="$2"
                shift 2
                ;;
            --client-ids)
                CLIENT_IDS="$2"
                shift 2
                ;;
            --target)
                TARGET_IP="$2"
                shift 2
                ;;
            --server-url)
                SERVER_URL="$2"
                shift 2
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
}

# Generate registry script
generate_registry_script() {
    local client_id=$1
    
    print_info "Generating registry script for $client_id..."
    
    # Get client info from API
    client_info=$(curl -s "${SERVER_URL}/api/clients/${client_id}")
    computer_name=$(echo "$client_info" | jq -r '.name')
    
    # Generate registry script
    curl -s -X POST "${SERVER_URL}/api/clients/${client_id}/registry-script" \
      -H "Content-Type: application/json" \
      -d "{
        \"script_type\": \"install\",
        \"computer_name\": \"${computer_name}\",
        \"server_url\": \"${SERVER_URL}\",
        \"client_id\": \"${client_id}\"
      }" > "/tmp/ggnet2-${client_id}.reg"
    
    print_info "Registry script generated: /tmp/ggnet2-${client_id}.reg"
}

# Package client installer
package_installer() {
    local client_id=$1
    
    print_info "Packaging client installer for $client_id..."
    
    # Create installer package
    mkdir -p "/tmp/ggnet2-${client_id}-installer"
    
    # Copy client files
    cp -r windows_client/ggnet2-toolchain/* "/tmp/ggnet2-${client_id}-installer/"
    
    # Copy registry script
    cp "/tmp/ggnet2-${client_id}.reg" "/tmp/ggnet2-${client_id}-installer/"
    
    # Create installer script
    cat > "/tmp/ggnet2-${client_id}-installer/install.bat" <<EOF
@echo off
echo Installing ggnet2 Windows Client...

REM Apply registry script
reg import ggnet2-${client_id}.reg

REM Install .NET service
sc create ggnet2-toolchain binPath="C:\Program Files\ggnet2\ggnet2-toolchain.exe"
sc start ggnet2-toolchain

echo Installation complete!
EOF
    
    # Create ZIP archive
    cd /tmp
    zip -r "ggnet2-${client_id}-installer.zip" "ggnet2-${client_id}-installer"
    
    print_info "Installer packaged: /tmp/ggnet2-${client_id}-installer.zip"
}

# Deploy to target machine
deploy_to_target() {
    local client_id=$1
    local target_ip=$2
    
    print_info "Deploying client $client_id to $target_ip..."
    
    # Copy installer to target machine
    scp "/tmp/ggnet2-${client_id}-installer.zip" "administrator@${target_ip}:/tmp/"
    
    # Execute installer on target machine
    ssh "administrator@${target_ip}" <<EOF
cd /tmp
unzip -o ggnet2-${client_id}-installer.zip
cd ggnet2-${client_id}-installer
install.bat
EOF
    
    print_info "Client deployed to $target_ip"
}

# Verify client installation
verify_installation() {
    local client_id=$1
    
    print_info "Verifying client installation for $client_id..."
    
    # Wait for client to register
    sleep 10
    
    # Check client status
    client_status=$(curl -s "${SERVER_URL}/api/clients/${client_id}")
    status=$(echo "$client_status" | jq -r '.status')
    
    if [ "$status" = "online" ]; then
        print_info "Client $client_id is online"
        return 0
    else
        print_error "Client $client_id is not online"
        return 1
    fi
}

# Deploy single client
deploy_single_client() {
    local client_id=$1
    local target_ip=$2
    
    print_info "Deploying client: $client_id"
    
    # Generate registry script
    generate_registry_script "$client_id"
    
    # Package installer
    package_installer "$client_id"
    
    # Deploy to target
    if [ -n "$target_ip" ]; then
        deploy_to_target "$client_id" "$target_ip"
    else
        print_info "Installer ready: /tmp/ggnet2-${client_id}-installer.zip"
        print_info "Manual deployment required"
    fi
    
    # Verify installation
    if [ -n "$target_ip" ]; then
        verify_installation "$client_id"
    fi
}

# Deploy multiple clients
deploy_multiple_clients() {
    local client_ids=$1
    
    IFS=',' read -ra IDS <<< "$client_ids"
    
    for client_id in "${IDS[@]}"; do
        deploy_single_client "$client_id" ""
    done
}

# Main
main() {
    print_info "Starting Windows client deployment..."
    
    # Parse arguments
    parse_args "$@"
    
    # Deploy single client
    if [ -n "$CLIENT_ID" ]; then
        deploy_single_client "$CLIENT_ID" "$TARGET_IP"
    # Deploy multiple clients
    elif [ -n "$CLIENT_IDS" ]; then
        deploy_multiple_clients "$CLIENT_IDS"
    else
        print_error "No client ID specified"
        exit 1
    fi
    
    print_info "Deployment complete!"
}

main "$@"
```

## Configuration

### Deployment Options

**Single Client:**
- `--client-id`: Client ID to deploy
- `--target`: Target machine IP address

**Multiple Clients:**
- `--client-ids`: Comma-separated list of client IDs

**Server Configuration:**
- `--server-url`: Server URL (default: http://localhost:8000)

## Deployment Process

### 1. Generate Registry Script

Registry script is generated from server API:

```bash
curl -X POST "${SERVER_URL}/api/clients/${client_id}/registry-script" \
  -H "Content-Type: application/json" \
  -d '{
    "script_type": "install",
    "computer_name": "PC-1",
    "server_url": "http://server:8000",
    "client_id": "client-001"
  }'
```

### 2. Package Installer

Installer package includes:

- Client binaries
- Registry script
- Installer script
- Configuration files

### 3. Deploy to Target

Deployment options:

- **SCP/SSH**: Automated deployment via SSH
- **Network Share**: Manual deployment from network share
- **Group Policy**: Deployment via Group Policy

### 4. Verify Installation

Verification checks:

- Client registration
- Client connection status
- Service status

## Verification

### Check Client Status

```bash
# Check client status from server
curl "${SERVER_URL}/api/clients/${client_id}"

# Response
{
  "id": "client-001",
  "name": "PC-1",
  "status": "online",
  "last_seen": "2024-01-01T12:00:00Z"
}
```

### Check Client Service

**On Target Machine:**
```bash
# Check service status
sc query ggnet2-toolchain

# Check service logs
Get-EventLog -LogName Application -Source ggnet2-toolchain
```

## Troubleshooting

### Deployment Fails

**Check SSH Connection:**
```bash
# Test SSH connection
ssh administrator@target_ip

# Check SSH key
ssh-keygen -t rsa -b 4096
```

### Client Not Registering

**Check Client Configuration:**
```bash
# Check registry values
reg query HKEY_LOCAL_MACHINE\SOFTWARE\ggnet2

# Check service status
sc query ggnet2-toolchain
```

### Network Issues

**Check Network Connectivity:**
```bash
# Test server connection
ping server
telnet server 8000

# Check firewall
netsh advfirewall firewall show rule name="ggnet2-client"
```

## Development Notes

- Deployment requires SSH access to target machines
- Registry scripts are generated from server API
- Installer packages are created in `/tmp/`
- Verification waits for client registration
- Multiple clients can be deployed in parallel

## To-Do

- [ ] Add deployment progress tracking
- [ ] Implement rollback mechanism
- [ ] Add deployment logging
- [ ] Implement deployment verification
- [ ] Add deployment automation
- [ ] Implement deployment scheduling

