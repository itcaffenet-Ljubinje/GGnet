# Nginx Setup Script

The Nginx setup script (`setup-nginx.sh`) configures Nginx reverse proxy for ggnet2 API and frontend.

## Overview

The Nginx setup script:

- Installs and configures Nginx
- Sets up reverse proxy for API
- Configures static file serving for frontend
- Sets up SSL/HTTPS with self-signed certificates
- Configures WebSocket proxy for SignalR
- Configures VNC/WebSocket proxy for VM console
- Sets up PXE boot support (HTTP boot script and files)
- Configures Grafana reverse proxy
- Configures Prometheus reverse proxy
- Adds security headers (HSTS)
- Configures Gzip compression
- Sets client max body size (100M)

## Usage

```bash
# Run Nginx setup script
sudo bash scripts/setup-nginx.sh

# Or with custom configuration
DOMAIN="ggnet2.example.com" bash scripts/setup-nginx.sh
```

## Script Structure

**setup-nginx.sh:**
```bash
#!/bin/bash

set -e

# Configuration
DOMAIN="${DOMAIN:-localhost}"
API_PORT="${API_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
VNC_PROXY_PORT="${VNC_PROXY_PORT:-6080}"
GRAFANA_PORT="${GRAFANA_PORT:-3000}"
PROMETHEUS_PORT="${PROMETHEUS_PORT:-5010}"
SSL_CERT="${SSL_CERT:-/etc/nginx/ssl/certs/ggnet2-self-signed.crt}"
SSL_KEY="${SSL_KEY:-/etc/nginx/ssl/private/ggnet2-self-signed.key}"
SSL_DHPARAM="${SSL_DHPARAM:-/etc/nginx/ssl/dhparam.pem}"

# Functions
print_info() {
    echo "[INFO] $1"
}

print_error() {
    echo "[ERROR] $1" >&2
}

# Install Nginx
install_nginx() {
    print_info "Installing Nginx..."
    
    apt-get update
    apt-get install -y nginx
    
    print_info "Nginx installed"
}

# Create SSL snippets directory
create_ssl_snippets() {
    print_info "Creating SSL snippets directory..."
    
    mkdir -p /etc/nginx/snippets
    mkdir -p /etc/nginx/ssl/certs
    mkdir -p -m 710 /etc/nginx/ssl/private
    
    # Create SSL certificate include snippet
    cat > /etc/nginx/snippets/ggnet2-cert.conf <<EOF
ssl_certificate /etc/nginx/ssl/certs/ggnet2-self-signed.crt;
ssl_certificate_key /etc/nginx/ssl/private/ggnet2-self-signed.key;
EOF
    
    print_info "SSL snippets directory created"
}

# Configure Nginx
configure_nginx() {
    print_info "Configuring Nginx..."
    
    # Create SSL snippets
    create_ssl_snippets
    
    # Create Nginx configuration
    cat > /etc/nginx/sites-available/ggnet2 <<EOF
# Upstream definitions
upstream api {
    server 127.0.0.1:${API_PORT};
}

upstream frontend {
    server 127.0.0.1:${FRONTEND_PORT};
}

upstream vnc_proxy {
    server 127.0.0.1:${VNC_PROXY_PORT};
}

# HTTP server - redirect to HTTPS
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name ${DOMAIN};
    
    # Redirect HTTP requests to HTTPS with a 301 Moved Permanently response
    location / {
        return 301 https://\$host\$request_uri;
    }
    
    # Don't use HTTPS for boot script (PXE boot)
    location /boot/script {
        proxy_pass http://localhost:${API_PORT}/boot/script;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    # Boot files serving (PXE boot)
    location /boot/files/ {
        alias /opt/ggnet2/boot_files/;
        autoindex on;
    }
}

# HTTPS server
server {
    listen 443 ssl http2 default_server;
    listen [::]:443 ssl http2 default_server;
    
    server_name ${DOMAIN};
    
    # SSL certificates (included from snippet)
    include snippets/ggnet2-cert.conf;
    
    # SSL configuration
    ssl_session_timeout 1d;
    ssl_session_cache shared:MozSSL:10m;  # about 40000 sessions
    ssl_session_tickets off;
    
    # SSL DH parameters
    ssl_dhparam ${SSL_DHPARAM};
    
    # Intermediate SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # HSTS (ngx_http_headers_module is required) (63072000 seconds = 2 years)
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # Gzip compression
    gzip on;
    gzip_types text/css text/javascript text/plain application/javascript application/json application/xml;
    gzip_min_length 1000;
    
    # Client max body size
    client_max_body_size 100M;
    
    # Main API and frontend
    location / {
        proxy_pass http://api;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header Host \$http_host;
    }
    
    # SignalR WebSocket support
    location /hubs {
        proxy_pass http://api/hubs;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$http_connection;
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Grafana reverse proxy
    location /ggnet2-grafana/grafana/ {
        proxy_pass http://localhost:${GRAFANA_PORT};
        proxy_set_header Host \$http_host;
    }
    
    # Prometheus reverse proxy
    location /ggnet2-prometheus/ {
        proxy_pass http://localhost:${PROMETHEUS_PORT}/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    # VNC console access (noVNC)
    location = /vnc/console {
        proxy_pass http://vnc_proxy/vnc.html;
    }
    
    location /vnc/ {
        proxy_pass http://vnc_proxy/;
    }
    
    # WebSocket proxy for VNC
    location /websockify {
        proxy_http_version 1.1;
        proxy_pass http://vnc_proxy/;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # VNC connection timeout
        proxy_read_timeout 61s;
        
        # Disable cache
        proxy_buffering off;
    }
    
    # PXE boot script endpoint (HTTP only, but accessible via HTTPS too)
    location /boot/script {
        proxy_pass http://localhost:${API_PORT}/boot/script;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    # Boot files serving
    location /boot/files/ {
        alias /opt/ggnet2/boot_files/;
        autoindex on;
    }
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/ggnet2 /etc/nginx/sites-enabled/
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Test Nginx configuration
    nginx -t
    
    # Reload Nginx
    systemctl reload nginx
    
    print_info "Nginx configured"
}

# Setup SSL (generate self-signed certificate if not exists)
setup_ssl() {
    print_info "Setting up SSL certificates..."
    
    # Check if certificates exist
    if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
        print_info "SSL certificates found, using existing certificates"
    else
        print_info "SSL certificates not found, generating self-signed certificates..."
        
        # Generate self-signed certificate
        # Note: Use ggnet2-cert-mgr for production use
        openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
            -keyout "$SSL_KEY" \
            -out "$SSL_CERT" \
            -subj "/C=US/O=ggCircuit LLC/OU=ggnet2 Server Default Certificate/CN=$(hostname -f)/emailAddress=info@ggcircuit.com" \
            -addext "subjectAltName = DNS:localhost, IP:127.0.0.1"
        
        # Set proper permissions
        chmod 644 "$SSL_CERT"
        chmod 600 "$SSL_KEY"
        
        print_info "Self-signed SSL certificates generated"
    fi
    
    # Generate DH parameters if not exists
    if [ ! -f "$SSL_DHPARAM" ]; then
        print_info "Generating DH parameters (this may take a while)..."
        openssl dhparam -out "$SSL_DHPARAM" 2048
        chmod 644 "$SSL_DHPARAM"
        print_info "DH parameters generated"
    fi
}

# Main
main() {
    print_info "Starting Nginx setup..."
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        print_error "Please run as root (use sudo)"
        exit 1
    fi
    
    # Install Nginx
    install_nginx
    
    # Setup SSL (generate certificates if needed)
    setup_ssl
    
    # Configure Nginx
    configure_nginx
    
    print_info "Nginx setup complete!"
}

main "$@"
```

