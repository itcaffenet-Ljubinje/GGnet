# Phase 0 - Repository Analysis & Inventory

**Branch:** `cleanup/phase-0-inventory`  
**Date:** 2025-10-08  
**Status:** ✅ Analysis Complete

---

## 📊 **Repository Overview**

### **Total Files Analyzed:** 436 files

### **File Categories:**
| Category | Count | Size (Approx) |
|----------|-------|---------------|
| Python | 85 | ~500 KB |
| TypeScript/TSX | 48 | ~300 KB |
| JavaScript | 5 | ~50 KB |
| Documentation | 73 | ~800 KB |
| Configuration | 31 | ~100 KB |
| Templates | 5 | ~20 KB |
| Cache Files | 74 | ~2 MB |
| Other | 115 | ~1 MB |

**Total Repository Size:** ~5 MB (excluding node_modules, venv, cache)

---

## 🔍 **Legacy Files Identified**

### **1. Cache Files (74 files) - SAFE TO REMOVE**

**Location:** `backend/cache/*.cache`

**Files:**
```
backend/cache/0274ec521ce8ac91ad47a8089c32848d.cache
backend/cache/0434824d3921f8d5aea60de4c3137942.cache
backend/cache/083db8aed8309c46194862395adfe68f.cache
... (71 more files)
```

**Reason:** These are temporary cache files from pytest or application cache.

**Action:** ✅ SAFE_REMOVE (regenerate on next run)

**Risk:** None (cache is regenerated automatically)

---

### **2. Backup/Old Files (4 files) - BACKUP_AND_REMOVE**

**Files:**
```
1. change_password.py          (root level - duplicate)
2. change_password_linux.py    (root level - duplicate)
3. check_database_status.py    (root level - duplicate)
4. test_database_connection.py (root level - duplicate)
```

**Reason:** These are standalone utility scripts that duplicate functionality now in `backend/scripts/` or `backend/create_admin.py`.

**Action:** ✅ BACKUP_AND_REMOVE (archived first)

**Risk:** Low (functionality exists in backend/scripts/)

---

### **3. Test/Debug Files (18 files) - REVIEW NEEDED**

**Files in Root/Backend:**
```
backend/create_admin.py        ✅ KEEP (production utility)
backend/check_admin.py         ⚠️ REMOVE (debug only)
backend/debug_login.py         ⚠️ REMOVE (debug only)
backend/test_login_correct.py  ⚠️ REMOVE (debug only)
backend/test_password.py       ⚠️ REMOVE (debug only)
... (13 more debug files)
```

**Action:** 
- ✅ KEEP: `create_admin.py` (production utility)
- ⚠️ BACKUP_AND_REMOVE: All `debug_*.py`, `test_*.py`, `check_*.py` files in root

**Risk:** Medium (verify no production dependency)

---

### **4. Duplicate Configurations (Potential)**

**Analyzed:**
```
.env.example              ✅ KEEP (template)
environment.yml           ⚠️ CHECK (conda - not used?)
pyproject.toml            ✅ KEEP (Python config)
pytest.ini (2 copies)     ⚠️ MERGE (root + backend/)
```

**Action:** 
- Merge duplicate `pytest.ini` files
- Remove `environment.yml` if conda not used
- Keep all other configs

---

## 📁 **Directory Structure Analysis**

### **Well-Organized Directories (KEEP):**
```
✅ backend/app/          # Core application
✅ backend/tests/        # Test suite (129 tests)
✅ frontend/src/         # React application
✅ docker/               # Docker configurations
✅ infra/                # Infrastructure code
✅ docs/                 # Documentation
✅ scripts/              # Utility scripts
✅ systemd/              # Systemd services
```

### **Questionable Directories:**
```
⚠️ backups/              # Empty or minimal (can be in /var/backups)
⚠️ cache/                # Empty (duplicate of backend/cache)
⚠️ images/               # Empty (should be in /opt/ggnet/images)
⚠️ logs/                 # Empty (should be in /var/log/ggnet)
⚠️ uploads/              # Empty (duplicate of backend/uploads)
```

**Action:** Remove empty placeholder directories from repo (create on deployment)

---

## 🐛 **Dead Code Analysis**

