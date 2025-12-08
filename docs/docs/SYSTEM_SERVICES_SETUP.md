# System Services Setup Guide

**Datum kreiranja:** 2025-01-26  
**Status:** 📋 System Services Configuration Guide

---

## 📊 Pregled

Ovaj dokument opisuje konfiguraciju system services za ggNET2 sistem: systemd services, Nginx reverse proxy, i firewall.

**Napomena:** Sve ovo je već pokriveno u `docs/DEPLOYMENT_COMPLETE_GUIDE.md`. Ovaj dokument je sažetak i referenca.

---

## 🔧 Systemd Services

### Backend Service

**Fajl:** `/etc/systemd/system/ggnet2-backend.service`

**Konfiguracija:**
```ini
[Unit]
Description=ggNET2 Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=ggnet2
Group=ggnet2
WorkingDirectory=/opt/ggnet2
Environment="PATH=/opt/ggnet2/venv/bin"
ExecStart=/opt/ggnet2/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Komande:**
```bash
# Create service file
sudo vim /etc/systemd/system/ggnet2-backend.service
# (paste configuration above)

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ggnet2-backend
sudo systemctl start ggnet2-backend
sudo systemctl status ggnet2-backend
```

**Verifikacija:**
```bash
# Check service status
sudo systemctl status ggnet2-backend

# Check logs
sudo journalctl -u ggnet2-backend -n 50

# Test API
curl http://localhost:8000/api/v1/ping
```

---

## 🌐 Nginx Reverse Proxy

### Nginx Configuration

**Fajl:** `/etc/nginx/sites-available/ggnet2`

**Konfiguracija:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /opt/ggnet2/app/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Komande:**
```bash
# Create configuration file
sudo vim /etc/nginx/sites-available/ggnet2
# (paste configuration above)

# Enable site
sudo ln -s /etc/nginx/sites-available/ggnet2 /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

**Verifikacija:**
```bash
# Check Nginx status
sudo systemctl status nginx

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Test frontend
curl http://localhost/

# Test API through Nginx
curl http://localhost/api/v1/ping
```

---

## 🔥 Firewall Configuration

### UFW (Uncomplicated Firewall)

**Komande:**
```bash
# Install UFW (if not installed)
sudo apt install -y ufw

# Configure firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Backend only accessible via Nginx

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

**Firewall Rules:**
- **SSH (22/tcp)**: Allowed (for server access)
- **HTTP (80/tcp)**: Allowed (for frontend)
- **HTTPS (443/tcp)**: Allowed (for SSL/TLS)
- **Backend (8000/tcp)**: Denied (only accessible via Nginx on localhost)

**Verifikacija:**
```bash
# Check firewall status
sudo ufw status

# Check specific port
sudo ufw status | grep 80
sudo ufw status | grep 443
```

---

## ✅ Services Checklist

### Systemd Services
- [ ] Backend service file created
- [ ] Service enabled
- [ ] Service started
- [ ] Service status verified
- [ ] Logs accessible
- [ ] Auto-start on boot verified

### Nginx
- [ ] Nginx installed
- [ ] Configuration file created
- [ ] Site enabled
- [ ] Configuration tested
- [ ] Nginx reloaded
- [ ] Frontend accessible
- [ ] API accessible through Nginx
- [ ] WebSocket working

### Firewall
- [ ] UFW installed
- [ ] Default rules configured
- [ ] SSH allowed
- [ ] HTTP/HTTPS allowed
- [ ] Backend port denied
- [ ] Firewall enabled
- [ ] Rules verified

---

## 🔍 Troubleshooting

### Backend Service Not Starting

```bash
# Check service status
sudo systemctl status ggnet2-backend

# Check logs
sudo journalctl -u ggnet2-backend -n 100

# Check if port is in use
sudo netstat -tulpn | grep 8000

# Check permissions
ls -la /opt/ggnet2
```

### Nginx Not Working

```bash
# Test configuration
sudo nginx -t

# Check Nginx status
sudo systemctl status nginx

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Check if Nginx is listening
sudo netstat -tulpn | grep nginx
```

### Firewall Blocking Access

```bash
# Check firewall status
sudo ufw status

# Check if port is allowed
sudo ufw status | grep 80
sudo ufw status | grep 443

# Temporarily disable firewall for testing (NOT recommended in production)
sudo ufw disable
# Test access
# Re-enable firewall
sudo ufw enable
```

---

## 📚 Reference

- **Deployment Guide:** `docs/DEPLOYMENT_COMPLETE_GUIDE.md`
- **Production Readiness:** `docs/PRODUCTION_READINESS_GUIDE.md`
- **Nginx Documentation:** https://nginx.org/en/docs/
- **Systemd Documentation:** https://www.freedesktop.org/software/systemd/man/

---

**System Services Setup Complete!** ✅

