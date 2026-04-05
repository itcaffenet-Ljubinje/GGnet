# Monitoring & Alerting Setup - Complete Guide

**Date:** 2025-01-26  
**Status:** ✅ **SETUP COMPLETE**

---

## 🎯 **Overview**

Complete monitoring and alerting setup for GGnet using Prometheus and Grafana.

---

## 📊 **What's Included**

### **1. Prometheus Metrics Collection** ✅

- ✅ Backend metrics endpoint: `/metrics`
- ✅ Prometheus scraping configuration
- ✅ Metrics for:
  - HTTP requests
  - System resources (CPU, memory, disk)
  - Database metrics
  - Machine status
  - Session metrics
  - Storage metrics

### **2. Grafana Dashboards** ✅

- ✅ **GGnet Overview Dashboard** - High-level metrics
- ✅ **GGnet Detailed Dashboard** - Comprehensive monitoring
- ✅ Auto-provisioned from JSON files
- ✅ Pre-configured Prometheus datasource

### **3. Prometheus Alerting Rules** ✅

- ✅ Service health alerts
- ✅ System resource alerts
- ✅ Storage alerts
- ✅ Session alerts
- ✅ Network alerts
- ✅ Security alerts

---

## 🚀 **Quick Start**

### **1. Start Monitoring Services**

```bash
# Start Prometheus and Grafana
docker-compose up -d prometheus grafana

# Or start all services
docker-compose up -d
```

### **2. Access Dashboards**

- **Grafana:** http://localhost:3001
  - Username: `admin`
  - Password: `admin` (change on first login!)

- **Prometheus:** http://localhost:9090
  - Query metrics directly
  - View alerts

- **Alert Rules:** Configured in `docker/prometheus/alerts.yml`

---

## 📈 **Available Metrics**

### **System Metrics**

```prometheus
ggnet_system_cpu_percent          # CPU usage percentage
ggnet_system_memory_percent       # Memory usage percentage
ggnet_system_disk_percent         # Disk usage percentage
ggnet_system_memory_bytes         # Memory usage in bytes
ggnet_system_disk_bytes           # Disk usage in bytes
```

### **Application Metrics**

```prometheus
ggnet_http_requests_total         # Total HTTP requests
ggnet_http_request_duration_seconds  # Request duration
ggnet_active_sessions             # Active sessions
ggnet_total_machines              # Total machines
ggnet_machines_online             # Online machines
ggnet_total_images                # Total images
ggnet_total_targets               # Total iSCSI targets
ggnet_total_users                 # Total users
```

### **Network Metrics**

```prometheus
ggnet_network_boot_requests_total # PXE boot requests
ggnet_network_dhcp_leases_active  # Active DHCP leases
ggnet_network_iscsi_connections   # iSCSI connections
```

---

## 🚨 **Alert Rules**

### **Critical Alerts**

1. **BackendDown** - Backend service is down
2. **DatabaseDown** - Database connection failed
3. **CriticalDiskUsage** - Disk usage > 95%

### **Warning Alerts**

1. **HighCPUUsage** - CPU > 90%
2. **HighMemoryUsage** - Memory > 90%
3. **HighDiskUsage** - Disk > 85%
4. **StorageLowSpace** - Storage < 10% free
5. **HighSessionFailureRate** - > 20% session failures
6. **SlowResponseTime** - API response > 2 seconds

### **Info Alerts**

1. **NoActiveSessions** - No sessions for 10+ minutes
2. **NoBootRequests** - No PXE boots in 30+ minutes

---

## 📧 **Setting Up Notifications**

### **Option 1: Email Notifications (Alertmanager)**

1. **Add Alertmanager to docker-compose.yml:**

```yaml
alertmanager:
  image: prom/alertmanager:latest
  container_name: ggnet-alertmanager
  volumes:
    - ./docker/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml
  ports:
    - "9093:9093"
  restart: unless-stopped
```

2. **Configure Alertmanager** (`docker/alertmanager/alertmanager.yml`):

```yaml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alerts@ggnet.local'
  smtp_auth_username: 'alerts@ggnet.local'
  smtp_auth_password: 'your-password'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical'
      continue: true

receivers:
  - name: 'default'
    email_configs:
      - to: 'admin@ggnet.local'
        send_resolved: true

  - name: 'critical'
    email_configs:
      - to: 'oncall@ggnet.local'
        send_resolved: true
```

### **Option 2: Slack Notifications**

Add to Alertmanager configuration:

```yaml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#ggnet-alerts'
        title: 'GGnet Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

---

## 📊 **Grafana Dashboards**

### **1. GGnet Overview**

**URL:** `http://localhost:3001/d/ggnet-overview`

**Panels:**
- Total Machines
- Machines Online
- Active Sessions
- Boot Success Rate
- Sessions & Machines Timeline
- Storage Capacity

### **2. GGnet Detailed**

**URL:** `http://localhost:3001/d/ggnet-detailed`

**Panels:**
- System Overview (row)
- CPU Usage (graph)
- Memory Usage (graph)
- Storage Usage (graph)
- HTTP Request Rate (graph)
- Active Sessions (graph)
- Machines Status (graph)

---

## 🔧 **Configuration Files**

### **Prometheus Configuration**

- **Location:** `docker/prometheus/prometheus.yml`
- **Alerts:** `docker/prometheus/alerts.yml`
- **Scrape Interval:** 15 seconds
- **Retention:** 30 days

### **Grafana Configuration**

- **Dashboards:** `docker/grafana/dashboards/*.json`
- **Datasource:** Auto-configured Prometheus
- **Provisioning:** `docker/grafana/provisioning/`

---

## 📋 **Alert Configuration Checklist**

- [ ] Review alert thresholds in `docker/prometheus/alerts.yml`
- [ ] Adjust alert intervals based on your needs
- [ ] Set up Alertmanager for notifications (optional)
- [ ] Configure email/Slack notifications
- [ ] Test alert rules in Prometheus UI
- [ ] Verify alerts appear in Grafana

---

## 🎯 **Next Steps**

### **Immediate:**
1. Review and adjust alert thresholds
2. Set up Alertmanager (if notifications needed)
3. Configure notification channels
4. Test alert rules

### **Short-term:**
1. Add more custom dashboards
2. Set up additional exporters (PostgreSQL, Redis)
3. Configure alert routing and grouping
4. Create runbook documentation

### **Long-term:**
1. Set up external alerting services
2. Integrate with incident management
3. Create custom metrics exporters
4. Set up log aggregation (Loki)

---

## ✅ **Status: Complete**

All monitoring and alerting infrastructure is set up and ready to use!

**Files Created:**
- ✅ `docker/prometheus/alerts.yml` - Alert rules
- ✅ `docker/grafana/dashboards/ggnet-detailed.json` - Detailed dashboard
- ✅ `MONITORING_ALERTING_SETUP.md` - This guide

**Files Updated:**
- ✅ `docker/prometheus/prometheus.yml` - Added alert rules loading

---

**Last Updated:** 2025-01-26

