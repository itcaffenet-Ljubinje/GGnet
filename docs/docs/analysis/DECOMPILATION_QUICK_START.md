# DLL Dekompajliranje - Quick Start Guide

**Cilj:** Dekompajlirati `GgRock.Api.dll` iz verzije 2289 za 10 minuta

---

## ⚡ Brzi Start (3 Koraka)

### 1. Download ILSpy (2 min)

1. Idite na: https://github.com/icsharpcode/ILSpy/releases
2. Download `ILSpy_binaries_8.x.x.zip`
3. Extract bilo gde (npr. `C:\Tools\ILSpy\`)
4. Pokrenuti `ILSpy.exe`

### 2. Dekompajlirati DLL (3 min)

1. U ILSpy: **File → Open**
2. Navigate to:
   ```
   C:\Users\SERVER-PC\Desktop\ggnet-hack\ggrock_0.1.2289.2303-1_amd64\data\opt\ggrock\app\GgRock.Api.dll
   ```
3. Desni klik na **GgRock.Api** → **Save Code...**
4. Output:
   ```
   C:\Users\SERVER-PC\PROJECTS\ggNET2\dll_analysis\GgRock.Api\decompiled
   ```
5. Kliknite **OK** i sačekajte (2-5 minuta)

### 3. Ekstraktovati Informacije (2 min)

```powershell
cd C:\Users\SERVER-PC\PROJECTS\ggNET2
powershell -ExecutionPolicy Bypass -File scripts/extract_api_info.ps1
```

**Gotovo!** Rezultati su u `dll_analysis/GgRock.Api/`

---

## 📊 Rezultati

Nakon izvršavanja, imaćete:

- ✅ `api_endpoints.txt` - Svi API endpoint-i
- ✅ `api_controllers.txt` - Svi kontroleri  
- ✅ `dto_models.txt` - Svi DTO modeli
- ✅ `analysis_summary.txt` - Sažetak

---

## 🔍 Šta Dalje?

1. **Pregledati rezultate:**
   - Otvoriti `api_endpoints.txt`
   - Otvoriti `dto_models.txt`

2. **Uporediti sa verzijom 2200** (ako je dostupna)

3. **Dokumentovati nalaze:**
   - Kreirati `docs/analysis/api_comparison_2200_vs_2289.md`

---

## 🆘 Problemi?

Pogledajte:
- `docs/analysis/ILSPY_DECOMPILATION_INSTRUCTIONS.md` - Detaljne instrukcije
- `docs/analysis/DECOMPILATION_WORKFLOW.md` - Kompletan workflow

---

*Quick start guide za brzo dekompajliranje.*

