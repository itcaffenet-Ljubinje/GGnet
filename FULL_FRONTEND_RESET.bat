@echo off
echo ========================================
echo  FULL FRONTEND CLEAN INSTALL
echo ========================================
echo.

cd /d C:\Users\SERVER-PC\Documents\GGnet-projects\GGnet\frontend

echo [1/5] Stopping any running processes...
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

echo [2/5] Removing node_modules...
if exist node_modules rmdir /s /q node_modules
if exist .vite rmdir /s /q .vite
if exist dist rmdir /s /q dist

echo [3/5] Removing package-lock.json...
if exist package-lock.json del /f package-lock.json

echo [4/5] Installing fresh dependencies...
call npm install

echo [5/5] Starting dev server...
echo.
echo ========================================
echo  Starting Vite Dev Server
echo ========================================
echo.
call npm run dev

pause

