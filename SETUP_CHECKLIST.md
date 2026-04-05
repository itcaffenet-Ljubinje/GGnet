# CI/CD Setup Checklist

**Codecov Token:** Retrieve the upload token from the Codecov dashboard (Repository Settings → General → Upload token) and store it only in secret managers such as GitHub Actions secrets.

---

## ✅ **Setup Steps**

### **1. Add GitHub Secret** (5 minutes)

- [ ] Go to GitHub repository
- [ ] Settings → Secrets and variables → Actions
- [ ] Click "New repository secret"
- [ ] Name: `CODECOV_TOKEN`
- [ ] Value: Paste the upload token you copied from Codecov (do not commit it)
- [ ] Click "Add secret"
- [ ] Verify secret appears in list

---

### **2. Verify Files** (2 minutes)

- [ ] `.github/workflows/ci.yml` exists
- [ ] `codecov.yml` exists
- [ ] `backend/pytest.ini` has JUnit XML config
- [ ] All files are committed to git

---

### **3. Trigger Workflow** (1 minute)

- [ ] Push code to repository:
  ```bash
  git add .github/workflows/ci.yml codecov.yml backend/pytest.ini
  git commit -m "Add CI/CD pipeline with Codecov"
  git push origin main
  ```

---

### **4. Monitor Results** (5 minutes)

- [ ] Go to GitHub → Actions tab
- [ ] See workflow running
- [ ] Check all jobs complete successfully
- [ ] View coverage reports in Codecov

---

## 🔍 **Quick Verification**

### **Check Secret is Set** (GitHub CLI)

```bash
gh secret list
```

Should show `CODECOV_TOKEN` in the list.

---

### **Test Locally First** (Optional)

Before pushing, test locally:

```bash
# Backend tests
cd backend
pytest --cov --junitxml=junit.xml -o junit_family=legacy

# Frontend
cd ../frontend
npm run lint
npm run type-check
```

---

## 📊 **Expected Results**

### **Workflow Jobs:**

- ✅ `backend-tests` - Should pass
- ✅ `frontend-lint` - Should pass
- ✅ `frontend-tests` - Should pass
- ✅ `frontend-e2e` - Should pass (may take longer)
- ✅ `build-check` - Should pass

### **Codecov:**

- ✅ Coverage report uploaded
- ✅ Coverage badge appears
- ✅ PR comments with coverage

---

## 🚨 **If Something Fails**

1. **Check workflow logs** in GitHub Actions
2. **Verify secret name** is exactly `CODECOV_TOKEN`
3. **Check token** is valid in Codecov dashboard
4. **Review error messages** for specific issues

---

**Status:** Ready when you add the GitHub secret! ✅

