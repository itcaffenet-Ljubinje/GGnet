# 🚀 GGnet - Final Complete Startup Guide

## 🎯 Current Status

✅ Backend: WORKING (tested with curl)  
✅ Login API: WORKING (admin/admin123 returns 200 OK)  
✅ Admin User: EXISTS in database  
❌ Frontend: HMR WebSocket issues  

---

## 🔧 Complete Startup Procedure

### **TERMINAL 1 - Backend**

```powershell
# Navigate to backend
cd C:\Users\SERVER-PC\Documents\GGnet-projects\GGnet\backend

# Activate virtual environment
.\venv\Scripts\activate

# Start backend server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Test:**
```powershell
curl http://127.0.0.1:8000/health
# Should return: {"status":"healthy",...}
```

---

### **TERMINAL 2 - Frontend**

```powershell
# Navigate to frontend
cd C:\Users\SERVER-PC\Documents\GGnet-projects\GGnet\frontend

# Kill any existing Node processes
taskkill /F /IM node.exe 2>nul

# Remove cache
rmdir /s /q node_modules\.vite 2>nul
rmdir /s /q dist 2>nul

# Start dev server
npm run dev
```

**Expected Output:**
```
  VITE v5.4.20  ready in 1234 ms

  ➜  Local:   http://127.0.0.1:3000/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**Open Browser:**
```
http://127.0.0.1:3000
```

---

## 🐛 Troubleshooting

### Problem: WebSocket Connection Failed

```
[vite] failed to connect to websocket
```

**Solution 1: Check if Vite is actually running**
```powershell
netstat -ano | findstr :3000
```

Should show process listening on port 3000.

**Solution 2: Use different port**

Edit `frontend/vite.config.ts`:
```typescript
server: {
  port: 5173,  // Different port
  // ...
}
```

Then restart:
```powershell
npm run dev
```

And open: `http://localhost:5173`

**Solution 3: Disable HMR**

Edit `frontend/vite.config.ts`:
```typescript
server: {
  hmr: false,  // Disable HMR
  // ...
}
```

You'll need to manually refresh (Ctrl+R) after code changes.

---

### Problem: Blank White Page

**Check Console (F12):**

1. **If you see:**
   ```
   NS_BINDING_ABORTED
   Loading failed for module
   ```
   → **Solution:** Clear cache and restart Vite

2. **If you see:**
   ```
   Uncaught Error: ...
   ```
   → **Solution:** Copy the exact error and fix the component

3. **If you see:**
   ```
   [vite] connected.
   ```
   → **Good!** HMR is working

**Check Elements (F12 → Elements tab):**

```html
<div id="root">
  <!-- Should have content here -->
</div>
```

If `#root` is empty → React not rendering.

**Quick Test:**

Open Console and type:
```javascript
document.getElementById('root').innerHTML
```

- If empty (`""`) → React crashed
- If has content → CSS problem

---

### Problem: React Not Rendering

**Check for errors in:**

1. **main.tsx** - Entry point
2. **App.tsx** - Root component  
3. **authStore.ts** - State management
4. **LoginPage.simple.tsx** - First rendered page

**Run type check:**
```powershell
cd frontend
npm run type-check
```

Should return no errors.

---

## 📋 Simplified Stack (Current)

To avoid complex dependencies, we're using:

- ✅ **LoginPage.simple.tsx** - No react-hook-form
- ✅ **Inline styles** - No Tailwind complexity
- ✅ **esbuild JSX** - No @vitejs/plugin-react
- ✅ **Direct useState** - No complex hooks

---

## 🎯 Expected Login Screen

You should see:

```
┌────────────────────────────────────┐
│  Blue gradient background          │
│                                    │
│      ┌──────────────┐              │
│      │   🔵 GG      │              │
│      └──────────────┘              │
│                                    │
│   Sign in to GGnet                 │
│                                    │
│   Username: [admin        ]        │
│   Password: [admin123     ]        │
│                                    │
│        [ Sign In ]                 │
│                                    │
│   Default: admin / admin123        │
└────────────────────────────────────┘
```

---

## ✅ Verification Checklist

After starting both terminals:

- [ ] Backend health check returns 200 OK
- [ ] Vite shows "ready in XXX ms"  
- [ ] Browser shows login page (not blank)
- [ ] Console shows no red errors
- [ ] Can type in username/password fields
- [ ] Click "Sign In" triggers API call
- [ ] After login, redirects to Dashboard

---

## 🚀 Quick Start Commands

**One-liner for Backend:**
```powershell
cd C:\Users\SERVER-PC\Documents\GGnet-projects\GGnet\backend; .\venv\Scripts\activate; uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**One-liner for Frontend:**
```powershell
cd C:\Users\SERVER-PC\Documents\GGnet-projects\GGnet\frontend; taskkill /F /IM node.exe 2>nul; npm run dev
```

---

## 📞 If Still Not Working

1. **Take screenshot of:**
   - Browser window
   - Console (F12)
   - Terminal output

2. **Copy from Console:**
   - All red errors
   - Network tab (failed requests)

3. **Check:**
   ```powershell
   # Is Vite running?
   netstat -ano | findstr :3000
   
   # Is backend running?
   netstat -ano | findstr :8000
   ```

---

## 🎊 Success Indicators

✅ Terminal shows: `VITE v5.4.20 ready`  
✅ Terminal shows: `Local: http://127.0.0.1:3000/`  
✅ Browser shows: Login form with blue background  
✅ Console shows: `[vite] connected.`  
✅ No red errors in console  

**Then you're ready to login with admin/admin123!** 🚀

---

**Current Time:** Please execute these commands NOW in 2 separate terminals and tell me what you see!