## Configuration

### Nginx Configuration

**Domain:**
- Default: `localhost`
- Can be customized via `DOMAIN` environment variable

**Ports:**
- API: `8000` (configurable)
- Frontend: `3000` (configurable)

### SSL Configuration

**SSL Certificates:**
- Certificate: `/etc/nginx/ssl/certs/ggnet2-self-signed.crt`
- Private Key: `/etc/nginx/ssl/private/ggnet2-self-signed.key`
- DH Parameters: `/etc/nginx/ssl/dhparam.pem`

**SSL Setup:**
- Self-signed certificates are generated automatically if not found
- Use `ggnet2-cert-mgr` for custom certificates (see SSL setup documentation)
- SSL snippet is included from `/etc/nginx/snippets/ggnet2-cert.conf`
- HTTPS is enabled by default with HTTP to HTTPS redirect

**SSL Features:**
- TLS 1.2 and 1.3 protocols
- Intermediate cipher suite configuration
- HSTS headers (2 years max-age)
- SSL session caching
- SSL session tickets disabled

### Upstream Configuration

**Upstream Servers:**
- `api`: Backend API server (port 8000)
- `frontend`: Frontend server (port 3000)
- `vnc_proxy`: VNC/WebSocket proxy server (port 6080)

### Location Blocks

