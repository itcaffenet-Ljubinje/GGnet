# Frontend Troubleshooting - Blank White Screen

## Problem
Frontend se učitava ali prikazuje prazan beli ekran sa "Read localhost" u donjem uglu.

## Moguće Uzroke

### 1. CSS Ne Učitava Pravilno
- **Simptom:** Beli ekran, nema stilova
- **Rešenje:** ✅ Dodao `dark` klasu na `document.documentElement`
- **Rešenje:** ✅ Dodao eksplicitne stilove za `html`, `body`, `#root`

### 2. React Ne Renderuje
- **Simptom:** `#root` je prazan
- **Provera:** Otvori Developer Console (F12) → Elements tab → Proveri da li `<div id="root">` ima sadržaj

### 3. JavaScript Greška
- **Simptom:** Greška u konzoli sprečava rendering
- **Provera:** Otvori Developer Console (F12) → Console tab → Proveri za crvene greške

### 4. Routing Problem
- **Simptom:** URL nije prepoznat
- **Provera:** Proveri da li URL je `http://localhost:3000` ili `http://localhost:3000/`

## Kako Testirati

### Korak 1: Proveri Console
```
F12 → Console tab
```
Traži:
- ❌ Crvene greške (errors)
- ⚠️ Žuta upozorenja (warnings - OK)
- ✅ "[vite] connected" (dobro)

### Korak 2: Proveri Network
```
F12 → Network tab → Reload stranicu (Ctrl+R)
```
Traži:
- ✅ `/src/main.tsx` → 200 OK
- ✅ `/src/index.css` → 200 OK
- ✅ `/src/App.tsx` → 200 OK

### Korak 3: Proveri Elements
```
F12 → Elements tab
```
Pronađi:
```html
<div id="root">
  <!-- Trebalo bi biti sadržaja ovde -->
</div>
```

Ako je prazan:
```html
<div id="root"></div>  <!-- ❌ BAD -->
```

Trebalo bi da bude:
```html
<div id="root">
  <div>
    <div class="flex h-screen overflow-hidden">
      <!-- App content -->
    </div>
  </div>
</div>  <!-- ✅ GOOD -->
```

### Korak 4: Hard Refresh
```
Ctrl + Shift + R (ili Ctrl + F5)
```
Ovo briše cache i reload-uje sve.

### Korak 5: Proveri Tailwind
Otvori Console i kucaj:
```javascript
getComputedStyle(document.body).backgroundColor
```
Trebalo bi da vrati nešto kao: `"rgb(17, 24, 39)"` (tamna boja)

Ako vraća `"rgb(255, 255, 255)"` → CSS se ne učitava!

## Privremeno Rešenje (Test)

Ako ništa ne pomaže, hajde da napravim minimal test file.

**frontend/public/test.html:**
```html
<!DOCTYPE html>
<html>
<head>
  <title>Test</title>
  <style>
    body {
      background: #1a1a1a;
      color: #fff;
      font-family: Arial;
      padding: 50px;
    }
  </style>
</head>
<body>
  <h1>TEST - If you see this, static files work!</h1>
  <p>Now check http://localhost:3000 again</p>
</body>
</html>
```

Pristupi: http://localhost:3000/test.html

Ako vidiš "TEST" poruku → Vite radi, problem je u React app-u
Ako i dalje vidiš beli ekran → Vite nije pravilno pokrenut

## Šta Sam Promenio

### 1. `frontend/src/main.tsx`
```typescript
// Dodao PRE render-a:
document.documentElement.classList.add('dark')

// Uklonio nested div wrapper:
<App />  // Umesto <div className="dark"><App /></div>
```

### 2. `frontend/src/index.css`
```css
html,
body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  background: dark gradient;
}

#root {
  min-height: 100vh;
  width: 100%;
}
```

## Ako I Dalje Ne Radi

**Opcija 1: Restart Vite Dev Server**
```powershell
# Ctrl+C u terminalu gde radi `npm run dev`
# Pa ponovo:
npm run dev
```

**Opcija 2: Clear Vite Cache**
```powershell
# Zaustavi dev server
# Obriši cache:
rm -rf node_modules/.vite
# Pokreni ponovo:
npm run dev
```

**Opcija 3: Full Clean Install**
```powershell
rm -rf node_modules
rm -rf node_modules/.vite
npm install
npm run dev
```

## Debug Output

Kada otvoriš stranicu, u Console-u bi trebalo da vidiš:
```
[vite] connecting...
[vite] connected.
```

Ako vidiš crvenu grešku, kopiraj je i pošalji mi!

## Expected Behavior

Trebalo bi da vidiš:
- ✅ Tamni gradient background (sivo-crni)
- ✅ Login formu (ako nisi ulogovan)
- ✅ Dashboard (ako si ulogovan)
- ✅ Sidebar navigation
- ✅ Header sa username-om

## Current Status

✅ Backend: Running (port 8000)
✅ Frontend Dev Server: Running (port 3000)
✅ All modules loaded
⏳ Rendering: FIXING...

---

**Refresh stranicu sada (Ctrl+Shift+R) i reci mi šta vidiš!**

