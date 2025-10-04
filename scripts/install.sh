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
DB_USER="ggnet"
DB_PASS="ggnet_password"
DB_NAME="ggnet"

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
        python3 \
        python3-venv \
        python3-dev \
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
        logrotate \
        ipxe \
        grub-efi-amd64-bin
    
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
    
    # Wait for PostgreSQL to start
    sleep 5
    
    # Create database and user
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || log_info "User $DB_USER already exists"
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || log_info "Database $DB_NAME already exists"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || log_info "Privileges already granted"
    
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
    sudo -u "$GGNET_USER" python3 -m venv "$INSTALL_DIR/venv"
    
    # Install Python dependencies
    sudo -u "$GGNET_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
    sudo -u "$GGNET_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/backend/requirements.txt"
    
    # Install PostgreSQL driver and additional dependencies
    sudo -u "$GGNET_USER" "$INSTALL_DIR/venv/bin/pip" install psycopg2-binary asyncpg
    
    # Copy environment file
    cp "$PROJECT_ROOT/env.example" "$CONFIG_DIR/backend.env"
    chown "$GGNET_USER:$GGNET_GROUP" "$CONFIG_DIR/backend.env"
    chmod 640 "$CONFIG_DIR/backend.env"
    
    # Update environment file with correct paths and PostgreSQL database
    sed -i "s|UPLOAD_DIR=.*|UPLOAD_DIR=$DATA_DIR/uploads|g" "$CONFIG_DIR/backend.env"
    sed -i "s|IMAGES_DIR=.*|IMAGES_DIR=$DATA_DIR/images|g" "$CONFIG_DIR/backend.env"
    sed -i "s|AUDIT_LOG_FILE=.*|AUDIT_LOG_FILE=$LOG_DIR/audit.log|g" "$CONFIG_DIR/backend.env"
    sed -i "s|ERROR_LOG_FILE=.*|ERROR_LOG_FILE=$LOG_DIR/error.log|g" "$CONFIG_DIR/backend.env"
    sed -i "s|BACKUP_DIR=.*|BACKUP_DIR=$DATA_DIR/backups|g" "$CONFIG_DIR/backend.env"
    sed -i "s|ENVIRONMENT=.*|ENVIRONMENT=production|g" "$CONFIG_DIR/backend.env"
    sed -i "s|DEBUG=.*|DEBUG=false|g" "$CONFIG_DIR/backend.env"
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=$(openssl rand -hex 32)|g" "$CONFIG_DIR/backend.env"
    
    # Set PostgreSQL database URL
    if grep -q "DATABASE_URL=" "$CONFIG_DIR/backend.env"; then
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost/$DB_NAME|g" "$CONFIG_DIR/backend.env"
    else
        echo "DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost/$DB_NAME" >> "$CONFIG_DIR/backend.env"
    fi
    
    # Test PostgreSQL connection
    log_info "Testing PostgreSQL connection..."
    if sudo -u "$GGNET_USER" env DATABASE_URL="postgresql://$DB_USER:$DB_PASS@localhost/$DB_NAME" "$INSTALL_DIR/venv/bin/python" -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://$DB_USER:$DB_PASS@localhost/$DB_NAME')
    print('PostgreSQL connection successful')
    conn.close()
except Exception as e:
    print(f'PostgreSQL connection failed: {e}')
    exit(1)
"; then
        log_success "PostgreSQL connection test passed"
    else
        log_error "PostgreSQL connection test failed"
        exit 1
    fi
    
    # Run database migrations with PostgreSQL
    log_info "Running database migrations..."
    cd "$INSTALL_DIR/backend"
    sudo -u "$GGNET_USER" env DATABASE_URL="postgresql://$DB_USER:$DB_PASS@localhost/$DB_NAME" "$INSTALL_DIR/venv/bin/alembic" upgrade head
    
    log_success "Backend installed"
}

# Create initial admin user
create_admin_user() {
    log_info "Creating initial admin user..."
    
    cd "$INSTALL_DIR/backend"
    
    # Use PostgreSQL connection string
    sudo -u "$GGNET_USER" env DATABASE_URL="postgresql://$DB_USER:$DB_PASS@localhost/$DB_NAME" "$INSTALL_DIR/venv/bin/python" - <<'EOF'
import asyncio
import os
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash

async def create_admin():
    async with AsyncSessionLocal() as db:
        # Check if admin user exists
        result = await db.execute(select(User).where(User.username == 'admin'))
        if result.scalar_one_or_none():
            print("Admin user already exists")
            return
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@ggnet.local",
            full_name="System Administrator",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_active=True
        )
        
        db.add(admin_user)
        await db.commit()
        print("Admin user created successfully")
        print("Username: admin")
        print("Password: admin123")
        print("Please change the password after first login!")

asyncio.run(create_admin())
EOF
    
    log_success "Initial admin user created"
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
    
    # Set proper ownership
    chown -R www-data:www-data /var/www/html
    
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
    
    # Create backend service file
    cat > /etc/systemd/system/ggnet-backend.service << EOF
[Unit]
Description=GGnet Diskless Server Backend
Documentation=https://github.com/ggnet/diskless-server
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service
Requires=network.target

