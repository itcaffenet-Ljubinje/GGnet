# Changelog

All notable changes to GGnet will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2025-10-08

### 🎉 Major Release - Phase 1 & 2 Complete

**90% ggRock Feature Parity Achieved!**

### Added - Phase 2 (Enhanced Monitoring & Management)

#### Monitoring
- **Grafana Dashboards** - Real-time monitoring with system overview dashboard
- **Prometheus Integration** - 15+ metrics exported (machines, sessions, storage, network, iSCSI)
- **Metrics API** - `/metrics` endpoint for Prometheus scraping
- 30-day data retention for historical analysis

#### Remote Access
- **noVNC Remote Console** - Browser-based remote desktop on port 6080
- **websockify Proxy** - VNC proxy on port 5900
- HTML5 canvas rendering with 1920x1080 default resolution

#### Automation
- **Hardware Auto-Detection** - `/api/hardware/report` endpoint for client reporting
- **Hardware Detection Script** - `scripts/hardware_detect.py` with lshw/dmidecode support
- **Auto-Discovery** - Automatic machine creation from hardware reports
- Detects: CPU, RAM, MAC, manufacturer, model, serial, BIOS, SecureBoot status

#### System Validation
- **Pre-flight Checks** - `backend/scripts/preflight.py` with 7 comprehensive checks
- **Systemd Service** - `systemd/ggnet-preflight.service` for automatic validation
- Checks: Database, Redis, Storage, iSCSI, Network, DHCP, TFTP

#### Documentation
- `PHASE2_COMPLETION.md` - Complete Phase 2 summary (600+ lines)
- `docker/grafana/README.md` - Grafana setup guide
- Updated `README.md` with Phase 2 features

### Changed - Phase 2
- `docker-compose.yml` - Added Prometheus, Grafana, noVNC, websockify services
- `backend/app/main.py` - Added hardware router
- Enhanced metrics collection and export

---

## [1.0.0] - 2025-10-08

### 🎉 Initial Release - Phase 1 Complete

**85% ggRock Feature Parity Achieved!**

### Added - Phase 1 (Critical Features)

#### SecureBoot Support
- **iPXE Binaries Setup** - `infra/tftp/` directory with download scripts
- **snponly.efi** - Microsoft-signed iPXE for Windows 11 SecureBoot
- **ipxe.efi** - Standard UEFI x64 boot
- **ipxe32.efi** - UEFI IA32 (32-bit) boot
- **undionly.kpxe** - Legacy BIOS boot
- **boot.ipxe.example** - Example iPXE boot script
- PowerShell and Bash download scripts for all binaries

#### Windows Registry Toolchain
- **9 Registry Scripts** - Complete Windows automation
  - `01-disable-uac.reg` - Disable UAC prompts
  - `02-disable-firewall.reg` - Disable Windows Firewall
  - `03-enable-autologon.reg.template` - Auto-login configuration
  - `04-rename-computer.reg.template` - Computer rename
  - `05-ggnet-client-install.reg` - **Critical diskless optimizations**
  - `06-inject-environment-vars.reg.template` - GGnet environment variables
  - `07-enable-rdp.reg` - Enable Remote Desktop
  - `08-optimize-performance.reg` - Performance tweaks
  - `09-disable-telemetry.reg` - Disable Windows tracking
- **apply-all.bat** - Automated application script
- Template system for per-machine customization

#### Dynamic DHCP Configuration
- **Enhanced dhcpd.conf** - Architecture detection (option 93)
- **Dynamic Boot File Selection**:
  - UEFI x64 → `snponly.efi` (SecureBoot)
  - UEFI x64 HTTP → `snponly.efi`
  - UEFI IA32 → `ipxe32.efi`
  - Legacy BIOS → `undionly.kpxe`
- **iPXE Chainloading** - Detects if already in iPXE
- Logging for unknown architectures

#### Documentation
- `GGROCK_COMPARISON.md` - Comprehensive ggRock analysis (800 lines)
- `MISSING_FEATURES_ROADMAP.md` - Prioritized feature roadmap (883 lines)
- `PHASE1_COMPLETION.md` - Complete Phase 1 summary (562 lines)
- `docs/SECUREBOOT_SETUP.md` - SecureBoot setup guide (503 lines)
- `docs/WINDOWS_TOOLCHAIN_GUIDE.md` - Windows toolchain guide (600+ lines)
- `docs/PHASE1_TESTING_PLAN.md` - Comprehensive testing plan (570 lines)

### Changed - Phase 1
- `docker/dhcp/dhcpd.conf` - Complete rewrite with dynamic boot file selection
- Enhanced CORS configuration for frontend development
- Improved error handling in authentication endpoints

---

## [0.9.0] - 2025-10-07

### Added - Pre-Phase 1

