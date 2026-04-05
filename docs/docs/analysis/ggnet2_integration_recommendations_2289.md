# ggNET2 - Preporuke za Integraciju Verzije 2289

**Datum:** 2025-01-XX  
**Verzija:** 1.0.0  
**Izvor:** ggrock_0.1.2289.2303-1_amd64

---

## 📋 Pregled

Ovaj dokument sadrži preporuke za integraciju konfiguracija iz verzije 2289 u ggNET2, uključujući:
- Nginx konfiguraciju
- Systemd service fajlove
- Frontend build analizu
- DLL dekompajliranje preporuke

---

## 1. Nginx Konfiguracija

### 🔍 Analiza Razlika

#### Verzija 2289 (`/etc/nginx/conf.d/ggrock.conf`)
- Koristi `conf.d` direktorijum (umesto `sites-available/sites-enabled`)
- API port: `5000` (umesto `8000`)
- Nema `/api/` prefix - direktno proxy na root
- Frontend je build-in u API (nema SPA routing)
- VNC konfiguracija: `/vnc/console`, `/vnc/`, `/websockify`
- Grafana: `/ggrock-grafana/grafana/`
- Nema Prometheus reverse proxy

#### Trenutna ggNET2 (`/etc/nginx/sites-available/ggnet2`)
- Koristi `sites-available/sites-enabled` strukturu
- API port: `8000`
- Ima `/api/` prefix za API endpoint-e
- Frontend je odvojen SPA sa routing-om
- VNC konfiguracija: `/vnc/console`, `/vnc/`, `/websockify`
- Grafana: `/ggnet2-grafana/grafana/`
- Prometheus: `/ggnet2-prometheus/`

### ✅ Preporuke

#### 1.1. Koristiti `conf.d` Strukturu (Prioritet: Srednji)

**Razlog:** Verzija 2289 koristi `conf.d` što je jednostavnije i standardnije za Debian/Ubuntu pakete.

**Akcija:**
- Ažurirati `scripts/setup_nginx.sh` da koristi `/etc/nginx/conf.d/ggnet2.conf`
- Ukloniti `sites-available/sites-enabled` logiku
- Direktno kreirati fajl u `conf.d`

**Primer:**
```bash
# Umesto:
cat > /etc/nginx/sites-available/ggnet2 <<EOF
...
EOF
ln -sf /etc/nginx/sites-available/ggnet2 /etc/nginx/sites-enabled/

# Koristiti:
cat > /etc/nginx/conf.d/ggnet2.conf <<EOF
...
EOF
```

#### 1.2. Dodati VNC Timeout Konfiguraciju (Prioritet: Visok)

**Razlog:** Verzija 2289 ima specifičan `proxy_read_timeout 61s` za VNC konekcije.

**Akcija:**
- Dodati `proxy_read_timeout 61s` u `/websockify` lokaciju
- Dodati `proxy_buffering off` za VNC

**Primer:**
```nginx
location /websockify {
    proxy_http_version 1.1;
    proxy_pass http://vnc_proxy/;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    
    # VNC connection timeout
    proxy_read_timeout 61s;
    
    # Disable cache
    proxy_buffering off;
}
```

#### 1.3. Zadržati `/api/` Prefix (Prioritet: Visok)

**Razlog:** ggNET2 koristi `/api/` prefix što je bolje za organizaciju i kompatibilnost sa modernim API standardima.

**Status:** ✅ Zadržati trenutnu implementaciju

#### 1.4. Zadržati Frontend SPA Routing (Prioritet: Visok)

**Razlog:** ggNET2 ima odvojen frontend build što je bolje za development i deployment.

**Status:** ✅ Zadržati trenutnu implementaciju

#### 1.5. Dodati Prometheus Reverse Proxy (Prioritet: Srednji)

**Razlog:** ggNET2 ima Prometheus monitoring koji nije u verziji 2289.

**Status:** ✅ Zadržati trenutnu implementaciju

### 📝 Ažurirana Nginx Konfiguracija

Kreirati novu verziju `scripts/setup_nginx.sh` koja:
1. Koristi `conf.d` strukturu
2. Uključuje VNC timeout konfiguraciju
3. Zadržava `/api/` prefix
4. Zadržava frontend SPA routing
5. Zadržava Prometheus reverse proxy

---

## 2. Systemd Service Fajlovi

### 🔍 Analiza Razlika

#### Verzija 2289 (`ggrock.service`)

**Karakteristike:**
- Minimalna konfiguracija
- Nema environment variables
- Nema resource limits
- Nema StandardOutput/StandardError journal
- Executable: `/opt/ggrock/app/GgRock.Api`
- WorkingDirectory: `/opt/ggrock/app`

#### Trenutna ggNET2 (`ggnet2-api.service`)

