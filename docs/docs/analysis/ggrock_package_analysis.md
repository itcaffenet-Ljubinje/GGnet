# ggRock Package Analysis

Analiza `ggrock_0.1.2200.2324-1_amd64` paketa i šta možemo iskoristiti za ggnet2 projekt.

## Struktura Paketa

```
ggrock_0.1.2200.2324-1_amd64/data/
├── etc/
│   ├── default/prometheus.ggrock
│   ├── grafana/
│   │   ├── grafana.ini.ggrock
│   │   └── provisioning/
│   │       ├── dashboards/ggrock.yml
│   │       ├── dashboards/ggrock/basic.json
│   │       └── datasources/datasources.yml
│   ├── nginx/
│   │   ├── conf.d/ggrock.conf
│   │   ├── snippets/ggrock-cert.conf
│   │   └── ssl/
│   └── prometheus/prometheus.yml.ggrock
├── lib/systemd/system/
│   ├── ggrock.service
│   └── ggrock-novnc.service
├── opt/ggrock/app/
│   ├── GgRock.Api (executable)
│   ├── GgRock.Api.dll
│   └── ggRockPocUi/ (frontend build)
└── usr/sbin/ggrock-cert-mgr
```

## Komponente koje možemo iskoristiti

### 1. Nginx Konfiguracija

**Fajl:** `etc/nginx/conf.d/ggrock.conf`

**Ključne funkcionalnosti:**
- **SSL/HTTPS konfiguracija** sa self-signed sertifikatima
- **SignalR WebSocket proxy** (`/hubs` location)
- **VNC/WebSocket proxy** za VM konzolu (`/vnc/`, `/websockify`)
- **PXE Boot support** (`/boot/script`, `/boot/files/`)
- **Grafana reverse proxy** (`/ggrock-grafana/grafana/`)
- **HTTP to HTTPS redirect**
- **HSTS headers**
- **Gzip compression**
- **Client max body size** (100M)

**Primenljivo za ggnet2:**
- ✅ Kompletan SSL/HTTPS setup
- ✅ SignalR WebSocket proxy konfiguracija
- ✅ VNC proxy za VM konzolu
- ✅ PXE boot podrška
- ✅ Security headers (HSTS)
- ✅ Compression i optimizacije

### 2. Systemd Service Fajlovi

**Fajlovi:**
- `lib/systemd/system/ggrock.service` - Backend API service
- `lib/systemd/system/ggrock-novnc.service` - VNC/WebSocket proxy service

**ggrock.service:**
```ini
[Unit]
Description=ggRock diskless boot system
After=libvirtd.service

[Service]
WorkingDirectory=/opt/ggrock/app
ExecStart=/opt/ggrock/app/GgRock.Api
Restart=always
RestartSec=10
KillSignal=SIGINT
SyslogIdentifier=ggrock

[Install]
WantedBy=multi-user.target
```

**ggrock-novnc.service:**
```ini
[Unit]
Description=ggRock VNC client for VMs
After=network.target

[Service]
ExecStart=/usr/bin/websockify --web=/usr/share/novnc \
  --token-plugin TokenFile \
  --token-source /etc/ggrock/websockify/target.config.d/ \
  127.0.0.1:6080
Restart=always
RestartSec=2
SyslogIdentifier=ggrock-novnc

[Install]
WantedBy=multi-user.target
```

**Primenljivo za ggnet2:**
- ✅ Backend API service struktura
- ✅ VNC/WebSocket service sa token-based pristupom
- ✅ Restart policies
- ✅ Dependency management (`After=libvirtd.service`)

### 3. SSL Certificate Management

**Fajl:** `usr/sbin/ggrock-cert-mgr`

**Funkcionalnosti:**
- Generiše self-signed SSL sertifikate
- Podržava custom DNS i IP adrese
- Automatski dodaje hostname i IP adrese
- Kreira sertifikate sa 10 godina važenja
- Konfiguriše `/etc/nginx/ssl/certs/` i `/etc/nginx/ssl/private/`

**Primenljivo za ggnet2:**
- ✅ Automatska generacija self-signed sertifikata
- ✅ Podrška za custom DNS/IP adrese
- ✅ Integracija sa Nginx konfiguracijom

### 4. Prometheus Konfiguracija

**Fajl:** `etc/prometheus/prometheus.yml.ggrock`

**Funkcionalnosti:**
- Scrape interval: 15s
- Evaluation interval: 15s
- Prometheus metrics scraping na portu 9100
- External labels sa `monitor: 'ggrock-monitor'`

**Default konfiguracija:**
```yaml
# /etc/default/prometheus.ggrock
ARGS="--web.listen-address=localhost:5010 \
      --web.external-url=http://localhost/prometheus \
      --web.route-prefix=/"
```

**Primenljivo za ggnet2:**
- ✅ Prometheus monitoring setup
- ✅ Metrics scraping konfiguracija
- ✅ External URL konfiguracija za reverse proxy

### 5. Grafana Konfiguracija

