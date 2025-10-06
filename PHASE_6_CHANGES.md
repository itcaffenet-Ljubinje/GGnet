## Phase 6 — Infra & Deploy Scripts

This phase introduces installation automation, container orchestration for local dev, reverse proxy configuration, example PXE/iPXE and DHCP configs, and systemd unit files.

### What was added

- `infra/install.sh`
  - Debian/Ubuntu oriented installer
  - Supports `--dry-run` to preview steps without changing the system
  - Installs: python3(+venv/pip), redis-server, qemu-utils, targetcli-fb, tftpd-hpa, isc-dhcp-server, nginx, docker
  - Creates `ggnet` system user and directories
  - Creates Python venv at `/opt/ggnet/venv`, installs backend requirements if present
  - Installs systemd units and nginx site config, enables services

- `infra/docker-compose.yml`
  - Services: `db` (Postgres 15), `redis` (Redis 7), `backend`, `frontend`
  - Volumes for persistence and image storage
  - Exposes `8000` (backend API) and `5173` (frontend dev)

- `infra/nginx/ggnet.conf`
  - Proxies `/` to `http://localhost:5173` (frontend dev) and `/api/` to `http://localhost:8000`
  - WebSocket upgrade on `/ws/`

- `infra/systemd/ggnet-backend.service`, `infra/systemd/ggnet-worker.service`
  - Backend served by `uvicorn` from `/opt/ggnet/backend`
  - Worker runs `python -m worker.convert`

- `infra/examples/dhcpd.conf`
  - Example ISC-DHCP server pool with TFTP info and static reservation

- `infra/examples/tftp/boot.ipxe`
  - Example iPXE script that chains to backend-generated script; fallback iSCSI boot

### Notes and assumptions

- Host OS: Debian/Ubuntu (tested target)
- Backend code expected under `/opt/ggnet/backend` when using systemd units
- Nginx site references localhost ports for dev; adjust for production
- For production, serve built frontend via nginx root instead of Vite dev server


