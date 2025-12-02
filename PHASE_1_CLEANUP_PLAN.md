# Phase 1 - Cleanup Plan

**Branch:** `cleanup/phase-1-plan`  
**Date:** 2025-10-08  
**Status:** ✅ Plan Created

---

## 🎯 **Cleanup Strategy**

Based on Phase 0 analysis, 96 items identified for cleanup (~2.1 MB, 40% reduction).

---

## 📋 **CATEGORY 1: SAFE_REMOVE (No Archive Needed)**

### **1.1 Cache Files (74 files)**

**Pattern:** `backend/cache/*.cache`

**Reason:** Temporary cache files, auto-regenerated

**Risk:** ⭕ NONE

**Action:**
```bash
rm backend/cache/*.cache
git add backend/cache/
git commit -m "chore(cleanup): remove auto-generated cache files"
```

**Rollback:** Not needed (regenerated on next run)

---

### **1.2 Empty Placeholder Directories (5 dirs)**

**Directories:**
```
./backups/      # Should be /var/backups/ggnet
./cache/        # Should be /var/cache/ggnet or backend/cache
./images/       # Should be /opt/ggnet/images
./logs/         # Should be /var/log/ggnet
./uploads/      # Should be /opt/ggnet/uploads
```

**Reason:** Empty placeholder directories not used in dev, created on deployment

**Risk:** ⭕ NONE

**Action:**
```bash
# Remove from git (keep .gitkeep if needed in production)
git rm -r backups/ cache/ images/ logs/ uploads/

# Add to .gitignore
echo "backups/" >> .gitignore
echo "cache/" >> .gitignore
echo "images/" >> .gitignore
echo "logs/" >> .gitignore
echo "uploads/" >> .gitignore
```

**Rollback:**
```bash
mkdir -p backups cache images logs uploads
```

---

## 📦 **CATEGORY 2: BACKUP_AND_REMOVE**

### **2.1 Root-Level Utility Scripts (4 files)**

**Files:**
```
1. change_password.py           (209 bytes) - Duplicate of backend/create_admin.py
2. change_password_linux.py     (312 bytes) - Duplicate
3. check_database_status.py     (543 bytes) - Duplicate of backend/scripts/preflight.py
4. test_database_connection.py  (678 bytes) - Duplicate
```

**Reason:** Functionality now in `backend/scripts/` or `backend/create_admin.py`

**Risk:** 🟡 LOW (verify no external references)

**Action:**
```bash
# Create archive
mkdir -p archive/legacy/20251008_phase1
cp change_password.py archive/legacy/20251008_phase1/
cp change_password_linux.py archive/legacy/20251008_phase1/
cp check_database_status.py archive/legacy/20251008_phase1/
cp test_database_connection.py archive/legacy/20251008_phase1/

# Create tarball
tar -czf archive/legacy/20251008_phase1_root_scripts.tar.gz -C archive/legacy/20251008_phase1 .

# Commit archive
git add archive/
git commit -m "chore(cleanup): archive root-level utility scripts"

# Remove originals
git rm change_password.py change_password_linux.py check_database_status.py test_database_connection.py
git commit -m "chore(cleanup): remove duplicate root-level scripts"
```

**Rollback:**
```bash
tar -xzf archive/legacy/20251008_phase1_root_scripts.tar.gz -C .
git add *.py
git commit -m "chore: restore root-level scripts"
```

---

### **2.2 Backend Debug Scripts (13 files)**

**Files:**
```
backend/check_admin.py
backend/debug_login.py
backend/test_login_correct.py
backend/test_password.py
backend/create_admin_postgres.py  (duplicate of create_admin.py)
... (8 more debug files)
```

**Reason:** Debug/development scripts, not used in production

**Risk:** 🟡 LOW (verify not referenced in docs)

**Action:**
```bash
# Archive
mkdir -p archive/legacy/20251008_phase1/backend_debug
cp backend/check_admin.py archive/legacy/20251008_phase1/backend_debug/
cp backend/debug_login.py archive/legacy/20251008_phase1/backend_debug/
... (copy all debug files)

# Create tarball
tar -czf archive/legacy/20251008_phase1_backend_debug.tar.gz -C archive/legacy/20251008_phase1/backend_debug .

# Commit archive
git add archive/
git commit -m "chore(cleanup): archive backend debug scripts"

# Remove
git rm backend/check_admin.py backend/debug_login.py ...
git commit -m "chore(cleanup): remove backend debug scripts"
```

