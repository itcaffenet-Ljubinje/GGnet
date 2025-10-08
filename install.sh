#!/bin/bash
###############################################################################
# GGnet Automated Installation Script
#
# One-click installation for GGnet diskless boot system
# Compatible with: Debian 11+, Ubuntu 20.04+
#
# Usage:
#   sudo ./install.sh
#   sudo ./install.sh --dry-run   # Show what would be installed
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
GGNET_DIR="/opt/ggnet"
GGNET_USER="ggnet"
GGNET_GROUP="ggnet"
DRY_RUN=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
    esac
done

# Helper functions
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
step() { echo -e "${BLUE}[STEP]${NC} $1"; }

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        error "Please run as root: sudo ./install.sh"
        exit 1
    fi
}

detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
        info "Detected OS: $OS $VER"
    else
        error "Cannot detect OS. Please use Debian/Ubuntu."
        exit 1
    fi
}

run_command() {
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY-RUN] Would run: $@"
    else
        "$@"
    fi
}

# Banner
echo ""
echo "========================================="
echo " GGnet Diskless System Installer"
echo "========================================="
echo ""

if [ "$DRY_RUN" = true ]; then
    warn "DRY-RUN MODE - No changes will be made"
    echo ""
fi

# Checks
check_root
detect_os

# Step 1: Install system dependencies
step "1/10 Installing system dependencies..."

PACKAGES=(
    # Build tools
    build-essential
    python3-dev
    python3-pip
    python3-venv
    
    # Database
    postgresql
    postgresql-contrib
    
    # Cache
    redis-server
    
    # Network services
    isc-dhcp-server
    tftpd-hpa
    dnsmasq
    nginx
    
    # iSCSI
    targetcli-fb
    
    # Image tools
    qemu-utils
    pv
    
    # Hardware detection
    lshw
    dmidecode
    parted
    
    # Monitoring
    prometheus-node-exporter
    
    # Network tools
    bridge-utils
    ifenslave
    
    # Windows tools
    chntpw
    
    # File sharing
    cifs-utils
    smbclient
    
    # SSH automation
    sshpass
    
    # Utilities
    curl
    wget
    git
    jq
    unzip
    wakeonlan
    xmlstarlet
    dialog
)

if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    run_command apt-get update
    run_command apt-get install -y "${PACKAGES[@]}"
else
    error "Unsupported OS: $OS"
    exit 1
fi

# Step 2: Create ggnet user
step "2/10 Creating ggnet user..."

if ! id -u $GGNET_USER > /dev/null 2>&1; then
    run_command useradd -r -s /bin/bash -d $GGNET_DIR -m $GGNET_USER
    info "Created user: $GGNET_USER"
else
    info "User already exists: $GGNET_USER"
fi

# Step 3: Create directory structure
step "3/10 Creating directory structure..."

DIRS=(
    "$GGNET_DIR"
    "$GGNET_DIR/backend"
    "$GGNET_DIR/frontend"
    "$GGNET_DIR/images"
    "$GGNET_DIR/targets"
    "$GGNET_DIR/uploads"
    "/var/lib/tftp"
    "/var/log/ggnet"
    "/etc/ggnet"
)

for dir in "${DIRS[@]}"; do
    run_command mkdir -p "$dir"
    run_command chown $GGNET_USER:$GGNET_GROUP "$dir"
done

# Step 4: Copy application files
step "4/10 Copying application files..."

if [ "$DRY_RUN" = false ]; then
    rsync -av --exclude='venv' --exclude='node_modules' --exclude='__pycache__' \
        backend/ "$GGNET_DIR/backend/"
    
    rsync -av --exclude='node_modules' --exclude='dist' \
        frontend/ "$GGNET_DIR/frontend/"
    
    rsync -av scripts/ "$GGNET_DIR/scripts/"
    rsync -av infra/ "$GGNET_DIR/infra/"
    
    chown -R $GGNET_USER:$GGNET_GROUP "$GGNET_DIR"
fi

# Step 5: Setup Python virtual environment
step "5/10 Setting up Python virtual environment..."

if [ "$DRY_RUN" = false ]; then
    cd "$GGNET_DIR/backend"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
fi

# Step 6: Setup PostgreSQL database
step "6/10 Configuring PostgreSQL database..."

