# Zero-Config Setup Guide

**Datum kreiranja:** 2025-01-26  
**Status:** 📋 Zero-Config Setup Documentation

---

## 📊 Pregled

ggNET2 sada podržava **zero-config setup** - možete pokrenuti aplikaciju bez `.env` fajla! Aplikacija automatski:

- ✅ Detektuje server IP adresu
- ✅ Generiše JWT secret key
- ✅ Postavlja default database URL (localhost)
- ✅ Konfiguriše CORS origins
- ✅ Omogućava postavljanje ZFS pool-a preko web interfejsa

---

## 🚀 Quick Start (Bez .env fajla)

### 1. Instalirajte Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Frontend dependencies
cd app/frontend
npm install
```

### 2. Setup Database

```bash
# Kreirajte PostgreSQL database
sudo -u postgres psql
CREATE DATABASE ggnet2;
CREATE USER ggnet2 WITH PASSWORD 'ggnet2_password';
GRANT ALL PRIVILEGES ON DATABASE ggnet2 TO ggnet2;
\q
```

### 3. Pokrenite Migrations

```bash
alembic upgrade head
```

### 4. Pokrenite Aplikaciju

```bash
# Backend
uvicorn app.main:app --reload

# Frontend (u drugom terminalu)
cd app/frontend
npm run dev
```

**To je sve!** Aplikacija će automatski:
- Detektovati server IP
- Generisati JWT secret key
- Konfigurisati CORS origins
- Pokrenuti sa default vrednostima

---

## 🔧 Automatska Detekcija i Generisanje

### Server IP Detekcija

Aplikacija automatski detektuje server IP adresu:

```python
# Automatski detektuje IP
SERVER_IP = detect_server_ip()  # npr. "192.168.1.100"
```

**Kako radi:**
1. Pokušava da se konektuje na eksterni host (8.8.8.8) da odredi lokalni IP
2. Ako to ne uspe, koristi hostname IP
3. Ako ni to ne uspe, koristi `None` (možete postaviti preko web interfejsa)

### JWT Secret Key Generisanje

Aplikacija automatski generiše siguran JWT secret key:

```python
# Automatski generiše secret key
SECRET_KEY = generate_secret_key()  # 32-byte secure random string
```

**Kako radi:**
1. Proverava environment variable (`SECRET_KEY` ili `JWT_SECRET_KEY`)
2. Ako nije postavljen, pokušava da učita iz `/etc/ggnet2/secret.key`
3. Ako fajl ne postoji, generiše novi key i čuva ga u fajl
4. Key se čuva za buduće pokretanja

**Lokacija secret key fajla:**
- `/etc/ggnet2/secret.key` (Linux)
- Automatski se kreira sa permissions `600` (read/write samo za owner)

### CORS Origins Auto-Konfiguracija

Aplikacija automatski konfiguriše CORS origins:

```python
# Automatski generiše CORS origins
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    f"http://{SERVER_IP}:3000",  # Ako je SERVER_IP detektovan
    f"http://{SERVER_IP}:5173",  # Ako je SERVER_IP detektovan
]
```

### URL Auto-Generisanje

Aplikacija automatski generiše URL-ove:

```python
# Automatski generiše URL-ove
EXTERNAL_URL = f"http://{SERVER_IP}:{PORT}"
BACKEND_BASE_URL = f"http://{SERVER_IP}:{PORT}"
FRONTEND_ORIGIN = f"http://{SERVER_IP}:5173"
```

---

## 📋 Default Vrednosti

### Database

```python
DATABASE_URL = "postgresql://ggnet2:ggnet2_password@localhost:5432/ggnet2"
```

**Napomena:** Ovo je statična default vrednost za localhost. Možete je promeniti preko environment variable ili web interfejsa.

### ZFS Pool

```python
ZFS_POOL_NAME = None  # Opciono - postavlja se preko web interfejsa
ZFS_BASE_PATH = None
ZFS_IMAGES_PATH = None
ZFS_CLONES_PATH = None
```

**Napomena:** ZFS pool se ne postavlja tokom instalacije - postavlja se preko web interfejsa kada je potrebno.

### Server

```python
HOST = "0.0.0.0"
PORT = 8000
API_PREFIX = "/api"
```

---

## 🔒 Security

### Secret Key Persistence

Secret key se automatski čuva u `/etc/ggnet2/secret.key`:

```bash
# Automatski kreiran fajl
/etc/ggnet2/secret.key  # Permissions: 600 (read/write owner only)
```

**Zašto je ovo važno:**
- Secret key se generiše jednom i čuva za buduće pokretanja
- Ako se key promeni, svi postojeći JWT tokeni će biti nevažeći
- Fajl se automatski kreira sa sigurnim permissions

### Environment Variables (Opciono)

Ako želite da override-ujete automatske vrednosti, možete koristiti environment variables:

```bash
# Set environment variables
export SECRET_KEY="your-custom-secret-key"
export SERVER_IP="192.168.1.100"
export DATABASE_URL="postgresql://user:pass@host:5432/db"
```

Ili koristite `.env` fajl (opciono):

```bash
cp .env.example .env
vim .env
```

---

## 🌐 Web Interface Configuration

### ZFS Pool Setup

ZFS pool se postavlja preko web interfejsa:

1. **Login** u web interfejs
2. **Settings** → **Storage** tab
3. **Configure ZFS Pool**
4. Unesite pool name i paths
5. **Save**

### Network Configuration

Network settings se mogu postaviti preko web interfejsa:

1. **Settings** → **Network** tab
2. **Configure Network**
3. Unesite IP adrese, bridge name, DHCP range
4. **Save**

---

## 📝 Logging

Aplikacija loguje automatski detektovane vrednosti:

```
INFO: Starting ggnet2 v0.1.0
INFO: Debug mode: False
INFO: Database URL: localhost:5432/ggnet2
INFO: Server IP: 192.168.1.100 (auto-detected)
INFO: External URL: http://192.168.1.100:8000 (auto-generated)
INFO: CORS Origins: http://localhost:3000, http://localhost:5173, http://192.168.1.100:3000, http://192.168.1.100:5173
INFO: SECRET_KEY: ***abc12345 (auto-generated)
```

---

## ✅ Checklist

- [ ] PostgreSQL instaliran i pokrenut
- [ ] Database `ggnet2` kreiran
- [ ] User `ggnet2` kreiran sa password-om
- [ ] Migrations pokrenute (`alembic upgrade head`)
- [ ] Backend pokrenut (`uvicorn app.main:app --reload`)
- [ ] Frontend pokrenut (`npm run dev`)
- [ ] Web interfejs dostupan
- [ ] ZFS pool konfigurisan preko web interfejsa (kada je potrebno)

---

## 🐛 Troubleshooting

### Server IP Nije Detektovan

**Problem:** `SERVER_IP` je `None`

**Rešenje:**
1. Proverite network konfiguraciju
2. Postavite `SERVER_IP` preko environment variable:
   ```bash
   export SERVER_IP="192.168.1.100"
   ```
3. Ili postavite preko web interfejsa

### Secret Key Se Ne Čuva

**Problem:** Secret key se generiše svaki put

**Rešenje:**
1. Proverite permissions na `/etc/ggnet2/` direktorijumu
2. Kreirajte direktorijum ručno:
   ```bash
   sudo mkdir -p /etc/ggnet2
   sudo chown $USER:$USER /etc/ggnet2
   ```
3. Aplikacija će automatski kreirati `secret.key` fajl

### CORS Errors

**Problem:** CORS errors u browser-u

**Rešenje:**
1. Proverite da li je `SERVER_IP` detektovan
2. Proverite `CORS_ORIGINS` u logovima
3. Dodajte frontend URL ručno preko environment variable:
   ```bash
   export CORS_ORIGINS="http://localhost:5173,http://192.168.1.100:5173"
   ```

---

## 📚 Reference

- **Settings Class:** `app/backend/config/settings.py`
- **Environment Variables:** `docs/ENVIRONMENT_VARIABLES.md`
- **Deployment Guide:** `docs/DEPLOYMENT_COMPLETE_GUIDE.md`

---

## 🎯 Preporuka

**Za Development:**
- Koristite zero-config setup (bez `.env` fajla)
- Aplikacija automatski detektuje sve potrebno

**Za Production:**
- Razmotrite korišćenje `.env` fajla za eksplicitnu konfiguraciju
- Postavite `SECRET_KEY` ručno za veću sigurnost
- Konfigurišite `DATABASE_URL` za production database

---

**Zero-Config Setup Complete!** ✅

