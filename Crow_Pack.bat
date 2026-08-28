@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Crow Pack v1.0K
cd /d "%~dp0"

if exist "CrowPack\CrowPack.exe" (
    start "" "CrowPack\CrowPack.exe" %*
    exit /b 0
)

if exist "dist\CrowPack\CrowPack.exe" (
    start "" "dist\CrowPack\CrowPack.exe" %*
    exit /b 0
)

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" main.py %*
    exit /b 0
)

set "CROW_PYTHONW="
for /f "delims=" %%P in ('where pythonw.exe 2^>nul') do if not defined CROW_PYTHONW set "CROW_PYTHONW=%%P"
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do if not defined CROW_PYTHONW if exist "%%~fD\pythonw.exe" set "CROW_PYTHONW=%%~fD\pythonw.exe"

if defined CROW_PYTHONW (
    start "" "!CROW_PYTHONW!" main.py %*
    exit /b 0
)

echo Python may be installed but missing from the py launcher registry.
echo Use the CrowPack.exe release or create a local .venv.
pause
exit /b 1
