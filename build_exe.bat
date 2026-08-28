@echo off
chcp 65001 > nul
echo ===================================================
echo   Crow Pack v1.0d - EXE 빌드 스크립트
echo ===================================================
echo.
if exist ".venv\Scripts\python.exe" (
    set "CROW_PYTHON=.venv\Scripts\python.exe"
) else (
    set "CROW_PYTHON="
    for /f "delims=" %%P in ('where python.exe 2^>nul') do if not defined CROW_PYTHON set "CROW_PYTHON=%%P"
    for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do if not defined CROW_PYTHON if exist "%%~fD\python.exe" set "CROW_PYTHON=%%~fD\python.exe"
    if not defined CROW_PYTHON (
        echo Python 3.10 이상을 설치하거나 .venv를 먼저 만들어 주세요.
        exit /b 1
    )
)

echo 의존성과 PyInstaller를 설치합니다...
echo.

"%CROW_PYTHON%" -m pip install -e ".[build]" || exit /b 1
"%CROW_PYTHON%" -m PyInstaller --noconfirm --clean --onedir --windowed ^
    --add-data "src/ui;src/ui" ^
    --name "CrowPack" ^
    main.py || exit /b 1

echo.
echo ===================================================
echo   빌드가 완료되었습니다! dist/CrowPack/CrowPack.exe
echo ===================================================
pause
