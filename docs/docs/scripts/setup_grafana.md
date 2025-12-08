# Grafana Setup Script

The Grafana setup script (`setup-grafana.sh`) installs and configures Grafana for monitoring visualization in ggnet2.

## Overview

The Grafana setup script:

- Installs Grafana
- Configures Grafana sub-path serving
- Sets up JWT authentication
- Configures Prometheus datasource provisioning
- Sets up dashboard provisioning
- Creates basic dashboard
- Configures Nginx reverse proxy for Grafana
- Enables and starts Grafana service

## Usage

```bash
# Run Grafana setup script
sudo bash scripts/setup-grafana.sh

# Or with custom configuration
GRAFANA_PORT=3000 bash scripts/setup-grafana.sh
```

## Script Structure

**setup-grafana.sh:**
```bash
#!/bin/bash

set -e

# Configuration
GRAFANA_PORT="${GRAFANA_PORT:-3000}"
SUBPATH="${SUBPATH:-/ggnet2-grafana/grafana/}"

# Functions
print_info() {
    echo "[INFO] $1"
}

print_error() {
    echo "[ERROR] $1" >&2
}

# Install Grafana
install_grafana() {
    print_info "Installing Grafana..."
    
    # Add Grafana repository
    apt-get update
    apt-get install -y software-properties-common
    add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
    wget -q -O - https://packages.grafana.com/gpg.key | apt-key add -
    
    # Install Grafana
    apt-get update
    apt-get install -y grafana
    
    print_info "Grafana installed"
}

# Configure Grafana
configure_grafana() {
    print_info "Configuring Grafana..."
    
    # Create Grafana configuration directory
    mkdir -p /etc/grafana
    
    # Create Grafana ini configuration file
    cat > /etc/grafana/grafana.ini.ggnet2 <<EOF
[server]
;domain = foo.bar
root_url = %(protocol)s://%(domain)s${SUBPATH}
serve_from_sub_path = true

[auth.jwt]
enabled = true

# HTTP header to look into to get a JWT token.
header_name = X-JWT-Assertion

# auto-create users if they are not already matched
auto_sign_up = true

# Path to the public key pem file to validate JWT
key_file = /etc/grafana/certs/public_key.pem

# Claim to use as a username to sign in.
username_claim = sub

url_login = true

[security]
disable_initial_admin_creation = true
allow_embedding = true
EOF
    
    # Link configuration file
    ln -sf /etc/grafana/grafana.ini.ggnet2 /etc/grafana/grafana.ini
    
    print_info "Grafana configured"
}

# Setup JWT certificate
setup_jwt_cert() {
    print_info "Setting up JWT certificate..."
    
    # Create certificates directory
    mkdir -p /etc/grafana/certs
    
    # Generate JWT public key (if not exists)
    if [ ! -f /etc/grafana/certs/public_key.pem ]; then
        print_info "JWT public key not found, creating placeholder..."
        # Note: This should be replaced with actual JWT public key from backend
        echo "JWT public key should be placed here" > /etc/grafana/certs/public_key.pem
        print_info "Please replace /etc/grafana/certs/public_key.pem with actual JWT public key"
    fi
    
    # Set permissions
    chmod 644 /etc/grafana/certs/public_key.pem
    
    print_info "JWT certificate setup complete"
}

# Configure Prometheus datasource
configure_datasource() {
    print_info "Configuring Prometheus datasource..."
    
    # Create datasource provisioning directory
    mkdir -p /etc/grafana/provisioning/datasources
    
    # Create datasource configuration
    cat > /etc/grafana/provisioning/datasources/datasources.yml <<EOF
# config file version
apiVersion: 1

# list of datasources to insert/update depending
# what's available in the database
datasources:
  # <string, required> name of the datasource. Required
- name: Prometheus
  # <string, required> datasource type. Required
  type: prometheus
  # <string, required> access mode. proxy or direct (Server or Browser in the UI). Required
  access: proxy
  # <int> org id. will default to orgId 1 if not specified
  orgId: 1
  # <string> url
  url: http://localhost:5010
  # <bool> mark as default datasource. Max one per org
  isDefault: true
  # <map> fields that will be converted to json and stored in jsonData
  jsonData:
  # <string> json object of data that will be encrypted.
  secureJsonData:
  version: 1
  # <bool> allow users to edit datasources from the UI.
  editable: false
EOF
    
    print_info "Prometheus datasource configured"
}

# Configure dashboard provisioning
configure_dashboards() {
    print_info "Configuring dashboard provisioning..."
    
    # Create dashboard provisioning directory
    mkdir -p /etc/grafana/provisioning/dashboards
    mkdir -p /etc/grafana/provisioning/dashboards/ggnet2
    
    # Create dashboard provisioning configuration
    cat > /etc/grafana/provisioning/dashboards/ggnet2.yml <<EOF
apiVersion: 1

providers:
  # <string> an unique provider name
- name: 'ggnet2'
  # <int> org id. will default to orgId 1 if not specified
  orgId: 1
  # <string, required> name of the dashboard folder. Required
  folder: ''
  # <string> folder UID. will be automatically generated if not specified
  folderUid: ''
  # <string, required> provider type. Required
  type: file
  # <bool> disable dashboard deletion
  disableDeletion: true
  # <bool> enable dashboard editing
  editable: false
  # <int> how often Grafana will scan for changed dashboards
  updateIntervalSeconds: 60
  options:
    # <string, required> path to dashboard files on disk. Required
    path: /etc/grafana/provisioning/dashboards/ggnet2
EOF
    
    # Create basic dashboard
    create_basic_dashboard
    
    print_info "Dashboard provisioning configured"
}

# Create basic dashboard
create_basic_dashboard() {
    print_info "Creating basic dashboard..."
    
    # Create basic dashboard JSON
    cat > /etc/grafana/provisioning/dashboards/ggnet2/basic.json <<'EOF'
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": "-- Grafana --",
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": 1,
  "links": [],
  "panels": [
    {
      "datasource": "Prometheus",
      "description": "System uptime",
      "format": "s",
      "gridPos": {
        "h": 4,
        "w": 2,
        "x": 0,
        "y": 0
      },
      "id": 1,
      "targets": [
        {
          "expr": "node_time_seconds - node_boot_time_seconds",
          "refId": "A"
        }
      ],
      "title": "Uptime",
      "type": "stat"
    }
  ],
  "schemaVersion": 16,
  "style": "dark",
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-6h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "Basic Dashboard",
  "uid": "basic",
  "version": 1
}
EOF
    
    print_info "Basic dashboard created"
}

# Configure Systemd service
configure_systemd() {
    print_info "Configuring Grafana systemd service..."
    
    # Enable and start Grafana
    systemctl enable grafana-server
    systemctl start grafana-server
    
    print_info "Grafana systemd service configured"
}

# Main
main() {
    print_info "Starting Grafana setup..."
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        print_error "Please run as root (use sudo)"
        exit 1
    fi
    
    # Install Grafana
    install_grafana
    
    # Configure Grafana
    configure_grafana
    
    # Setup JWT certificate
    setup_jwt_cert
    
    # Configure Prometheus datasource
    configure_datasource
    
    # Configure dashboard provisioning
    configure_dashboards
    
    # Configure Systemd service
    configure_systemd
    
    print_info "Grafana setup complete!"
    print_info "Grafana is available at: https://localhost${SUBPATH}"
}

main "$@"
```

