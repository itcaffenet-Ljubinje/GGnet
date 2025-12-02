# Phase 0 - Testing Guide

**Branch:** `cleanup/phase-0-inventory`

---

## 🧪 **How to Test Locally**

### **1. Verify Analysis Script**

```bash
# Run analyzer
python scripts/analyze_repo.py

# Check output
cat repo_inventory_detailed.json | jq '.total_files'
# Should show: 436

cat repo_inventory_detailed.json | jq '.categories'
# Should show file categories
```

**Expected Output:**
```json
{
  "python": 85,
  "javascript": 5,
  "typescript": 48,
  "config": 31,
  "docs": 73,
  "templates": 5,
  "cache": 74,
  "other": 115
}
```

---

### **2. Verify Inventory Files Exist**

```bash
# Check inventory files
ls -lh repo_inventory.json
ls -lh repo_inventory_detailed.json

# Check documentation
ls -lh PHASE_0_*.md
```

**Expected Files:**
- `repo_inventory.json` (~150 KB)
- `repo_inventory_detailed.json` (~200 KB)
- `PHASE_0_ANALYSIS.md`
- `PHASE_0_CHECKLIST.md`
- `PHASE_0_ASSUMPTIONS.md`
- `PHASE_0_TESTS.md` (this file)

---

### **3. Verify Git Branch**

```bash
# Check current branch
git branch --show-current
# Should show: cleanup/phase-0-inventory

# Check git status
git status
# Should show new files ready to commit
```

---

### **4. Validate JSON Structure**

```bash
# Validate JSON syntax
cat repo_inventory_detailed.json | jq '.' > /dev/null && echo "Valid JSON" || echo "Invalid JSON"

# Check required fields
cat repo_inventory_detailed.json | jq '.timestamp, .total_files, .categories, .legacy_files' > /dev/null && echo "All fields present"
```

---

### **5. Review Identified Legacy Files**

```bash
# Show legacy files summary
cat repo_inventory_detailed.json | jq '.legacy_details'

# Count cache files
cat repo_inventory_detailed.json | jq '.legacy_details.cache_files | length'
# Should show: 74

# Show backup files
cat repo_inventory_detailed.json | jq '.legacy_details.backup_files[]'
```

---

## ✅ **Success Criteria**

Phase 0 is successful if:

- [x] Analysis script runs without errors
- [x] Inventory JSON files generated
- [x] 436 files cataloged
- [x] 96 legacy files identified
- [x] All Phase 0 documents created
- [x] Git branch created
- [x] Ready to commit

---

## 🔄 **Rollback (if needed)**

If analysis reveals issues:

```bash
# Discard changes
git checkout main
git branch -D cleanup/phase-0-inventory

# Start over
git checkout -b cleanup/phase-0-inventory
```

---

**Test Status:** ✅ All checks passed  
**Ready for Commit:** ✅ Yes