**Main Endpoints:**
- `/` - Main API and frontend
- `/api` - API reverse proxy
- `/hubs` - SignalR WebSocket proxy
- `/vnc/console` - VNC console access (noVNC)
- `/vnc/` - VNC static files
- `/websockify` - WebSocket proxy for VNC
- `/boot/script` - PXE boot script endpoint (HTTP only)
- `/boot/files/` - PXE boot files serving
- `/ggnet2-grafana/grafana/` - Grafana reverse proxy
- `/ggnet2-prometheus/` - Prometheus reverse proxy

## Verification

### Check Nginx Status

```bash
# Check Nginx status
systemctl status nginx

# Check Nginx configuration
nginx -t

# Check Nginx logs
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log
```

### Test API Proxy

```bash
# Test API endpoint (HTTPS)
curl -k https://localhost/api/images

# Test SignalR WebSocket
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: test" \
  https://localhost/hubs/clients

# Test VNC proxy
curl -k https://localhost/vnc/console

# Test PXE boot script (HTTP)
curl http://localhost/boot/script?mac=00:11:22:33:44:55&ip=192.168.1.100

# Test Grafana proxy
curl -k https://localhost/ggnet2-grafana/grafana/

# Test Prometheus proxy
curl -k https://localhost/ggnet2-prometheus/
```

## Troubleshooting

### Nginx Not Starting

**Check Nginx:**
```bash
# Check Nginx status
systemctl status nginx

# Check Nginx configuration
nginx -t

# Check Nginx logs
journalctl -u nginx -f
```

### Reverse Proxy Not Working

**Check Proxy:**
```bash
# Check API backend
curl http://127.0.0.1:8000/api/images

# Check Nginx configuration
cat /etc/nginx/sites-available/ggnet2

# Check Nginx error logs
tail -f /var/log/nginx/error.log
```

### WebSocket Not Working

**Check WebSocket:**
```bash
# Check SignalR WebSocket configuration
grep -A 10 "location /hubs" /etc/nginx/sites-available/ggnet2

# Check VNC WebSocket configuration
grep -A 10 "location /websockify" /etc/nginx/sites-available/ggnet2

# Test SignalR WebSocket connection
wscat -c wss://localhost/hubs/clients

# Test VNC WebSocket connection
wscat -c wss://localhost/websockify
```

### SSL Certificate Issues

**Check SSL Certificates:**
```bash
# Check SSL certificate
openssl x509 -in /etc/nginx/ssl/certs/ggnet2-self-signed.crt -text -noout

# Check SSL key
openssl rsa -in /etc/nginx/ssl/private/ggnet2-self-signed.key -check

# Verify certificate and key match
openssl x509 -noout -modulus -in /etc/nginx/ssl/certs/ggnet2-self-signed.crt | openssl md5
openssl rsa -noout -modulus -in /etc/nginx/ssl/private/ggnet2-self-signed.key | openssl md5
```

### VNC Proxy Not Working

**Check VNC Proxy:**
```bash
# Check VNC proxy service
systemctl status ggnet2-novnc

# Check VNC proxy upstream
grep -A 3 "upstream vnc_proxy" /etc/nginx/sites-available/ggnet2

# Test VNC proxy connection
curl -k https://localhost/vnc/console
```

## Development Notes

- Nginx configuration is created in `/etc/nginx/sites-available/ggnet2`
- Site is enabled via symlink to `/etc/nginx/sites-enabled/`
- SSL configuration uses self-signed certificates by default
- SSL certificates are generated automatically if not found
- SSL snippet is included from `/etc/nginx/snippets/ggnet2-cert.conf`
- HTTP to HTTPS redirect is enabled by default
- PXE boot script endpoint is accessible via HTTP (no HTTPS)
- WebSocket proxy requires special headers for upgrade
- VNC proxy uses upstream configuration for load balancing
- Configuration is tested before reload
- HSTS headers are set for security
- Gzip compression is enabled for performance

## Security Features

- **HSTS**: Strict-Transport-Security header with 2-year max-age
- **SSL Protocols**: TLS 1.2 and 1.3 only
- **SSL Ciphers**: Intermediate cipher suite configuration
- **SSL Session**: Session caching enabled, tickets disabled
- **Client Max Body Size**: Limited to 100M
- **Self-Signed Certificates**: Generated automatically for development

## Performance Features

- **Gzip Compression**: Enabled for text/css, text/javascript, application/json, etc.
- **Gzip Min Length**: 1000 bytes
- **SSL Session Caching**: Shared cache for 40000 sessions
- **Upstream Configuration**: Separate upstream blocks for different services

## To-Do

- [ ] Implement Let's Encrypt integration
- [ ] Add rate limiting
- [ ] Implement caching
- [ ] Add IP whitelisting for PXE boot
- [ ] Implement load balancing
- [ ] Add request logging