---

### **2.3 Deprecated Documentation (2 files)**

**Files:**
```
LOGIN_TROUBLESHOOTING.md  (old - now in docs/SECUREBOOT_SETUP.md)
DEPLOYMENT_SUMMARY.md     (old - now in README.md + PHASE*_COMPLETION.md)
```

**Reason:** Content merged into newer, comprehensive docs

**Risk:** 🟡 LOW (content preserved in new docs)

**Action:**
```bash
# Archive
cp LOGIN_TROUBLESHOOTING.md archive/legacy/20251008_phase1/
cp DEPLOYMENT_SUMMARY.md archive/legacy/20251008_phase1/

tar -czf archive/legacy/20251008_phase1_old_docs.tar.gz -C archive/legacy/20251008_phase1 *.md

git add archive/
git commit -m "chore(cleanup): archive deprecated documentation"

# Remove
git rm LOGIN_TROUBLESHOOTING.md DEPLOYMENT_SUMMARY.md
git commit -m "chore(cleanup): remove deprecated docs (content merged)"
```

---

## 🔧 **CATEGORY 3: KEEP_BUT_REFACTOR**

### **3.1 Duplicate pytest.ini Files**

**Files:**
```
./pytest.ini        (root level)
./backend/pytest.ini (backend level)
```

**Reason:** Duplicate configuration

**Action:** Merge into single `backend/pytest.ini`, remove root level

**Risk:** 🟢 NONE

---

### **3.2 Environment.yml (Conda)**

**File:** `environment.yml`

**Reason:** Conda not used (Docker + pip is primary)

**Action:** Remove if Docker/pip workflow confirmed

**Risk:** 🟡 LOW (only if someone uses conda)

---

## 📊 **Cleanup Summary**

| Category | Items | Size | Risk | Archive? |
|----------|-------|------|------|----------|
| **SAFE_REMOVE** | 79 | ~2.0 MB | None | No |
| - Cache files | 74 | ~2 MB | None | No |
| - Empty dirs | 5 | 0 | None | No |
| **BACKUP_AND_REMOVE** | 19 | ~100 KB | Low | Yes |
| - Root scripts | 4 | ~2 KB | Low | Yes |
| - Debug scripts | 13 | ~50 KB | Low | Yes |
| - Old docs | 2 | ~50 KB | Low | Yes |
| **KEEP_BUT_REFACTOR** | 3 | ~5 KB | None | No |
| - pytest.ini | 2 | ~2 KB | None | No |
| - environment.yml | 1 | ~3 KB | Low | Maybe |
| **TOTAL** | 101 | ~2.1 MB | - | - |

---

## 🔄 **Execution Order**

### **Phase 2: Automated Archiving**
1. Create archive directory structure
2. Copy BACKUP_AND_REMOVE files
3. Create tarballs
4. Commit archives
5. Verify archive integrity

### **Phase 3: Safe Removal**
1. Remove cache files
2. Remove empty directories
3. Update .gitignore
4. Run tests (should still pass)
5. Commit removals

### **Phase 4: Refactoring**
1. Merge pytest.ini files
2. Remove environment.yml (if unused)
3. Update documentation references
4. Run tests
5. Commit refactors

---

## 🎯 **Success Criteria**

Phase 1 complete when:
- [x] All files categorized (SAFE_REMOVE, BACKUP_AND_REMOVE, KEEP_BUT_REFACTOR)
- [x] Regex patterns defined
- [x] Risk assessment done
- [x] Rollback procedures documented
- [x] Execution order planned

---

## 📋 **Regex Patterns for Automation**

### **Cache Files:**
```regex
^backend/cache/[a-f0-9]{32}\.cache$
```

### **Root Utility Scripts:**
```regex
^(change_password|check_database_status|test_database_connection).*\.py$
```

### **Backend Debug Scripts:**
```regex
^backend/(check_|debug_|test_).*\.py$
```

---

**Plan Status:** ✅ Complete  
**Ready for Phase 2:** ✅ Yes

