#!/bin/bash

# GGnet iSCSI Configuration Script
# Configures iSCSI target server using targetcli

set -e

# Configuration
ISCSI_BASE_IQN="iqn.2024.ggnet.local"
TARGET_BASE_DIR="/opt/ggnet/targets"
BACKSTORE_DIR="/opt/ggnet/backstores"
PORTAL_IP="0.0.0.0"
PORTAL_PORT="3260"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root"
   exit 1
fi

# Install iSCSI target software
log_info "Installing iSCSI target software..."
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y targetcli-fb python3-rtslib-fb
elif command -v yum &> /dev/null; then
    yum install -y targetcli
elif command -v dnf &> /dev/null; then
    dnf install -y targetcli
else
    log_error "Package manager not supported. Please install targetcli manually."
    exit 1
fi

# Create directories
log_info "Creating iSCSI directories..."
mkdir -p "$TARGET_BASE_DIR"
mkdir -p "$BACKSTORE_DIR"
chown -R root:root "$TARGET_BASE_DIR"
chown -R root:root "$BACKSTORE_DIR"
chmod 755 "$TARGET_BASE_DIR"
chmod 755 "$BACKSTORE_DIR"

# Enable and start target service
log_info "Enabling and starting target service..."
systemctl enable target
systemctl start target

# Check if target service is running
if ! systemctl is-active --quiet target; then
    log_error "Failed to start target service"
    systemctl status target
    exit 1
fi

# Configure firewall
log_info "Configuring firewall..."
if command -v ufw &> /dev/null; then
    # Ubuntu/Debian UFW
    ufw allow 3260/tcp
elif command -v firewall-cmd &> /dev/null; then
    # CentOS/RHEL firewalld
    firewall-cmd --permanent --add-service=iscsi-target
    firewall-cmd --reload
elif command -v iptables &> /dev/null; then
    # Generic iptables
    iptables -A INPUT -p tcp --dport 3260 -j ACCEPT
    iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
fi

# Create initial iSCSI configuration
log_info "Creating initial iSCSI configuration..."
cat > "/etc/target/saveconfig.json" << EOF
{
    "fabric_modules": [],
    "storage_objects": [],
    "targets": [],
    "tpgs": [],
    "luns": [],
    "portals": [],
    "nodes": [],
    "node_acls": [],
    "node_attribs": [],
    "node_auths": [],
    "node_maps": [],
    "node_groups": [],
    "node_group_members": []
}
EOF

# Create management script
log_info "Creating iSCSI management script..."
cat > "/usr/local/bin/ggnet-iscsi" << 'EOF'
#!/bin/bash
# GGnet iSCSI Management Script

ISCSI_BASE_IQN="iqn.2024.ggnet.local"
TARGET_BASE_DIR="/opt/ggnet/targets"
BACKSTORE_DIR="/opt/ggnet/backstores"

show_help() {
    echo "GGnet iSCSI Management Script"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  list                    - List all iSCSI targets"
    echo "  create <name> <image>   - Create iSCSI target"
    echo "  delete <name>           - Delete iSCSI target"
    echo "  start <name>            - Start iSCSI target"
    echo "  stop <name>             - Stop iSCSI target"
    echo "  status                  - Show iSCSI service status"
    echo "  restart                 - Restart iSCSI service"
    echo "  save                    - Save configuration"
    echo "  restore                 - Restore configuration"
    echo "  help                    - Show this help"
    echo
    echo "Examples:"
    echo "  $0 create windows11 /opt/ggnet/images/windows11.vhd"
    echo "  $0 delete windows11"
    echo "  $0 start windows11"
    echo "  $0 stop windows11"
}

list_targets() {
    echo "iSCSI Targets:"
    targetcli ls /iscsi
    echo
    echo "Backstores:"
    targetcli ls /backstores
    echo
    echo "Active Sessions:"
    iscsiadm -m session -P 3 2>/dev/null || echo "No active sessions"
}

create_target() {
    local name="$1"
    local image_path="$2"
    
    if [[ -z "$name" || -z "$image_path" ]]; then
        echo "Error: Target name and image path are required"
        echo "Usage: $0 create <name> <image_path>"
        exit 1
    fi
    
    if [[ ! -f "$image_path" ]]; then
        echo "Error: Image file not found: $image_path"
        exit 1
    fi
    
    local iqn="${ISCSI_BASE_IQN}:${name}"
    local backstore_name="${name}_lun1"
    
    echo "Creating iSCSI target: $name"
    echo "IQN: $iqn"
    echo "Image: $image_path"
    
    # Create backstore
    echo "Creating backstore..."
    targetcli /backstores/fileio create "$backstore_name" "$image_path"
    
    # Create target
    echo "Creating target..."
    targetcli /iscsi create "$iqn"
    
    # Create portal
    echo "Creating portal..."
    targetcli "/iscsi/$iqn/tpg1/portals" create 0.0.0.0:3260
    
    # Create LUN
    echo "Creating LUN..."
    targetcli "/iscsi/$iqn/tpg1/luns" create "/backstores/fileio/$backstore_name"
    
    # Enable target
    echo "Enabling target..."
    targetcli "/iscsi/$iqn/tpg1" set attribute generate_node_acls=1
    targetcli "/iscsi/$iqn/tpg1" set attribute cache_dynamic_acls=1
    
    # Save configuration
    targetcli saveconfig
    
    echo "Target '$name' created successfully!"
    echo "IQN: $iqn"
    echo "Portal: 0.0.0.0:3260"
}

