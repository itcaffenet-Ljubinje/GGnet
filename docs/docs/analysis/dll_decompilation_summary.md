# DLL Dekompajliranje - Sažetak i Preporuke

**Datum:** 2025-01-XX  
**Verzija:** 2289.2303

---

## 📊 Status

### Automatska Dekompajliranje

**Status:** ⚠️ Delimično uspešno

**Rezultati:**
- ✅ **File metadata:** Ekstraktovana
  - Veličina: 4,463,128 bytes (~4.26 MB)
  - Verzija: 0.1.2289.2303
  - Runtime: .NET Framework v4.0.30319
- ⚠️ **Assembly metadata:** Delimično (neki tipovi nisu dostupni)
- ❌ **ILSpy command-line:** Nije dostupan (zahteva .NET SDK konfiguraciju)

---

## 🎯 Preporučeni Pristup

### Opcija 1: ILSpy GUI (Najlakše) ⭐ Preporučeno

**Koraci:**
1. Download ILSpy: https://github.com/icsharpcode/ILSpy/releases
2. Extract `ILSpy.exe` (ne zahteva instalaciju)
3. Pokrenuti `ILSpy.exe`
4. File → Open → Select `GgRock.Api.dll`
5. File → Save Code → Save all files
6. Select output directory (npr. `dll_analysis/GgRock.Api/decompiled`)

**Vreme:** 5-10 minuta  
**Težina:** Lako

### Opcija 2: dnSpy (Alternativa)

**Koraci:**
1. Download dnSpy: https://github.com/dnSpy/dnSpy/releases
2. Extract i pokrenuti `dnSpy.exe`
3. File → Open → Select `GgRock.Api.dll`
4. File → Export to Project → Select output directory

**Vreme:** 5-10 minuta  
**Težina:** Lako

### Opcija 3: dotPeek (JetBrains)

**Koraci:**
1. Download dotPeek: https://www.jetbrains.com/decompiler/
2. Install i pokrenuti
3. File → Open → Select `GgRock.Api.dll`
4. File → Export to Project → Select output directory

**Vreme:** 10-15 minuta (uključujući instalaciju)  
**Težina:** Srednje

---

## 📍 Lokacija DLL Fajla

**Verzija 2289:**
```
C:\Users\SERVER-PC\Desktop\ggnet-hack\ggrock_0.1.2289.2303-1_amd64\data\opt\ggrock\app\GgRock.Api.dll
```

**Veličina:** 4.26 MB  
**Verzija:** 0.1.2289.2303  
**Runtime:** .NET Framework v4.0.30319

---

## 🔍 Šta Tražiti Nakon Dekompajliranja

### 1. API Kontroleri

**Lokacija:** `Controllers/` folder

**Pretražiti za:**
- `[Route("api/...")]` atribut
- `[HttpGet]`, `[HttpPost]`, `[HttpPut]`, `[HttpDelete]` atributi
- Klase koje nasleđuju `Controller` ili `ControllerBase`

**Primer strukture:**
```
Controllers/
├── MachinesController.cs
├── ImagesController.cs
├── VMsController.cs
├── StorageController.cs
└── ...
```

### 2. DTO Modeli

**Lokacija:** `Models/` ili `DTOs/` folder

**Pretražiti za:**
- Klase sa `Dto`, `Request`, `Response`, `Model` u imenu
- `public class` ili `public record` definicije

**Primer strukture:**
```
Models/
├── DTOs/
│   ├── MachineDto.cs
│   ├── ImageDto.cs
│   ├── MachineCreateRequest.cs
│   └── ...
└── Entities/
    ├── Machine.cs
    └── ...
```

### 3. SignalR Hub-ovi

**Lokacija:** `Hubs/` ili `SignalR/` folder

**Pretražiti za:**
- Klase koje nasleđuju `Hub`
- Metode sa `HubMethodName` atributom

### 4. Servisi i Manageri

**Lokacija:** `Services/` ili `Managers/` folder

**Pretražiti za:**
- Interface definicije (`IMachineService`, `IStorageManager`)
- Implementacije servisa

---

## 📊 Analiza Rezultata

### Ekstrakcija API Endpoint-a

**PowerShell:**
```powershell
# Ekstraktovati sve API endpoint-e
Select-String -Path "decompiled\**\*.cs" -Pattern "\[Route|\[HttpGet|\[HttpPost|\[HttpPut|\[HttpDelete" | 
    Select-Object Filename, LineNumber, Line | 
    Export-Csv -Path "api_endpoints.csv" -NoTypeInformation

# Ekstraktovati kontrolere
Select-String -Path "decompiled\**\*.cs" -Pattern "class.*Controller" | 
    Select-Object Filename, LineNumber, Line | 
    Export-Csv -Path "api_controllers.csv" -NoTypeInformation
```

