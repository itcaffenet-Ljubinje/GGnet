# CI/CD Quick Start Guide

**Get your CI/CD pipeline running in 5 minutes!** ⚡

---

## 🚀 **Setup Steps**

### **1. Add Codecov Token (2 minutes)**

1. Go to https://codecov.io and sign in with GitHub
2. Add your repository: Click "Add repository"
3. Copy your upload token from repository settings
4. Add to GitHub:
   - Go to: Repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `CODECOV_TOKEN`
   - Value: Paste your Codecov token
   - Click "Add secret"

### **2. Push Code to Trigger Workflow (1 minute)**

```bash
git add .github/workflows/ci.yml
git commit -m "Add CI/CD pipeline"
git push origin main
```

### **3. View Results (2 minutes)**

- **GitHub Actions:** Go to "Actions" tab in your repository
- **Codecov:** Visit https://codecov.io/gh/your-org/ggnet
- **PR Comments:** Create a PR to see automatic coverage comments

---

## ✅ **What Runs Automatically**

### **On Every Push/PR:**

1. ✅ **Backend Tests** - All pytest tests with coverage
2. ✅ **Frontend Lint** - TypeScript + ESLint checks
3. ✅ **Frontend Tests** - Unit tests with coverage
4. ✅ **E2E Tests** - Playwright end-to-end tests
5. ✅ **Build Check** - Verify everything builds

**Total Time:** ~25-35 minutes (jobs run in parallel)

---

## 📊 **Coverage Requirements**

- ✅ **Project Coverage:** 80% (overall)
- ✅ **Patch Coverage:** 70% (new/changed code)

The pipeline will fail if coverage drops below these thresholds.

---

## 🔍 **Pytest Command Used**

Exactly as you specified:

```bash
pytest --cov --junitxml=junit.xml -o junit_family=legacy
```

Plus additional options for better reporting:
- `--cov-report=xml` - For Codecov
- `--cov-report=term-missing` - Terminal output
- `--cov-report=html` - HTML report
- `-v` - Verbose output

---

## 🚨 **Troubleshooting**

### **Workflow Fails - Codecov Token Missing**

**Error:** `CODECOV_TOKEN not found`

**Fix:** Add the secret as described in Step 1 above.

### **Tests Fail - Database Connection**

**Error:** `Could not connect to database`

**Fix:** The workflow automatically sets up PostgreSQL and Redis. Check service health in workflow logs.

### **Coverage Too Low**

**Error:** `Coverage below threshold`

**Fix:** Increase test coverage or adjust thresholds in `codecov.yml`:
```yaml
target: 70%  # Lower from 80% if needed
```

---

## 📝 **Test Locally First**

Before pushing, test locally:

```bash
# Backend tests
cd backend
pytest --cov --junitxml=junit.xml -o junit_family=legacy

# Frontend lint
cd frontend
npm run lint
npm run type-check

# Frontend tests
npm run test

# E2E tests
npm run test:e2e
```

---

## 🎯 **Next Steps After Setup**

1. ✅ **Monitor First Run** - Watch the workflow execute
2. ✅ **Review Coverage** - Check Codecov dashboard
3. ✅ **Create PR** - See coverage comments in action
4. ✅ **Adjust Thresholds** - Modify `codecov.yml` if needed

---

## 📚 **More Information**

- Full setup guide: `CI_CD_SETUP.md`
- Complete summary: `CI_CD_COMPLETE_SUMMARY.md`
- Workflow file: `.github/workflows/ci.yml`

---

**Ready? Let's go!** 🚀

1. Add Codecov token
2. Push code
3. Watch the magic happen!

---

**Last Updated:** 2025-01-26

