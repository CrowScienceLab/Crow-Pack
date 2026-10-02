@echo off
chcp 65001 > nul
setlocal

if defined CROW_PYTHON if exist "%CROW_PYTHON%" goto :python_ready
if exist ".venv\Scripts\python.exe" (
    set "CROW_PYTHON=.venv\Scripts\python.exe"
) else (
    for /f "delims=" %%P in ('py -3.12 -c "import sys; print(sys.executable)" 2^>nul') do if not defined CROW_PYTHON set "CROW_PYTHON=%%P"
)
if not defined CROW_PYTHON (
    echo Python 3.12를 찾을 수 없습니다.
    exit /b 1
)

:python_ready
if not exist "dist\CrowPack\CrowPack.exe" call build_exe.bat || exit /b 1
"%CROW_PYTHON%" tools\build_msix.py %* || exit /b 1
echo Microsoft Store 패키지: release\CrowPack-v1.5.3-Store-x64.msix
endlocal
