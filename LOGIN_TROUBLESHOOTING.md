# GGnet Login Troubleshooting Guide

## Problem: Ne mogu da se logujem sa username: admin i password: admin123

### Status: ✅ REŠENO

**Glavni problem**: Rate limiting je bio previše restriktivan (5 pokušaja na 15 minuta). Sada je povećan na 10 pokušaja na 5 minuta.

Sistem je ispravno konfigurisan i login funkcioniše. Evo šta je provereno:

## Provera sistema

### 1. Backend server
- **Status**: ✅ Radi na portu 8000
- **Health check**: ✅ Odgovara
- **Login endpoint**: ✅ Radi ispravno

### 2. Frontend server  
- **Status**: ✅ Radi na portu 3000
- **Proxy konfiguracija**: ✅ Ispravno podešena

### 3. Admin korisnik
- **Username**: admin
- **Password**: admin123
- **Status**: ✅ Aktivan i otključan
- **Role**: admin

### 4. CORS konfiguracija
- **Status**: ✅ Ispravno podešena za localhost:3000

## Rešenje problema

### Glavni problem: Rate limiting je bio previše restriktivan
- **Staro**: 5 pokušaja na 15 minuta
- **Novo**: 10 pokušaja na 5 minuta

### Korak 1: Očistite browser cache
```bash
# U browseru:
Ctrl + Shift + Delete (Windows/Linux)
Cmd + Shift + Delete (Mac)

# Ili otvorite Developer Tools (F12) i:
# Right-click na refresh dugme → "Empty Cache and Hard Reload"
```

### Korak 2: Proverite da li su serveri pokrenuti
```bash
# Backend (port 8000)
cd backend
.\venv\Scripts\Activate.ps1  # Windows
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (port 3000)  
cd frontend
npm run dev
```

### Korak 3: Testirajte direktno
Otvorite browser i idite na:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs

### Korak 4: Proverite Developer Tools
1. Otvorite Developer Tools (F12)
2. Idite na Network tab
3. Pokušajte login
4. Proverite da li se šalju zahtevi i kakvi su odgovori

## Test kredencijali

```
Username: admin
Password: admin123
```

## Kontakt

Ako problem i dalje postoji:
1. Proverite browser console za greške
2. Proverite Network tab za failed requests
3. Restartujte oba servera
4. Očistite browser cache ponovo

## Tehnički detalji

- **Backend**: FastAPI na portu 8000
- **Frontend**: React + Vite na portu 3000
- **Database**: SQLite (ggnet.db)
- **CORS**: Podešeno za localhost:3000
- **Proxy**: Vite proxy /api → http://localhost:8000
- **Rate Limiting**: 10 pokušaja na 5 minuta (ranije 5 na 15 minuta)

## Izmene u kodu

### 1. Rate limiting u auth.py
```python
# Stara konfiguracija
if not rate_limiter.is_allowed(rate_key, max_attempts=5, window_minutes=15):

# Nova konfiguracija  
if not rate_limiter.is_allowed(rate_key, max_attempts=10, window_minutes=5):
```

### 2. Rate limiting u middleware
```python
# Stara konfiguracija
"/auth/login": (5, 300),  # 5 requests per 5 minutes

# Nova konfiguracija
"/auth/login": (10, 300),  # 10 requests per 5 minutes
```
