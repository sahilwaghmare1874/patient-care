@echo off
title Healthcare Platform Public Live Tunnel
echo ========================================================
echo   HEALTHCARE PLATFORM - PUBLIC INTERNET TUNNEL LAUNCHER
echo ========================================================
echo.
echo Starting Cloudflare Tunnel for port 3000...
echo.
.\cloudflared.exe tunnel --url http://localhost:3000
pause
