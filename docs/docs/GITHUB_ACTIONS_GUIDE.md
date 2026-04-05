# GitHub Actions Guide za ggNET2

**Datum kreiranja:** 2025-01-26  
**Status:** 📋 Kompletan GitHub Actions Guide

---

## 📊 Pregled

Ovaj dokument opisuje sve GitHub Actions workflows kreirane za ggNET2 projekat. Workflows su optimizovani za Debian/Ubuntu OS i pokrivaju CI/CD pipeline.

---

## 🚀 Quick Start

### Aktivacija Workflows

Workflows se automatski pokreću kada:
- Push-ujete kod na `main` ili `develop` branch
- Kreirate Pull Request
- Push-ujete tag (za release workflow)
- Manual trigger (workflow_dispatch)

### Prvi Put Setup

1. **Push kod na GitHub:**
   ```bash
   git add .
   git commit -m "Add GitHub Actions workflows"
   git push origin main
   ```

2. **Proverite Actions tab:**
   - Idite na GitHub repository
   - Kliknite na "Actions" tab
   - Workflows će se automatski pokrenuti

---

## 📋 Workflow Overview

### 1. CI Workflow (`ci.yml`)
**Glavni CI workflow koji pokreće sve osnovne checks.**

**Kada se pokreće:**
- Push na main/develop
- Pull Request

**Šta radi:**
- Backend: Linting, testovi, migrations
- Frontend: Linting, build

**Vreme izvršavanja:** ~5-10 minuta

---

### 2. Backend Tests (`backend-test.yml`)
**Dedikovani workflow za backend testove sa coverage.**

**Kada se pokreće:**
- Promene u `app/backend/**`
- Promene u `tests/**`
- Promene u `requirements.txt`

**Šta radi:**
- Postavlja PostgreSQL servis
- Instalira dependencies
- Pokreće migrations
- Pokreće pytest sa coverage
- Upload-uje coverage na Codecov

**Vreme izvršavanja:** ~3-5 minuta

---

### 3. Frontend Tests (`frontend-test.yml`)
**Dedikovani workflow za frontend testove i build.**

**Kada se pokreće:**
- Promene u `app/frontend/**`

**Šta radi:**
- Instalira Node.js dependencies
- Pokreće ESLint
- Build-uje frontend
- Proverava build output

**Vreme izvršavanja:** ~2-3 minuta

---

### 4. Backend Lint (`backend-lint.yml`)
**Dedikovani workflow za backend code quality.**

**Kada se pokreće:**
- Promene u `app/backend/**`

**Šta radi:**
- Pokreće flake8
- Proverava black formatting
- Proverava isort import sorting
- Pokreće pylint

**Vreme izvršavanja:** ~1-2 minuta

---

### 5. Build (`build.yml`)
**Workflow za build verifikaciju.**

**Kada se pokreće:**
- Push na main/develop
- Pull Request
- Manual trigger

**Šta radi:**
- Build-uje backend (verifikuje imports)
- Build-uje frontend
- Upload-uje build artifacts

**Vreme izvršavanja:** ~3-5 minuta

---

### 6. Security Scan (`security-scan.yml`)
**Workflow za security scanning.**

**Kada se pokreće:**
- Push/PR
- Weekly schedule (nedeljno)

**Šta radi:**
- Safety check (Python dependencies)
- Bandit (Python security linter)
- npm audit (frontend dependencies)
- Upload-uje security reports

**Vreme izvršavanja:** ~2-3 minuta

---

### 7. Deploy to Debian (`deploy-debian.yml`)
**Workflow za deployment package kreiranje.**

**Kada se pokreće:**
- Push na main branch
- Push tag (v*)
- Manual trigger (sa environment selection)

**Šta radi:**
- Instalira sve dependencies
- Build-uje frontend
- Kreira deployment package (tar.gz)
- Kreira deployment script
- Upload-uje artifacts

**Vreme izvršavanja:** ~5-7 minuta

---

### 8. Release (`release.yml`)
**Workflow za GitHub Release kreiranje.**

**Kada se pokreće:**
- Push tag u formatu `v*.*.*` (npr. v1.0.0)

**Šta radi:**
- Build-uje aplikaciju
- Kreira release package
- Kreira checksums (SHA256)
- Kreira GitHub Release sa artifacts

**Vreme izvršavanja:** ~5-7 minuta

---

### 9. Dependency Update Check (`dependency-update.yml`)
**Workflow za dependency update checking.**

**Kada se pokreće:**
- Weekly schedule (ponedeljak)
- Manual trigger

**Šta radi:**
- Proverava outdated Python packages
- Proverava outdated Node.js packages
- Pokreće security audit
- Generiše dependency report

**Vreme izvršavanja:** ~2-3 minuta

---

### 10. Code Quality (`code-quality.yml`)
**Workflow za code quality checks.**

**Kada se pokreće:**
- Push/PR na main/develop

