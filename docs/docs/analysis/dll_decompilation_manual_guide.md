# DLL Dekompajliranje - Ručni Vodič

**Datum:** 2025-01-XX  
**Verzija:** 2289.2303

---

## 📋 Pregled

Pošto automatska dekompajliranje nije moguće bez pravilno konfigurisanog .NET SDK-a, ovaj vodič objašnjava ručne metode za dekompajliranje `GgRock.Api.dll`.

---

## 🛠️ Metode Dekompajliranja

### Metod 1: ILSpy GUI (Preporučeno)

**Koraci:**
1. Download ILSpy: https://github.com/icsharpcode/ILSpy/releases
2. Extract i pokrenuti `ILSpy.exe`
3. File → Open → Select `GgRock.Api.dll`
4. File → Save Code → Save all files
5. Select output directory

**Prednosti:**
- Ne zahteva instalaciju
- GUI interfejs
- Brzo i jednostavno

### Metod 2: dnSpy (Alternativa)

**Koraci:**
1. Download dnSpy: https://github.com/dnSpy/dnSpy/releases
2. Extract i pokrenuti `dnSpy.exe`
3. File → Open → Select `GgRock.Api.dll`
4. File → Export to Project → Select output directory

**Prednosti:**
- Debugging support
- Edit and recompile
- GUI interfejs

### Metod 3: dotPeek (JetBrains)

**Koraci:**
1. Download dotPeek: https://www.jetbrains.com/decompiler/
2. Install i pokrenuti
3. File → Open → Select `GgRock.Api.dll`
4. File → Export to Project → Select output directory

**Prednosti:**
- Professional tool
- Good code formatting
- Integration sa JetBrains IDE-ovima

### Metod 4: Online Decompiler (Za brzu proveru)

**Online alati:**
- https://www.jetbrains.com/decompiler/ (dotPeek online)
- https://www.decompiler.com/

**Napomena:** Ne preporučuje se za velike DLL-ove zbog sigurnosnih razloga.

---

## 📍 Lokacija DLL Fajla

**Verzija 2289:**
```
C:\Users\SERVER-PC\Desktop\ggnet-hack\ggrock_0.1.2289.2303-1_amd64\data\opt\ggrock\app\GgRock.Api.dll
```

**Verzija 2200 (ako postoji):**
```
C:\Users\SERVER-PC\Desktop\ggnet-hack\ggrock_0.1.2200.2213-1_amd64\data\opt\ggrock\app\GgRock.Api.dll
```

---

## 🔍 Šta Tražiti Nakon Dekompajliranja

### 1. API Kontroleri

Pretražiti za:
- `[Route]` atribut
- `[HttpGet]`, `[HttpPost]`, `[HttpPut]`, `[HttpDelete]` atributi
- Klase koje nasleđuju `Controller` ili `ControllerBase`
- Metode sa HTTP atributima

**Primer:**
```csharp
[Route("api/[controller]")]
[ApiController]
public class MachinesController : ControllerBase
{
    [HttpGet]
    public IActionResult GetMachines() { ... }
}
```

### 2. DTO Modeli

Pretražiti za:
- Klase sa `Dto`, `Request`, `Response`, `Model` u imenu
- `public class` ili `public record` definicije
- Properties sa `[JsonProperty]` ili `[DataMember]` atributima

**Primer:**
```csharp
public class MachineDto
{
    public int Id { get; set; }
    public string Name { get; set; }
}
```

### 3. Servisi i Manageri

Pretražiti za:
- Interface definicije (`IMachineService`, `IStorageManager`, itd.)
- Implementacije servisa
- Dependency injection setup

### 4. SignalR Hub-ovi

Pretražiti za:
- Klase koje nasleđuju `Hub`
- Metode sa `HubMethodName` atributom

---

## 📊 Analiza Rezultata

### Struktura Direktorijuma