#### Core Backend
- FastAPI application with async support
- PostgreSQL 15 database integration
- Redis 7 for caching and sessions
- JWT authentication with refresh tokens
- Role-based access control (RBAC)
- Audit logging for all actions
- Rate limiting middleware
- Structured logging with structlog

#### API Endpoints
- Authentication: `/api/auth/login`, `/api/auth/refresh`, `/api/auth/logout`
- Users: CRUD operations with role management
- Images: Upload, list, convert, delete
- Machines: CRUD with hardware specs
- Sessions: Start, stop, list with status tracking
- Targets: iSCSI target management
- Storage: Storage info and cleanup
- Health: System health checks
- Monitoring: Metrics and stats

#### Frontend
- React 18 with TypeScript
- Tailwind CSS with dark mode
- Zustand for state management
- React Query for data fetching
- React Router for navigation
- Axios with token refresh interceptor
- WebSocket support for real-time updates

#### iSCSI Management
- targetcli adapter for iSCSI operations
- File-backed backstore creation
- iSCSI target/TPG/LUN creation
- ACL management for initiators
- Target status monitoring

#### Image Management
- Image upload with streaming
- qemu-img wrapper for conversion
- Background worker (RQ/Celery ready)
- VHDX, QCOW2, RAW format support
- Image metadata and status tracking

#### Testing
- pytest with async support
- 129 passing tests
- 85%+ code coverage
- Integration tests for full flow
- CI/CD with GitHub Actions

#### Infrastructure
- Docker Compose configuration
- PostgreSQL container
- Redis container
- Nginx reverse proxy
- DHCP server (networkboot/dhcpd)
- TFTP server (pghalliday/tftp)
- iSCSI target (openebs/tgt)

### Fixed - Pre-Phase 1
- Database lazy initialization to prevent import errors
- Redis segmentation fault in CI/CD
- Bcrypt password hashing 72-byte limit
- Audit logging session management
- Event loop conflicts in PostgreSQL tests
- CORS issues with Vite dev server
- WebSocket infinite re-render loop
- Frontend test suite configuration

---

## [Unreleased]

### Planned - Phase 3
- Alerting with Alertmanager
- Email/Slack notifications
- Advanced automation scripts
- Multi-site support
- Load balancing
- High Availability (HA)

### Planned - Phase 4
- Active Directory integration
- LDAP authentication
- Multi-tenancy support
- Advanced reporting
- Backup/restore automation
- Disaster recovery

---

## Release Notes

### Version 2.0.0 Highlights

**GGnet has reached 90% ggRock feature parity!**

This major release adds comprehensive monitoring, remote access, and automation:
- ✅ Grafana dashboards for real-time monitoring
- ✅ noVNC for browser-based remote console
- ✅ Hardware auto-detection for zero-touch discovery
- ✅ Pre-flight checks for system validation

**Breaking Changes:** None (fully backward compatible)

**Upgrade Path:** Run `docker-compose up -d` to pull new services

---

### Version 1.0.0 Highlights

**GGnet initial production release!**

This release provides complete Windows 11 SecureBoot support:
- ✅ Microsoft-signed iPXE (snponly.efi)
- ✅ 9 registry scripts for automated Windows configuration
- ✅ Dynamic DHCP with architecture detection
- ✅ 4,000+ lines of comprehensive documentation

**Breaking Changes:** DHCP configuration format changed (see migration guide)

**Upgrade Path:** Update `docker/dhcp/dhcpd.conf` with new format

---

## Migration Guides

### Migrating to 2.0.0 from 1.0.0

1. Pull latest code:
   ```bash
   git pull origin main
   ```

2. Update Docker Compose:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

3. Access new services:
   - Grafana: http://localhost:3001 (admin/admin)
   - noVNC: http://localhost:6080

4. Optional: Run pre-flight checks:
   ```bash
   python3 backend/scripts/preflight.py
   ```

**No database migrations required.**

---

### Migrating to 1.0.0 from 0.9.0

1. **Update DHCP Configuration:**

   Old format (`docker/dhcp/dhcpd.conf`):
   ```conf
   filename "ipxe.efi";
   ```

   New format:
   ```conf
   option arch code 93 = unsigned integer 16;
   
   if option arch = 00:07 {
       filename "snponly.efi";
   } elsif option arch = 00:00 {
       filename "undionly.kpxe";
   }
   ```

2. **Download iPXE Binaries:**
   ```bash
   cd infra/tftp
   ./download-ipxe.sh
   sudo cp *.efi *.kpxe /var/lib/tftp/
   ```

3. **Restart DHCP Service:**
   ```bash
   docker-compose restart dhcp
   ```

**No database migrations required.**

---

## Links

- [GitHub Repository](https://github.com/your-org/ggnet)
- [Documentation](docs/)
- [ggRock Comparison](GGROCK_COMPARISON.md)
- [Roadmap](MISSING_FEATURES_ROADMAP.md)

---

**Thank you for using GGnet!** 🚀
