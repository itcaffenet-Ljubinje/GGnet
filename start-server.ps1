# GGnet Server Startup Script
# Run this from the project root directory

Write-Host "🚀 Starting GGnet Server..." -ForegroundColor Green

# Change to backend directory first
Set-Location "$PSScriptRoot\backend"

# Set environment variables (relative to backend directory)
$env:DATABASE_URL = "sqlite+aiosqlite:///./ggnet.db"
$env:REDIS_URL = ""
$env:SECRET_KEY = "dev-secret-key-change-in-production"
$env:DEBUG = "true"
$env:PYTHONPATH = "$PSScriptRoot\backend"

Write-Host "📁 Working directory: $(Get-Location)" -ForegroundColor Cyan
Write-Host "🔧 Environment:" -ForegroundColor Cyan
Write-Host "   DATABASE_URL: $env:DATABASE_URL"
Write-Host "   REDIS_URL: $env:REDIS_URL"
Write-Host "   DEBUG: $env:DEBUG"
Write-Host ""

# Start the server
Write-Host "🌐 Starting Uvicorn server on http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "📚 API Docs will be available at: http://127.0.0.1:8000/docs" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

