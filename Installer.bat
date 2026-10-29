@echo off
rem Installation guidee de Geek Magic Vibe (a lancer une fois apres le clonage).
cd /d "%~dp0"
where python >nul 2>nul || (echo Python 3.11 ou plus est requis : https://www.python.org/downloads/ & pause & exit /b 1)
python setup.py
pause
