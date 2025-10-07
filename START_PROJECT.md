# 🚀 GGnet Project - Start Guide

## ✅ **TRENUTNI STATUS:**

### **Backend: ✅ POKRENUT I RADI**
- URL: `http://localhost:8000`
- Health Check: http://localhost:8000/health → ✅ 200 OK
- Swagger UI: http://localhost:8000/docs
- Login Endpoint: `POST http://localhost:8000/auth/login`
- **Login TEST: ✅ USPEŠAN!**

### **Admin Credentials:**
```
Username: admin
Password: admin123
```

---

## 📋 **KAKO POKRENUTI PROJEKAT**

### **Opcija 1: Manuelno (Backend + Frontend odvojeno)**

#### **1. Backend (FastAPI)**

```powershell
# Terminal 1 - Backend
cd C:\Users\SERVER-PC\Documents\GGnet-projects\GGnet\backend

# Aktiviraj virtualenv
venv\Scripts\activate

# Pokreni backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend će biti dostupan na: http://localhost:8000

#### **2. Frontend (React + Vite)**

```powershell
# Terminal 2 - Frontend
cd C:\Users\SERVER-PC\Documents\GGnet-projects\GGnet\frontend

# Pokreni dev server
npm run dev
```

Frontend će biti dostupan na: http://localhost:3000

---

### **Opcija 2: Docker (Preporučeno za produkciju)**

**Napomena:** Docker nije instaliran na ovom sistemu. Ako želiš da koristiš Docker:

1. Instaliraj Docker Desktop za Windows
2. Pokreni:

```powershell
cd C:\Users\SERVER-PC\Documents\GGnet-projects\GGnet

# Build i pokreni sve servise
docker-compose up --build

# Ili u pozadini
docker-compose up -d
```

Docker će automatski:
- Pokrenuti PostgreSQL bazu
- Pokrenuti Redis cache
- Izvršiti migracije
- Kreirati admin korisnika
- Pokrenuti backend na portu 8000
- Pokrenuti frontend na portu 80

---

## 🧪 **TESTIRANJE**

### **1. Test Backend Health**

```powershell
curl http://localhost:8000/health
```

Očekivani output:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-07T20:13:29.415508+00:00",
  "version": "1.0.0",
  "service": "ggnet-diskless-server"
}
```

### **2. Test Admin Login**

```powershell
cd backend
venv\Scripts\python.exe test_login_correct.py
```

Očekivani output:
```
Status Code: 200
✓ Login successful!
Access Token: eyJhbGci...
```

### **3. Test Frontend**

Otvori browser: http://localhost:3000

Trebalo bi da vidiš login stranicu. Unesi:
- Username: `admin`
- Password: `admin123`

---

## 📊 **API ENDPOINTS**

### **Authentication:**
- `POST /auth/login` - Login
- `POST /auth/logout` - Logout
- `POST /auth/refresh` - Refresh token
- `POST /auth/change-password` - Change password

### **Images:**
- `GET /images` - List images
- `POST /images/upload` - Upload image
- `GET /images/{id}` - Get image
- `DELETE /images/{id}` - Delete image

### **Machines:**
- `GET /machines` - List machines
- `POST /machines` - Create machine
- `GET /machines/{id}` - Get machine
- `PUT /machines/{id}` - Update machine
- `DELETE /machines/{id}` - Delete machine

### **Sessions:**
- `POST /api/v1/sessions/start` - Start diskless session
- `POST /api/v1/sessions/stop` - Stop session
- `GET /api/v1/sessions/` - List sessions

### **Targets:**
- `POST /api/v1/targets` - Create iSCSI target
- `GET /api/v1/targets` - List targets
- `DELETE /api/v1/targets/{id}` - Delete target

### **Monitoring:**
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /monitoring/realtime` - Real-time stats

---

## 🐛 **TROUBLESHOOTING**

### **Problem: Backend ne startuje**

**Rešenje:**
```powershell
# Proveri da li port 8000 je slobodan
netstat -ano | findstr :8000

# Ako je zauzet, ubij proces
taskkill /PID <PID> /F

# Ili promeni port
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### **Problem: Frontend ne može da se poveže na backend**

**Rešenje:**
1. Proveri da li backend radi: http://localhost:8000/health
2. Proveri Vite proxy config u `frontend/vite.config.ts`:
   ```typescript
   server: {
     proxy: {
       '/api': {
         target: 'http://localhost:8000',
         changeOrigin: true,
         rewrite: (path) => path.replace(/^\/api/, '')
       }
     }
   }
   ```

### **Problem: Login ne radi**

**Rešenje:**
1. Proveri da li admin postoji:
   ```powershell
   cd backend
   venv\Scripts\python.exe test_password.py
   ```

2. Ako admin ne postoji, kreiraj ga:
   ```powershell
   venv\Scripts\python.exe create_admin.py
   ```

3. Test login direktno:
   ```powershell
   venv\Scripts\python.exe test_login_correct.py
   ```

### **Problem: CORS errors**

**Rešenje:**
Backend već ima CORS middleware konfigurisan za `http://localhost:3000`.
Ako frontend radi na drugom portu, ažuriraj `backend/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # dodaj tvoj port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📝 **DATABASE**

### **SQLite (Development)**
- Lokacija: `backend/ggnet.db`
- Automatski se kreira na prvi start

### **PostgreSQL (Production/Docker)**
- Host: `localhost:5432`
- Database: `ggnet`
- User: `ggnet`
- Password: `ggnet_password`

### **Migracije**

```powershell
cd backend

# Generiši novu migraciju
alembic revision --autogenerate -m "Your message"

# Primeni migracije
alembic upgrade head

# Vrati migraciju
alembic downgrade -1
```

---

## 🔐 **SECURITY**

### **Production Checklist:**

1. ✅ Promeni admin password odmah nakon prvog logina
2. ✅ Generiši jak SECRET_KEY:
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```
3. ✅ Koristi HTTPS
4. ✅ Postavi jak POSTGRES_PASSWORD
5. ✅ Enable rate limiting (već konfigurisano)
6. ✅ Postavi firewall rules
7. ✅ Regular security updates

---

## 📚 **ADDITIONAL RESOURCES**

- **API Documentation:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Admin Login Guide:** `ADMIN_LOGIN_GUIDE.md`
- **ESLint Cleanup Summary:** `ESLINT_CLEANUP_SUMMARY.md`
- **Project Completion:** `PROJECT_COMPLETION.md`
- **Deployment Summary:** `DEPLOYMENT_SUMMARY.md`

---

## ✅ **FINAL CHECKLIST**

- [x] Backend pokrenut na port 8000
- [x] Admin korisnik kreiran (`admin`/`admin123`)
- [x] Login endpoint radi (200 OK)
- [x] Health check prolazi
- [ ] Frontend pokrenut na port 3000
- [ ] Login test iz browsera
- [ ] WebSocket konekcija radi
- [ ] Image upload radi
- [ ] Machine management radi
- [ ] Session orchestration radi

---

**Aplikacija je spremna za testiranje! 🚀**

**Backend: ✅ RADI**  
**Login: ✅ RADI**  
**Frontend: ⏳ TREBA POKRENUTI**

Sledeći korak: Otvori novi terminal i pokreni frontend sa `npm run dev`!

