# 🔄 Restart Frontend - Fix NS_BINDING_ABORTED

## Problem
`NS_BINDING_ABORTED` error when loading `/src/main.tsx`

## Uzrok
Vite dev server ima stari cache ili nije reload-ovao App.test.tsx fajl.

## Rešenje

### **Korak 1: Zaustavi Vite Dev Server**
U terminalu gde radi `npm run dev`, pritisni:
```
Ctrl + C
```

### **Korak 2: Očisti Vite Cache**
```powershell
cd C:\Users\SERVER-PC\Documents\GGnet-projects\GGnet\frontend
Remove-Item -Recurse -Force node_modules\.vite
```

Ili u CMD/PowerShell:
```cmd
cd C:\Users\SERVER-PC\Documents\GGnet-projects\GGnet\frontend
rmdir /s /q node_modules\.vite
```

### **Korak 3: Restartuj Dev Server**
```powershell
npm run dev
```

### **Korak 4: Refresh Browser**
```
Ctrl + Shift + R
```

---

## Alternativa: Force Restart

Ako gornje ne radi, full clean:

```powershell
# Zaustavi dev server (Ctrl+C)

# Očisti cache i temp fajlove
Remove-Item -Recurse -Force node_modules\.vite
Remove-Item -Recurse -Force dist
Remove-Item -Recurse -Force .vite

# Reinstaliraj dependencies (opciono)
npm install

# Pokreni ponovo
npm run dev
```

---

## Šta Očekujemo

Nakon restarta, trebalo bi da vidiš:

### U Terminalu:
```
VITE v5.4.20  ready in XXX ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

### U Browser-u (http://localhost:3000):
- Tamna pozadina
- Veliki plavi tekst "REACT WORKS!"
- Poruke o Backend-u i Login-u

### U Console-u (F12):
```
=== MAIN.TSX EXECUTING ===
Root element: HTMLDivElement
Root element found, creating React root...
=== APP TEST RENDERING ===
React root created and rendered!
[vite] connected.
```

---

## Ako Problem Perzistira

Verovatno je **browser cache** problem. Probaj:

### Option 1: Inkognito Mode
```
Ctrl + Shift + N (Chrome)
Ctrl + Shift + P (Firefox)
```
Pa otvori: http://localhost:3000

### Option 2: Clear Browser Cache
```
F12 → Network tab → Disable cache (checkbox)
```
Pa refresh.

### Option 3: Different Port
Promeni port u `vite.config.ts`:
```typescript
server: {
  port: 3001,  // Umesto 3000
  // ...
}
```

---

## Status Check

Da proveriš da li Vite radi:
```powershell
curl http://localhost:3000
```

Trebalo bi da vrati HTML sa `<div id="root"></div>`.

---

**URADI OVO SADA:**

1. **Zaustavi** Vite dev server (Ctrl+C u terminalu)
2. **Obriši** cache: `rmdir /s /q node_modules\.vite`
3. **Pokreni** ponovo: `npm run dev`
4. **Refresh** browser: Ctrl+Shift+R

**I javi mi šta se dešava!** 🔍