**Šta radi:**
- Proverava Python formatting (black, isort)
- Proverava Python style (flake8)
- Proverava type hints (mypy)
- Pokreće frontend linter
- Generiše code quality report

**Vreme izvršavanja:** ~3-4 minuta

---

### 11. Database Migrations Check (`migrations-check.yml`)
**Workflow za database migrations verifikaciju.**

**Kada se pokreće:**
- Promene u `alembic/**`
- Promene u `app/backend/config/models.py`

**Šta radi:**
- Proverava migration fajlove
- Testira migrations up (upgrade head)
- Testira migrations down (downgrade)
- Verifikuje database schema
- Proverava da li su svi modeli pokriveni

**Vreme izvršavanja:** ~2-3 minuta

---

## 🔧 Konfiguracija

### Secrets (Opciono)

Za deployment workflow, možete dodati secrets u GitHub Settings → Secrets and variables → Actions:

- `DEPLOY_HOST` - Debian server hostname/IP
- `DEPLOY_USER` - SSH username za deployment
- `DEPLOY_SSH_KEY` - SSH private key za deployment

### Environment Variables

Workflows koriste sledeće environment variables:

```yaml
DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_ggnet2
JWT_SECRET_KEY: test_secret_key_for_ci
ENVIRONMENT: test
```

### Codecov Integration (Opciono)

Za coverage reports, možete dodati Codecov token:
- Repository Settings → Secrets → `CODECOV_TOKEN`

---

## 📊 Workflow Status Badges

Možete dodati status badges u README.md:

```markdown
![CI](https://github.com/your-org/ggnet2/workflows/CI/badge.svg)
![Backend Tests](https://github.com/your-org/ggnet2/workflows/Backend%20Tests/badge.svg)
![Frontend Tests](https://github.com/your-org/ggnet2/workflows/Frontend%20Tests/badge.svg)
```

---

## 🐛 Troubleshooting

### Workflow Ne Pokreće Se

**Problem:** Workflow se ne pokreće automatski

**Rešenje:**
- Proverite da li je workflow fajl u `.github/workflows/` folderu
- Proverite da li je workflow fajl validan YAML
- Proverite GitHub Actions permissions u repository settings

### Backend Tests Failing

**Problem:** Backend testovi padaju

**Rešenje:**
- Proverite da li je PostgreSQL servis pokrenut
- Proverite database connection string
- Proverite da li su migrations uspešne
- Proverite da li su sve dependencies instalirane

### Frontend Build Failing

**Problem:** Frontend build pada

**Rešenje:**
- Proverite Node.js verziju (treba 18+)
- Proverite da li su sve dependencies instalirane
- Proverite ESLint errors
- Proverite da li postoji `package-lock.json`

### Security Scan Warnings

**Problem:** Security scan pronalazi vulnerabilnosti

**Rešenje:**
- Review security reports u artifacts
- Update vulnerable dependencies
- Fix security issues u kodu
- Dodajte exceptions ako je potrebno

### Migrations Check Failing

**Problem:** Migrations check pada

**Rešenje:**
- Proverite da li su svi modeli pokriveni migrations
- Proverite da li su migrations validne
- Proverite database schema

---

## 📈 Workflow Optimization

### Caching

Workflows koriste caching za:
- Python dependencies (`pip cache`)
- Node.js dependencies (`npm cache`)

### Parallel Jobs

Neki workflows pokreću jobs paralelno:
- Backend i Frontend CI se pokreću paralelno
- Build i Test jobs se pokreću paralelno

### Conditional Execution

Workflows koriste `paths` filter za optimizaciju:
- Backend workflows se pokreću samo na backend promenama
- Frontend workflows se pokreću samo na frontend promenama

---

## 🎯 Best Practices

### 1. Commit Messages
- Koristite jasne commit messages
- Workflows se pokreću na svaki push

### 2. Branch Protection
- Zaštitite main branch
- Zahtevajte passing workflows pre merge

### 3. Pull Requests
- Review workflow status pre merge
- Fix failing workflows pre merge

### 4. Releases
- Koristite semantic versioning (v1.0.0)
- Release workflow se automatski pokreće na tag push

---

## 📚 Reference

- **Workflow Files:** `.github/workflows/`
- **Workflow README:** `.github/workflows/README.md`
- **GitHub Actions Docs:** https://docs.github.com/en/actions
- **Python Setup:** https://github.com/actions/setup-python
- **Node.js Setup:** https://github.com/actions/setup-node

---

## ✅ Checklist

- [ ] Workflows su kreirani i validni
- [ ] Workflows se pokreću na push/PR
- [ ] Backend testovi prolaze
- [ ] Frontend testovi prolaze
- [ ] Build workflow radi
- [ ] Security scan radi
- [ ] Deployment package se kreira
- [ ] Release workflow radi
- [ ] Status badges dodati (opciono)

---

**GitHub Actions Workflows Complete!** ✅

