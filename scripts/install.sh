#!/bin/bash
set -euo pipefail

# GGnet Diskless Server Installation Script
# This script installs GGnet on Ubuntu/Debian systems

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
GGNET_USER="ggnet"
GGNET_GROUP="ggnet"
INSTALL_DIR="/opt/ggnet"
CONFIG_DIR="/etc/ggnet"
LOG_DIR="/var/log/ggnet"
DATA_DIR="/var/lib/ggnet"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Detect OS
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        log_error "Cannot detect OS version"
        exit 1
    fi
    
    log_info "Detected OS: $OS $VER"
    
    if [[ "$OS" != *"Ubuntu"* ]] && [[ "$OS" != *"Debian"* ]]; then
        log_warning "This script is designed for Ubuntu/Debian. Proceed with caution."
    fi
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    apt-get update
    apt-get install -y \
        python3.11 \
        python3.11-venv \
        python3.11-dev \
        python3-pip \
        nodejs \
        npm \
        postgresql \
        postgresql-contrib \
        redis-server \
        nginx \
        targetcli-fb \
        open-iscsi \
        qemu-utils \
        tftpd-hpa \
        isc-dhcp-server \
        git \
        curl \
        wget \
        unzip \
        build-essential \
        libpq-dev \
        supervisor \
        logrotate
    
    log_success "System dependencies installed"
}

# Create user and directories
setup_user_and_dirs() {
    log_info "Creating user and directories..."
    
    # Create user
    if ! id "$GGNET_USER" &>/dev/null; then
        useradd --system --shell /bin/bash --home-dir "$INSTALL_DIR" --create-home "$GGNET_USER"
        log_success "Created user: $GGNET_USER"
    else
        log_info "User $GGNET_USER already exists"
    fi
    
    # Create directories
    mkdir -p "$INSTALL_DIR"/{backend,frontend,scripts}
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$DATA_DIR"/{uploads,images,backups}
    mkdir -p /var/lib/tftpboot
    
    # Set permissions
    chown -R "$GGNET_USER:$GGNET_GROUP" "$INSTALL_DIR"
    chown -R "$GGNET_USER:$GGNET_GROUP" "$LOG_DIR"
    chown -R "$GGNET_USER:$GGNET_GROUP" "$DATA_DIR"
    
    chmod 755 "$CONFIG_DIR"
    chmod 750 "$LOG_DIR"
    chmod 750 "$DATA_DIR"
    
    log_success "User and directories created"
}

# Setup PostgreSQL
setup_postgresql() {
    log_info "Setting up PostgreSQL..."
    
    # Start PostgreSQL
    systemctl enable postgresql
    systemctl start postgresql
    
    # Create database and user
    sudo -u postgres psql -c "CREATE USER ggnet WITH PASSWORD 'ggnet_password';" || true
    sudo -u postgres psql -c "CREATE DATABASE ggnet OWNER ggnet;" || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ggnet TO ggnet;" || true
    
    log_success "PostgreSQL configured"
}

# Setup Redis
setup_redis() {
    log_info "Setting up Redis..."
    
    systemctl enable redis-server
    systemctl start redis-server
    
    log_success "Redis configured"
}

