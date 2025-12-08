# How to Test Codecov Integration

**Date:** 2025-01-26

---

## 🤖 **What is @codecov-ai-reviewer?**

`@codecov-ai-reviewer` is a **GitHub bot** that automatically comments on Pull Requests with code coverage information. It's **not a command** you run - it's an automated bot that works when you create PRs.

---

## ✅ **How to Test Codecov**

### **Method 1: Test Locally First** (Recommended)

1. **Run tests with coverage:**
   ```powershell
   cd backend
   python -m pytest --cov --cov-report=xml --junitxml=junit.xml -o junit_family=legacy -v
   ```

2. **Check files were generated:**
   ```powershell
   # Check if files exist
   Test-Path coverage.xml
   Test-Path junit.xml
   Test-Path htmlcov/index.html
   ```

3. **View HTML report:**
   ```powershell
   start htmlcov/index.html
   ```

---

### **Method 2: Create a Test PR** (To Test Bot)

This is how you'll see `@codecov-ai-reviewer` in action:

1. **Create a test branch:**
   ```bash
   git checkout -b test/codecov-bot
   ```

2. **Make a small change:**
   ```bash
   echo "# Test Codecov Bot" >> TEST_CODECOV.md
   git add TEST_CODECOV.md
   git commit -m "test: Test Codecov bot integration"
   git push origin test/codecov-bot
   ```

3. **Create Pull Request:**
   - Go to: https://github.com/itcaffenet-Ljubinje/GGnet
   - Click "New Pull Request"
   - Select `test/codecov-bot` → `main`
   - Create the PR

4. **Wait for CI/CD to Run:**
   - GitHub Actions will run automatically
   - It will upload coverage to Codecov

5. **See the Bot Comment:**
   - After workflow completes, `@codecov-ai-reviewer` will comment
   - The comment will show coverage report
   - It will look like this:

   ```
   @codecov-ai-reviewer commented on this pull request
   
   ## Codecov Report
   
   Project coverage: 85.2% (+0.5%)
   Patch coverage: 90.1% (+2.3%)
   
   [View full report →]
   ```

---

### **Method 3: Check Codecov Dashboard**

1. **Visit Codecov Dashboard:**
   - https://codecov.io/gh/itcaffenet-Ljubinje/GGnet
   - Sign in with GitHub if needed

2. **Check Coverage:**
   - View overall coverage percentage
   - See coverage trends
   - Download reports

---

## 🔍 **Verify Setup**

### **Checklist:**

- [ ] **GitHub Secret Added:**
  - Go to: Repository Settings → Secrets → Actions
  - Verify `CODECOV_TOKEN` exists
  - Value is copied from the Codecov dashboard and stored only in the secret (never in source control)

- [ ] **Workflow File:**
  - File exists: `.github/workflows/ci.yml`
  - Contains Codecov upload steps

- [ ] **Codecov Config:**
  - File exists: `codecov.yml`
  - Config is valid

- [ ] **CI/CD Runs:**
  - Check: https://github.com/itcaffenet-Ljubinje/GGnet/actions
  - Workflow runs successfully

---

## 🎯 **What Happens Automatically**

When you create a PR:

1. ✅ **CI/CD Workflow Runs:**
   - Tests execute
   - Coverage XML generated
   - Files uploaded to Codecov

2. ✅ **Codecov Processes:**
   - Receives coverage data
   - Calculates coverage diff
   - Prepares report

3. ✅ **Bot Comments:**
   - `@codecov-ai-reviewer` bot comments on PR
   - Shows coverage summary
   - Highlights changes

---

## 🚨 **Troubleshooting**

### **Bot Not Commenting?**

1. **Check workflow logs:**
   - GitHub Actions → Latest workflow run
   - Look for "Upload coverage to Codecov" step
   - Verify it succeeded

2. **Check token:**
   - Verify `CODECOV_TOKEN` secret is set
   - Check token is valid in Codecov dashboard

3. **Wait a bit:**
   - Bot comments may take 1-2 minutes after workflow completes

### **No Coverage Upload?**

1. **Check files exist:**
   - `backend/coverage.xml` should be generated
   - `backend/junit.xml` should be generated

2. **Check workflow step:**
   - Look at "Upload coverage to Codecov" step
   - Check for error messages

---

## 📊 **Test Script**

Run the test script:

```powershell
.\test_codecov_local.bat
```

Or manually:

```powershell
cd backend
python -m pytest --cov --cov-report=xml --junitxml=junit.xml -o junit_family=legacy -v
```

---

## ✅ **Quick Test**

The fastest way to test:

1. **Create a PR** (any small change)
2. **Wait for workflow** to complete
3. **Check PR comments** for `@codecov-ai-reviewer`

That's it! The bot will automatically comment. 🚀

---

**Remember:** `@codecov-ai-reviewer` is a bot - you don't run it manually. It runs automatically when you create PRs!