delete_target() {
    local name="$1"
    
    if [[ -z "$name" ]]; then
        echo "Error: Target name is required"
        echo "Usage: $0 delete <name>"
        exit 1
    fi
    
    local iqn="${ISCSI_BASE_IQN}:${name}"
    local backstore_name="${name}_lun1"
    
    echo "Deleting iSCSI target: $name"
    
    # Delete target
    echo "Deleting target..."
    targetcli /iscsi delete "$iqn"
    
    # Delete backstore
    echo "Deleting backstore..."
    targetcli /backstores/fileio delete "$backstore_name"
    
    # Save configuration
    targetcli saveconfig
    
    echo "Target '$name' deleted successfully!"
}

start_target() {
    local name="$1"
    
    if [[ -z "$name" ]]; then
        echo "Error: Target name is required"
        echo "Usage: $0 start <name>"
        exit 1
    fi
    
    local iqn="${ISCSI_BASE_IQN}:${name}"
    
    echo "Starting iSCSI target: $name"
    targetcli "/iscsi/$iqn/tpg1" set attribute enable=1
    targetcli saveconfig
    
    echo "Target '$name' started successfully!"
}

stop_target() {
    local name="$1"
    
    if [[ -z "$name" ]]; then
        echo "Error: Target name is required"
        echo "Usage: $0 stop <name>"
        exit 1
    fi
    
    local iqn="${ISCSI_BASE_IQN}:${name}"
    
    echo "Stopping iSCSI target: $name"
    targetcli "/iscsi/$iqn/tpg1" set attribute enable=0
    targetcli saveconfig
    
    echo "Target '$name' stopped successfully!"
}

show_status() {
    echo "iSCSI Target Service Status:"
    systemctl status target --no-pager
    echo
    echo "Active Targets:"
    targetcli ls /iscsi
    echo
    echo "Active Sessions:"
    iscsiadm -m session -P 3 2>/dev/null || echo "No active sessions"
}

restart_service() {
    echo "Restarting iSCSI target service..."
    systemctl restart target
    echo "Service restarted successfully!"
}

save_config() {
    echo "Saving iSCSI configuration..."
    targetcli saveconfig
    echo "Configuration saved successfully!"
}

restore_config() {
    echo "Restoring iSCSI configuration..."
    targetcli restoreconfig
    echo "Configuration restored successfully!"
}

# Main script logic
case "$1" in
    list)
        list_targets
        ;;
    create)
        create_target "$2" "$3"
        ;;
    delete)
        delete_target "$2"
        ;;
    start)
        start_target "$2"
        ;;
    stop)
        stop_target "$2"
        ;;
    status)
        show_status
        ;;
    restart)
        restart_service
        ;;
    save)
        save_config
        ;;
    restore)
        restore_config
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Error: Unknown command '$1'"
        echo
        show_help
        exit 1
        ;;
esac
EOF

chmod +x /usr/local/bin/ggnet-iscsi

# Create example target
log_info "Creating example iSCSI target..."
if [[ -f "/opt/ggnet/images/example.vhd" ]]; then
    /usr/local/bin/ggnet-iscsi create example /opt/ggnet/images/example.vhd
else
    log_warn "Example image not found. Skipping example target creation."
fi

# Create systemd service for automatic target startup
log_info "Creating systemd service for automatic target startup..."
cat > "/etc/systemd/system/ggnet-iscsi.service" << EOF
[Unit]
Description=GGnet iSCSI Target Service
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/ggnet-iscsi restore
ExecStop=/usr/local/bin/ggnet-iscsi save
TimeoutStartSec=30

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ggnet-iscsi

# Create log directory
mkdir -p /var/log/ggnet
chown root:root /var/log/ggnet

# Configure logrotate
log_info "Configuring log rotation..."
cat > "/etc/logrotate.d/ggnet-iscsi" << EOF
/var/log/ggnet/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload target > /dev/null 2>&1 || true
    endscript
}
EOF

log_info "iSCSI configuration completed successfully!"
log_info "Base IQN: $ISCSI_BASE_IQN"
log_info "Target Directory: $TARGET_BASE_DIR"
log_info "Backstore Directory: $BACKSTORE_DIR"
log_info "Portal: $PORTAL_IP:$PORTAL_PORT"
log_info "Management Script: /usr/local/bin/ggnet-iscsi"

echo
log_info "Next steps:"
echo "1. Create image files in /opt/ggnet/images/"
echo "2. Use 'ggnet-iscsi create <name> <image>' to create targets"
echo "3. Configure client machines to connect to iSCSI targets"
echo "4. Test iSCSI connections"

echo
log_info "Example usage:"
echo "  ggnet-iscsi create windows11 /opt/ggnet/images/windows11.vhd"
echo "  ggnet-iscsi list"
echo "  ggnet-iscsi start windows11"
echo "  ggnet-iscsi status"