[Service]
Type=exec
User=$GGNET_USER
Group=$GGNET_GROUP
WorkingDirectory=$INSTALL_DIR/backend
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$INSTALL_DIR/backend
EnvironmentFile=$CONFIG_DIR/backend.env
ExecStart=$INSTALL_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
Restart=always
RestartSec=5
TimeoutStopSec=30

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA_DIR $LOG_DIR
PrivateTmp=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictRealtime=true
RestrictSUIDSGID=true
LockPersonality=true
MemoryDenyWriteExecute=true

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ggnet-backend

[Install]
WantedBy=multi-user.target
EOF

    # Create worker service file
    cat > /etc/systemd/system/ggnet-worker.service << EOF
[Unit]
Description=GGnet Background Worker
Documentation=https://github.com/ggnet/diskless-server
After=network.target postgresql.service redis.service ggnet-backend.service
Wants=postgresql.service redis.service
Requires=network.target

[Service]
Type=exec
User=$GGNET_USER
Group=$GGNET_GROUP
WorkingDirectory=$INSTALL_DIR/backend
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$INSTALL_DIR/backend
EnvironmentFile=$CONFIG_DIR/backend.env
ExecStart=$INSTALL_DIR/venv/bin/python -m app.worker
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
Restart=always
RestartSec=10
TimeoutStopSec=60

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA_DIR $LOG_DIR
PrivateTmp=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictRealtime=true
RestrictSUIDSGID=true
LockPersonality=true

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ggnet-worker

[Install]
WantedBy=multi-user.target
EOF
    
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
    
    # Create nginx config for native installation
    cat > /etc/nginx/nginx.conf << 'EOF'
user www-data;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json
        application/xml
        image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=2r/s;

    # Upstream backend
    upstream ggnet_backend {
        server 127.0.0.1:8000;
        keepalive 32;
    }

    # Main server block
    server {
        listen 80;
        server_name _;
        root /var/www/html;
        index index.html;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

        # Client max body size for uploads
        client_max_body_size 10G;
        client_body_timeout 300s;
        client_header_timeout 60s;

        # Frontend static files
        location / {
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
                access_log off;
            }
        }

        # API proxy
        location /api/ {
            # Rate limiting
            limit_req zone=api burst=20 nodelay;
            
            # Proxy settings
            proxy_pass http://ggnet_backend/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
            
            # Buffer settings
            proxy_buffering on;
            proxy_buffer_size 128k;
            proxy_buffers 4 256k;
            proxy_busy_buffers_size 256k;
        }

        # Special handling for file uploads
        location /api/images/upload {
            limit_req zone=upload burst=5 nodelay;
            
            proxy_pass http://ggnet_backend/images/upload;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Extended timeouts for large uploads
            proxy_connect_timeout 60s;
            proxy_send_timeout 600s;
            proxy_read_timeout 600s;
            
            # Disable buffering for uploads
            proxy_buffering off;
            proxy_request_buffering off;
        }

        # Health check endpoint
        location /health {
            proxy_pass http://ggnet_backend/health;
            access_log off;
        }

        # Error pages
        error_page 404 /index.html;
        error_page 500 502 503 504 /50x.html;
        
        location = /50x.html {
            root /var/www/html;
        }
    }
}
EOF
    
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
    
    # Copy UEFI boot files
    if [[ -f /usr/lib/ipxe/ipxe.efi ]]; then
        cp /usr/lib/ipxe/ipxe.efi /var/lib/tftpboot/bootx64.efi
    elif [[ -f /usr/share/ipxe/ipxe.efi ]]; then
        cp /usr/share/ipxe/ipxe.efi /var/lib/tftpboot/bootx64.efi
    else
        log_warning "iPXE EFI binary not found, please install ipxe package"
    fi
    
    # Create iPXE boot script
    cat > /var/lib/tftpboot/boot.ipxe << 'EOF'
#!ipxe
dhcp
set server-ip ${next-server}
set iscsi-server ${server-ip}
set initiator-iqn iqn.2025.ggnet.client:${mac}
set target-name ${mac}
sanboot iscsi:${iscsi-server}:::1:${initiator-iqn}:${target-name}
EOF
    
    # Set permissions
    chown -R tftp:tftp /var/lib/tftpboot
    chmod 644 /var/lib/tftpboot/bootx64.efi
    chmod 644 /var/lib/tftpboot/boot.ipxe
    
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
    echo "Backend Service: /etc/systemd/system/ggnet-backend.service"
    echo "Worker Service: /etc/systemd/system/ggnet-worker.service"
    echo
    echo "=== Useful Commands ==="
    echo "Check backend status: systemctl status ggnet-backend"
    echo "View backend logs: journalctl -u ggnet-backend -f"
    echo "Restart backend: systemctl restart ggnet-backend"
    echo "Check nginx status: systemctl status nginx"
    echo "Test nginx config: nginx -t"
    echo
    log_warning "Remember to configure your firewall and network settings!"
    log_warning "Make sure to open ports 80 (HTTP), 3260 (iSCSI), and 69 (TFTP) in your firewall!"
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
