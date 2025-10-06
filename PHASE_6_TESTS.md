## Phase 6 — Testing Guide

### 1) Install script dry-run

Commands:
```bash
sudo bash infra/install.sh --dry-run
```
Acceptance:
- Outputs apt install list
- Creates/owns dirs in echo only
- Installs systemd/nginx files in echo only

### 2) Local stack with Docker

Commands:
```bash
cd infra
docker compose up -d --build
docker compose ps
```
Acceptance:
- `db`, `redis`, `backend`, `frontend` are healthy/running
- `curl http://localhost:8000/api/v1/health` returns 200 (if health endpoint exists)
- Frontend served on `http://localhost:5173`

### 3) Nginx proxy (optional local)

Commands:
```bash
sudo cp infra/nginx/ggnet.conf /etc/nginx/sites-available/ggnet.conf
sudo ln -sf /etc/nginx/sites-available/ggnet.conf /etc/nginx/sites-enabled/ggnet.conf
sudo systemctl restart nginx
```
Acceptance:
- `http://localhost/` proxies to `:5173`
- `http://localhost/api/` proxies to `:8000`

### 4) Systemd units (staging host)

Commands:
```bash
sudo cp infra/systemd/ggnet-*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ggnet-backend ggnet-worker
sudo systemctl start ggnet-backend ggnet-worker
sudo systemctl status ggnet-backend ggnet-worker
```
Acceptance:
- Services start and restart on failure
- Logs visible via `journalctl -u ggnet-backend -f`

### 5) DHCP/TFTP examples

Manual validation:
- `infra/examples/dhcpd.conf` contains correct subnet, range, next-server
- `infra/examples/tftp/boot.ipxe` chains to backend script and has iSCSI fallback


