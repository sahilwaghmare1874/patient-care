# PatientCare - One-Click Live Internet Launcher
# Starts Django Backend, Node Reverse Proxy, and Cloudflare Live Public Tunnel

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " LAUNCHING PATIENTCARE TO THE LIVE INTERNET " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Start Django if not running
$djangoPort = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if (-not $djangoPort) {
    Write-Host "[1/3] Starting Django REST Backend on Port 8000..." -ForegroundColor Yellow
    Start-Process -FilePath "python" -ArgumentList "backend/manage.py runserver 127.0.0.1:8000" -WindowStyle Minimized
    Start-Sleep -Seconds 2
} else {
    Write-Host "[1/3] Django Backend is already running on Port 8000." -ForegroundColor Green
}

# 2. Start Node server if not running
$nodePort = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if (-not $nodePort) {
    Write-Host "[2/3] Starting Node.js Reverse Proxy on Port 3000..." -ForegroundColor Yellow
    Start-Process -FilePath "node" -ArgumentList "server.js" -WindowStyle Minimized
    Start-Sleep -Seconds 2
} else {
    Write-Host "[2/3] Node Frontend is already running on Port 3000." -ForegroundColor Green
}

# 3. Start Cloudflare Tunnel
Write-Host "[3/3] Starting Cloudflare Public HTTPS Tunnel..." -ForegroundColor Yellow
.\deployment\cloudflared.exe tunnel --url http://localhost:3000
