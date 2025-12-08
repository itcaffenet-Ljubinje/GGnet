# GGnet Frontend Startup Script
# Run this from the project root directory

Write-Host "🚀 Starting GGnet Frontend..." -ForegroundColor Green

# Change to frontend directory
Set-Location "$PSScriptRoot\frontend"

Write-Host "📁 Working directory: $(Get-Location)" -ForegroundColor Cyan
Write-Host ""

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install
    Write-Host ""
}

# Start the development server
Write-Host "🌐 Starting Vite development server on http://127.0.0.1:3000" -ForegroundColor Yellow
Write-Host "📚 Backend API should be running on: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host ""

npm run dev




