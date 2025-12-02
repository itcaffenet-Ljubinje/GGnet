#!/bin/bash

# GGnet DHCP Configuration Script
# Configures ISC DHCP server for PXE boot

set -e

# Configuration
DHCP_CONFIG="/etc/dhcp/dhcpd.conf"
DHCP_INTERFACE="eth0"
SUBNET="192.168.1.0"
NETMASK="255.255.255.0"
RANGE_START="192.168.1.100"
RANGE_END="192.168.1.200"
GATEWAY="192.168.1.1"
DNS_SERVERS="8.8.8.8,8.8.4.4"
TFTP_SERVER="192.168.1.1"
PXE_FILENAME="ipxe.efi"

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

# Install ISC DHCP server
log_info "Installing ISC DHCP server..."
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y isc-dhcp-server
elif command -v yum &> /dev/null; then
    yum install -y dhcp
elif command -v dnf &> /dev/null; then
    dnf install -y dhcp-server
else
    log_error "Package manager not supported. Please install isc-dhcp-server manually."
    exit 1
fi

# Backup existing configuration
if [[ -f "$DHCP_CONFIG" ]]; then
    log_info "Backing up existing DHCP configuration..."
    cp "$DHCP_CONFIG" "${DHCP_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Create DHCP configuration
log_info "Creating DHCP configuration..."
cat > "$DHCP_CONFIG" << EOF
# GGnet DHCP Configuration
# Generated on $(date)

# Global settings
default-lease-time 600;
max-lease-time 7200;
authoritative;

# Log settings
log-facility local7;

# Subnet configuration
subnet $SUBNET netmask $NETMASK {
    range $RANGE_START $RANGE_END;
    option routers $GATEWAY;
    option domain-name-servers $DNS_SERVERS;
    option domain-name "ggnet.local";
    
    # PXE Boot configuration
    next-server $TFTP_SERVER;
    filename "$PXE_FILENAME";
    
    # Allow booting
    allow booting;
    allow bootp;
    
    # PXE Boot options
    option architecture-type code 93 = unsigned integer 16;
    
    # Client classes for different architectures
    class "pxeclients" {
        match if substring(option vendor-class-identifier, 0, 9) = "PXEClient";
    }
    
    # UEFI x64 clients
    class "UEFI-64" {
        match if substring(option vendor-class-identifier, 15, 5) = "00007";
    }
    
    # Legacy BIOS clients
    class "BIOS" {
        match if substring(option vendor-class-identifier, 15, 5) = "00006";
    }
    
    # Pool for dynamic assignments
    pool {
        range $RANGE_START $RANGE_END;
        allow members of "pxeclients";
    }
}

# Static host entries will be added here by GGnet
# Example:
# host client01 {
#     hardware ethernet 00:11:22:33:44:55;
#     fixed-address 192.168.1.101;
#     option host-name "client01";
# }

# Include additional configurations
include "/etc/dhcp/ggnet-hosts.conf";
EOF

# Create hosts configuration file
log_info "Creating hosts configuration file..."
cat > "/etc/dhcp/ggnet-hosts.conf" << EOF
# GGnet Static Host Entries
# This file is managed by GGnet application
# Do not edit manually

# Host entries will be added here automatically
EOF

# Configure DHCP server interface
log_info "Configuring DHCP server interface..."
if [[ -f "/etc/default/isc-dhcp-server" ]]; then
    # Ubuntu/Debian
    sed -i "s/^INTERFACESv4=.*/INTERFACESv4=\"$DHCP_INTERFACE\"/" /etc/default/isc-dhcp-server
    sed -i "s/^INTERFACESv6=.*/INTERFACESv6=\"\"/" /etc/default/isc-dhcp-server
elif [[ -f "/etc/sysconfig/dhcpd" ]]; then
    # CentOS/RHEL
    echo "DHCPDARGS=\"$DHCP_INTERFACE\"" > /etc/sysconfig/dhcpd
fi

# Configure firewall
log_info "Configuring firewall..."
if command -v ufw &> /dev/null; then
    # Ubuntu/Debian UFW
    ufw allow 67/udp
    ufw allow 68/udp
elif command -v firewall-cmd &> /dev/null; then
    # CentOS/RHEL firewalld
    firewall-cmd --permanent --add-service=dhcp
    firewall-cmd --reload
elif command -v iptables &> /dev/null; then
    # Generic iptables
    iptables -A INPUT -p udp --dport 67 -j ACCEPT
    iptables -A INPUT -p udp --dport 68 -j ACCEPT
    iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
fi

# Enable and start DHCP server
log_info "Enabling and starting DHCP server..."
systemctl enable isc-dhcp-server
systemctl restart isc-dhcp-server

# Check status
if systemctl is-active --quiet isc-dhcp-server; then
    log_info "DHCP server started successfully"
else
    log_error "Failed to start DHCP server"
    systemctl status isc-dhcp-server
    exit 1
fi

# Create log directory
mkdir -p /var/log/ggnet
chown dhcp:dhcp /var/log/ggnet

# Configure logrotate
log_info "Configuring log rotation..."
cat > "/etc/logrotate.d/ggnet-dhcp" << EOF
/var/log/ggnet/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 dhcp dhcp
    postrotate
        systemctl reload isc-dhcp-server > /dev/null 2>&1 || true
    endscript
}
EOF

log_info "DHCP configuration completed successfully!"
log_info "Configuration file: $DHCP_CONFIG"
log_info "Interface: $DHCP_INTERFACE"
log_info "Subnet: $SUBNET/$NETMASK"
log_info "Range: $RANGE_START - $RANGE_END"
log_info "TFTP Server: $TFTP_SERVER"
log_info "PXE Filename: $PXE_FILENAME"

echo
log_info "Next steps:"
echo "1. Configure TFTP server with iPXE boot files"
echo "2. Add static host entries using GGnet web interface"
echo "3. Test PXE boot with a client machine"