**Karakteristike:**
- Detaljna konfiguracija
- Environment variables (PYTHONPATH, PATH, EnvironmentFile)
- Resource limits (LimitNOFILE, LimitNPROC)
- StandardOutput/StandardError journal
- Executable: Python uvicorn
- WorkingDirectory: `/opt/ggnet2/app`

### ✅ Preporuke

#### 2.1. Zadržati Detaljnu Konfiguraciju (Prioritet: Visok)

**Razlog:** ggNET2 koristi Python/FastAPI što zahteva environment variables i resource limits.

**Status:** ✅ Zadržati trenutnu implementaciju

#### 2.2. Pojednostaviti ggrock-novnc.service (Prioritet: Nizak)

**Razlog:** Verzija 2289 ima jednostavniju konfiguraciju za novnc service.

**Akcija:**
- Možemo ukloniti resource limits iz `ggnet2-novnc.service` ako nisu potrebni
- Zadržati StandardOutput/StandardError journal

**Primer:**
```ini
[Unit]
Description=ggnet2 VNC client for VMs
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/websockify --web=/usr/share/novnc --token-plugin TokenFile --token-source /etc/ggnet2/websockify/target.config.d/ 127.0.0.1:6080
Restart=always
RestartSec=2
SyslogIdentifier=ggnet2-novnc
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### 2.3. Dodati Dependencies (Prioritet: Srednji)

**Razlog:** Verzija 2289 ima `After=libvirtd.service` za glavni service.

**Akcija:**
- Već postoji u trenutnoj implementaciji (`After=network.target postgresql.service libvirtd.service`)
- ✅ Zadržati

---

## 3. Frontend Build Analiza

### 🔍 Analiza Razlika

#### Verzija 2289
- Frontend je build-in u API (ASP.NET Core)
- Nema odvojen frontend build
- Static fajlovi su servirani direktno iz API-ja

#### Trenutna ggNET2
- Frontend je odvojen React SPA
- Build se generiše odvojeno
- Static fajlovi su servirani iz `/opt/ggnet2/frontend`

### ✅ Preporuke

#### 3.1. Analizirati Build Hash-ove (Prioritet: Srednji)

**Razlog:** Potrebno je uporediti build hash-ove da vidimo šta se promenilo u frontend-u.

**Akcija:**
1. Ekstraktovati frontend build iz verzije 2289
2. Uporediti build hash-ove sa verzijom 2200
3. Identifikovati promene u bundle-ovima
4. Dokumentovati razlike

**Metod:**
```bash
# Ekstraktovati frontend build iz verzije 2289
cd /path/to/ggrock_0.1.2289.2303-1_amd64/data/opt/ggrock/app
find . -name "*.js" -o -name "*.css" | xargs md5sum > build_2289_hashes.txt

# Uporediti sa verzijom 2200
cd /path/to/ggrock_0.1.2200.2213-1_amd64/data/opt/ggrock/app
find . -name "*.js" -o -name "*.css" | xargs md5sum > build_2200_hashes.txt

# Uporediti
diff build_2200_hashes.txt build_2289_hashes.txt
```

#### 3.2. Zadržati Odvojen Frontend Build (Prioritet: Visok)

**Razlog:** ggNET2 koristi React SPA što je bolje za development i deployment.

**Status:** ✅ Zadržati trenutnu implementaciju

---

## 4. DLL Dekompajliranje

### 🔍 Analiza Potrebe

#### Verzija 2289
- `GgRock.Api.dll` je noviji build
- Može sadržati nove API endpoint-e
- Može imati izmene u DTO modelima
- Može imati nove funkcionalnosti

### ✅ Preporuke

#### 4.1. Dekompajlirati DLL (Prioritet: Visok)

**Razlog:** Potrebno je uporediti API između verzija 2200 i 2289 da identifikujemo nove funkcionalnosti.

**Akcija:**

**Metod 1: ILSpy (Preporučeno)**
```bash
# Instalirati ILSpy
# Windows: Download from https://github.com/icsharpcode/ILSpy/releases
# Linux: Use AvaloniaILSpy

