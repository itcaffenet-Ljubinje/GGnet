## Phase 6 — Assumptions

### Platform
- Debian/Ubuntu host with sudo/root access
- Python 3.11+ available as `python3`
- Node 18+ for frontend builds (if building on host)

### Paths and users
- System user `ggnet` will own `/opt/ggnet` and runtime dirs
- Backend code deployed to `/opt/ggnet/backend`
- Python venv at `/opt/ggnet/venv`
- Image storage under `/var/lib/gg/images`
- TFTP root at `/var/lib/tftpboot`

### Networking
- Backend on `:8000`, frontend dev on `:5173`
- Nginx reverse proxy on `:80`
- DHCP/TFTP examples assume LAN `192.168.1.0/24`

### External tools
- `qemu-img` from `qemu-utils`
- `targetcli-fb` for iSCSI target management (requires root)
- `tftpd-hpa` and `isc-dhcp-server` for PXE/iPXE infra
- `redis-server` for cache/sessions

### Container stack
- Postgres 15, Redis 7 managed by `docker compose`
- Backend and frontend built inside containers for local dev

### Production notes
- Serve built frontend via nginx static root (not via Vite dev server)
- Consider TLS termination and hardened nginx headers
- Run database on managed service or hardened VM


