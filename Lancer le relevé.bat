@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Cherche un Python qui marche (le "python" de Windows ouvre souvent juste le Microsoft Store)
set "PY="
for %%V in (313 312 311 310) do if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
if not defined PY for /f "delims=" %%P in ('py -3 -c "import sys;print(sys.executable)" 2^>nul') do set "PY=%%P"
if not defined PY for /f "delims=" %%P in ('python -c "import sys;print(sys.executable)" 2^>nul') do set "PY=%%P"
if not defined PY (
  echo Python est introuvable. Relance la ligne d'installation dans PowerShell.
  pause
  exit /b 1
)
"%PY%" -X utf8 lancer_windows.py & exit /b