**Bash (Linux/WSL):**
```bash
# Ekstraktovati sve API endpoint-e
grep -r "\[Route\|\[HttpGet\|\[HttpPost\|\[HttpPut\|\[HttpDelete" decompiled/ > api_endpoints.txt

# Ekstraktovati kontrolere
grep -r "class.*Controller" decompiled/ > api_controllers.txt
```

### Ekstrakcija DTO Modela

**PowerShell:**
```powershell
# Ekstraktovati DTO modele
Select-String -Path "decompiled\**\*.cs" -Pattern "class.*Dto|class.*Request|class.*Response" | 
    Select-Object Filename, LineNumber, Line | 
    Export-Csv -Path "dto_models.csv" -NoTypeInformation
```

**Bash:**
```bash
# Ekstraktovati DTO modele
grep -r "class.*Dto\|class.*Request\|class.*Response" decompiled/ > dto_models.txt
```

---

## 🔄 Uporedna Analiza (2200 vs 2289)

### Koraci

1. **Dekompajlirati obe verzije:**
   ```
   decompiled_2200/  (iz verzije 2200)
   decompiled_2289/  (iz verzije 2289)
   ```

2. **Ekstraktovati API endpoint-e iz obe verzije:**
   ```powershell
   # Verzija 2200
   Select-String -Path "decompiled_2200\**\*.cs" -Pattern "\[Route" | Out-File api_2200.txt
   
   # Verzija 2289
   Select-String -Path "decompiled_2289\**\*.cs" -Pattern "\[Route" | Out-File api_2289.txt
   ```

3. **Uporediti:**
   ```powershell
   $api2200 = Get-Content api_2200.txt
   $api2289 = Get-Content api_2289.txt
   
   # Novi u 2289
   Compare-Object $api2200 $api2289 | Where-Object {$_.SideIndicator -eq "=>"} | Select-Object InputObject
   
   # Obrisani u 2289
   Compare-Object $api2200 $api2289 | Where-Object {$_.SideIndicator -eq "<="} | Select-Object InputObject
   ```

4. **Dokumentovati razlike:**
   - Kreirati `docs/analysis/api_comparison_2200_vs_2289.md`
   - Lista novih endpoint-a
   - Lista izmenjenih endpoint-a
   - Lista obrisanih endpoint-a

---

## 📝 Template za Dokumentaciju

Nakon dekompajliranja i analize, kreirati:

### `docs/analysis/api_comparison_2200_vs_2289.md`

```markdown
# API Uporedna Analiza - Verzija 2200 vs 2289

## Novi Endpoint-i u 2289

### Machines API
- `GET /api/machines/{id}/status` - Status machine-a
- `POST /api/machines/bulk` - Bulk operacije

### Images API
- `POST /api/images/{id}/export` - Export image-a

## Izmenjeni Endpoint-i

### Machines API
- `PUT /api/machines/{id}` - Dodati `force` parametar

## Obrisani Endpoint-i

- `GET /api/machines/{id}/legacy` - Uklonjen

## Novi DTO Modeli

- `MachineStatusDto`
- `ImageExportRequest`
- `BulkOperationRequest`
```

---

## ✅ Sledeći Koraci

### Odmah (1-2 sata)

1. **Dekompajlirati DLL iz verzije 2289**
   - Koristiti ILSpy GUI
   - Save to: `dll_analysis/GgRock.Api/decompiled`

2. **Ekstraktovati API endpoint-e**
   - Koristiti PowerShell skripte iznad
   - Kreirati `api_endpoints.txt`

3. **Ekstraktovati DTO modele**
   - Kreirati `dto_models.txt`

### Kratkoročno (1-2 dana)

1. **Uporediti sa verzijom 2200** (ako je dostupna)
2. **Dokumentovati sve razlike**
3. **Identifikovati nove funkcionalnosti**

### Dugoročno (1-2 nedelje)

1. **Integrisati nove funkcionalnosti u ggNET2**
2. **Ažurirati API dokumentaciju**
3. **Kreirati migration guide**

---

## 🔗 Reference

- **ILSpy:** https://github.com/icsharpcode/ILSpy/releases
- **dnSpy:** https://github.com/dnSpy/dnSpy/releases
- **dotPeek:** https://www.jetbrains.com/decompiler/
- **Ručni vodič:** `docs/analysis/dll_decompilation_manual_guide.md`
- **Status:** `docs/analysis/dll_analysis_status.md`

---

*Sažetak je kreiran na osnovu pokušaja automatske dekompajliranja i preporuka za ručni pristup.*

