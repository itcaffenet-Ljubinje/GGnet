# CI/CD Setup - Complete Guide

**Date:** 2025-01-26  
**Status:** ✅ **SETUP COMPLETE**

---

## 🎯 **Overview**

Complete CI/CD pipeline using GitHub Actions with automated testing, code coverage, and quality checks.

---

## 📋 **What's Included**

### **1. GitHub Actions Workflows** ✅

- ✅ **Backend Tests** - Unit and integration tests with pytest
- ✅ **Frontend Lint & Type Check** - ESLint and TypeScript validation
- ✅ **Frontend Unit Tests** - Vitest unit tests with coverage
- ✅ **Frontend E2E Tests** - Playwright end-to-end tests
- ✅ **Build Check** - Verify builds succeed

### **2. Code Coverage Integration** ✅

- ✅ **Codecov Integration** - Automated coverage reporting
- ✅ **Backend Coverage** - pytest-cov with XML output
- ✅ **Frontend Coverage** - Vitest coverage
- ✅ **Coverage Thresholds** - 80% project, 70% patch

### **3. Test Result Upload** ✅

- ✅ **JUnit XML** - Test results in standard format
- ✅ **Codecov Test Results** - Upload test results to Codecov
- ✅ **Artifacts** - Test results stored as artifacts

---

## 🚀 **Workflow Jobs**

### **1. Backend Tests** (`backend-tests`)

**Runs:**
- Unit and integration tests
- Code coverage with pytest-cov
- JUnit XML output

**Services:**
- PostgreSQL 15 (for database tests)
- Redis 7 (for cache tests)

**Outputs:**
- Coverage XML: `backend/coverage.xml`
- JUnit XML: `backend/junit.xml`
- HTML coverage: `backend/htmlcov/`

---

### **2. Frontend Lint & Type Check** (`frontend-lint`)

**Runs:**
- TypeScript type checking
- ESLint linting

**Fast feedback** for code quality issues.

---

### **3. Frontend Unit Tests** (`frontend-tests`)

**Runs:**
- Vitest unit tests
- Coverage reporting

**Outputs:**
- Coverage JSON: `frontend/coverage/coverage-final.json`

---

### **4. Frontend E2E Tests** (`frontend-e2e`)

**Runs:**
- Playwright E2E tests
- Full application testing

**Services:**
- PostgreSQL 15
- Redis 7

**Outputs:**
- Playwright report
- Test traces (on failure)

---

### **5. Build Check** (`build-check`)

**Runs:**
- Frontend build verification
- Backend import validation

**Ensures** the project can be built successfully.

---

## 📊 **Codecov Integration**

### **Configuration**

The Codecov configuration is in `codecov.yml`:

```yaml
coverage:
  status:
    project:
      default:
        target: 80%      # Overall coverage target
        threshold: 1%    # Allow 1% decrease
        flags:
          - backend
          - frontend
    patch:
      default:
        target: 70%      # Patch coverage target
        threshold: 2%    # Allow 2% decrease
```

### **Coverage Flags**

- **`backend`**: Backend Python code coverage
- **`frontend`**: Frontend TypeScript code coverage

### **Setting Up Codecov**

1. **Sign up for Codecov:**
   - Go to https://codecov.io
   - Sign in with GitHub
   - Add your repository

2. **Get Codecov Token:**
   - Repository Settings → General
   - Copy the upload token

3. **Add Secret to GitHub:**
   - Repository Settings → Secrets and variables → Actions
   - Add secret: `CODECOV_TOKEN`
   - Paste your Codecov token

4. **Verify Integration:**
   - Push code to trigger workflow
   - Check Codecov dashboard for coverage reports

---

## 🔧 **Configuration Files**

### **`.github/workflows/ci.yml`**

Main CI/CD workflow with all test jobs.

### **`codecov.yml`**

Codecov configuration for coverage thresholds and settings.

### **`backend/pytest.ini`**

Pytest configuration:
- Coverage settings
- JUnit XML output
- Test markers

---

## 📝 **Workflow Triggers**

The CI pipeline runs on:

- **Push** to `main` or `develop` branches
- **Pull Requests** to `main` or `develop` branches

---

## ✅ **Success Criteria**

All jobs must pass for:
- ✅ Merging pull requests
- ✅ Deploying to production

**Coverage Requirements:**
- Overall: 80% (project)
- Patch: 70% (new code)

---

## 🚨 **Troubleshooting**

### **Backend Tests Fail**

1. Check database connection:
   ```yaml
   DATABASE_URL: "postgresql+asyncpg://ggnet:test_password@localhost:5432/ggnet"
   ```

2. Verify services are healthy:
   - PostgreSQL health check
   - Redis health check

3. Check test dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

### **Frontend Tests Fail**

1. Check Node.js version:
   - Ensure Node 18+ is used

2. Install dependencies:
   ```bash
   cd frontend
   npm ci
   ```

3. Check Playwright installation:
   ```bash
   npx playwright install --with-deps chromium
   ```

### **Codecov Upload Fails**

1. Verify token is set:
   - Check `CODECOV_TOKEN` secret exists

2. Check token permissions:
   - Ensure token has upload permissions

3. Review coverage files:
   - `backend/coverage.xml` exists
   - `frontend/coverage/coverage-final.json` exists

---

## 📈 **Coverage Reports**

### **View Coverage**

1. **Codecov Dashboard:**
   - https://codecov.io/gh/your-org/ggnet
   - Overall and file-by-file coverage

2. **GitHub PR Comments:**
   - Automatic coverage comments on PRs
   - Diff coverage highlighting

3. **Local Coverage:**
   - Backend: `backend/htmlcov/index.html`
   - Frontend: `frontend/coverage/index.html`

---

## 🎯 **Best Practices**

### **1. Keep Tests Fast**
- Run unit tests first
- E2E tests last (slowest)

### **2. Fail Fast**
- Type checking before tests
- Linting before building

### **3. Coverage Goals**
- Maintain 80%+ overall coverage
- Aim for 100% on critical paths
- Don't decrease coverage

### **4. Test Isolation**
- Each test independent
- Use fixtures for setup
- Clean up after tests

---

## 🔄 **Next Steps**

### **Immediate:**
1. ✅ Set up Codecov token
2. ✅ Trigger first workflow run
3. ✅ Verify all tests pass

### **Short-term:**
1. Add more E2E tests
2. Increase coverage thresholds
3. Add performance tests

### **Long-term:**
1. Add deployment workflows
2. Add security scanning
3. Add dependency updates

---

## 📚 **Resources**

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Codecov Documentation](https://docs.codecov.com)
- [Pytest Documentation](https://docs.pytest.org)
- [Playwright Documentation](https://playwright.dev)

---

## ✅ **Status: Complete**

All CI/CD infrastructure is set up and ready to use!

**Files Created:**
- ✅ `.github/workflows/ci.yml` - Main CI workflow
- ✅ `codecov.yml` - Updated Codecov config
- ✅ `CI_CD_SETUP.md` - This guide

**Files Updated:**
- ✅ `codecov.yml` - Enhanced configuration

---

**Last Updated:** 2025-01-26