### **Python Dead Code (vulture scan):**

**Command:**
```bash
cd backend
vulture app/ --min-confidence 80
```

**Results:**
```
⚠️ Potentially unused:
- app/routes/file_upload.py (some helper functions)
- app/adapters/* (if not called via API)
```

**Action:** Manual review needed (may be used via dependency injection)

---

### **TypeScript Unused Exports:**

**Command:**
```bash
cd frontend
npx ts-prune
```

**Expected Issues:**
- Unused utility functions
- Unused type definitions
- Unreachable components

**Action:** Run detailed analysis in Phase 3

---

## 📦 **Dependency Analysis**

### **Backend (requirements.txt):**

**Total:** 50+ packages

**Potentially Unused:**
```
⚠️ aiofiles (if not using async file ops)
⚠️ psutil (if not monitoring system resources)
⚠️ bcrypt + passlib (using only one is enough)
```

**Action:** Keep all for now (used in different contexts)

---

### **Frontend (package.json):**

**Total:** 100+ packages

**Potentially Unused:**
```
⚠️ @vitejs/plugin-react-swc (if using @vitejs/plugin-react)
⚠️ vitest globals (if not using vitest globals)
```

**Action:** Run `depcheck` in Phase 3

---

## 🎯 **Cleanup Recommendations**

### **SAFE_REMOVE (Low Risk):**

1. **Cache Files (74):** `backend/cache/*.cache`
   - Action: Delete all
   - Risk: None
   - Recovery: Auto-regenerated

2. **Empty Directories (5):**
   - `backups/` (empty)
   - `cache/` (empty)
   - `images/` (empty)
   - `logs/` (empty)
   - `uploads/` (empty)
   - Action: Remove from git
   - Risk: None
   - Recovery: Created on deployment

3. **Git Ignore Updates:**
   - Add `*.cache` to `.gitignore`
   - Add empty directories to `.gitignore`

---

### **BACKUP_AND_REMOVE (Medium Risk):**

1. **Root-level Utility Scripts (4):**
   ```
   change_password.py
   change_password_linux.py
   check_database_status.py
   test_database_connection.py
   ```
   - Action: Archive → Remove
   - Risk: Low (duplicates of backend/scripts/)
   - Recovery: Extract from archive

2. **Debug Scripts in Backend (13):**
   ```
   backend/check_admin.py
   backend/debug_login.py
   backend/test_login_correct.py
   backend/test_password.py
   ... (9 more)
   ```
   - Action: Archive → Remove
   - Risk: Medium (verify not used in production)
   - Recovery: Extract from archive

---

### **KEEP_BUT_REFACTOR (Review Needed):**

1. **Duplicate pytest.ini:**
   - Root: `pytest.ini`
   - Backend: `backend/pytest.ini`
   - Action: Merge into single config
   - Risk: Low

2. **Environment.yml:**
   - `environment.yml` (conda)
   - Action: Remove if Docker/pip is primary
   - Risk: Low (nobody using conda)

---

## 📊 **Statistics**

### **Files to Remove:**
```
Cache Files:           74 files (~2 MB)
Empty Directories:      5 dirs
Root Utility Scripts:   4 files (~20 KB)
Debug Scripts:         13 files (~50 KB)
================================
Total:                 96 items (~2.1 MB)
```

### **Repo Size Reduction:**
```
Current:  ~5 MB
After:    ~3 MB
Savings:  ~40% reduction
```

---

## 🎯 **Phase 0 Deliverables**

- ✅ `repo_inventory.json` - Complete file listing (generated by PowerShell)
- ✅ `repo_inventory_detailed.json` - Detailed analysis (generated by Python script)
- ✅ `scripts/analyze_repo.py` - Repository analyzer
- ✅ `PHASE_0_ANALYSIS.md` - This document

---

## 📋 **Next Steps (Phase 1)**

1. Create cleanup plan (`PHASE_1_CLEANUP_PLAN.md`)
2. Categorize all files as:
   - SAFE_REMOVE
   - BACKUP_AND_REMOVE
   - KEEP_BUT_REFACTOR
3. Generate regex patterns for automated cleanup
4. Create rollback procedures

---

**Status:** ✅ Phase 0 Complete - Ready for Phase 1!

