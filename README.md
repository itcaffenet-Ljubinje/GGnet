# GGnet Diskless Server

Potpuno funkcionalan, produkcijski spreman diskless server inspirisan GGrock/CCBoot, fokusiran na igre i laboratore. Omogućava Windows 11 UEFI+SecureBoot klijentima da se bootuju iz VHD/VHDX imidža sa mogućnošću dodavanja sekundarnog virtuelnog diska (D:\) za igre.

## 🎯 Funkcionalnosti

- **Backend (FastAPI)**: REST API za upravljanje imidžima, mašinama, sesijama i iSCSI targetima
- **Frontend (React + Tailwind)**: Moderni web interface za administraciju
- **Diskless Infrastructure**: Skripte za UEFI boot, iSCSI i image konverziju
- **Sigurnost**: JWT auth, RBAC, audit logging
- **Production Ready**: Systemd servisi, Docker podrška, deployment guide

## 🚀 Brza instalacija

### Development (Docker)
```bash
git clone <repo-url>
cd GGnet
docker-compose up -d
```

### Production (Ubuntu/Debian)
```bash
# Instalacija zavisnosti
sudo apt update
sudo apt install -y python3.11 python3-pip nodejs npm postgresql targetcli-fb qemu-utils

# Backend setup
cd backend
pip install -r requirements.txt
alembic upgrade head

# Frontend build
cd ../frontend
npm install
npm run build

# Systemd service
sudo cp systemd/diskless-backend.service /etc/systemd/system/
sudo systemctl enable diskless-backend
sudo systemctl start diskless-backend
```

## 📋 MVP Prioriteti

1. **P0 (Kritično)**: Backend auth + basic image upload/list
2. **P1 (Visok)**: iSCSI target kreiranje + frontend login/dashboard
3. **P2 (Srednji)**: Image konverzija + machine management
4. **P3 (Nizak)**: Advanced features + monitoring

## 🏗️ Arhitektura

```
GGnet/
├── backend/           # FastAPI aplikacija
├── frontend/          # React aplikacija
├── scripts/           # Diskless infrastructure skripte
├── docker/            # Docker konfiguracija
├── systemd/           # Systemd unit fajlovi
├── docs/              # Dokumentacija
└── tests/             # Testovi
```

## 🔧 API Endpoints

### Auth
- `POST /auth/login` - Login sa username/password
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout

### Images
- `POST /images/upload` - Upload VHD/VHDX fajla
- `GET /images` - Lista dostupnih imidža
- `POST /images/{id}/convert` - Konvertuj image format
- `DELETE /images/{id}` - Obriši image

### Machines
- `POST /machines` - Kreiraj novu mašinu
- `GET /machines` - Lista mašina
- `PUT /machines/{id}` - Ažuriraj mašinu
- `DELETE /machines/{id}` - Obriši mašinu

### Targets
- `POST /targets` - Kreiraj iSCSI target
- `GET /targets` - Lista targeta
- `DELETE /targets/{id}` - Obriši target

### Sessions
- `POST /sessions/start` - Pokreni diskless sesiju
- `GET /sessions/{id}/status` - Status sesije
- `POST /sessions/{id}/stop` - Zaustavi sesiju

## 🔒 Sigurnost

- JWT access + refresh token flow
- Bcrypt password hashing
- Role-based access control (admin/operator)
- Rate limiting za upload
- Audit logging
- Server-side checksum validacija

## ⚖️ Pravna napomena

**VAŽNO**: Distribucija Windows VHD/VHDX imidža može biti ograničena Microsoft licencnim uslovima. Korisnici su odgovorni za:
- Posedovanje validnih Windows licenci
- Poštovanje Microsoft Volume Licensing uslova
- Korišćenje samo legalno nabavljenih imidža

## 🧪 Testiranje

```bash
# Backend testovi
cd backend
pytest

# Frontend testovi
cd frontend
npm test

# Integration testovi
docker-compose -f docker-compose.test.yml up
```

## 📚 Dokumentacija

- [Installation Guide](docs/installation.md)
- [API Documentation](docs/api.md)
- [UEFI Boot Setup](docs/uefi-boot.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Doprinos

1. Fork repository
2. Kreiraj feature branch
3. Commit izmene
4. Push na branch
5. Otvori Pull Request

## 📄 Licenca

MIT License - pogledaj [LICENSE](LICENSE) fajl za detalje.
