# Phase 0 - Assumptions

**Branch:** `cleanup/phase-0-inventory`

---

## 🎯 **Environment Assumptions**

### **Operating System:**
- Primary: Debian 11+ / Ubuntu 20.04+
- Alternative: Any Linux with Docker support
- Development: Windows 10/11 (via WSL or Docker Desktop)

### **Software Versions:**
- Python: 3.11+
- Node.js: 18+
- PostgreSQL: 15+
- Redis: 7+
- Docker: 20.10+
- Docker Compose: 2.0+

### **Network:**
- Server has static IP
- Clients on same subnet (for PXE boot)
- Firewall allows: 8000 (API), 3000 (Frontend), 69 (TFTP), 3260 (iSCSI)

---

## 📁 **Repository Structure Assumptions**

### **Production Directories:**
- `/opt/ggnet/` - Production installation
- `/var/lib/tftp/` - TFTP boot files
- `/var/log/ggnet/` - Application logs
- `/var/backups/ggnet/` - Backup storage

### **Development Directories:**
- `backend/` - FastAPI application
- `frontend/` - React application
- `docker/` - Docker configurations
- `infra/` - Infrastructure code
- `scripts/` - Utility scripts

### **Temporary/Cache Directories (Not in Repo):**
- `node_modules/` - NPM packages
- `venv/` - Python virtual environment
- `__pycache__/` - Python bytecode
- `dist/` - Frontend build output
- `.pytest_cache/` - Pytest cache

---

## 🧹 **Cleanup Assumptions**

### **Safe to Remove:**
- Cache files (*.cache) - Regenerated automatically
- Empty directories - Created on deployment
- Temporary test scripts - Not used in production

### **Archive Before Removing:**
- Utility scripts in root - May have historical value
- Debug scripts - Useful for troubleshooting

### **Keep:**
- All production code (`backend/app/`, `frontend/src/`)
- All tests (`backend/tests/`, `frontend/src/**/*.test.tsx`)
- All documentation (`docs/`, `*.md`)
- All configuration (`docker/`, `infra/`)

---

## 🔒 **Safety Assumptions**

### **Git Workflow:**
- Every phase = separate branch
- Archived files committed before deletion
- Rollback possible via git revert

### **Testing:**
- All tests must pass after cleanup
- CI/CD must succeed
- Manual smoke test required

### **Backup Strategy:**
- Create `archive/legacy/<timestamp>.tar.gz` before deletion
- Archive committed to repo
- Can restore via `tar -xzf archive/legacy/<timestamp>.tar.gz`

---

## ⚠️ **Known Limitations**

### **Analysis:**
- File analysis based on patterns (may have false positives)
- Import analysis may miss dynamic imports
- Manual review recommended for BACKUP_AND_REMOVE

### **Cleanup:**
- Some files may be referenced in documentation only
- External dependencies (system configs) not analyzed
- Production deployment may reveal missing files

---

## ✅ **Validation Criteria**

### **Phase 0 Success:**
- [x] Inventory generated
- [x] Legacy files identified
- [x] Categories defined
- [x] Analysis documented

### **Phase 1 Prerequisites:**
- Must have file categorization
- Must have removal patterns
- Must have rollback plan

---

**Assumptions Valid:** ✅ Yes  
**Ready for Phase 1:** ✅ Yes
