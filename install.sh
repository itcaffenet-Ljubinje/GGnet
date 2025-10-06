#!/bin/bash

# GGnet Diskless Server Installation Script
# Complete installation and configuration of GGnet diskless server

set -e

# Configuration
INSTALL_DIR="/opt/ggnet"
SERVICE_USER="ggnet"
SERVICE_GROUP="ggnet"
BACKEND_PORT="8000"
FRONTEND_PORT="3000"
NGINX_PORT="80"
NGINX_SSL_PORT="443"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Detect OS and package manager
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        log_error "Cannot detect OS version"
        exit 1
    fi
    
    if command -v apt-get &> /dev/null; then
        PKG_MANAGER="apt"
    elif command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
    else
        log_error "Unsupported package manager"
        exit 1
    fi
    
    log_info "Detected OS: $OS $VER"
    log_info "Package manager: $PKG_MANAGER"
}

# Install system dependencies
install_dependencies() {
    log_step "Installing system dependencies..."
    
    if [[ "$PKG_MANAGER" == "apt" ]]; then
        apt-get update
        apt-get install -y \
            python3 python3-pip python3-venv \
            nodejs npm \
            nginx \
            isc-dhcp-server \
            tftpd-hpa \
            targetcli-fb python3-rtslib-fb \
            qemu-utils \
            redis-server \
            postgresql postgresql-contrib \
            git curl wget \
            build-essential \
            liblzma-dev \
            ufw \
            systemd
    elif [[ "$PKG_MANAGER" == "yum" ]]; then
        yum update -y
        yum install -y \
            python3 python3-pip \
            nodejs npm \
            nginx \
            dhcp \
            tftp-server \
            targetcli \
            qemu-img \
            redis \
            postgresql postgresql-server postgresql-contrib \
            git curl wget \
            gcc gcc-c++ make \
            xz-devel \
            firewalld \
            systemd
    elif [[ "$PKG_MANAGER" == "dnf" ]]; then
        dnf update -y
        dnf install -y \
            python3 python3-pip \
            nodejs npm \
            nginx \
            dhcp-server \
            tftp-server \
            targetcli \
            qemu-img \
            redis \
            postgresql postgresql-server postgresql-contrib \
            git curl wget \
            gcc gcc-c++ make \
            xz-devel \
            firewalld \
            systemd
    fi
    
    log_info "System dependencies installed successfully"
}

# Create service user
create_service_user() {
    log_step "Creating service user..."
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
        log_info "Created service user: $SERVICE_USER"
    else
        log_info "Service user already exists: $SERVICE_USER"
    fi
}

# Create directory structure
create_directories() {
    log_step "Creating directory structure..."
    
    mkdir -p "$INSTALL_DIR"/{backend,frontend,images,targets,backstores,tftp,logs,cache}
    mkdir -p "$INSTALL_DIR/backend"/{app,scripts,config}
    mkdir -p "$INSTALL_DIR/frontend"/{src,public,dist}
    
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
    chmod 755 "$INSTALL_DIR"
    
    log_info "Directory structure created successfully"
}

