# ILSpy GUI - Detaljne Instrukcije za Dekompajliranje

**Datum:** 2025-01-XX  
**Cilj:** Dekompajlirati `GgRock.Api.dll` iz verzije 2289

---

## 📥 Korak 1: Download i Instalacija ILSpy

### Download

1. Idite na: https://github.com/icsharpcode/ILSpy/releases
2. Download najnoviju verziju (npr. `ILSpy_binaries_8.x.x.zip`)
3. Extract ZIP fajl na lokaciju (npr. `C:\Tools\ILSpy\`)

**Napomena:** ILSpy ne zahteva instalaciju - samo extract i pokretanje.

### Verifikacija

1. Navigate to extracted folder
2. Pokrenuti `ILSpy.exe`
3. Ako se otvori prozor, ILSpy je spreman za korišćenje

---

## 🔓 Korak 2: Dekompajliranje DLL-a

### Otvaranje DLL-a

1. U ILSpy, kliknite **File → Open**
2. Navigate to:
   ```
   C:\Users\SERVER-PC\Desktop\ggnet-hack\ggrock_0.1.2289.2303-1_amd64\data\opt\ggrock\app\GgRock.Api.dll
   ```
3. Kliknite **Open**

### Pregled Strukture

Nakon otvaranja, videćete strukturu assembly-ja u tree view-u:
- Namespaces
- Classes
- Interfaces
- Enums
- etc.

### Export Decompiled Code

1. U tree view-u, desni klik na **GgRock.Api** (root node)
2. Select **Save Code...**
3. U dijalogu:
   - **Output directory:** `C:\Users\SERVER-PC\PROJECTS\ggNET2\dll_analysis\GgRock.Api\decompiled`
   - **Language:** C# (default)
   - **File format:** Save as project (recommended)
4. Kliknite **OK**

**Vreme:** 2-5 minuta (zavisi od veličine DLL-a)

---

## 📂 Korak 3: Verifikacija Rezultata

### Proveriti Output Direktorijum

Nakon export-a, proverite da li postoji:
```
dll_analysis/GgRock.Api/decompiled/
├── Controllers/
├── Models/
├── Services/
├── Hubs/
└── ...
```

### Proveriti Ključne Fajlove

Proverite da li postoje:
- `Controllers/` folder sa API kontrolerima
- `Models/` folder sa DTO modelima
- `Services/` folder sa servisima

---

## 🔍 Korak 4: Analiza Rezultata

### Pronaći API Kontrolere

1. Otvoriti `decompiled/Controllers/` folder
2. Pronaći fajlove sa `Controller.cs` u imenu
3. Otvoriti svaki controller i pregledati metode

**Primer strukture:**
```
Controllers/
├── MachinesController.cs
├── ImagesController.cs
├── VMsController.cs
├── StorageController.cs
└── ...
```

### Pronaći DTO Modele

1. Otvoriti `decompiled/Models/` ili `decompiled/DTOs/` folder
2. Pronaći fajlove sa `Dto.cs`, `Request.cs`, `Response.cs` u imenu

**Primer strukture:**
```
Models/
├── DTOs/
│   ├── MachineDto.cs
│   ├── ImageDto.cs
│   └── ...
└── Entities/
    └── ...
```

---

## 📊 Korak 5: Ekstrakcija Informacija

### Koristiti PowerShell Skripte

Nakon dekompajliranja, pokrenuti:

```powershell
cd C:\Users\SERVER-PC\PROJECTS\ggNET2

# Ekstraktovati API endpoint-e
Select-String -Path "dll_analysis\GgRock.Api\decompiled\**\*.cs" -Pattern "\[Route|\[HttpGet|\[HttpPost|\[HttpPut|\[HttpDelete" | 
    Select-Object Filename, LineNumber, Line | 
    Export-Csv -Path "dll_analysis\GgRock.Api\api_endpoints.csv" -NoTypeInformation

# Ekstraktovati kontrolere
Select-String -Path "dll_analysis\GgRock.Api\decompiled\**\*.cs" -Pattern "class.*Controller" | 
    Select-Object Filename, LineNumber, Line | 
    Export-Csv -Path "dll_analysis\GgRock.Api\api_controllers.csv" -NoTypeInformation

# Ekstraktovati DTO modele
Select-String -Path "dll_analysis\GgRock.Api\decompiled\**\*.cs" -Pattern "class.*Dto|class.*Request|class.*Response" | 
    Select-Object Filename, LineNumber, Line | 
    Export-Csv -Path "dll_analysis\GgRock.Api\dto_models.csv" -NoTypeInformation
```

---

## ✅ Checklist

- [ ] ILSpy downloaded i extracted
- [ ] ILSpy pokrenut uspešno
- [ ] `GgRock.Api.dll` otvoren u ILSpy
- [ ] Code exported u `dll_analysis/GgRock.Api/decompiled/`
- [ ] Verifikovana struktura direktorijuma
- [ ] Pronađeni API kontroleri
- [ ] Pronađeni DTO modeli
- [ ] PowerShell skripte pokrenute za ekstrakciju
- [ ] CSV fajlovi kreirani

---

## 🆘 Troubleshooting

### Problem: ILSpy ne može da otvori DLL

**Rešenje:**
- Proverite da li je DLL fajl validan
- Pokušajte sa dnSpy umesto ILSpy
- Proverite da li imate dovoljno memorije

### Problem: Export ne radi

**Rešenje:**
- Proverite da li imate dovoljno prostora na disku
- Proverite permissions za output direktorijum
- Pokušajte sa manjim output direktorijumom

### Problem: Neki tipovi nedostaju

**Rešenje:**
- Ovo je normalno - neki tipovi zavise od drugih assembly-ja
- Fokusirajte se na tipove koje možete videti
- Koristite "Go to Definition" za navigaciju

---

## 📝 Sledeći Koraci Nakon Dekompajliranja

1. **Analizirati API kontrolere**
   - Dokumentovati sve endpoint-e
   - Identifikovati HTTP metode
   - Identifikovati route pattern-e

2. **Analizirati DTO modele**
   - Dokumentovati sve DTO modele
   - Identifikovati properties
   - Identifikovati validacije

3. **Uporediti sa verzijom 2200** (ako je dostupna)
   - Identifikovati nove endpoint-e
   - Identifikovati izmenjene endpoint-e
   - Identifikovati obrisane endpoint-e

4. **Kreirati dokumentaciju**
   - `docs/analysis/api_comparison_2200_vs_2289.md`
   - `docs/analysis/new_endpoints_2289.md`
   - `docs/analysis/new_dto_models_2289.md`

---

## 🔗 Reference

- **ILSpy GitHub:** https://github.com/icsharpcode/ILSpy
- **ILSpy Releases:** https://github.com/icsharpcode/ILSpy/releases
- **ILSpy Documentation:** https://github.com/icsharpcode/ILSpy/wiki

---

*Instrukcije su kreirane za ručno dekompajliranje koristeći ILSpy GUI.*