# Install backend
install_backend() {
    log_info "Installing backend..."
    
    # Copy backend files
    cp -r "$PROJECT_ROOT/backend"/* "$INSTALL_DIR/backend/"
    
    # Create virtual environment
    sudo -u "$GGNET_USER" python3.11 -m venv "$INSTALL_DIR/venv"
    
    # Install Python dependencies
    sudo -u "$GGNET_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
    sudo -u "$GGNET_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/backend/requirements.txt"
    
    # Copy environment file
    cp "$PROJECT_ROOT/env.example" "$CONFIG_DIR/backend.env"
    chown "$GGNET_USER:$GGNET_GROUP" "$CONFIG_DIR/backend.env"
    chmod 640 "$CONFIG_DIR/backend.env"
    
    # Update environment file with correct paths
    sed -i "s|UPLOAD_DIR=.*|UPLOAD_DIR=$DATA_DIR/uploads|g" "$CONFIG_DIR/backend.env"
    sed -i "s|IMAGES_DIR=.*|IMAGES_DIR=$DATA_DIR/images|g" "$CONFIG_DIR/backend.env"
    sed -i "s|AUDIT_LOG_FILE=.*|AUDIT_LOG_FILE=$LOG_DIR/audit.log|g" "$CONFIG_DIR/backend.env"
    sed -i "s|ERROR_LOG_FILE=.*|ERROR_LOG_FILE=$LOG_DIR/error.log|g" "$CONFIG_DIR/backend.env"
    
    # Run database migrations
    cd "$INSTALL_DIR/backend"
    sudo -u "$GGNET_USER" "$INSTALL_DIR/venv/bin/alembic" upgrade head
    
    log_success "Backend installed"
}

# Install frontend
install_frontend() {
    log_info "Installing frontend..."
    
    # Copy frontend files
    cp -r "$PROJECT_ROOT/frontend"/* "$INSTALL_DIR/frontend/"
    
    # Install Node.js dependencies and build
    cd "$INSTALL_DIR/frontend"
    
    # Install dependencies as ggnet user (package-lock.json will be generated)
    sudo -u "$GGNET_USER" npm install --no-audit --no-fund
    sudo -u "$GGNET_USER" npm run build
    
    # Copy built files to nginx
    rm -rf /var/www/html/*
    cp -r "$INSTALL_DIR/frontend/dist"/* /var/www/html/
    
    log_success "Frontend installed"
}

# Install scripts
install_scripts() {
    log_info "Installing scripts..."
    
    # Copy scripts
    cp -r "$PROJECT_ROOT/scripts"/* "$INSTALL_DIR/scripts/"
    
    # Make scripts executable
    chmod +x "$INSTALL_DIR/scripts"/*.py
    chmod +x "$INSTALL_DIR/scripts"/*.sh
    
    # Create symlinks in PATH
    ln -sf "$INSTALL_DIR/scripts/iscsi_manager.py" /usr/local/bin/ggnet-iscsi
    ln -sf "$INSTALL_DIR/scripts/image_converter.py" /usr/local/bin/ggnet-convert
    ln -sf "$INSTALL_DIR/scripts/uefi_boot_manager.py" /usr/local/bin/ggnet-boot
    
    log_success "Scripts installed"
}

# Setup systemd services
setup_systemd() {
    log_info "Setting up systemd services..."
    
    # Copy service files
    cp "$PROJECT_ROOT/systemd"/*.service /etc/systemd/system/
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable services
    systemctl enable ggnet-backend.service
    systemctl enable ggnet-worker.service
    
    log_success "Systemd services configured"
}

# Setup nginx
setup_nginx() {
    log_info "Setting up Nginx..."
    
    # Backup original config
    cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup
    
    # Copy our nginx config
    cp "$PROJECT_ROOT/docker/nginx/nginx.conf" /etc/nginx/nginx.conf
    
    # Test nginx config
    nginx -t
    
    # Enable and start nginx
    systemctl enable nginx
    systemctl restart nginx
    
    log_success "Nginx configured"
}

# Setup TFTP server
setup_tftp() {
    log_info "Setting up TFTP server..."
    
    # Configure TFTP
    cat > /etc/default/tftpd-hpa << EOF
TFTP_USERNAME="tftp"
TFTP_DIRECTORY="/var/lib/tftpboot"
TFTP_ADDRESS="0.0.0.0:69"
TFTP_OPTIONS="--secure"
EOF
    
    # Create TFTP directory structure
    mkdir -p /var/lib/tftpboot/{EFI/BOOT,pxelinux.cfg}
    
    # Set permissions
    chown -R tftp:tftp /var/lib/tftpboot
    
    # Enable and start TFTP
    systemctl enable tftpd-hpa
    systemctl restart tftpd-hpa
    
    log_success "TFTP server configured"
}

# Setup logrotate
setup_logrotate() {
    log_info "Setting up log rotation..."
    
    cat > /etc/logrotate.d/ggnet << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $GGNET_USER $GGNET_GROUP
    postrotate
        systemctl reload ggnet-backend || true
    endscript
}
EOF
    
    log_success "Log rotation configured"
}

# Start services
start_services() {
    log_info "Starting services..."
    
    # Start backend services
    systemctl start ggnet-backend
    systemctl start ggnet-worker
    
    # Check service status
    if systemctl is-active --quiet ggnet-backend; then
        log_success "Backend service started"
    else
        log_error "Failed to start backend service"
        systemctl status ggnet-backend
    fi
    
    if systemctl is-active --quiet ggnet-worker; then
        log_success "Worker service started"
    else
        log_warning "Worker service failed to start (this is normal if no background tasks are configured)"
    fi
}

# Create initial admin user
create_admin_user() {
    log_info "Creating initial admin user..."
    
    cd "$INSTALL_DIR/backend"
    sudo -u "$GGNET_USER" "$INSTALL_DIR/venv/bin/python" -c "
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash

async def create_admin():
    async with AsyncSessionLocal() as db:
        # Check if admin user exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.username == 'admin'))
        if result.scalar_one_or_none():
            print('Admin user already exists')
            return
        
        # Create admin user
        admin_user = User(
            username='admin',
            email='admin@ggnet.local',
            full_name='System Administrator',
            hashed_password=get_password_hash('admin123'),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_active=True
        )
        
        db.add(admin_user)
        await db.commit()
        print('Admin user created successfully')
        print('Username: admin')
        print('Password: admin123')
        print('Please change the password after first login!')

asyncio.run(create_admin())
"
    
    log_success "Initial admin user created"
}

# Print installation summary
print_summary() {
    log_success "GGnet Diskless Server installation completed!"
    echo
    echo "=== Installation Summary ==="
    echo "Install Directory: $INSTALL_DIR"
    echo "Config Directory: $CONFIG_DIR"
    echo "Data Directory: $DATA_DIR"
    echo "Log Directory: $LOG_DIR"
    echo
    echo "=== Services ==="
    echo "Backend: systemctl status ggnet-backend"
    echo "Worker: systemctl status ggnet-worker"
    echo "Nginx: systemctl status nginx"
    echo "PostgreSQL: systemctl status postgresql"
    echo "Redis: systemctl status redis-server"
    echo
    echo "=== Access ==="
    echo "Web Interface: http://$(hostname -I | awk '{print $1}')"
    echo "API Documentation: http://$(hostname -I | awk '{print $1}')/api/docs"
    echo
    echo "=== Default Credentials ==="
    echo "Username: admin"
    echo "Password: admin123"
    echo
    echo "=== Next Steps ==="
    echo "1. Change the default admin password"
    echo "2. Configure DHCP server for network boot"
    echo "3. Upload your first disk image"
    echo "4. Add client machines"
    echo "5. Create iSCSI targets"
    echo
    echo "=== Configuration Files ==="
    echo "Backend: $CONFIG_DIR/backend.env"
    echo "Nginx: /etc/nginx/nginx.conf"
    echo "TFTP: /etc/default/tftpd-hpa"
    echo
    log_warning "Remember to configure your firewall and network settings!"
}

# Main installation function
main() {
    log_info "Starting GGnet Diskless Server installation..."
    
    check_root
    detect_os
    install_dependencies
    setup_user_and_dirs
    setup_postgresql
    setup_redis
    install_backend
    install_frontend
    install_scripts
    setup_systemd
    setup_nginx
    setup_tftp
    setup_logrotate
    start_services
    create_admin_user
    print_summary
}

# Run main function
main "$@"

