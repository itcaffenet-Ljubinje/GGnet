#!/usr/bin/env bash
set -euo pipefail

# GGnet Infra Installer (Phase 6)
# Usage: ./infra/install.sh [--dry-run]

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
fi

exec_step() {
  local desc="$1"; shift
  local cmd="$*"
  if $DRY_RUN; then
    echo "DRY-RUN: $desc"
    echo "  $cmd"
  else
    echo "EXEC: $desc"
    eval "$cmd"
  fi
}

require_root() {
  if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root (or with sudo)." >&2
    exit 1
  fi
}

echo "== GGnet Infra Install =="
echo "Dry run: $DRY_RUN"

# Detect OS (Debian/Ubuntu assumed)
OS_ID="debian"
if [[ -f /etc/os-release ]]; then
  . /etc/os-release
  OS_ID=$ID
fi

if [[ "$OS_ID" != "debian" && "$OS_ID" != "ubuntu" ]]; then
  echo "Warning: Tested on Debian/Ubuntu. Proceeding anyway..."
fi

require_root

# Packages
PACKAGES=(
  python3 python3-venv python3-pip
  redis-server
  qemu-utils
  targetcli-fb
  tftpd-hpa
  isc-dhcp-server
  nginx
  docker.io docker-compose-plugin
)

exec_step "Update apt index" "apt-get update -y"
exec_step "Install packages" "apt-get install -y ${PACKAGES[*]}"

# Create ggnet user/group if missing
if ! id -u ggnet >/dev/null 2>&1; then
  exec_step "Create ggnet user" "useradd -r -m -d /opt/ggnet -s /usr/sbin/nologin ggnet"
fi

# Directories
APP_ROOT="/opt/ggnet"
BACKEND_DIR="$APP_ROOT/backend"
IMAGES_DIR="/var/lib/gg/images"
TFTP_ROOT="/var/lib/tftpboot"

exec_step "Create directories" "mkdir -p $BACKEND_DIR $IMAGES_DIR $TFTP_ROOT $APP_ROOT/venv"
exec_step "Set ownership" "chown -R ggnet:ggnet $APP_ROOT $IMAGES_DIR $TFTP_ROOT"

# Python venv
exec_step "Create venv" "python3 -m venv $APP_ROOT/venv"
exec_step "Upgrade pip" "$APP_ROOT/venv/bin/pip install --upgrade pip"

# Backend install (expects code synced to $BACKEND_DIR)
if [[ -f $BACKEND_DIR/requirements.txt ]]; then
  exec_step "Install backend deps" "$APP_ROOT/venv/bin/pip install -r $BACKEND_DIR/requirements.txt"
else
  echo "Note: $BACKEND_DIR/requirements.txt not found. Skip deps install."
fi

# Systemd services
exec_step "Install systemd unit ggnet-backend" "install -m 0644 -o root -g root infra/systemd/ggnet-backend.service /etc/systemd/system/ggnet-backend.service"
exec_step "Install systemd unit ggnet-worker" "install -m 0644 -o root -g root infra/systemd/ggnet-worker.service /etc/systemd/system/ggnet-worker.service"
exec_step "Daemon-reload" "systemctl daemon-reload"
exec_step "Enable services" "systemctl enable ggnet-backend ggnet-worker redis-server nginx"

# Nginx config
exec_step "Install nginx config" "install -m 0644 -o root -g root infra/nginx/ggnet.conf /etc/nginx/sites-available/ggnet.conf"
exec_step "Enable nginx site" "ln -sf /etc/nginx/sites-available/ggnet.conf /etc/nginx/sites-enabled/ggnet.conf && systemctl restart nginx"

echo "== Done. Use --dry-run to preview steps =="

exit 0


