# Prometheus Setup Script

The Prometheus setup script (`setup-prometheus.sh`) installs and configures Prometheus for system monitoring in ggnet2.

## Overview

The Prometheus setup script:

- Installs Prometheus and node_exporter
- Configures Prometheus scraping targets
- Sets up Prometheus web interface
- Configures Nginx reverse proxy for Prometheus
- Enables and starts Prometheus service

## Usage

```bash
# Run Prometheus setup script
sudo bash scripts/setup-prometheus.sh

# Or with custom configuration
PROMETHEUS_PORT=5010 bash scripts/setup-prometheus.sh
```

## Script Structure

**setup-prometheus.sh:**
```bash
#!/bin/bash

set -e

# Configuration
PROMETHEUS_PORT="${PROMETHEUS_PORT:-5010}"
NODE_EXPORTER_PORT="${NODE_EXPORTER_PORT:-9100}"
EXTERNAL_URL="${EXTERNAL_URL:-http://localhost/ggnet2-prometheus}"

# Functions
print_info() {
    echo "[INFO] $1"
}

print_error() {
    echo "[ERROR] $1" >&2
}

# Install Prometheus
install_prometheus() {
    print_info "Installing Prometheus..."
    
    apt-get update
    apt-get install -y prometheus prometheus-node-exporter
    
    print_info "Prometheus installed"
}

# Configure Prometheus
configure_prometheus() {
    print_info "Configuring Prometheus..."
    
    # Create Prometheus configuration directory
    mkdir -p /etc/prometheus
    
    # Create Prometheus configuration file
    cat > /etc/prometheus/prometheus.yml.ggnet2 <<EOF
# my global config
global:
  scrape_interval:     15s # Set the scrape interval to every 15 seconds. Default is every 1 minute.
  evaluation_interval: 15s # Evaluate rules every 15 seconds. The default is every 1 minute.
  # scrape_timeout is set to the global default (10s).

  # Attach these labels to any time series or alerts when communicating with
  # external systems (federation, remote storage, Alertmanager).
  external_labels:
    monitor: 'ggnet2-monitor'

# Alertmanager configuration
alerting:
  alertmanagers:
  - static_configs:
    - targets:
      # - alertmanager:9093

# Load rules once and periodically evaluate them according to the global 'evaluation_interval'.
rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

# A scrape configuration containing exactly one endpoint to scrape:
# Here it's Prometheus itself.
scrape_configs:
  # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
  - job_name: 'prometheus'

    # Override the global default and scrape targets from this job every 5 seconds.
    scrape_interval: 5s
    
    # metrics_path defaults to '/metrics'
    # scheme defaults to 'http'.

    static_configs:
    - targets: ['localhost:${NODE_EXPORTER_PORT}']
EOF
    
    # Create default configuration file
    cat > /etc/default/prometheus.ggnet2 <<EOF
ARGS="--web.listen-address=localhost:${PROMETHEUS_PORT} --web.external-url=${EXTERNAL_URL} --web.route-prefix=/"
EOF
    
    # Link configuration file
    ln -sf /etc/prometheus/prometheus.yml.ggnet2 /etc/prometheus/prometheus.yml
    
    # Link default configuration file
    ln -sf /etc/default/prometheus.ggnet2 /etc/default/prometheus
    
    print_info "Prometheus configured"
}

# Configure Systemd service
configure_systemd() {
    print_info "Configuring Prometheus systemd service..."
    
    # Create systemd override directory
    mkdir -p /etc/systemd/system/prometheus.service.d
    
    # Create override file
    cat > /etc/systemd/system/prometheus.service.d/override.conf <<EOF
[Service]
EnvironmentFile=-/etc/default/prometheus
ExecStart=
ExecStart=/usr/bin/prometheus \$ARGS --config.file=/etc/prometheus/prometheus.yml --storage.tsdb.path=/var/lib/prometheus
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable and start Prometheus
    systemctl enable prometheus
    systemctl start prometheus
    
    print_info "Prometheus systemd service configured"
}

# Main
main() {
    print_info "Starting Prometheus setup..."
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        print_error "Please run as root (use sudo)"
        exit 1
    fi
    
    # Install Prometheus
    install_prometheus
    
    # Configure Prometheus
    configure_prometheus
    
    # Configure Systemd service
    configure_systemd
    
    print_info "Prometheus setup complete!"
    print_info "Prometheus is available at: ${EXTERNAL_URL}"
}

main "$@"
```

## Configuration

### Prometheus Configuration File

**File:** `/etc/prometheus/prometheus.yml.ggnet2`

