@echo off
chcp 65001 > nul
echo ===================================================
echo   Crow Pack v1.5.0 - EXE 빌드 스크립트
echo ===================================================
echo.
if defined CROW_PYTHON if exist "%CROW_PYTHON%" goto :python_ready

if exist ".venv\Scripts\python.exe" (
    set "CROW_PYTHON=.venv\Scripts\python.exe"
) else (
    set "CROW_PYTHON="
    for /f "delims=" %%P in ('py -3.12 -c "import sys; print(sys.executable)" 2^>nul') do if not defined CROW_PYTHON set "CROW_PYTHON=%%P"
    if not defined CROW_PYTHON if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "CROW_PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    if not defined CROW_PYTHON (
        echo 설치본 빌드에는 Python 3.12 또는 Python 3.12 기반 .venv가 필요합니다.
        exit /b 1
    )
)

:python_ready

echo 의존성과 PyInstaller를 설치합니다...
echo.

"%CROW_PYTHON%" -m pip install -e ".[build]" || exit /b 1
"%CROW_PYTHON%" -m PyInstaller --noconfirm --clean --onedir --windowed ^
    --add-data "src/ui;src/ui" ^
    --add-data "assets;assets" ^
    --icon "assets/crow_pack.ico" ^
    --version-file "installer/version_info.txt" ^
    --name "CrowPack" ^
    main.py || exit /b 1

rem 개발 도구 PATH의 타사 ICU가 잘못 수집되면 Windows 시스템 ICU와 충돌한다.
if exist "dist\CrowPack\_internal\icuuc.dll" del /q "dist\CrowPack\_internal\icuuc.dll"
if exist "dist\CrowPack\_internal\icudt78.dll" del /q "dist\CrowPack\_internal\icudt78.dll"

echo.
echo ===================================================
echo   빌드가 완료되었습니다! dist/CrowPack/CrowPack.exe
echo ===================================================
exit /b 0
