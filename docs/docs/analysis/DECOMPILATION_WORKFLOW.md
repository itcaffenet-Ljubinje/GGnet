# DLL Dekompajliranje - Kompletan Workflow

**Datum:** 2025-01-XX  
**Cilj:** Dekompajlirati i analizirati `GgRock.Api.dll` iz verzije 2289

---

## 📋 Pregled Workflow-a

1. **Download ILSpy GUI**
2. **Dekompajlirati DLL**
3. **Ekstraktovati API informacije**
4. **Analizirati rezultate**
5. **Dokumentovati nalaze**

---

## 🔧 Korak 1: Priprema

### Download ILSpy

1. Idite na: https://github.com/icsharpcode/ILSpy/releases
2. Download najnoviju verziju (npr. `ILSpy_binaries_8.x.x.zip`)
3. Extract na `C:\Tools\ILSpy\` (ili bilo gde)

### Verifikacija

1. Pokrenuti `ILSpy.exe`
2. Ako se otvori prozor, ILSpy je spreman

**Vreme:** 2-3 minuta

---

## 🔓 Korak 2: Dekompajliranje

### Otvaranje DLL-a

1. U ILSpy: **File → Open**
2. Navigate to:
   ```
   C:\Users\SERVER-PC\Desktop\ggnet-hack\ggrock_0.1.2289.2303-1_amd64\data\opt\ggrock\app\GgRock.Api.dll
   ```
3. Kliknite **Open**

### Export Code

1. Desni klik na **GgRock.Api** (root node)
2. **Save Code...**
3. Output directory:
   ```
   C:\Users\SERVER-PC\PROJECTS\ggNET2\dll_analysis\GgRock.Api\decompiled
   ```
4. **Language:** C#
5. **File format:** Save as project
6. Kliknite **OK**

**Vreme:** 2-5 minuta

### Verifikacija

Proverite da li postoji:
```
dll_analysis/GgRock.Api/decompiled/
├── Controllers/
├── Models/
└── ...
```

---

## 📊 Korak 3: Ekstrakcija Informacija

### Pokretanje PowerShell Skripte

```powershell
cd C:\Users\SERVER-PC\PROJECTS\ggNET2
powershell -ExecutionPolicy Bypass -File scripts/extract_api_info.ps1
```

**Ili sa custom putanjom:**
```powershell
powershell -ExecutionPolicy Bypass -File scripts/extract_api_info.ps1 -DecompiledDir ".\dll_analysis\GgRock.Api\decompiled"
```

### Rezultati

Skripta će kreirati:
- `api_endpoints.txt` / `.csv` - Svi API endpoint-i
- `api_controllers.txt` / `.csv` - Svi kontroleri
- `dto_models.txt` / `.csv` - Svi DTO modeli
- `signalr_hubs.txt` / `.csv` - SignalR hub-ovi (ako postoje)
- `analysis_summary.txt` - Sažetak analize

**Vreme:** 1-2 minuta

---

## 🔍 Korak 4: Analiza Rezultata

### Pregled API Endpoint-a

1. Otvoriti `dll_analysis/GgRock.Api/api_endpoints.txt`
2. Identifikovati:
   - Route pattern-e
   - HTTP metode
   - Controller metode

**Primer:**
```
File: Controllers/MachinesController.cs
  Line 25: [Route("api/[controller]")]
  Line 30: [HttpGet]
  Line 35: public IActionResult GetMachines() { ... }
```

### Pregled DTO Modela

1. Otvoriti `dll_analysis/GgRock.Api/dto_models.txt`
2. Identifikovati:
   - DTO strukture
   - Properties
   - Validacije

### Pregled Kontrolera

1. Otvoriti `dll_analysis/GgRock.Api/api_controllers.txt`
2. Identifikovati:
   - Controller strukture
   - Dependencies
   - Base classes

---

## 📝 Korak 5: Dokumentacija

### Kreirati Dokumentaciju

Nakon analize, kreirati:

1. **`docs/analysis/api_endpoints_2289.md`**
   - Lista svih API endpoint-a
   - Route pattern-i
   - HTTP metode
   - Request/Response tipovi

2. **`docs/analysis/dto_models_2289.md`**
   - Lista svih DTO modela
   - Properties
   - Validacije

3. **`docs/analysis/api_comparison_2200_vs_2289.md`** (ako je verzija 2200 dostupna)
   - Novi endpoint-i
   - Izmenjeni endpoint-i
   - Obrisani endpoint-i

### Template za Dokumentaciju

Koristiti template iz `docs/analysis/dll_decompilation_summary.md`

---

## ✅ Checklist

### Priprema
- [ ] ILSpy downloaded
- [ ] ILSpy extracted i pokrenut
- [ ] DLL lokacija verifikovana

### Dekompajliranje
- [ ] DLL otvoren u ILSpy
- [ ] Code exported u `decompiled/` folder
- [ ] Struktura direktorijuma verifikovana

### Analiza
- [ ] PowerShell skripta pokrenuta
- [ ] API endpoint-i ekstraktovani
- [ ] DTO modeli ekstraktovani
- [ ] Kontroleri ekstraktovani

### Dokumentacija
- [ ] API endpoint-i dokumentovani
- [ ] DTO modeli dokumentovani
- [ ] Uporedna analiza kreirana (ako je moguće)

---

## 🎯 Očekivani Rezultati

### API Endpoint-i

Očekivano:
- Machines API endpoint-i
- Images API endpoint-i
- VMs API endpoint-i
- Storage API endpoint-i
- Settings API endpoint-i

### DTO Modeli

Očekivano:
- MachineDto, MachineCreateRequest, MachineUpdateRequest
- ImageDto, ImageCreateRequest
- VMDto, VMCreateRequest
- StorageDto, ArrayDto
- SettingsDto

### SignalR Hub-ovi

Očekivano:
- Real-time update hub-ovi
- Progress tracking hub-ovi

---

## 🔗 Reference

- **ILSpy Instrukcije:** `docs/analysis/ILSPY_DECOMPILATION_INSTRUCTIONS.md`
- **Ručni Vodič:** `docs/analysis/dll_decompilation_manual_guide.md`
- **Sažetak:** `docs/analysis/dll_decompilation_summary.md`
- **Status:** `docs/analysis/dll_analysis_status.md`

---

*Workflow je kreiran za kompletan proces dekompajliranja i analize.*

