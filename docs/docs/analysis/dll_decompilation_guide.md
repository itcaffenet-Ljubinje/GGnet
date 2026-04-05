# DLL Dekompajliranje Vodič

Ovaj vodič objašnjava kako da dekompajliramo i analiziramo .NET DLL fajlove iz ggRock paketa.

## 📋 Pregled

Za analizu `GgRock.Api.dll` iz verzije 2289, možemo koristiti nekoliko alata:

1. **ILSpy** (preporučeno) - Open source, command-line i GUI
2. **dnSpy** - Open source, GUI
3. **dotPeek** - JetBrains, GUI

## 🛠️ Instalacija Alata

### ILSpy (Command-Line)

```bash
# Instalirati .NET SDK ako nije instaliran
# Ubuntu/Debian:
sudo apt-get install -y dotnet-sdk-8.0

# Instalirati ILSpy command-line tool
dotnet tool install -g ilspycmd

# Verifikovati instalaciju
ilspycmd --version
```

### ILSpy (GUI)

```bash
# Download from: https://github.com/icsharpcode/ILSpy/releases
# Or install via package manager:
# Ubuntu/Debian:
sudo apt-get install -y ilspy
```

### dnSpy

```bash
# Download from: https://github.com/dnSpy/dnSpy/releases
# Extract and run:
./dnSpy.exe
```

### dotPeek

```bash
# Download from: https://www.jetbrains.com/decompiler/
# Install and run
```

## 📝 Korišćenje

### Automatska Analiza (Preporučeno)

Koristiti `scripts/analyze_dll.sh`:

```bash
# Analizirati DLL iz verzije 2289
./scripts/analyze_dll.sh /path/to/ggrock_0.1.2289.2303-1_amd64/data/opt/ggrock/app/GgRock.Api.dll

# Sa custom output direktorijumom
./scripts/analyze_dll.sh /path/to/GgRock.Api.dll -o ./analysis_output

# Sa specifičnim tool-om
./scripts/analyze_dll.sh /path/to/GgRock.Api.dll -t ilspycmd
```

### Ručna Analiza

#### ILSpy Command-Line

```bash
# Dekompajlirati DLL
ilspycmd GgRock.Api.dll -o ./decompiled

# Sa progress bar-om
ilspycmd GgRock.Api.dll -o ./decompiled -p

# Samo C# kod
ilspycmd GgRock.Api.dll -o ./decompiled -lang CSharp
```

#### ILSpy GUI

1. Otvoriti ILSpy
2. File → Open → Select `GgRock.Api.dll`
3. File → Save Code → Save all files

#### dnSpy

1. Otvoriti dnSpy
2. File → Open → Select `GgRock.Api.dll`
3. File → Export to Project → Select output directory

#### dotPeek

1. Otvoriti dotPeek
2. File → Open → Select `GgRock.Api.dll`
3. File → Export to Project → Select output directory

## 🔍 Analiza Rezultata

### API Endpoint-i

Pretražiti dekompajlirani kod za API kontrolere:

```bash
# Pronaći API kontrolere
grep -r "\[Route\|\[HttpGet\|\[HttpPost" ./decompiled

# Pronaći sve endpoint-e
grep -r "public.*ActionResult\|public.*IActionResult" ./decompiled
```

### DTO Modeli

Pretražiti dekompajlirani kod za DTO modele:

```bash
# Pronaći DTO klase
grep -r "class.*Dto\|class.*Request\|class.*Response" ./decompiled

# Pronaći sve modele
grep -r "public class\|public record" ./decompiled
```

### Uporedna Analiza

```bash
# Dekompajlirati obe verzije
ilspycmd GgRock.Api.dll.2200 -o ./decompiled_2200
ilspycmd GgRock.Api.dll.2289 -o ./decompiled_2289

# Uporediti strukturu
diff -r ./decompiled_2200 ./decompiled_2289

# Uporediti API endpoint-e
diff <(grep -r "\[Route" ./decompiled_2200) <(grep -r "\[Route" ./decompiled_2289)
```

## 📊 Generisanje Izveštaja

### API Endpoint Izveštaj

```bash
# Ekstraktovati sve endpoint-e
grep -rh "\[Route\|\[HttpGet\|\[HttpPost\|\[HttpPut\|\[HttpDelete" ./decompiled > api_endpoints.txt

# Formatirati izveštaj
cat api_endpoints.txt | sort | uniq > api_endpoints_sorted.txt
```

### DTO Model Izveštaj

```bash
# Ekstraktovati sve DTO modele
grep -rh "class.*Dto\|class.*Request\|class.*Response" ./decompiled > dto_models.txt

# Formatirati izveštaj
cat dto_models.txt | sort | uniq > dto_models_sorted.txt
```

## 🎯 Preporuke

### Za Brzu Analizu

1. Koristiti `scripts/analyze_dll.sh` za automatsku analizu
2. Pregledati `api_endpoints.txt` i `dto_models.txt`
3. Fokusirati se na nove endpoint-e i modele

### Za Detaljnu Analizu

1. Dekompajlirati obe verzije (2200 i 2289)
2. Uporediti strukturu direktorijuma
3. Uporediti API kontrolere
4. Uporediti DTO modele
5. Dokumentovati sve razlike

### Za Produkciju

1. Koristiti ILSpy command-line za automatsku analizu
2. Integrisati u CI/CD pipeline
3. Generisati automatske izveštaje
4. Ažurirati dokumentaciju

## 📚 Reference

- [ILSpy Documentation](https://github.com/icsharpcode/ILSpy)
- [dnSpy Documentation](https://github.com/dnSpy/dnSpy)
- [dotPeek Documentation](https://www.jetbrains.com/help/decompiler/)
- [.NET Assembly Analysis](https://docs.microsoft.com/en-us/dotnet/standard/assembly/)

---

*Ovaj vodič je kreiran za analizu ggRock DLL fajlova u kontekstu ggNET2 projekta.*

