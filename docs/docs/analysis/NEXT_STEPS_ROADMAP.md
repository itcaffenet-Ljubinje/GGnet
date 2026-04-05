# Sledeći Koraci - Roadmap za ggNET2

**Datum:** 2025-11-18  
**Status:** 📋 Plan Akcije

---

## 📊 Šta je Urađeno

### ✅ Kompletirano

1. **Frontend Build Analiza** ✅
   - Analizirana verzija 2289
   - Identifikovane nove integracije (HubSpot, Stripe)
   - Dokumentovane i18n proširenja

2. **DLL Dekompajliranje** ✅
   - Dekompajliran `GgRock.Api.dll` iz verzije 2289
   - Ekstraktovano 199 API endpoint-a
   - Identifikovano 26 kontrolera

3. **API Analiza** ✅
   - Detaljna analiza verzije 2289
   - Uporedna analiza verzija 2200 vs 2289
   - Identifikovane sve funkcionalnosti

4. **Prioriteti Implementacije** ✅
   - Kategorizovano 23 funkcionalnosti
   - Vremenski plan (24-32 nedelje)
   - Dependencies graph

---

## 🎯 Sledeći Koraci - Preporuke

### Opcija 1: Početi sa Implementacijom (Preporučeno) ⭐

**Fokus:** P0 - Kritično za MVP

#### Korak 1: Authentication & Authorization (2-3 nedelje)

**Zašto prvo:**
- Bez autentifikacije sistem nije siguran
- Sve ostale funkcionalnosti zavise od autentifikacije
- Osnova za RBAC i audit trail

**Šta uraditi:**
1. Kreirati `app/backend/auth/` modul
2. Implementirati JWT handler
3. Implementirati password manager
4. Implementirati RBAC sistem
5. Kreirati `app/backend/api/users.py`
6. Dodati authentication dependencies u postojeće API-je

**Dokumentacija:**
- `docs/backend/auth_implementation.md` (kreirati)
- API dokumentacija

**Testovi:**
- Unit testovi za JWT
- Integration testovi za authentication flow
- Security testovi

---

#### Korak 2: Bulk Operations - Machines (1 nedelja)

**Zašto drugo:**
- Kritično za UX
- Relativno jednostavno za implementaciju
- Ne zavisi od drugih kompleksnih sistema

**Šta uraditi:**
1. Proširiti `app/backend/api/machines.py`
2. Dodati `POST /api/machines/batch` endpoint
3. Dodati `POST /api/machines/restart` (bulk)
4. Dodati `POST /api/machines/shutdown` (bulk)
5. Dodati `POST /api/machines/wake` (bulk)
6. Dodati `POST /api/machines/turnOn` (bulk)
7. Integrisati WebSocket za progress tracking

**Dokumentacija:**
- API dokumentacija
- Frontend integration guide

**Testovi:**
- Bulk operations testovi
- Progress tracking testovi

---

#### Korak 3: Writebacks Management (1 nedelja)

**Zašto treće:**
- WritebackManager već postoji
- Relativno jednostavno za implementaciju
- Važno za storage management

**Šta uraditi:**
1. Proširiti `app/backend/api/machines.py`
2. Dodati `POST /api/machines/{id}/writebacks/{writebackPath}/keep`
3. Dodati `POST /api/machines/{id}/writebacks/keep`
4. Dodati `DELETE /api/machines/{id}/writebacks/{writebackPath}`
5. Proširiti `app/backend/api/images.py`
6. Dodati `DELETE /api/images/{path}/writebacks`

**Dokumentacija:**
- API dokumentacija

**Testovi:**
- Writeback operations testovi

---

### Opcija 2: Detaljnije Planiranje

**Fokus:** Kreirati detaljne planove implementacije

#### Korak 1: Detaljni Plan za Authentication

**Šta uraditi:**
1. Kreirati `docs/backend/auth_implementation.md`
2. Dizajnirati database schema
3. Dizajnirati API endpoints
4. Dizajnirati security model
5. Kreirati test plan

#### Korak 2: Detaljni Plan za Bulk Operations

**Šta uraditi:**
1. Kreirati `docs/backend/bulk_operations_implementation.md`
2. Dizajnirati batch processing sistem
3. Dizajnirati progress tracking
4. Kreirati test plan

---

### Opcija 3: Frontend Integracija

**Fokus:** Integrisati nove funkcionalnosti u frontend

#### Korak 1: Authentication UI

**Šta uraditi:**
1. Kreirati login page
2. Kreirati user management UI
3. Integrisati JWT u API client
4. Dodati role-based UI restrictions

#### Korak 2: Bulk Operations UI

**Šta uraditi:**
1. Dodati bulk selection u Machines page
2. Dodati bulk actions toolbar
3. Integrisati progress tracking
4. Dodati batch operations dialog

---

## 📋 Preporučeni Redosled

### Faza 1: Osnova (Nedelja 1-4)

**Nedelja 1-2:**
- ✅ Authentication & Authorization
- ✅ Setup test environment

