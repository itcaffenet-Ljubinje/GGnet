#!/bin/bash

# GGnet dnsmasq Configuration Script
# Configures dnsmasq for DHCP + TFTP + DNS (ggRock-style)

set -e

# Configuration
DNSMASQ_CONFIG="/etc/dnsmasq.conf"
DHCP_INTERFACE="eth0"
SUBNET="192.168.1.0"
NETMASK="255.255.255.0"
RANGE_START="192.168.1.100"
RANGE_END="192.168.1.200"
GATEWAY="192.168.1.1"
DNS_SERVERS="8.8.8.8,8.8.4.4"
TFTP_SERVER="192.168.1.10"
TFTP_ROOT="/var/lib/tftpboot"

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

# Install dnsmasq
log_info "Installing dnsmasq..."
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y dnsmasq
elif command -v yum &> /dev/null; then
    yum install -y dnsmasq
elif command -v dnf &> /dev/null; then
    dnf install -y dnsmasq
else
    log_error "Package manager not supported. Please install dnsmasq manually."
    exit 1
fi

# Backup existing configuration
if [[ -f "$DNSMASQ_CONFIG" ]]; then
    log_info "Backing up existing dnsmasq configuration..."
    cp "$DNSMASQ_CONFIG" "${DNSMASQ_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Create dnsmasq configuration
log_info "Creating dnsmasq configuration..."
cat > "$DNSMASQ_CONFIG" << EOF
# ============================================================================
# GGnet - dnsmasq Configuration
# Generated on $(date)
# ============================================================================
# dnsmasq provides integrated DHCP + TFTP + DNS (ggRock-style)
# ============================================================================

# Interface configuration
interface=$DHCP_INTERFACE
bind-interfaces

# DHCP configuration
dhcp-range=$RANGE_START,$RANGE_END,$NETMASK,12h
dhcp-option=option:router,$GATEWAY
dhcp-option=option:dns-server,$DNS_SERVERS
dhcp-option=option:domain-name,ggnet.local

# PXE Boot configuration - Architecture detection
# UEFI SecureBoot support
dhcp-match=set:efi-x86_64,option:client-arch,7
dhcp-match=set:efi-x86_64,option:client-arch,9
dhcp-match=set:efi-x86,option:client-arch,6
dhcp-match=set:bios,option:client-arch,0
dhcp-match=set:ipxe,175

# Boot files per architecture
dhcp-boot=tag:efi-x86_64,tag:!ipxe,snponly.efi,$TFTP_SERVER
dhcp-boot=tag:efi-x86,tag:!ipxe,ipxe32.efi,$TFTP_SERVER
dhcp-boot=tag:bios,tag:!ipxe,undionly.kpxe,$TFTP_SERVER
dhcp-boot=tag:ipxe,http://$TFTP_SERVER:8000/boot/script.ipxe

# TFTP configuration
enable-tftp
tftp-root=$TFTP_ROOT
tftp-secure
tftp-no-blocksize

# DNS configuration
domain=ggnet.local
expand-hosts

# Logging
log-dhcp
log-queries
log-facility=/var/log/dnsmasq.log

# Performance
cache-size=1000
dns-forward-max=150

# Security
bogus-priv
domain-needed
no-resolv
server=8.8.8.8
server=8.8.4.4

# GGnet machines
# Static DHCP leases will be added here automatically by GGnet
# Format: dhcp-host=<mac>,<ip>,<hostname>,<lease-time>,set:<tag>

# GGnet machine boot files
# Machine-specific boot files will be added here automatically by GGnet
# Format: dhcp-boot=tag:<tag>,<filename>,<server>
EOF

# Create TFTP root directory if it doesn't exist
log_info "Creating TFTP root directory..."
mkdir -p "$TFTP_ROOT"
chmod 755 "$TFTP_ROOT"

# Configure firewall
log_info "Configuring firewall..."
if command -v ufw &> /dev/null; then
    # Ubuntu/Debian UFW
    ufw allow 67/udp
    ufw allow 68/udp
    ufw allow 69/udp  # TFTP
elif command -v firewall-cmd &> /dev/null; then
    # CentOS/RHEL firewalld
    firewall-cmd --permanent --add-service=dhcp
    firewall-cmd --permanent --add-service=tftp
    firewall-cmd --reload
elif command -v iptables &> /dev/null; then
    # Generic iptables
    iptables -A INPUT -p udp --dport 67 -j ACCEPT
    iptables -A INPUT -p udp --dport 68 -j ACCEPT
    iptables -A INPUT -p udp --dport 69 -j ACCEPT
    iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
fi

# Enable and start dnsmasq
log_info "Enabling and starting dnsmasq..."
systemctl enable dnsmasq
systemctl restart dnsmasq

# Check status
if systemctl is-active --quiet dnsmasq; then
    log_info "dnsmasq started successfully"
else
    log_error "Failed to start dnsmasq"
    systemctl status dnsmasq
    exit 1
fi

# Create log directory
mkdir -p /var/log/ggnet
chown dnsmasq:dnsmasq /var/log/ggnet 2>/dev/null || chown root:root /var/log/ggnet

# Configure logrotate
log_info "Configuring log rotation..."
cat > "/etc/logrotate.d/ggnet-dnsmasq" << EOF
/var/log/dnsmasq.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 dnsmasq dnsmasq
    postrotate
        systemctl reload dnsmasq > /dev/null 2>&1 || true
    endscript
}
EOF

log_info "dnsmasq configuration completed successfully!"
log_info "Configuration file: $DNSMASQ_CONFIG"
log_info "Interface: $DHCP_INTERFACE"
log_info "Subnet: $SUBNET/$NETMASK"
log_info "Range: $RANGE_START - $RANGE_END"
log_info "TFTP Server: $TFTP_SERVER"
log_info "TFTP Root: $TFTP_ROOT"

echo
log_info "Next steps:"
echo "1. Configure TFTP server with iPXE boot files in $TFTP_ROOT"
echo "2. Add static host entries using GGnet web interface"
echo "3. Test PXE boot with a client machine"



