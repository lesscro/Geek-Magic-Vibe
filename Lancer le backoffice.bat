@echo off
rem Lance le backoffice GeekMagic (http://localhost:8780) puis ouvre le navigateur.
cd /d "%~dp0"
set "PYW=.venv\Scripts\pythonw.exe"
if not exist "%PYW%" set "PYW=pythonw"
powershell -NoProfile -Command "if (-not (Get-NetTCPConnection -LocalPort 8780 -State Listen -ErrorAction SilentlyContinue)) { Start-Process '%PYW%' -ArgumentList 'backoffice\server.py' -WindowStyle Hidden; Start-Sleep -Seconds 2 }"
start "" http://localhost:8780
