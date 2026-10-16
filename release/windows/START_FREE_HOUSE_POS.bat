@echo off
setlocal
title FREE HOUSE BAR & RESTAURANT POS

if not defined LOCALAPPDATA (
    echo Windows did not provide LOCALAPPDATA. Cannot locate the app data folder.
    pause
    exit /b 1
)

set "CHIWAS_DATA_DIR=%LOCALAPPDATA%\FREE HOUSE POS"
if not exist "%CHIWAS_DATA_DIR%\venv\Scripts\python.exe" (
    echo Run SETUP_FREE_HOUSE_POS.bat first to install the Django requirements.
    pause
    exit /b 1
)

"%CHIWAS_DATA_DIR%\venv\Scripts\python.exe" "%~dp0run_django_pos.py"
if errorlevel 1 (
    echo.
    echo FREE HOUSE POS stopped with an error.
    pause
    exit /b 1
)