Nakon dekompajliranja, očekivana struktura:
```
decompiled/
├── Controllers/
│   ├── MachinesController.cs
│   ├── ImagesController.cs
│   ├── VMsController.cs
│   └── ...
├── Models/
│   ├── DTOs/
│   │   ├── MachineDto.cs
│   │   ├── ImageDto.cs
│   │   └── ...
│   └── Entities/
│       ├── Machine.cs
│       └── ...
├── Services/
│   ├── IMachineService.cs
│   ├── MachineService.cs
│   └── ...
└── ...
```

### Generisanje Izveštaja

Nakon dekompajliranja, koristiti grep/ripgrep za ekstrakciju:

**API Endpoint-i:**
```bash
# Windows PowerShell
Select-String -Path "decompiled\**\*.cs" -Pattern "\[Route|\[HttpGet|\[HttpPost" | Out-File api_endpoints.txt

# Linux/Mac
grep -r "\[Route\|\[HttpGet\|\[HttpPost" decompiled/ > api_endpoints.txt
```

**DTO Modeli:**
```bash
# Windows PowerShell
Select-String -Path "decompiled\**\*.cs" -Pattern "class.*Dto|class.*Request|class.*Response" | Out-File dto_models.txt

# Linux/Mac
grep -r "class.*Dto\|class.*Request\|class.*Response" decompiled/ > dto_models.txt
```

---

## 🔄 Uporedna Analiza

### Koraci za Uporednu Analizu

1. **Dekompajlirati obe verzije:**
   - Verzija 2200 → `decompiled_2200/`
   - Verzija 2289 → `decompiled_2289/`

2. **Ekstraktovati API endpoint-e:**
   ```bash
   # Verzija 2200
   Select-String -Path "decompiled_2200\**\*.cs" -Pattern "\[Route" | Out-File api_2200.txt
   
   # Verzija 2289
   Select-String -Path "decompiled_2289\**\*.cs" -Pattern "\[Route" | Out-File api_2289.txt
   ```

3. **Uporediti:**
   ```bash
   Compare-Object (Get-Content api_2200.txt) (Get-Content api_2289.txt)
   ```

4. **Identifikovati razlike:**
   - Novi endpoint-i u 2289
   - Izmenjeni endpoint-i
   - Obrisani endpoint-i

---

## 📝 Template za Dokumentaciju

Nakon dekompajliranja, kreirati dokument sa:

```markdown
# API Uporedna Analiza - Verzija 2200 vs 2289

## Novi Endpoint-i u 2289

### Machines API
- `GET /api/machines/{id}/status` - Novi endpoint za status

### Images API
- `POST /api/images/{id}/export` - Novi endpoint za export

## Izmenjeni Endpoint-i

### Machines API
- `PUT /api/machines/{id}` - Dodati novi parametar `force`

## Obrisani Endpoint-i

- `GET /api/machines/{id}/legacy` - Uklonjen u 2289

## Novi DTO Modeli

- `MachineStatusDto` - Novi DTO za status
- `ImageExportRequest` - Novi request model
```

---

## 🎯 Preporuke

### Za Brzu Analizu

1. Koristiti ILSpy GUI za dekompajliranje
2. Pretražiti za `[Route]` atribut
3. Fokusirati se na Controllers folder
4. Dokumentovati samo nove/izmenjene endpoint-e

### Za Detaljnu Analizu

1. Dekompajlirati obe verzije
2. Uporediti strukturu direktorijuma
3. Uporediti sve API kontrolere
4. Uporediti sve DTO modele
5. Dokumentovati sve razlike

### Za Produkciju

1. Koristiti ILSpy command-line (kada bude dostupan)
2. Integrisati u CI/CD pipeline
3. Generisati automatske izveštaje
4. Ažurirati dokumentaciju

---

## 🔗 Reference

- [ILSpy Documentation](https://github.com/icsharpcode/ILSpy)
- [dnSpy Documentation](https://github.com/dnSpy/dnSpy)
- [dotPeek Documentation](https://www.jetbrains.com/help/decompiler/)
- [.NET Assembly Analysis](https://docs.microsoft.com/en-us/dotnet/standard/assembly/)

---

*Ovaj vodič je kreiran za ručno dekompajliranje kada automatska skripta nije dostupna.*

