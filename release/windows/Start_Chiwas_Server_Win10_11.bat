@echo off
setlocal
cd /d "%~dp0"

if not exist "ChiwasLiquorPOS.exe" (
    echo The Django server executable is not included in this package.
    echo On Windows 10 or 11, run build_windows.bat from the project source folder first.
    pause
    exit /b 1
)

start "" "ChiwasLiquorPOS.exe"
