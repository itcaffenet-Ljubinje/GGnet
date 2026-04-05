# Environment Variables Guide

**Datum kreiranja:** 2025-01-26  
**Status:** 📋 Environment Variables Documentation

---

## 📊 Pregled

Ovaj dokument opisuje environment variables koje koristi ggNET2 aplikacija i kako ih konfigurisati.

---

## 📁 Environment File Locations

### 1. `.env` (Root Directory) - **PREPORUČENO**

**Lokacija:** `/opt/ggnet2/.env` (ili project root)

**Kako se koristi:**
- Aplikacija automatski učitava `.env` fajl iz root direktorijuma
- Koristi se `python-dotenv` i `pydantic-settings`
- Definisano u `app/backend/config/settings.py`:
  ```python
  model_config = SettingsConfigDict(
      env_file=".env",
      case_sensitive=True,
      extra="ignore",
  )
  ```

**Template fajl:** `.env.example` (root)

### 2. `config/ggnet2.env.example` (Config Directory)

**Lokacija:** `config/ggnet2.env.example`

**Kako se koristi:**
- Alternativni template fajl
- Koristi se u nekim setup script-ovima
- Može se kopirati u `.env` ali zahteva prilagođavanje

**Napomena:** Ovaj fajl ima nešto drugačije ime varijabli i može zahtevati prilagođavanje.

---

## 🔧 Kako Koristiti

### Opcija 1: Koristite `.env.example` (Preporučeno)

```bash
# Kopirajte template u .env
cp .env.example .env

# Uredite .env sa svojim vrednostima
vim .env
```

### Opcija 2: Koristite `config/ggnet2.env.example`

```bash
# Kopirajte template u .env
cp config/ggnet2.env.example .env

# Uredite .env i prilagodite imena varijabli prema Settings klasi
vim .env
```

**Napomena:** `config/ggnet2.env.example` koristi nešto drugačije ime varijabli (npr. `APP_ENV` umesto `ENVIRONMENT`), pa će možda trebati prilagođavanje.

---

## 📋 Environment Variables

### Application Settings

```env
APP_NAME=ggNET2
APP_VERSION=1.0.0
ENVIRONMENT=production  # development, staging, production
DEBUG=false
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Server Settings

```env
HOST=0.0.0.0
PORT=8000
API_PREFIX=/api
```

### Database Settings

```env
DATABASE_URL=postgresql://ggnet2:password@localhost:5432/ggnet2
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

**Format DATABASE_URL:**
- PostgreSQL: `postgresql://user:password@host:port/database`
- SQLite: `sqlite:///./ggnet2.db`

### CORS Settings

```env
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,https://your-domain.com
CORS_ALLOW_CREDENTIALS=true
```

**Napomena:** `CORS_ORIGINS` je comma-separated lista URL-ova.

### ZFS Settings

```env
ZFS_POOL_NAME=pool0
ZFS_BASE_PATH=pool0/ggnet2
ZFS_IMAGES_PATH=pool0/ggnet2/images
ZFS_CLONES_PATH=pool0/ggnet2/clones
```

### Network Settings

```env
SERVER_IP=192.168.1.100
BRIDGE_NAME=vmbr0
DHCP_RANGE_START=192.168.1.100
DHCP_RANGE_END=192.168.1.200
```

### Security Settings

```env
SECRET_KEY=your_very_secure_secret_key_minimum_32_characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Napomena:** `SECRET_KEY` i `JWT_SECRET_KEY` su sinonimni - koristite jedan ili drugi.

### Authentication Settings

```env
JWT_SECRET_KEY=your_very_secure_secret_key_minimum_32_characters
JWT_ALGORITHM=HS256
```

**Napomena:** Ako nije postavljen `JWT_SECRET_KEY`, koristi se `SECRET_KEY`.

### Admin User (Initial Setup)

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_this_password
ADMIN_EMAIL=admin@ggnet2.local
```

**Napomena:** Ovo se koristi samo za inicijalno kreiranje admin user-a. Nakon toga, promenite password preko UI-a.

### Optional Settings

