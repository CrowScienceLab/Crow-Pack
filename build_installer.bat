@echo off
setlocal EnableExtensions
chcp 65001 > nul
cd /d "%~dp0"

echo ===================================================
echo   Crow Pack v1.5.0 - Windows 설치본 빌드
echo ===================================================

call build_exe.bat < nul
if errorlevel 1 exit /b 1

set "CROW_ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%CROW_ISCC%" set "CROW_ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%CROW_ISCC%" set "CROW_ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%CROW_ISCC%" (
    echo Inno Setup 6을 찾을 수 없습니다.
    echo https://jrsoftware.org/isdl.php 에서 설치한 뒤 다시 실행해 주세요.
    exit /b 1
)

"%CROW_ISCC%" "installer\CrowPack.iss"
if errorlevel 1 exit /b 1

echo 설치본: release\CrowPack-v1.5.0-Setup-x64.exe
exit /b 0
