# PHASE 0 - MAPPING: Current State to ggRock Functionality

## Executive Summary

The current GGnet project is a well-structured FastAPI + React application with solid foundations for a diskless server system. The core models (User, Machine, Image, Target, Session) are already in place and properly designed. The main gap is the integration with external system tools (qemu-img, targetcli, DHCP, TFTP) to create a complete diskless boot solution.

## Current Architecture Assessment

### ✅ STRENGTHS
- **Modern Tech Stack**: FastAPI + React + TypeScript + Pydantic V2
- **Solid Data Models**: Well-designed SQLAlchemy models for all core entities
- **Authentication**: JWT + Redis session management
- **Real-time Updates**: WebSocket implementation for live monitoring
- **Comprehensive Testing**: Unit tests, edge cases, integration tests
- **Code Quality**: Pydantic V2, proper error handling, structured logging

### ⚠️ GAPS TO ADDRESS
- **System Integration**: Missing qemu-img, targetcli, DHCP, TFTP integration
- **Image Conversion**: No background processing for image format conversion
- **PXE Boot**: No iPXE script generation or DHCP configuration
- **Session Orchestration**: Manual target creation vs automated workflow
- **Infrastructure**: Missing systemd services, nginx config, install scripts

## Detailed Component Mapping

### 1. BACKEND CORE (✅ COMPLETE)
**Current State**: Well-implemented FastAPI application
- `backend/app/main.py` → ✅ FastAPI app with proper middleware
- `backend/app/core/` → ✅ Configuration, database, security, dependencies
- `backend/app/models/` → ✅ All core models implemented
- `backend/app/routes/` → ✅ All CRUD endpoints implemented

**ggRock Mapping**: 
- ✅ `POST /api/v1/auth/login` → `backend/app/routes/auth.py`
- ✅ `CRUD /api/v1/users` → `backend/app/routes/auth.py`
- ✅ `CRUD /api/v1/machines` → `backend/app/routes/machines.py`
- ✅ `CRUD /api/v1/images` → `backend/app/routes/images.py`
- ✅ `CRUD /api/v1/targets` → `backend/app/routes/targets.py`
- ✅ `POST /api/v1/sessions/start` → `backend/app/routes/sessions.py`

### 2. IMAGE STORAGE & CONVERSION (⚠️ PARTIAL)
**Current State**: Upload and metadata tracking implemented
- `backend/app/routes/images.py` → ✅ File upload with progress tracking
- `backend/app/models/image.py` → ✅ Image model with status tracking

**Missing for ggRock**:
- ❌ Background worker for image conversion
- ❌ qemu-img integration for format conversion
- ❌ Streaming upload with checksum validation
- ❌ Atomic file operations

**Required Additions**:
- `backend/worker/convert.py` → Background image conversion worker
- `backend/scripts/qemu_convert.py` → qemu-img wrapper script
- Enhanced upload endpoint with streaming and checksum

### 3. iSCSI TARGET WRAPPER (⚠️ PARTIAL)
**Current State**: Target model and basic CRUD
- `backend/app/models/target.py` → ✅ Complete target model
- `backend/app/routes/targets.py` → ✅ Target CRUD operations

**Missing for ggRock**:
- ❌ targetcli command execution
- ❌ Automated backstore creation
- ❌ LUN mapping automation
- ❌ ACL configuration

**Required Additions**:
- `backend/adapters/targetcli.py` → targetcli command wrapper
- Enhanced target creation endpoint with automation
- Subprocess execution with error handling

### 4. SESSION ORCHESTRATION & PXE (⚠️ PARTIAL)
**Current State**: Session tracking and monitoring
- `backend/app/models/session.py` → ✅ Complete session model
- `backend/app/routes/sessions.py` → ✅ Session lifecycle management

**Missing for ggRock**:
- ❌ iPXE script generation
- ❌ Automated target creation on session start
- ❌ DHCP server configuration
- ❌ TFTP server setup

**Required Additions**:
- `backend/api/sessions.py` → Enhanced session orchestration
- `infra/examples/dhcpd.conf` → DHCP configuration template
- `infra/examples/tftp/boot.ipxe` → iPXE script template
- Session start endpoint with full automation

### 5. FRONTEND (✅ COMPLETE)
**Current State**: Modern React SPA with all required pages
- `frontend/src/pages/` → ✅ All required pages implemented
- `frontend/src/components/` → ✅ UI components and modals
- `frontend/src/lib/api.ts` → ✅ API client functions