**Nedelja 3:**
- ✅ Bulk Operations - Machines
- ✅ Writebacks Management

**Nedelja 4:**
- ✅ Testing & Bug Fixes
- ✅ Documentation

---

### Faza 2: Storage (Nedelja 5-8)

**Nedelja 5-6:**
- ✅ Array Operations - Drive Management
- ✅ Array Operations - TRIM Management

**Nedelja 7:**
- ✅ Bulk Operations - Images

**Nedelja 8:**
- ✅ Testing & Bug Fixes
- ✅ Documentation

---

### Faza 3: Napredne Funkcionalnosti (Nedelja 9-16)

**Nedelja 9-12:**
- ✅ Scheduling System

**Nedelja 13-14:**
- ✅ Progress Tracking - WebSocket Events
- ✅ Activity Logging & Audit Trail

**Nedelja 15-16:**
- ✅ Server Management API
- ✅ Image Snapshot Management
- ✅ Image Import/Export

---

## 🛠️ Konkretni Sledeći Koraci

### Odmah (Danas)

1. **Odlučiti prioritet:**
   - [ ] Početi sa implementacijom (Opcija 1)
   - [ ] Detaljnije planiranje (Opcija 2)
   - [ ] Frontend integracija (Opcija 3)

2. **Ako Opcija 1 (Preporučeno):**
   - [ ] Kreirati `app/backend/auth/` folder strukturu
   - [ ] Kreirati `docs/backend/auth_implementation.md`
   - [ ] Dizajnirati database schema za users i roles
   - [ ] Početi sa JWT handler implementacijom

3. **Ako Opcija 2:**
   - [ ] Kreirati detaljne planove za sve P0 funkcionalnosti
   - [ ] Dizajnirati database schemas
   - [ ] Dizajnirati API endpoints
   - [ ] Kreirati test planove

4. **Ako Opcija 3:**
   - [ ] Analizirati frontend strukturu
   - [ ] Kreirati plan za authentication UI
   - [ ] Kreirati plan za bulk operations UI

---

## 📝 Checklist za Početak

### Priprema

- [ ] Review `docs/analysis/implementation_priorities_ggnet2.md`
- [ ] Review `docs/analysis/api_analysis_2289.md`
- [ ] Review `docs/analysis/api_comparison_2200_vs_2289.md`
- [ ] Odlučiti prioritet (Opcija 1, 2, ili 3)

### Setup

- [ ] Setup development environment
- [ ] Setup test environment
- [ ] Setup database migrations
- [ ] Review existing codebase

### Dokumentacija

- [ ] Kreirati implementation plan za prvu funkcionalnost
- [ ] Kreirati API documentation template
- [ ] Kreirati test plan template

---

## 🎯 Preporuka

**Preporučujem Opciju 1: Početi sa Implementacijom**

**Razlozi:**
1. **Authentication je kritičan** - Bez njega sistem nije siguran
2. **Bulk Operations su kritični za UX** - Korisnici očekuju bulk operacije
3. **Writebacks Management je jednostavan** - WritebackManager već postoji
4. **Momentum** - Bolje je početi sa implementacijom nego planirati beskonačno

**Prvi Korak:**
1. Kreirati `app/backend/auth/` modul
2. Implementirati osnovni JWT handler
3. Implementirati password hashing
4. Kreirati `app/backend/api/users.py` sa authentication endpoint-ima
5. Dodati authentication dependencies u postojeće API-je

---

## 📚 Reference Dokumenti

### Analiza
- `docs/analysis/api_analysis_2289.md` - API analiza verzije 2289
- `docs/analysis/api_comparison_2200_vs_2289.md` - Uporedna analiza
- `docs/analysis/implementation_priorities_ggnet2.md` - Prioriteti implementacije
- `docs/analysis/frontend_build_analysis_2289.md` - Frontend analiza

### Integracija
- `docs/analysis/ggnet2_integration_recommendations_2289.md` - Preporuke za integraciju
- `docs/analysis/INTEGRATION_2289_COMPLETE_SUMMARY.md` - Kompletan sažetak

### Planovi
- `docs/analysis/ggrock_api_mapping.md` - API mapping
- `docs/analysis/project_diagnostic_report.md` - Dijagnostički izveštaj

---

## ❓ Pitanja za Odluku

1. **Koji prioritet želiš da implementiramo prvo?**
   - [ ] Authentication & Authorization (P0)
   - [ ] Bulk Operations - Machines (P0)
   - [ ] Writebacks Management (P0)
   - [ ] Array Operations (P0)
   - [ ] Nešto drugo?

2. **Da li želiš da kreiram detaljne planove pre implementacije?**
   - [ ] Da, kreiraj detaljne planove
   - [ ] Ne, kreni direktno sa implementacijom

3. **Da li želiš da fokusiramo na backend ili frontend?**
   - [ ] Backend (API implementacija)
   - [ ] Frontend (UI integracija)
   - [ ] Oba paralelno

---

*Roadmap kreiran na osnovu analize i prioriteta implementacije.*