## Configuration

### Grafana Configuration File

**File:** `/etc/grafana/grafana.ini.ggnet2`

**Server Configuration:**
- **root_url**: `%(protocol)s://%(domain)s/ggnet2-grafana/grafana/` (sub-path serving)
- **serve_from_sub_path**: `true` (enable sub-path serving)

**JWT Authentication:**
- **enabled**: `true` (enable JWT authentication)
- **header_name**: `X-JWT-Assertion` (JWT token header)
- **auto_sign_up**: `true` (auto-create users)
- **key_file**: `/etc/grafana/certs/public_key.pem` (JWT public key)
- **username_claim**: `sub` (username claim)
- **url_login**: `true` (enable URL login)

**Security Configuration:**
- **disable_initial_admin_creation**: `true` (disable initial admin)
- **allow_embedding**: `true` (allow embedding)

### Prometheus Datasource Provisioning

**File:** `/etc/grafana/provisioning/datasources/datasources.yml`

**Datasource Configuration:**
- **name**: `Prometheus`
- **type**: `prometheus`
- **access**: `proxy` (server-side proxy)
- **url**: `http://localhost:5010` (Prometheus URL)
- **isDefault**: `true` (default datasource)
- **editable**: `false` (non-editable)

### Dashboard Provisioning

**File:** `/etc/grafana/provisioning/dashboards/ggnet2.yml`

**Provider Configuration:**
- **name**: `ggnet2`
- **orgId**: `1` (organization ID)
- **folder**: `` (root folder)
- **type**: `file` (file-based provisioning)
- **disableDeletion**: `true` (disable deletion)
- **editable**: `false` (non-editable)
- **updateIntervalSeconds**: `60` (scan interval)
- **path**: `/etc/grafana/provisioning/dashboards/ggnet2` (dashboard path)

### Basic Dashboard

**File:** `/etc/grafana/provisioning/dashboards/ggnet2/basic.json`

**Dashboard Configuration:**
- **title**: `Basic Dashboard`
- **uid**: `basic`
- **panels**: Uptime panel with Prometheus query
- **query**: `node_time_seconds - node_boot_time_seconds` (system uptime)

### Nginx Reverse Proxy

**Location Block:**
```nginx
# Grafana reverse proxy
location /ggnet2-grafana/grafana/ {
    proxy_pass http://localhost:3000;
    proxy_set_header Host $http_host;
}
```

**Access URL:**
- Grafana UI: `https://localhost/ggnet2-grafana/grafana/`

### JWT Certificate Setup

**Certificate File:** `/etc/grafana/certs/public_key.pem`