```env
# External URLs (for production)
EXTERNAL_URL=https://your-domain.com
BACKEND_BASE_URL=https://your-domain.com
FRONTEND_ORIGIN=https://your-domain.com

# Monitoring
PROMETHEUS_PUSHGATEWAY_URL=http://localhost:9091
SENTRY_DSN=https://your-sentry-dsn

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100

# Timezone
TIMEZONE=UTC
```

---

## 🔒 Security Best Practices

### 1. Never Commit `.env` to Git

```bash
# Ensure .env is in .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo ".env.*.local" >> .gitignore
```

### 2. Use Strong Secrets

```bash
# Generate secure secret key
openssl rand -hex 32
```

### 3. Use Different Secrets for Each Environment

- Development: `.env.development`
- Staging: `.env.staging`
- Production: `.env.production`

### 4. Restrict File Permissions

```bash
# On Linux/Unix
chmod 600 .env
chown ggnet2:ggnet2 .env
```

---

## 📝 Variable Mapping

### Settings Class → Environment Variable

| Settings Property | Environment Variable | Default |
|-------------------|---------------------|---------|
| `APP_NAME` | `APP_NAME` | `"ggnet2"` |
| `APP_VERSION` | `APP_VERSION` | `"0.1.0"` |
| `DEBUG` | `DEBUG` | `False` |
| `LOG_LEVEL` | `LOG_LEVEL` | `"INFO"` |
| `HOST` | `HOST` | `"0.0.0.0"` |
| `PORT` | `PORT` | `8000` |
| `DATABASE_URL` | `DATABASE_URL` | `"postgresql://..."` |
| `ZFS_POOL_NAME` | `ZFS_POOL_NAME` | `"pool0"` |
| `SECRET_KEY` | `SECRET_KEY` ili `JWT_SECRET_KEY` | `"your-secret-key..."` |
| `ALGORITHM` | `ALGORITHM` ili `JWT_ALGORITHM` | `"HS256"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |

---

## 🔄 Migration from `config/ggnet2.env.example`

Ako koristite `config/ggnet2.env.example`, evo mapping-a:

| `config/ggnet2.env.example` | `.env.example` (Settings) |
|------------------------------|---------------------------|
| `APP_ENV` | `ENVIRONMENT` |
| `HOST` | `HOST` |
| `PORT` | `PORT` |
| `DATABASE_URL` | `DATABASE_URL` |
| `JWT_SECRET_KEY` | `SECRET_KEY` ili `JWT_SECRET_KEY` |
| `JWT_ALGORITHM` | `ALGORITHM` ili `JWT_ALGORITHM` |
| `ZFS_POOL` | `ZFS_POOL_NAME` |
| `ZFS_IMAGES_DATASET` | `ZFS_IMAGES_PATH` |
| `LOG_LEVEL` | `LOG_LEVEL` |

---

## ✅ Checklist

- [ ] `.env.example` postoji u root-u (template)
- [ ] `.env` fajl kreiran iz template-a
- [ ] Svi required variables postavljeni
- [ ] `SECRET_KEY` promenjen na siguran value
- [ ] `DATABASE_URL` konfigurisan
- [ ] `ADMIN_PASSWORD` promenjen
- [ ] `.env` dodato u `.gitignore`
- [ ] File permissions postavljeni (600)

---

## 📚 Reference

- **Settings Class:** `app/backend/config/settings.py`
- **Deployment Guide:** `docs/DEPLOYMENT_COMPLETE_GUIDE.md`
- **Template Files:**
  - `.env.example` (root) - **Preporučeno**
  - `config/ggnet2.env.example` - Alternativni template

---

## 🎯 Preporuka

**Koristite `.env.example` iz root direktorijuma** jer je:
- ✅ Prilagođen Settings klasi
- ✅ Kompletan sa svim varijablama
- ✅ Standardna lokacija (root)
- ✅ Lako za korišćenje

**`config/ggnet2.env.example`** možete koristiti kao alternativu, ali zahteva prilagođavanje imena varijabli.

---

**Environment Variables Guide Complete!** ✅