**Fajlovi:**
- `etc/grafana/grafana.ini.ggrock` - Main Grafana konfiguracija
- `etc/grafana/provisioning/datasources/datasources.yml` - Prometheus datasource
- `etc/grafana/provisioning/dashboards/ggrock.yml` - Dashboard provisioning
- `etc/grafana/provisioning/dashboards/ggrock/basic.json` - Dashboard definicija

**Ključne funkcionalnosti:**
- **Sub-path serving:** `/ggrock-grafana/grafana/`
- **JWT authentication** sa custom header
- **Auto-signup** za nove korisnike
- **Dashboard provisioning** iz fajlova
- **Prometheus datasource** automatski konfigurisan

**Primenljivo za ggnet2:**
- ✅ Grafana sub-path konfiguracija
- ✅ JWT authentication setup
- ✅ Dashboard provisioning
- ✅ Prometheus datasource integracija

### 6. VNC/WebSocket Proxy Konfiguracija

**Nginx location blocks:**
```nginx
# VNC console access
location = /vnc/console {
    proxy_pass http://vnc_proxy/vnc.html;
}

location /vnc/ {
    proxy_pass http://vnc_proxy/;
}

location /websockify {
    proxy_http_version 1.1;
    proxy_pass http://vnc_proxy/;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 61s;
    proxy_buffering off;
}
```

**Upstream konfiguracija:**
```nginx
upstream vnc_proxy {
    server 127.0.0.1:6080;
}
```

**Primenljivo za ggnet2:**
- ✅ VNC/WebSocket proxy setup
- ✅ Timeout konfiguracija
- ✅ WebSocket upgrade headers
- ✅ noVNC integracija

### 7. PXE Boot Support

**Nginx location blocks:**
```nginx
# Don't use HTTPS for boot script
location /boot/script {
    proxy_pass http://localhost:5000/boot/script;
}

location /boot/files/ {
    alias /opt/ggrock/boot_files/;
    autoindex on;
}
```

**Primenljivo za ggnet2:**
- ✅ PXE boot endpoint podrška
- ✅ Boot files serving
- ✅ HTTP-only endpoint za PXE

## Preporuke za implementaciju

### Prioritet 1: Visoka važnost

1. **Nginx SSL/HTTPS konfiguracija**
   - Kompletan SSL setup sa self-signed sertifikatima
   - HTTP to HTTPS redirect
   - HSTS headers
   - Security best practices

2. **SignalR WebSocket proxy**
   - Kompletan WebSocket proxy setup
   - Upgrade headers
   - Timeout konfiguracija

3. **VNC/WebSocket proxy**
   - noVNC integracija
   - WebSocket proxy za VM konzolu
   - Timeout i buffering konfiguracija

4. **Systemd service fajlovi**
   - Backend API service
   - VNC/WebSocket service
   - Restart policies i dependency management

### Prioritet 2: Srednja važnost

5. **SSL Certificate Management**
   - Automatska generacija self-signed sertifikata
   - Custom DNS/IP podrška

6. **PXE Boot Support**
   - Boot script endpoint
   - Boot files serving

### Prioritet 3: Niska važnost (opcionalno)

7. **Prometheus Integration**
   - Metrics scraping setup
   - External URL konfiguracija

8. **Grafana Integration**
   - Sub-path serving
   - JWT authentication
   - Dashboard provisioning

## Implementacioni detalji

### Nginx Konfiguracija

**Ažurirati:** `docs/scripts/setup_nginx.md`

**Dodati:**
- Kompletan SSL/HTTPS setup
- VNC/WebSocket proxy konfiguracija
- PXE boot location blocks
- Security headers (HSTS)
- Gzip compression
- Client max body size

### Systemd Services

**Kreirati:** `docs/scripts/setup_systemd.md`

**Dodati:**
- Backend API service
- VNC/WebSocket service
- Service dependency management
- Restart policies

### SSL Certificate Management

**Kreirati:** `docs/scripts/setup_ssl.md`

**Dodati:**
- Self-signed certificate generation
- Custom DNS/IP podrška
- Nginx SSL konfiguracija integracija

### VNC/WebSocket Setup

**Ažurirati:** `docs/backend/vms.md`

**Dodati:**
- noVNC service setup
- WebSocket proxy konfiguracija
- Token-based pristup
- Nginx proxy setup

## Zaključak

**Komponente koje treba implementirati:**
1. ✅ Nginx SSL/HTTPS konfiguracija (visok prioritet)
2. ✅ SignalR WebSocket proxy (visok prioritet)
3. ✅ VNC/WebSocket proxy (visok prioritet)
4. ✅ Systemd service fajlovi (visok prioritet)
5. ✅ SSL Certificate Management (srednji prioritet)
6. ✅ PXE Boot Support (srednji prioritet)
7. ⚠️ Prometheus Integration (opcionalno)
8. ⚠️ Grafana Integration (opcionalno)

**Sledeći koraci:**
1. Ažurirati `docs/scripts/setup_nginx.md` sa kompletnom Nginx konfiguracijom
2. Kreirati `docs/scripts/setup_systemd.md` sa service fajlovima
3. Kreirati `docs/scripts/setup_ssl.md` sa SSL certificate management
4. Ažurirati `docs/backend/vms.md` sa VNC/WebSocket setup detaljima