**ggRock Mapping**:
- ✅ Login page → `frontend/src/pages/LoginPage.tsx`
- ✅ Dashboard → `frontend/src/pages/DashboardPage.tsx`
- ✅ Machines management → `frontend/src/pages/MachinesPage.tsx`
- ✅ Images management → `frontend/src/pages/ImagesPage.tsx`
- ✅ Sessions monitoring → `frontend/src/pages/SessionsPage.tsx`
- ✅ Image uploader → `frontend/src/components/FileUpload.tsx`
- ✅ Machine modal → `frontend/src/components/MachineModal.tsx`

### 6. INFRASTRUCTURE (❌ MISSING)
**Current State**: Basic Docker setup
- `docker-compose.yml` → ✅ Basic multi-container setup
- `backend/Dockerfile` → ✅ Backend container
- `frontend/Dockerfile` → ✅ Frontend container

**Missing for ggRock**:
- ❌ Systemd service definitions
- ❌ Nginx reverse proxy configuration
- ❌ Installation scripts for dependencies
- ❌ DHCP and TFTP server configuration

**Required Additions**:
- `infra/install.sh` → Dependency installation script
- `infra/systemd/` → Service definitions
- `infra/nginx/` → Reverse proxy configuration
- `infra/examples/` → Configuration templates

## Implementation Priority

### PHASE 1: Backend Core (✅ ALREADY COMPLETE)
- All FastAPI endpoints implemented
- Database models complete
- Authentication system working
- Tests passing

### PHASE 2: Image Storage & Conversion (🔧 NEEDS WORK)
**Priority**: HIGH
- Add background worker for image conversion
- Implement qemu-img wrapper
- Add streaming upload with checksum
- Test with real image files

### PHASE 3: iSCSI Target Wrapper (🔧 NEEDS WORK)
**Priority**: HIGH
- Implement targetcli adapter
- Add automated target creation
- Test with real iSCSI targets
- Handle root privilege requirements

### PHASE 4: Session Orchestration (🔧 NEEDS WORK)
**Priority**: MEDIUM
- Add iPXE script generation
- Implement automated session workflow
- Add DHCP/TFTP configuration templates
- Test end-to-end boot process

### PHASE 5: Frontend (✅ ALREADY COMPLETE)
- All required pages implemented
- Real-time updates working
- File upload with progress
- Responsive design

### PHASE 6: Infrastructure (🔧 NEEDS WORK)
**Priority**: MEDIUM
- Add systemd services
- Create installation scripts
- Add nginx configuration
- Test deployment process

## Risk Assessment

### HIGH RISK
- **Root Privileges**: targetcli, DHCP, TFTP require root access
- **System Dependencies**: qemu-img, targetcli may not be available
- **Network Configuration**: DHCP/TFTP setup can break network

### MEDIUM RISK
- **Image Conversion**: Large file processing may timeout
- **iSCSI Performance**: Network storage performance issues
- **Boot Compatibility**: UEFI/Secure Boot compatibility

### LOW RISK
- **API Changes**: Existing endpoints are stable
- **Database Schema**: Models are well-designed
- **Frontend Integration**: React app is complete

## Success Criteria

### Phase 2 Success
- [ ] Upload 10GB VHDX file successfully
- [ ] Convert VHDX to RAW format using qemu-img
- [ ] Verify checksum integrity
- [ ] Background worker processes conversion

### Phase 3 Success
- [ ] Create iSCSI target using targetcli
- [ ] Map image file to LUN
- [ ] Configure ACL for machine
- [ ] Test iSCSI connection from client

### Phase 4 Success
- [ ] Generate valid iPXE script
- [ ] Configure DHCP for PXE boot
- [ ] Test complete boot workflow
- [ ] Session starts automatically

### Overall Success
- [ ] Complete diskless boot from upload to desktop
- [ ] Multiple concurrent sessions
- [ ] Automated cleanup and resource management
- [ ] Production-ready deployment scripts

## Next Steps

1. **Start with Phase 2**: Image conversion is foundational
2. **Implement stubs**: Create mock adapters for testing
3. **Add integration tests**: Test with real system tools
4. **Document requirements**: System dependencies and privileges
5. **Create deployment guide**: Step-by-step production setup

The current codebase provides an excellent foundation. The main work is integrating with external system tools and creating the automated orchestration layer.
