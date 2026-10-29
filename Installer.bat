@echo off
rem Guided install of Geek Magic Vibe (run once after cloning).
cd /d "%~dp0"
where python >nul 2>nul || (echo Python 3.11 or newer is required : https://www.python.org/downloads/ & pause & exit /b 1)
python setup.py
pause
