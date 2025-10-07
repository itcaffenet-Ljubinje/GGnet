# Grafana Monitoring for GGnet

Grafana dashboards for visualizing GGnet diskless system metrics.

---

## 🎯 **What's Included**

### **Dashboards:**

1. **GGnet System Overview** (`ggnet-overview.json`)
   - Total Machines
   - Machines Online
   - Active Sessions
   - Boot Success Rate
   - Sessions & Machines Over Time
   - Storage Capacity

---

## 🚀 **Quick Start**

### **Start Grafana:**

```bash
docker-compose up -d grafana prometheus
```

### **Access Grafana:**

Open browser: `http://localhost:3001`

**Default Credentials:**
- Username: `admin`
- Password: `admin`

(Change on first login!)

---

## 📊 **Dashboards**

### **GGnet System Overview:**

**URL:** `http://localhost:3001/d/ggnet-overview`

**Panels:**
1. **Total Machines** - Total registered machines
2. **Machines Online** - Currently online machines
3. **Active Sessions** - Active diskless sessions
4. **Boot Success Rate** - PXE boot success percentage
5. **Sessions & Machines Timeline** - Historical data
6. **Storage Capacity** - Disk usage

---

## 🔧 **Configuration**

### **Datasource:**

Prometheus is automatically configured:
- **URL:** `http://prometheus:9090`
- **Scrape Interval:** 15s

### **Custom Dashboards:**

Add JSON files to `docker/grafana/dashboards/`

Example:
```bash
cp my-dashboard.json docker/grafana/dashboards/
docker-compose restart grafana
```

---

## 📈 **Metrics Available**

### **Machine Metrics:**
```prometheus
ggnet_machines_total      # Total machines
ggnet_machines_online     # Online machines
ggnet_machines_booting    # Currently booting
```

### **Session Metrics:**
```prometheus
ggnet_sessions_total       # Total sessions started
ggnet_sessions_active      # Active sessions
ggnet_session_duration_seconds  # Session duration histogram
ggnet_boot_success_rate    # Boot success percentage
```

### **Storage Metrics:**
```prometheus
ggnet_storage_total_bytes  # Total storage capacity
ggnet_storage_used_bytes   # Used storage
ggnet_storage_images_count # Number of images
```

### **Network Metrics:**
```prometheus
ggnet_network_boot_requests_total  # PXE boot requests
ggnet_network_dhcp_leases_active   # Active DHCP leases
ggnet_network_iscsi_connections    # iSCSI connections
```

### **iSCSI Metrics:**
```prometheus
ggnet_iscsi_targets_total   # Total iSCSI targets
ggnet_iscsi_targets_active  # Active targets
ggnet_iscsi_throughput_bytes_total  # iSCSI throughput
```

---

## 🔍 **Troubleshooting**

### **Dashboard Not Loading:**

```bash
# Check Grafana logs
docker-compose logs grafana

# Restart Grafana
docker-compose restart grafana
```

### **No Data Showing:**

```bash
# Check Prometheus
curl http://localhost:9090/api/v1/query?query=ggnet_machines_total

# Check if backend is exporting metrics
curl http://localhost:8000/metrics
```

### **Datasource Error:**

```bash
# Verify Prometheus is running
docker ps | grep prometheus

# Test Prometheus from Grafana container
docker exec -it ggnet-grafana wget -O- http://prometheus:9090/-/healthy
```

---

## 📚 **References**

- Grafana Docs: https://grafana.com/docs/
- Prometheus Docs: https://prometheus.io/docs/
- GGnet Metrics: `backend/app/middleware/metrics.py`