if [ "$DRY_RUN" = false ]; then
    sudo -u postgres psql -c "CREATE USER ggnet WITH PASSWORD 'ggnet_password';" || true
    sudo -u postgres psql -c "CREATE DATABASE ggnet OWNER ggnet;" || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ggnet TO ggnet;" || true
    
    # Run migrations
    cd "$GGNET_DIR/backend"
    source venv/bin/activate
    alembic upgrade head
    deactivate
fi

# Step 7: Setup Redis
step "7/10 Configuring Redis..."

if [ "$DRY_RUN" = false ]; then
    systemctl enable redis-server
    systemctl start redis-server
fi

# Step 8: Download iPXE binaries
step "8/10 Downloading iPXE binaries..."

if [ "$DRY_RUN" = false ]; then
    cd /var/lib/tftp
    
    wget -q https://boot.ipxe.org/ipxe.efi -O ipxe.efi || warn "Failed to download ipxe.efi"
    wget -q https://boot.ipxe.org/snponly.efi -O snponly.efi || warn "Failed to download snponly.efi"
    wget -q https://boot.ipxe.org/undionly.kpxe -O undionly.kpxe || warn "Failed to download undionly.kpxe"
    
    chmod 644 /var/lib/tftp/*
    chown tftp:tftp /var/lib/tftp/* || true
    
    info "iPXE binaries downloaded"
fi

# Step 9: Configure services
step "9/10 Configuring services..."

# DHCP
if [ "$DRY_RUN" = false ]; then
    cp docker/dhcp/dhcpd.conf /etc/dhcp/dhcpd.conf
    
    # Get server IP
    SERVER_IP=$(hostname -I | awk '{print $1}')
    sed -i "s/192\.168\.1\.10/$SERVER_IP/g" /etc/dhcp/dhcpd.conf
    
    systemctl enable isc-dhcp-server
    systemctl restart isc-dhcp-server
fi

# TFTP
if [ "$DRY_RUN" = false ]; then
    systemctl enable tftpd-hpa
    systemctl restart tftpd-hpa
fi

# Nginx
if [ "$DRY_RUN" = false ]; then
    cp docker/nginx/nginx.conf /etc/nginx/sites-available/ggnet
    ln -sf /etc/nginx/sites-available/ggnet /etc/nginx/sites-enabled/ggnet
    
    systemctl enable nginx
    systemctl restart nginx
fi

# Step 10: Install systemd services
step "10/10 Installing systemd services..."

if [ "$DRY_RUN" = false ]; then
    cp systemd/ggnet-backend.service /etc/systemd/system/
    cp systemd/ggnet-worker.service /etc/systemd/system/
    cp systemd/ggnet-preflight.service /etc/systemd/system/
    
    # Install CLI tools
    cp scripts/ggnet /usr/local/bin/
    cp scripts/ggnet-iscsi /usr/local/bin/
    chmod +x /usr/local/bin/ggnet
    chmod +x /usr/local/bin/ggnet-iscsi
    
    systemctl daemon-reload
    systemctl enable ggnet-backend
    systemctl enable ggnet-worker
    systemctl enable ggnet-preflight
    
    systemctl start ggnet-preflight
    systemctl start ggnet-backend
    systemctl start ggnet-worker
fi

# Final message
echo ""
echo "========================================="
echo " GGnet Installation Complete!"
echo "========================================="
echo ""
info "Services installed and started:"
echo "  ✓ PostgreSQL (port 5432)"
echo "  ✓ Redis (port 6379)"
echo "  ✓ GGnet Backend (port 8000)"
echo "  ✓ GGnet Frontend (port 3000 via nginx)"
echo "  ✓ DHCP Server"
echo "  ✓ TFTP Server (port 69)"
echo ""
info "Access points:"
echo "  • Frontend: http://$SERVER_IP:3000"
echo "  • Backend API: http://$SERVER_IP:8000"
echo "  • API Docs: http://$SERVER_IP:8000/docs"
echo "  • Grafana: http://$SERVER_IP:3001"
echo ""
info "Next steps:"
echo "  1. Create admin user: cd $GGNET_DIR/backend && python3 create_admin.py"
echo "  2. Run pre-flight checks: ggnet check"
echo "  3. Upload Windows 11 image via web UI"
echo "  4. Create machine entries"
echo "  5. Boot clients via PXE!"
echo ""
info "CLI commands available:"
echo "  • ggnet start|stop|restart|status"
echo "  • ggnet logs [service]"
echo "  • ggnet backup [target]"
echo "  • ggnet-iscsi create|delete|list"
echo ""
echo "========================================="
echo ""

exit 0
