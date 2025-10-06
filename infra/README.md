# GGnet Infra (Phase 6)

## Overview
Deployment and local development assets: installer, docker-compose, nginx, systemd, and example DHCP/TFTP configs.

## Quick Start

### Dry-run installer
```bash
sudo bash infra/install.sh --dry-run
```

### Local stack with Docker
```bash
cd infra
docker compose up -d --build
# Backend: http://localhost:8000
# Frontend (dev): http://localhost:5173
```

### Nginx reverse proxy (local)
```bash
sudo cp infra/nginx/ggnet.conf /etc/nginx/sites-available/ggnet.conf
sudo ln -sf /etc/nginx/sites-available/ggnet.conf /etc/nginx/sites-enabled/ggnet.conf
sudo systemctl restart nginx
```

### Systemd units (staging/production)
```bash
sudo cp infra/systemd/ggnet-*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ggnet-backend ggnet-worker
sudo systemctl start ggnet-backend ggnet-worker
```

## Paths
- Backend code: `/opt/ggnet/backend`
- Python venv: `/opt/ggnet/venv`
- Images: `/var/lib/gg/images`
- TFTP root: `/var/lib/tftpboot`

## Notes
- Adjust nginx upstreams for production (serve built frontend)
- `targetcli` operations require root; use with care
- DHCP/TFTP examples are templates—review IPs and paths