# Dekompajlirati DLL
ilspycmd GgRock.Api.dll -o GgRock.Api.decompiled
```

**Metod 2: dnSpy**
```bash
# Download dnSpy from https://github.com/dnSpy/dnSpy/releases
# Open GgRock.Api.dll in dnSpy
# Export to C# project
```

**Metod 3: dotPeek (JetBrains)**
```bash
# Download dotPeek from https://www.jetbrains.com/decompiler/
# Open GgRock.Api.dll
# Export to C# project
```

#### 4.2. Uporedna Analiza API-ja (Prioritet: Visok)

**Razlog:** Potrebno je identifikovati nove endpoint-e, DTO modele, i funkcionalnosti.

**Akcija:**
1. Dekompajlirati `GgRock.Api.dll` iz verzije 2200
2. Dekompajlirati `GgRock.Api.dll` iz verzije 2289
3. Uporediti API kontrolere
4. Uporediti DTO modele
5. Identifikovati nove funkcionalnosti
6. Dokumentovati razlike

**Struktura Analize:**
```
docs/analysis/
├── api_comparison_2200_vs_2289.md
├── new_endpoints_2289.md
├── new_dto_models_2289.md
└── api_changes_summary_2289.md
```

#### 4.3. Automatizovati Analizu (Prioritet: Nizak)

**Razlog:** Može biti korisno za buduće verzije.

**Akcija:**
- Kreirati Python skriptu za automatsku analizu dekompajliranih DLL-ova
- Koristiti regex za ekstrakciju API endpoint-a
- Koristiti regex za ekstrakciju DTO modela
- Generisati markdown dokumentaciju

---

## 5. Plan Akcije

### Faza 1: Nginx Konfiguracija (Prioritet: Visok)

**Vreme:** 1-2 sata

1. ✅ Ažurirati `scripts/setup_nginx.sh` da koristi `conf.d`
2. ✅ Dodati VNC timeout konfiguraciju
3. ✅ Testirati Nginx konfiguraciju
4. ✅ Dokumentovati izmene

**Status:** 🔄 U toku

### Faza 2: Systemd Services (Prioritet: Srednji)

**Vreme:** 30 minuta

1. ✅ Pojednostaviti `ggnet2-novnc.service` ako je potrebno
2. ✅ Verifikovati dependencies
3. ✅ Testirati servise
4. ✅ Dokumentovati izmene

**Status:** ✅ Gotovo (trenutna implementacija je bolja)

### Faza 3: Frontend Build Analiza (Prioritet: Srednji)

**Vreme:** 2-3 sata

1. ✅ Ekstraktovati frontend build iz verzije 2289
2. ✅ Analizirati build strukturu i hash-ove
3. ✅ Identifikovati nove integracije (HubSpot, Stripe)
4. ✅ Dokumentovati razlike

**Status:** ✅ Gotovo

**Rezultati:**
- Detaljna analiza: `docs/analysis/frontend_build_analysis_2289.md`
- Sažetak: `docs/analysis/frontend_build_summary.md`
- Ključni nalazi:
  - HubSpot Conversations API integracija
  - Stripe Checkout integracija
  - 19 JS bundle fajlova (~4.7 MB)
  - 15 lazy-loaded chunk-ova
  - i18n proširenja (ar, cn, mn, tr)

### Faza 4: DLL Dekompajliranje (Prioritet: Visok)

**Vreme:** 4-6 sati (uključujući ručno dekompajliranje)

1. ⏳ Dekompajlirati `GgRock.Api.dll` iz verzije 2289 (ručno sa ILSpy GUI)
2. ⏳ Ekstraktovati API endpoint-e i DTO modele
3. ⏳ Uporediti sa verzijom 2200 (ako je dostupna)
4. ⏳ Identifikovati nove endpoint-e
5. ⏳ Identifikovati nove DTO modele
6. ⏳ Dokumentovati razlike

**Status:** ⏳ Čeka ručno dekompajliranje

**Instrukcije:**
- Quick Start: `docs/analysis/DECOMPILATION_QUICK_START.md`
- Detaljne instrukcije: `docs/analysis/ILSPY_DECOMPILATION_INSTRUCTIONS.md`
- Kompletan workflow: `docs/analysis/DECOMPILATION_WORKFLOW.md`
- PowerShell skripta: `scripts/extract_api_info.ps1` (nakon dekompajliranja)

---

## 6. Prioriteti

### Visok Prioritet
1. ✅ Nginx konfiguracija - VNC timeout
2. ✅ Systemd services - verifikacija
3. ⏳ DLL dekompajliranje - API analiza

### Srednji Prioritet
1. ⏳ Nginx konfiguracija - `conf.d` struktura
2. ✅ Frontend build analiza - **GOTOVO**

### Nizak Prioritet
1. ⏳ Automatizovana DLL analiza

---

## 7. Sledeći Koraci

### Odmah
1. Ažurirati Nginx konfiguraciju sa VNC timeout-om
2. Dekompajlirati DLL iz verzije 2289
3. Uporediti API sa verzijom 2200

### Kratkoročno (1-2 nedelje)
1. Analizirati frontend build razlike
2. Dokumentovati sve izmene
3. Integrisati nove funkcionalnosti u ggNET2

### Dugoročno (1-2 meseca)
1. Automatizovati analizu DLL-ova
2. Kreirati CI/CD pipeline za build analizu
3. Integrisati sve nove funkcionalnosti

---

## 8. Reference

- [Nginx Configuration Guide](https://nginx.org/en/docs/)
- [Systemd Service Configuration](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [ILSpy Documentation](https://github.com/icsharpcode/ILSpy)
- [dnSpy Documentation](https://github.com/dnSpy/dnSpy)

---

*Dokument je kreiran na osnovu analize verzije 2289 i trenutne ggNET2 implementacije.*