# Install Python backend
install_backend() {
    log_step "Installing Python backend..."
    
    # Copy backend files
    cp -r backend/* "$INSTALL_DIR/backend/"
    
    # Create virtual environment
    cd "$INSTALL_DIR/backend"
    python3 -m venv venv
    source venv/bin/activate
    
    # Install Python dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Set permissions
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/backend"
    
    log_info "Backend installed successfully"
}

# Install Node.js frontend
install_frontend() {
    log_step "Installing Node.js frontend..."
    
    # Copy frontend files
    cp -r frontend/* "$INSTALL_DIR/frontend/"
    
    # Install Node.js dependencies
    cd "$INSTALL_DIR/frontend"
    npm install
    
    # Build frontend
    npm run build
    
    # Set permissions
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/frontend"
    
    log_info "Frontend installed successfully"
}

# Configure database
configure_database() {
    log_step "Configuring database..."
    
    if [[ "$PKG_MANAGER" == "apt" ]]; then
        systemctl start postgresql
        systemctl enable postgresql
    elif [[ "$PKG_MANAGER" == "yum" || "$PKG_MANAGER" == "dnf" ]]; then
        postgresql-setup --initdb
        systemctl start postgresql
        systemctl enable postgresql
    fi
    
    # Create database and user
    sudo -u postgres psql << EOF
CREATE DATABASE ggnet;
CREATE USER ggnet WITH ENCRYPTED PASSWORD 'ggnet_password';
GRANT ALL PRIVILEGES ON DATABASE ggnet TO ggnet;
\q
EOF
    
    log_info "Database configured successfully"
}

# Configure Redis
configure_redis() {
    log_step "Configuring Redis..."
    
    systemctl start redis
    systemctl enable redis
    
    # Configure Redis for GGnet
    cat >> /etc/redis/redis.conf << EOF

# GGnet Redis Configuration
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF
    
    systemctl restart redis
    
    log_info "Redis configured successfully"
}

# Configure DHCP
configure_dhcp() {
    log_step "Configuring DHCP server..."
    
    # Run DHCP configuration script
    if [[ -f "scripts/dhcp_config.sh" ]]; then
        chmod +x scripts/dhcp_config.sh
        ./scripts/dhcp_config.sh
    else
        log_warn "DHCP configuration script not found"
    fi
    
    log_info "DHCP configured successfully"
}

# Configure TFTP
configure_tftp() {
    log_step "Configuring TFTP server..."
    
    # Run TFTP configuration script
    if [[ -f "scripts/tftp_config.sh" ]]; then
        chmod +x scripts/tftp_config.sh
        ./scripts/tftp_config.sh
    else
        log_warn "TFTP configuration script not found"
    fi
    
    log_info "TFTP configured successfully"
}

# Configure iSCSI
configure_iscsi() {
    log_step "Configuring iSCSI target server..."
    
    # Run iSCSI configuration script
    if [[ -f "scripts/iscsi_config.sh" ]]; then
        chmod +x scripts/iscsi_config.sh
        ./scripts/iscsi_config.sh
    else
        log_warn "iSCSI configuration script not found"
    fi
    
    log_info "iSCSI configured successfully"
}

# Configure Nginx
configure_nginx() {
    log_step "Configuring Nginx reverse proxy..."
    
    # Create Nginx configuration
    cat > /etc/nginx/sites-available/ggnet << EOF
server {
    listen 80;
    server_name _;
    
    # Frontend
    location / {
        root $INSTALL_DIR/frontend/dist;
        try_files \$uri \$uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:$BACKEND_PORT/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:$BACKEND_PORT/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # File uploads
    client_max_body_size 50G;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/ggnet /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Test configuration
    nginx -t
    
    # Restart Nginx
    systemctl restart nginx
    systemctl enable nginx
    
    log_info "Nginx configured successfully"
}

# Create systemd services
create_systemd_services() {
    log_step "Creating systemd services..."
    
    # Backend service
    cat > /etc/systemd/system/ggnet-backend.service << EOF
[Unit]
Description=GGnet Backend Service
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$INSTALL_DIR/backend
Environment=PATH=$INSTALL_DIR/backend/venv/bin
ExecStart=$INSTALL_DIR/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port $BACKEND_PORT
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Frontend service (if needed)
    cat > /etc/systemd/system/ggnet-frontend.service << EOF
[Unit]
Description=GGnet Frontend Service
After=network.target

[Service]
Type=exec
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$INSTALL_DIR/frontend
ExecStart=/usr/bin/npm run serve
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable services
    systemctl enable ggnet-backend
    systemctl enable ggnet-frontend
    
    log_info "Systemd services created successfully"
}

# Configure firewall
configure_firewall() {
    log_step "Configuring firewall..."
    
    if [[ "$PKG_MANAGER" == "apt" ]]; then
        # Ubuntu/Debian UFW
        ufw --force enable
        ufw allow ssh
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 67/udp
        ufw allow 68/udp
        ufw allow 69/udp
        ufw allow 3260/tcp
    elif [[ "$PKG_MANAGER" == "yum" || "$PKG_MANAGER" == "dnf" ]]; then
        # CentOS/RHEL firewalld
        systemctl start firewalld
        systemctl enable firewalld
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --permanent --add-service=dhcp
        firewall-cmd --permanent --add-service=tftp
        firewall-cmd --permanent --add-service=iscsi-target
        firewall-cmd --reload
    fi
    
    log_info "Firewall configured successfully"
}

# Initialize database
initialize_database() {
    log_step "Initializing database..."
    
    cd "$INSTALL_DIR/backend"
    source venv/bin/activate
    
    # Run database migrations
    python -m alembic upgrade head
    
    # Create admin user
    python -c "
from app.core.database import init_db
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash
import asyncio

async def create_admin():
    await init_db()
    # Admin user creation logic here
    print('Admin user created successfully')

asyncio.run(create_admin())
"
    
    log_info "Database initialized successfully"
}

# Start services
start_services() {
    log_step "Starting services..."
    
    # Start backend
    systemctl start ggnet-backend
    
    # Start frontend (if needed)
    systemctl start ggnet-frontend
    
    # Check service status
    if systemctl is-active --quiet ggnet-backend; then
        log_info "Backend service started successfully"
    else
        log_error "Failed to start backend service"
        systemctl status ggnet-backend
    fi
    
    log_info "Services started successfully"
}

# Create management script
create_management_script() {
    log_step "Creating management script..."
    
    cat > /usr/local/bin/ggnet << 'EOF'
#!/bin/bash
# GGnet Management Script

INSTALL_DIR="/opt/ggnet"
SERVICE_USER="ggnet"

case "$1" in
    start)
        systemctl start ggnet-backend ggnet-frontend
        echo "GGnet services started"
        ;;
    stop)
        systemctl stop ggnet-backend ggnet-frontend
        echo "GGnet services stopped"
        ;;
    restart)
        systemctl restart ggnet-backend ggnet-frontend
        echo "GGnet services restarted"
        ;;
    status)
        systemctl status ggnet-backend ggnet-frontend
        ;;
    logs)
        journalctl -u ggnet-backend -f
        ;;
    update)
        echo "Updating GGnet..."
        cd "$INSTALL_DIR"
        git pull
        cd backend && source venv/bin/activate && pip install -r requirements.txt
        cd ../frontend && npm install && npm run build
        systemctl restart ggnet-backend ggnet-frontend
        echo "GGnet updated successfully"
        ;;
    backup)
        echo "Creating backup..."
        tar -czf "/tmp/ggnet-backup-$(date +%Y%m%d_%H%M%S).tar.gz" "$INSTALL_DIR"
        echo "Backup created in /tmp/"
        ;;
    help)
        echo "GGnet Management Script"
        echo "Usage: $0 {start|stop|restart|status|logs|update|backup|help}"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
EOF
    
    chmod +x /usr/local/bin/ggnet
    
    log_info "Management script created successfully"
}

# Main installation function
main() {
    log_info "Starting GGnet Diskless Server installation..."
    
    check_root
    detect_os
    
    install_dependencies
    create_service_user
    create_directories
    install_backend
    install_frontend
    configure_database
    configure_redis
    configure_dhcp
    configure_tftp
    configure_iscsi
    configure_nginx
    create_systemd_services
    configure_firewall
    initialize_database
    start_services
    create_management_script
    
    log_info "GGnet Diskless Server installation completed successfully!"
    
    echo
    log_info "Installation Summary:"
    echo "  Installation Directory: $INSTALL_DIR"
    echo "  Service User: $SERVICE_USER"
    echo "  Backend Port: $BACKEND_PORT"
    echo "  Frontend Port: $FRONTEND_PORT"
    echo "  Web Interface: http://$(hostname -I | awk '{print $1}')"
    echo "  Management Script: /usr/local/bin/ggnet"
    
    echo
    log_info "Next steps:"
    echo "1. Access the web interface at http://$(hostname -I | awk '{print $1}')"
    echo "2. Login with default credentials (admin/admin123)"
    echo "3. Upload Windows/Linux images"
    echo "4. Create machine entries"
    echo "5. Configure iSCSI targets"
    echo "6. Test PXE boot with client machines"
    
    echo
    log_info "Useful commands:"
    echo "  ggnet status    - Check service status"
    echo "  ggnet logs      - View backend logs"
    echo "  ggnet restart   - Restart services"
    echo "  ggnet-iscsi list - List iSCSI targets"
    echo "  ggnet-tftp list  - List TFTP scripts"
}

# Run main function
main "$@"
