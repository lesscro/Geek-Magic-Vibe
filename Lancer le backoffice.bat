@echo off
rem Lance le backoffice GeekMagic (http://localhost:8780) puis ouvre le navigateur.
cd /d "%~dp0"
powershell -NoProfile -Command "if (-not (Get-NetTCPConnection -LocalPort 8780 -State Listen -ErrorAction SilentlyContinue)) { Start-Process pythonw -ArgumentList 'backoffice\server.py' -WindowStyle Hidden; Start-Sleep -Seconds 2 }"
start "" http://localhost:8780
