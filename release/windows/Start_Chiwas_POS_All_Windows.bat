@echo off
setlocal
cd /d "%~dp0"

if not exist "portable-pos\index.html" (
    echo The offline POS files are missing. Extract the complete Windows package.
    pause
    exit /b 1
)

where powershell.exe >nul 2>nul
if errorlevel 1 (
    echo Windows PowerShell is required. It is included with Windows 7 and newer.
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start_Offline_Pos.ps1"
if errorlevel 1 (
    echo The local POS could not be started.
    pause
)
