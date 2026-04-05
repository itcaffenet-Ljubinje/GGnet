# Testing Codecov Integration

**Date:** 2025-01-26

---

## 🔍 **What is @codecov-ai-reviewer?**

`@codecov-ai-reviewer` is a **Codecov bot** that comments on GitHub Pull Requests. It's not a command you run locally - it's an automated bot that responds to PR events.

---

## ✅ **How to Test Codecov**

### **Method 1: Create a Test PR** (Recommended)

1. **Create a test branch:**
   ```bash
   git checkout -b test/codecov-integration
   ```

2. **Make a small change:**
   ```bash
   echo "# Test Codecov" >> TEST.md
   git add TEST.md
   git commit -m "test: Test Codecov integration"
   git push origin test/codecov-integration
   ```

3. **Create Pull Request:**
   - Go to GitHub
   - Create a PR from `test/codecov-integration` to `main`
   - The CI/CD workflow will run automatically

4. **Check Codecov:**
   - After the workflow completes, Codecov bot will comment on the PR
   - Look for `@codecov-ai-reviewer` comment with coverage report

---

### **Method 2: Verify Local Coverage**

Test coverage locally before pushing:

```bash
# Backend coverage
cd backend
pytest --cov --cov-report=xml --junitxml=junit.xml -o junit_family=legacy

# Check coverage file exists
ls -la coverage.xml junit.xml

# View HTML report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux
```

---

### **Method 3: Manual Upload to Codecov**

You can manually upload coverage to Codecov using curl. Before running the commands, make sure the `CODECOV_TOKEN` environment variable is set locally (copy the token from the Codecov dashboard or reuse the value stored in your GitHub secret—never commit it to source control):

```bash
# Upload coverage XML
curl -s https://codecov.io/bash | bash -s - \
  -t "${CODECOV_TOKEN:?Set CODECOV_TOKEN env var before running}" \
  -f backend/coverage.xml \
  -F backend

# Upload test results
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${CODECOV_TOKEN:?Set CODECOV_TOKEN env var before running}" \
  -d @backend/junit.xml \
  https://codecov.io/api/v2/test-results
```

---

## 🤖 **Codecov Bot Features**

The `@codecov-ai-reviewer` bot will:

1. **Comment on PRs** with coverage reports
2. **Show coverage diff** (what changed)
3. **Flag coverage decreases** automatically
4. **Provide file-by-file** coverage details
5. **Create coverage badges** for your README

---

## 📊 **What to Look For**

### **In GitHub PR Comments:**

```
@codecov-ai-reviewer
## [Codecov](https://codecov.io/...) Report

### Coverage Summary
- Project coverage: 85.2% (+0.5%)
- Patch coverage: 90.1% (+2.3%)

### Files Changed
- backend/app/main.py: 95% (+5%)
- frontend/src/App.tsx: 80% (no change)

[View full report →](https://codecov.io/...)
```

### **In Codecov Dashboard:**

- Go to: https://codecov.io/gh/itcaffenet-Ljubinje/GGnet
- View coverage graphs
- See coverage trends
- Download reports

---

## ✅ **Checklist for Testing**

- [ ] GitHub Secret `CODECOV_TOKEN` is set
- [ ] CI/CD workflow runs successfully
- [ ] Coverage XML files are generated
- [ ] Codecov receives uploads
- [ ] Bot comments on PRs
- [ ] Coverage badges appear

---

## 🚨 **Troubleshooting**

### **Bot Not Commenting?**

1. **Check workflow logs:**
   - GitHub Actions → Your workflow run
   - Look for "Upload coverage to Codecov" step
   - Check for errors

2. **Verify token:**
   - Check `CODECOV_TOKEN` secret exists
   - Verify token is valid in Codecov dashboard

3. **Check repository settings:**
   - Codecov → Repository Settings
   - Ensure repository is connected

### **No Coverage Reports?**

1. **Check files exist:**
   - `backend/coverage.xml`
   - `backend/junit.xml`

2. **Verify upload step:**
   - Look in workflow logs
   - Check upload succeeded

3. **Test manually:**
   - Try manual upload (see Method 3 above)

---

## 🎯 **Quick Test Command**

Run this to test everything locally:

```bash
# Test backend
cd backend
pytest --cov --cov-report=xml --junitxml=junit.xml -o junit_family=legacy -v

# Verify files
ls -la coverage.xml junit.xml htmlcov/

echo "✅ Coverage files generated successfully!"
```

---

## 📚 **Resources**

- **Codecov Dashboard:** https://codecov.io/gh/itcaffenet-Ljubinje/GGnet
- **Codecov Docs:** https://docs.codecov.com
- **Bot Documentation:** https://docs.codecov.com/docs/bot

---

**Ready to test?** Create a PR and watch the Codecov bot work! 🚀

