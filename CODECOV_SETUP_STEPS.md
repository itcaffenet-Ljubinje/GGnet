# Codecov Token Setup - Step-by-Step Guide

**Your Codecov Token:** `8af9069a-33d3-4237-9563-765e6832b26b`

---

## 🔐 **Step 1: Add Token to GitHub Secrets**

### **Method 1: Via GitHub Web Interface** (Recommended)

1. **Go to your repository on GitHub**
   - Navigate to: `https://github.com/YOUR-ORG/GGnet`
   - (Replace `YOUR-ORG` with your actual GitHub username/org)

2. **Open Repository Settings**
   - Click the **"Settings"** tab (top right of repository page)

3. **Navigate to Secrets**
   - In the left sidebar, click: **"Secrets and variables"**
   - Then click: **"Actions"**

4. **Add New Secret**
   - Click the **"New repository secret"** button
   - **Name:** `CODECOV_TOKEN`
   - **Value:** `8af9069a-33d3-4237-9563-765e6832b26b`
   - Click **"Add secret"**

5. **Verify Secret Added**
   - You should see `CODECOV_TOKEN` in the list of secrets
   - ✅ Done!

---

### **Method 2: Via GitHub CLI** (Command Line)

If you have GitHub CLI installed:

```bash
gh secret set CODECOV_TOKEN --body "8af9069a-33d3-4237-9563-765e6832b26b"
```

---

## ✅ **Step 2: Verify Setup**

### **Check Workflow File**

Your workflow file (`.github/workflows/ci.yml`) should already reference the token:

```yaml
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    token: ${{ secrets.CODECOV_TOKEN }}  # ← This is correct!
```

✅ This is already configured!

---

## 🚀 **Step 3: Test the Setup**

### **Option 1: Push Code to Trigger Workflow**

```bash
# Add all CI/CD files
git add .github/workflows/ci.yml
git add codecov.yml
git add backend/pytest.ini

# Commit
git commit -m "Add CI/CD pipeline with Codecov integration"

# Push to trigger workflow
git push origin main
```

### **Option 2: Create a Test PR**

```bash
# Create a test branch
git checkout -b test/cicd-setup

# Make a small change (optional)
echo "# Test CI/CD" >> TEST.md
git add TEST.md

# Commit
git commit -m "Test CI/CD pipeline"

# Push and create PR
git push origin test/cicd-setup
```

Then create a Pull Request on GitHub to trigger the workflow.

---

## 📊 **Step 4: View Results**

### **1. GitHub Actions**

After pushing:
- Go to your repository on GitHub
- Click the **"Actions"** tab
- You should see your workflow running
- Click on the workflow run to see progress

### **2. Codecov Dashboard**

- Go to: https://codecov.io
- Sign in with GitHub
- Select your repository
- You should see coverage reports appearing

### **3. PR Comments**

- Create a Pull Request
- Codecov will automatically comment with coverage information
- Shows coverage diff, file-by-file coverage, etc.

---

## 🔍 **Troubleshooting**

### **Issue: "CODECOV_TOKEN not found"**

**Problem:** Workflow can't find the secret

**Solution:**
1. Verify the secret name is exactly: `CODECOV_TOKEN` (case-sensitive)
2. Check you're in the correct repository
3. Ensure the secret was added to "Actions" secrets (not environment secrets)

### **Issue: "Invalid token"**

**Problem:** Token is incorrect or expired

**Solution:**
1. Go to https://codecov.io
2. Repository Settings → General
3. Copy the upload token again
4. Update the GitHub secret

### **Issue: Workflow Not Running**

**Problem:** Workflow doesn't trigger

**Solution:**
1. Check workflow triggers in `.github/workflows/ci.yml`:
   ```yaml
   on:
     push:
       branches: [ main, develop ]
     pull_request:
       branches: [ main, develop ]
   ```
2. Ensure you're pushing to the correct branch
3. Check the "Actions" tab is enabled for your repository

---

## ✅ **Verification Checklist**

- [ ] Secret added to GitHub (Name: `CODECOV_TOKEN`)
- [ ] Token value is correct: `8af9069a-33d3-4237-9563-765e6832b26b`
- [ ] Workflow file exists: `.github/workflows/ci.yml`
- [ ] Codecov config exists: `codecov.yml`
- [ ] Pushed code to trigger workflow
- [ ] Workflow running in GitHub Actions
- [ ] Coverage reports appearing in Codecov

---

## 🎯 **Next Steps After Setup**

1. **Monitor First Run**
   - Watch the workflow execute
   - Check for any errors

2. **Review Coverage**
   - Check Codecov dashboard
   - Review coverage reports

3. **Create PR**
   - See coverage comments in action
   - Verify coverage diffs work

4. **Adjust Thresholds** (if needed)
   - Edit `codecov.yml` to adjust coverage targets
   - Currently set to 80% project, 70% patch

---

## 📚 **Resources**

- **Codecov Dashboard:** https://codecov.io
- **GitHub Secrets:** https://docs.github.com/en/actions/security-guides/encrypted-secrets
- **CI/CD Setup Guide:** `CI_CD_SETUP.md`
- **Quick Start:** `CI_CD_QUICK_START.md`

---

**Ready to go!** Once you've added the secret to GitHub, push your code and watch the CI/CD pipeline run! 🚀

---

**Last Updated:** 2025-01-26