**Setup:**
- JWT public key should be placed in `/etc/grafana/certs/public_key.pem`
- Key is used to validate JWT tokens from backend
- Permissions: `644` (readable by Grafana)

**Note:** JWT public key should be generated by backend and placed in this location.

## Verification

### Check Grafana Status

```bash
# Check Grafana service status
systemctl status grafana-server

# Check Grafana logs
journalctl -u grafana-server -f

# Check Grafana configuration
grafana-server --config=/etc/grafana/grafana.ini --packaging=deb
```

### Check Grafana Web Interface

```bash
# Test Grafana endpoint (local)
curl http://localhost:3000/

# Test Grafana via Nginx reverse proxy
curl -k https://localhost/ggnet2-grafana/grafana/

# Check Grafana health endpoint
curl http://localhost:3000/api/health
```

### Check Datasource Provisioning

```bash
# Check datasource configuration
cat /etc/grafana/provisioning/datasources/datasources.yml

# Check datasource via API
curl http://localhost:3000/api/datasources
```

### Check Dashboard Provisioning

```bash
# Check dashboard provisioning configuration
cat /etc/grafana/provisioning/dashboards/ggnet2.yml

# Check dashboard files
ls -la /etc/grafana/provisioning/dashboards/ggnet2/

# Check dashboards via API
curl http://localhost:3000/api/search
```

### Verify Configuration

```bash
# Check Grafana configuration file
cat /etc/grafana/grafana.ini

# Check JWT certificate
cat /etc/grafana/certs/public_key.pem

# Check systemd service
systemctl status grafana-server
```

## Troubleshooting

### Grafana Not Starting

**Check Service Status:**
```bash
# Check Grafana service status
systemctl status grafana-server

# Check Grafana logs
journalctl -u grafana-server -n 50

# Check for errors
journalctl -u grafana-server | grep -i error
```

**Check Configuration:**
```bash
# Validate Grafana configuration
grafana-server --config=/etc/grafana/grafana.ini --packaging=deb --help

# Check if port is in use
netstat -tlnp | grep 3000
```

### JWT Authentication Not Working

**Check JWT Certificate:**
```bash
# Check JWT public key exists
test -f /etc/grafana/certs/public_key.pem && echo "Key exists" || echo "Key missing"

# Check JWT public key content
cat /etc/grafana/certs/public_key.pem

# Check permissions
ls -la /etc/grafana/certs/public_key.pem
```

**Check Grafana Configuration:**
```bash
# Check JWT authentication settings
grep -A 10 "auth.jwt" /etc/grafana/grafana.ini

# Check JWT header name
grep "header_name" /etc/grafana/grafana.ini
```

### Datasource Not Working

**Check Datasource:**
```bash
# Check datasource configuration
cat /etc/grafana/provisioning/datasources/datasources.yml

# Test Prometheus connection
curl http://localhost:5010/api/v1/query?query=up

# Check datasource via API
curl http://localhost:3000/api/datasources
```

**Check Prometheus:**
```bash
# Check Prometheus is running
systemctl status prometheus

# Test Prometheus endpoint
curl http://localhost:5010/
```

### Dashboard Not Loading

**Check Dashboard Files:**
```bash
# Check dashboard provisioning configuration
cat /etc/grafana/provisioning/dashboards/ggnet2.yml

# Check dashboard files
ls -la /etc/grafana/provisioning/dashboards/ggnet2/

# Validate dashboard JSON
cat /etc/grafana/provisioning/dashboards/ggnet2/basic.json | jq
```

**Check Dashboard via API:**
```bash
# List dashboards
curl http://localhost:3000/api/search

# Get dashboard by UID
curl http://localhost:3000/api/dashboards/uid/basic
```

### Nginx Reverse Proxy Not Working

**Check Nginx Configuration:**
```bash
# Check Nginx configuration
nginx -t

# Check Grafana location block
grep -A 5 "ggnet2-grafana" /etc/nginx/sites-available/ggnet2

# Check Nginx logs
tail -f /var/log/nginx/error.log
```

**Test Reverse Proxy:**
```bash
# Test Grafana via Nginx
curl -k https://localhost/ggnet2-grafana/grafana/

# Check Nginx access logs
tail -f /var/log/nginx/access.log | grep grafana
```

## Development Notes

- Grafana configuration is stored in `/etc/grafana/grafana.ini.ggnet2`
- Grafana listens on `localhost:3000` (not exposed publicly)
- Nginx reverse proxy provides HTTPS access at `/ggnet2-grafana/grafana/`
- JWT authentication is enabled for secure access
- Prometheus datasource is provisioned automatically
- Dashboards are provisioned from `/etc/grafana/provisioning/dashboards/ggnet2/`
- Sub-path serving is enabled for Nginx integration

## To-Do

- [ ] Add custom dashboard templates
- [ ] Implement alerting rules
- [ ] Add user management
- [ ] Implement backup and restore procedures
- [ ] Add high availability setup
- [ ] Implement custom panels