**Global Configuration:**
- **scrape_interval**: `15s` (scrape targets every 15 seconds)
- **evaluation_interval**: `15s` (evaluate rules every 15 seconds)
- **external_labels**: `monitor: 'ggnet2-monitor'` (label for all metrics)

**Scrape Configuration:**
- **job_name**: `prometheus`
- **scrape_interval**: `5s` (override global interval for Prometheus job)
- **targets**: `['localhost:9100']` (node_exporter)

**Default Configuration File:**

**File:** `/etc/default/prometheus.ggnet2`

**Arguments:**
- `--web.listen-address=localhost:5010` (listen on localhost:5010)
- `--web.external-url=http://localhost/ggnet2-prometheus` (external URL for reverse proxy)
- `--web.route-prefix=/` (route prefix for sub-path serving)

### Nginx Reverse Proxy

**Location Block:**
```nginx
# Prometheus reverse proxy
location /ggnet2-prometheus/ {
    proxy_pass http://localhost:5010/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

**Access URL:**
- Prometheus UI: `https://localhost/ggnet2-prometheus/`

### Systemd Service

**Service File:** `/etc/systemd/system/prometheus.service`

**Override Configuration:**
- Environment file: `/etc/default/prometheus`
- Config file: `/etc/prometheus/prometheus.yml`
- Storage path: `/var/lib/prometheus`

**Service Management:**
```bash
# Start Prometheus
systemctl start prometheus

# Enable Prometheus (start on boot)
systemctl enable prometheus

# Check Prometheus status
systemctl status prometheus
```

## Verification

### Check Prometheus Status

```bash
# Check Prometheus service status
systemctl status prometheus

# Check Prometheus logs
journalctl -u prometheus -f

# Check Prometheus configuration
prometheus --config.file=/etc/prometheus/prometheus.yml --check-config
```

### Check Prometheus Web Interface

```bash
# Test Prometheus endpoint (local)
curl http://localhost:5010/

# Test Prometheus metrics endpoint
curl http://localhost:5010/metrics

# Test Prometheus via Nginx reverse proxy
curl -k https://localhost/ggnet2-prometheus/
```

### Check Scrape Targets

```bash
# Check Prometheus targets
curl http://localhost:5010/api/v1/targets

# Check node_exporter metrics
curl http://localhost:9100/metrics
```

### Verify Configuration

```bash
# Check Prometheus configuration file
cat /etc/prometheus/prometheus.yml

# Check default configuration file
cat /etc/default/prometheus

# Check systemd override
cat /etc/systemd/system/prometheus.service.d/override.conf
```

## Troubleshooting

### Prometheus Not Starting

**Check Service Status:**
```bash
# Check Prometheus service status
systemctl status prometheus

# Check Prometheus logs
journalctl -u prometheus -n 50

# Check for errors
journalctl -u prometheus | grep -i error
```

**Check Configuration:**
```bash
# Validate Prometheus configuration
prometheus --config.file=/etc/prometheus/prometheus.yml --check-config

# Check if port is in use
netstat -tlnp | grep 5010
```

### Scrape Targets Not Working

**Check Targets:**
```bash
# Check Prometheus targets status
curl http://localhost:5010/api/v1/targets | jq

# Check node_exporter
systemctl status prometheus-node-exporter

# Test node_exporter endpoint
curl http://localhost:9100/metrics
```

**Check Network:**
```bash
# Test localhost connection
telnet localhost 9100

# Check firewall rules
iptables -L -n | grep 9100
```

### Nginx Reverse Proxy Not Working

**Check Nginx Configuration:**
```bash
# Check Nginx configuration
nginx -t

# Check Prometheus location block
grep -A 5 "ggnet2-prometheus" /etc/nginx/sites-available/ggnet2

# Check Nginx logs
tail -f /var/log/nginx/error.log
```

**Test Reverse Proxy:**
```bash
# Test Prometheus via Nginx
curl -k https://localhost/ggnet2-prometheus/

# Check Nginx access logs
tail -f /var/log/nginx/access.log | grep prometheus
```

## Development Notes

- Prometheus configuration is stored in `/etc/prometheus/prometheus.yml.ggnet2`
- Default configuration is stored in `/etc/default/prometheus.ggnet2`
- Prometheus listens on `localhost:5010` (not exposed publicly)
- Nginx reverse proxy provides HTTPS access at `/ggnet2-prometheus/`
- node_exporter runs on `localhost:9100` and provides system metrics
- External labels are added to all metrics for identification

## To-Do

- [ ] Add alerting rules configuration
- [ ] Implement alertmanager integration
- [ ] Add custom metrics collection
- [ ] Implement data retention policies
- [ ] Add backup and restore procedures
- [ ] Implement high availability setup

